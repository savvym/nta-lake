---
change_id: tree-nested-domain-20260520
target: services/commit.py + routers/commits.py（v2 修复提交 dc10a7d）
target_version: 2
review_version: 2
reviewer: claude-agent:tree-nested-domain-20260520-stage4-reviewer-v2
reviewed_at: 2026-05-20T00:00:00Z
verdict: REVISION REQUIRED
---

# Code Review v2

## §1 v1 MUST FIX 复检表

| # | v1 issue | 状态 | 证据 |
|---|---|---|---|
| MUST FIX-1 | N+1 查询：`_expand_tree_recursive` 每节点单独 SELECT | RESOLVED（含新引入 bug，见 §2） | 改为 BFS；`while pending` 循环内只做一次 `SELECT TreeORM WHERE hash IN (hashes_this_layer)`；N+1 模式已消除。但循环迭代键有重复问题（见下） |
| MUST FIX-2 | `_validate_tree_paths` 不拒 `entry_type="tree"` + 合法 mode | RESOLVED | `services/commit.py:88` 第一条 guard `if e.entry_type != "blob": raise ValueError(…)` 在所有 name 校验之前触发；`_normalize_to_nested` 内部冗余 guard 已移除（line 145 注释确认）；mode==16384 dead code 检查已随之删除（diff 证实）；唯一校验边界语义完整 |

**v1 SHOULD FIX 跟踪**

| # | v1 SHOULD FIX | 是否处理 |
|---|---|---|
| SHOULD FIX-1 | 递归深度保护（无 max_depth） | RESOLVED：新增 `_MAX_TREE_RECURSION_DEPTH = 64`，在 BFS while 循环入口 `depth >= 64` 时 raise HTTP 400 |
| SHOULD FIX-2 | deselect 3 个 pre-existing flake 无客观验证材料 | NOT FIXED：`coding_report_v1.md` 仍未补证据；v2 提交未触及此点（deferred 于 stage 5/8）；本轮 reviewer 维持原判，不升级 MUST FIX |
| SHOULD FIX-3 | `head_commit: TBD` 未补填 | NOT FIXED：`coding_report_v1.md` frontmatter `head_commit` 仍为 TBD；v2 实际 commit 为 `dc10a7d`；同样 deferred；维持 SHOULD FIX |

---

## §2 v2 新引入审查

### 2.1 BFS batch 正确性：`_expand_tree_recursive`（commits.py:236-296）

#### 2.1.1 MUST FIX：外层循环迭代含重复 hash 的 `hashes_this_layer`，导致重复输出

**位置**：`routers/commits.py:258-294`，`while pending` 循环体内

**问题描述**：

```python
hashes_this_layer = [h for h, _ in pending]         # 可含重复 hash
prefix_map: dict[str, list[str]] = {}
for h, p in pending:
    prefix_map.setdefault(h, []).append(p)           # hash → 所有 prefix 的映射

...

for h in hashes_this_layer:                         # ← BUG：按列表迭代，含重复
    tree = tree_by_hash.get(h)
    ...
    for prefix in prefix_map[h]:                    # prefix_map[h] 存全部 prefix
        for e in sorted_entries:
            ...emit...
```

当同层两个（或多个）子目录的**内容完全相同**时，`_normalize_to_nested` 对这些目录各自走独立的 trie 节点，但 `_walk` 对相同内容的节点返回**相同 `tree_hash`**（CAS 语义）。

例：root 包含 `assets/logo.png` 和 `backup/logo.png`（同文件，同 target_hash）：

- `_walk(assets_node)` = `tree_hash_X`
- `_walk(backup_node)` = `tree_hash_X`（内容等价 → hash 相同）
- root entries：`[assets/ → tree_hash_X, backup/ → tree_hash_X]`

进入下一层 BFS 时：

```
pending = [(tree_hash_X, "assets/"), (tree_hash_X, "backup/")]
hashes_this_layer = ["tree_hash_X", "tree_hash_X"]   # 重复！
prefix_map = {"tree_hash_X": ["assets/", "backup/"]}
```

外层 `for h in hashes_this_layer` 对 `"tree_hash_X"` 迭代**两次**，每次都处理 `prefix_map["tree_hash_X"]`（含两个 prefix），共输出 4 条记录：

```
assets/logo.png  (第 1 次迭代，prefix=assets/)
backup/logo.png  (第 1 次迭代，prefix=backup/)
assets/logo.png  (第 2 次迭代，prefix=assets/)  ← 重复
backup/logo.png  (第 2 次迭代，prefix=backup/)  ← 重复
```

此 bug 具有**级联效应**：若下层 `next_pending` 也接收了重复对，后续层的重复倍数持续乘积式增长。

**影响**：`GET /tree/{commit_hash}?recursive=True` 对含"等内容子目录"的提交返回**含重复条目的错误响应**，违反 spec AC-8（recursive expand 语义正确性）。这是现实场景（ML 数据集中 train/val 结构相同时极为常见）。

**建议修法**（最小改动）：

```python
# 把 `for h in hashes_this_layer:` 替换为：
for h, prefixes in prefix_map.items():
    tree = tree_by_hash.get(h)
    if tree is None:
        continue
    sorted_entries = sorted(tree.entries, key=lambda x: x.position)
    for prefix in prefixes:
        for e in sorted_entries:
            ...
```

同时 `hashes_this_layer` 的构建可改为去重后再传给 SQL `IN`（虽然重复 hash 在 SQL `IN` 里无害，但语义更清晰）：

```python
hashes_this_layer = list(dict.fromkeys(h for h, _ in pending))  # 保序去重
```

#### 2.1.2 PASS：`_MAX_TREE_RECURSION_DEPTH = 64` 触发条件合理

`depth` 从 0 起，每轮 BFS 处理一"层" tree 后 `depth += 1`。`depth >= 64` 时拒绝，意即成功处理至多 64 层 tree（对应 entry path 最多 64 个 `/` 分隔段）。正常代码仓库 / ML 数据集嵌套深度 10–20 层，64 层绰绰有余，不会误伤合理用例。PASS。

#### 2.1.3 PASS：entry_type guard 顺序够早

`_validate_tree_paths` 第一条 for 循环体内，`if e.entry_type != "blob"` 在 `if name == ""` 等所有 name 校验**之前**（代码行 88-93 vs 94 起）。校验边界清晰，对 `entry_type="tree"` 的非法输入第一时间 ValueError。PASS。

#### 2.1.4 PASS：移除 `_normalize` 内部 entry_type 检查后安全性

`_normalize_to_nested` 调用前必须经过 `_validate_tree_paths`（`create_commit` 步骤 2 第 295-296 行保证顺序）。两函数均在同一 try/except 块内。`_normalize` 内部删除冗余 guard 后，信任链来源唯一且上游可靠。PASS。

#### 2.1.5 PASS：移除 `mode==16384` dead code 合理

原 dead code：`if e.entry_type == "tree" and e.mode != _DIR_MODE: raise ValueError(…)`。v2 在 `_validate_tree_paths` 顶部加 `entry_type != "blob"` guard 后，`entry_type=="tree"` 的 entry **永远不会到达**原 mode check 位置（ValueError 在 line 88-93 已抛）。删除此 dead code 合理，降低代码混淆。PASS。

### 2.2 本地 import 问题（继承 v1 + v2 新增）

`_load_subtree_entries`（line 220）和 `_expand_tree_recursive`（line 246）各有一个 `from sqlalchemy import select` 局部 import。v2 在修改 `_expand_tree_recursive` 时新增了后者，使局部 import 由 1 处增至 2 处，v1 的 NICE TO HAVE-1 问题加重。Python import 系统有模块缓存，无运行时性能影响，但与项目同文件的 `from sqlalchemy.orm import selectinload`（module-level）风格不一致。维持 NICE TO HAVE 级别，不升级。

### 2.3 根节点二次 SELECT（继承 v1 NICE TO HAVE-2，未加重）

`get_tree` 在 `recursive=True` 时调用 `_expand_tree_recursive(session, repo.id, tree.hash)`，内部第一轮 BFS 对根 hash 再做一次 SELECT，而 `CommitService.get_tree_by_commit` 已通过 `selectinload` 把根 tree 的 entries 拉入内存。冗余根节点查询未变，维持 NICE TO HAVE。

---

## §3 检查清单结论（v2 artifact 模式）

| 条目 | 状态 | 说明 |
|---|---|---|
| v1 MUST FIX-1（N+1）已修 | PASS | BFS batch 逻辑消除 N+1；一层一次 IN 查询 |
| v1 MUST FIX-2（validate 边界）已修 | PASS | entry_type guard 位置正确，移除 normalize 冗余，删除 dead code |
| v1 SHOULD FIX-1（深度保护）已修 | PASS | `_MAX_TREE_RECURSION_DEPTH=64` 逻辑正确 |
| BFS 重复 hash 迭代 | FAIL | 见 §2.1.1；正确性 bug，MUST FIX |
| BFS prefix_map 构建 | PASS | `setdefault` 逻辑正确，多 prefix 归并无误 |
| 深度触发条件合理性 | PASS | 不误伤合理深度（64 层足够） |
| guard 顺序（在 name 校验前） | PASS | entry_type guard 在 line 88，name 空串检查在 line 94 |
| 移除 _normalize guard 后安全性 | PASS | 调用链保证，信任来源唯一 |
| dead mode check 删除合理性 | PASS | 代码已不可达，删除正确 |
| coding_report head_commit | FAIL（延续）| 仍为 TBD；实际为 dc10a7d（SHOULD FIX） |
| pre-existing flake deselect 证据 | FAIL（延续）| 未补，维持 SHOULD FIX |

---

## 问题列表

### MUST FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| MUST FIX-1 | `routers/commits.py:274`，`for h in hashes_this_layer:` | 外层循环遍历含重复 hash 的 list，而 prefix_map 已将同 hash 的所有 prefix 聚合；每次重复 h 都完整处理全部 prefix → 输出重复条目（两同内容目录 → 输出翻倍；多层级联倍增）。违反 recursive expand 正确性（spec AC-8）。 | 将 `for h in hashes_this_layer:` 改为 `for h, prefixes in prefix_map.items():`，内层 `for prefix in prefix_map[h]:` 改为 `for prefix in prefixes:`；可选：`hashes_this_layer` 构建时去重后传 SQL `IN`（语义更清晰，功能无差异）。 |

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| SHOULD FIX-1 | `coding_report_v1.md` frontmatter `head_commit` | 仍为 `TBD（commit 后填）`；v2 fix commit 为 `dc10a7d`。按 coding-style §4.0 应记录阶段最新 commit SHA。 | 将 `head_commit` 改为 `dc10a7d`；并在 summary.md coding 阶段行补记同 SHA。 |
| SHOULD FIX-2 | `coding_report_v1.md` "偏离 spec" 节 | pre-existing flake 3 个的 deselect 理由仍为 generator 自述，无客观验证材料（main baseline 跑同 3 个用例输出）。 | 补充 `git stash` 回到 main 跑 `pytest -k test_f_… test_g_… test_h_…` 的输出片段，证明 main 上同样失败。 |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| NICE TO HAVE-1 | `routers/commits.py:220,246` | v2 新增第 2 处 `from sqlalchemy import select` 局部 import；累计 2 处，与 module-level `from sqlalchemy.orm import selectinload` 风格不一致。 | 将两处局部 import 移至 `commits.py` 模块顶部，与 `selectinload` 放一起。 |
| NICE TO HAVE-2 | `routers/commits.py:319` `get_tree` | `recursive=True` 时调 `_expand_tree_recursive(session, repo.id, tree.hash)` 对根 tree 再做 SELECT，而 `get_tree_by_commit` 已 selectinload 预加载根节点 entries，冗余一次查询。 | 可将根节点 entries 直接传入 BFS 初始层，只对子 tree 做 IN 批查；或留 NICE TO HAVE 合并到后续性能优化。 |

---

## Verdict

**REVISION REQUIRED**

v1 两条 MUST FIX 均已真实修复（N+1 → BFS batch；validate 边界统一），但 v2 新引入一条 MUST FIX：

**MUST FIX-1（BFS 重复 hash 迭代）**：当同层出现相同 `tree_hash` 的多个子目录（ML 数据集中相同结构 train/val/test 分割极为常见），`hashes_this_layer` 含重复 hash，外层 `for h in hashes_this_layer` 对每个重复迭代一次，而 `prefix_map[h]` 每次均返回全部 prefix → 输出条目成倍重复。API 返回错误结果，违反 recursive expand 正确性。修法简洁（3 行改动），不影响非重复 hash 场景。

---

## 后续指引

**Generator 修 v3 自查（MUST FIX-1）**

```bash
# 验证修法：确认外层循环改为 prefix_map.items()
grep -n "for h" apps/api/dataplat_api/routers/commits.py | grep -v "hashes_this_layer"

# 单元测试自查（待 stage 5 写测试时必须覆盖）：
# 构造 root 含两个同内容子目录的 commit，调用 recursive expand，
# 断言输出 entry 数量 == 2（dir_a/file.txt + dir_b/file.txt），无重复
cd apps/api && uv run python -c "
# 人工 trace：pending 中同 hash 出现 2 次，用修复后的 prefix_map.items() 迭代
# 期望：每个 hash 只处理一次，各 prefix 输出一条，共 2 条，不重复
print('human trace: prefix_map.items() iteration deduplicated correctly')
"

# 全量 lint 不回退
uv run ruff check apps/api packages/core worker/src
uv run mypy apps/api/dataplat_api packages/core/src worker/src

# SHOULD FIX-1: head_commit 已补填
grep "head_commit" .harness/changes/tree-nested-domain-20260520/coding/coding_report_v1.md
# 期望：不再是 TBD
```

APPROVED → 进入 stage 5 单测（test_tree_nested.py）；**MUST FIX-1 须在单测覆盖前修复**，否则单测阶段无法验证正确语义。
