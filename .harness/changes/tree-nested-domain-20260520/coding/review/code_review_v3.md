---
change_id: tree-nested-domain-20260520
target: routers/commits.py（_expand_tree_recursive，v3 修复提交）
target_version: 3
review_version: 3
reviewer: claude-agent:tree-nested-domain-20260520-stage4-reviewer-v3
reviewed_at: 2026-05-20T00:00:00Z
verdict: APPROVED
---

# Code Review v3

## §1 v2 MUST FIX 复检表

| # | v2 issue | 状态 | 证据 |
|---|---|---|---|
| MUST FIX-1 | `for h in hashes_this_layer:` 外层循环遍历含重复 hash 的 list，`prefix_map[h]` 每次返回全部 prefix → 输出膨胀 | **RESOLVED** | `commits.py:275`：外层循环已改为 `for h, prefixes in prefix_map.items()`；`hashes_this_layer` 变量在 while 循环体内**完全消失**（`prefix_map.keys()` 直接传入 SQL IN）；`prefix_map.items()` 每个 hash 恰好迭代一次，内层 `for prefix in prefixes:` 覆盖该 hash 的全部前缀，无重复。bug 根因已彻底消除。 |

**v2 SHOULD FIX 跟踪**

| # | v2 SHOULD FIX | 是否处理 |
|---|---|---|
| SHOULD FIX-1 | `coding_report_v1.md` `head_commit` 仍为 TBD | 本轮未复查（不在 v3 修复范围内）；维持 SHOULD FIX |
| SHOULD FIX-2 | pre-existing flake deselect 无客观验证材料 | 同上；维持 SHOULD FIX |

---

## §2 v3 修复代码逐行核查

### 2.1 核心修复正确性（`commits.py:252-295`）

```
while pending:
    if depth >= _MAX_TREE_RECURSION_DEPTH: raise HTTP 400   # 深度保护不变
    prefix_map: dict[str, list[str]] = {}
    for h, p in pending:
        prefix_map.setdefault(h, []).append(p)              # hash → [prefix...] 聚合
    stmt = select(TreeORM).where(
        TreeORM.hash.in_(list(prefix_map.keys())),           # unique keys，无重复 SELECT
        ...
    )
    ...
    for h, prefixes in prefix_map.items():                   # ← 修复点：dict 迭代保证每 hash 恰好一次
        tree = tree_by_hash.get(h)
        if tree is None: continue
        sorted_entries = sorted(tree.entries, key=lambda x: x.position)
        for prefix in prefixes:                              # 覆盖该 hash 的全部前缀
            for e in sorted_entries:
                ...emit...
```

**正确性验证（人工 trace）**：

场景：root 含 `assets/` → `tree_X`，`backup/` → `tree_X`（同内容，同 hash）

- `pending = [(tree_X, "assets/"), (tree_X, "backup/")]`
- `prefix_map = {"tree_X": ["assets/", "backup/"]}`
- SQL IN：`hash IN (tree_X)` — 仅查一次，无冗余
- `for h, prefixes in prefix_map.items()` — `tree_X` 只处理一次
  - `for prefix in ["assets/", "backup/"]` — 两个前缀各生成一组 entries
  - 共输出 2 条 `assets/logo.png` + `backup/logo.png`，无重复

v2 描述的"4 条记录"（翻倍）问题不再出现。PASS。

### 2.2 `hashes_this_layer` 变量已完全移除

v2 bug 的载体 `hashes_this_layer` 变量在修复后的 while 循环体内**不存在**；SQL IN 直接使用 `list(prefix_map.keys())`，语义更清晰。v2 §2.1.1 中提到"可选：去重后传 SQL IN"的优化已顺带实现（`dict.keys()` 天然无重复）。PASS。

### 2.3 其余逻辑未引入新问题

- 深度保护（line 253-257）：`_MAX_TREE_RECURSION_DEPTH = 64`，逻辑不变，PASS。
- `next_pending` 追加（line 284）：仍为 `(e.target_hash, f"{full_name}/")`，正确。
- `depth += 1`（line 295）：位置不变，每 BFS 层递增一次，PASS。
- `_load_subtree_entries` 局部 import（line 220）和 `_expand_tree_recursive` 局部 import（line 246）：未变动，维持 NICE TO HAVE-1（不阻塞）。

---

## §3 检查清单结论（v3 artifact 模式）

| 条目 | 状态 | 说明 |
|---|---|---|
| v2 MUST FIX-1（BFS 重复 hash 迭代）已修 | PASS | `prefix_map.items()` 迭代，每 hash 恰好一次，输出无膨胀 |
| `hashes_this_layer` 重复变量已消除 | PASS | 变量完全移除，SQL IN 直接用 `prefix_map.keys()` |
| 同内容子目录场景人工 trace 正确 | PASS | 见 §2.1 trace |
| 深度保护未被误改 | PASS | 逻辑完整 |
| 未引入新 MUST FIX | PASS | 逐行核查无新问题 |
| coding_report head_commit | FAIL（延续）| 维持 SHOULD FIX |
| pre-existing flake deselect 证据 | FAIL（延续）| 维持 SHOULD FIX |

---

## 问题列表

### MUST FIX

_无。_

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| SHOULD FIX-1 | `coding_report_v1.md` frontmatter `head_commit` | 仍为 `TBD`；按 coding-style §4.0 应记录最新 commit SHA。 | 补填实际 commit SHA；在 `summary.md` coding 阶段行同步。 |
| SHOULD FIX-2 | `coding_report_v1.md` 偏离 spec 节 | pre-existing flake 3 个的 deselect 理由无客观验证材料。 | 补充 main baseline 跑同 3 个用例的 pytest 输出片段证明 main 同样失败。 |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| NICE TO HAVE-1 | `commits.py:220,246` | 2 处 `from sqlalchemy import select` 局部 import，与 module-level `selectinload` 风格不一致。 | 移至模块顶部，与 `selectinload` 合并。 |
| NICE TO HAVE-2 | `commits.py:319` `get_tree` | `recursive=True` 时对根 tree 仍有冗余 SELECT（`get_tree_by_commit` 已 selectinload 根节点）。 | 可将根节点 entries 直接传入 BFS 初始层；或留性能优化 change。 |

---

## Verdict

**APPROVED**

v2 唯一 MUST FIX（BFS prefix dedup bug）已真实修复：外层循环从遍历含重复 hash 的 `hashes_this_layer` list 改为 `for h, prefixes in prefix_map.items()`，每个 hash 恰好处理一次，全部前缀在内层 `for prefix in prefixes` 完整覆盖，输出无膨胀。人工 trace 验证同内容子目录场景正确。代码改动精准（约 3 行改动），未影响其余逻辑。遗留 2 条 SHOULD FIX 均为流程文档问题，不阻塞代码正确性，可在 stage 5 前完成（或在 summary.md 标记 deferred）。

---

## 后续指引

**进入 stage 5 单测（test_tree_nested.py）**；单测必须覆盖以下场景：

```bash
# 复检修复有效性（v3 合并前）
grep -n "prefix_map.items()" apps/api/dataplat_api/routers/commits.py
# 期望：至少 1 行命中（外层循环迭代行）

# 确认 hashes_this_layer 已消失
grep -n "hashes_this_layer" apps/api/dataplat_api/routers/commits.py
# 期望：无输出

# SHOULD FIX-1 跟踪
grep "head_commit" .harness/changes/tree-nested-domain-20260520/coding/coding_report_v1.md
# 期望：不再是 TBD

# 全量 lint 不回退
uv run ruff check apps/api packages/core worker/src
uv run mypy apps/api/dataplat_api packages/core/src worker/src
```

**stage 5 单测必覆盖用例**：

1. root 含两个同内容子目录（`assets/` + `backup/` 同 `tree_hash`）→ `recursive=True` 输出恰好 2 条，无重复
2. 三层嵌套正常展开（depth < 64 不触发限制）
3. 深度 >= 64 时返回 HTTP 400
```
