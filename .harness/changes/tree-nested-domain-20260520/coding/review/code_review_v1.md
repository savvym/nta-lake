---
change_id: tree-nested-domain-20260520
target: coding_report_v1.md + schemas/tree.py + services/commit.py + routers/commits.py
target_version: 1
review_version: 1
reviewer: claude-agent:tree-nested-domain-20260520-stage4-reviewer-v1
reviewed_at: 2026-05-20T00:00:00Z
verdict: REVISION REQUIRED
---

# Code Review v1

## 检查清单结论

| 条目 | 状态 | 说明 |
|---|---|---|
| 改动文件与 coding_report 声明一致 | PASS | 3 文件（schemas/tree.py + services/commit.py + routers/commits.py）与 git diff 完全吻合 |
| 关联 task 编号正确 | PASS | T-1/T-2a/T-2b/T-3/T-4 映射无误；T-5/T-6/T-7 明确标 pending |
| coding_report head_commit 字段填写 | FAIL | 值为 "TBD"；实际 commit 为 72a33fe，需补填 |
| ruff + mypy 报告 | PASS | coding_report 声明 "All checks passed / no issues found in 96 files"；本轮无法独立复核，接受自报 |
| AC-1 ~ AC-8 实现存在 | PASS | 逐一 grep 确认；schema Literal 放宽、两个新函数、create_commit 步骤 2/4 改造、router 改动均已落地 |
| 路径校验覆盖 spec AC-3 所有 8 类 | PASS（7/8 类）| 见 MUST FIX-1 详述 |
| _normalize_to_nested 逻辑正确性 | PASS | 空 entries、单段名、mixed blob+subtree、子→父顺序均正确；详见下方分析 |
| create_commit 步骤 4 dedup 安全性 | PASS | session.get 使用单列 PK（TreeORM.hash），符合模型定义；SQLAlchemy identity map 保证同 session 内重复 hash 不双插 |
| N+1 查询 | FAIL | _expand_tree_recursive 每节点单查，违反 coding-style §7.1 |
| 递归深度保护 | WARN | _expand_tree_recursive 无深度上限 |
| local import | INFO | _load_subtree_entries 内 local import select，轻微风格问题 |
| 向后兼容（AC-9）| PASS | 旧扁平 commit 路径不受影响，分析见下 |
| pre-existing flake deselect | PASS（条件）| 见 SHOULD FIX-2 |

---

## 问题列表

### MUST FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| MUST FIX-1 | `routers/commits.py:233-260` `_expand_tree_recursive` | N+1 查询：每个 type=tree entry 触发一次独立 SELECT。对有 K 个中间 tree 节点的提交调用 `?recursive=True` 产生 K+1 次查询。`coding-style.md §7.1` 明确："N+1 查询是评审硬性打回项；必须用 join / batch / dataloader 解决"。 | 改为两阶段：(1) 先通过一次 `SELECT * FROM trees WHERE hash IN (...)` 批量拉取当前层所有子 tree hash；(2) 逐层迭代（BFS）直到无 tree entry，避免每节点单查。或使用 PostgreSQL 递归 CTE 一次取完全部 tree + entries。实现复杂度可接受：主要改写 `_expand_tree_recursive` 为 BFS + batch fetch，不影响其他逻辑。 |
| MUST FIX-2 | `services/commit.py:141-147` `_normalize_to_nested` | `entry_type != "blob"` 的校验**在 `_validate_tree_paths` 之后**触发，但 `_validate_tree_paths` 对 `entry_type="tree"` + 正确 mode（16384）的 entry **不拒绝**（spec AC-3 仅要求 mode 不对时拒，允许正确 mode 的 tree entry 通过 validate）。结果：user POST 含 `entry_type="tree"` + `mode=16384` 的 entry 时，validate 通过，但到 normalize 被拒，错误信息语义正确但发生点不符合预期"AC-3 是唯一校验边界"的文档承诺。更关键的是：`_validate_tree_paths` 文档注释写"任一命中 → ValueError 含详细错误（路由层翻 400）"，但对 `entry_type="tree"` 的非法 API 直接提交是**静默放行到 normalize**，两处拒错误语义不一致。建议：在 `_validate_tree_paths` 内增加一条 `if e.entry_type != "blob": raise ValueError(...)` 的明确 guard，让校验边界统一在 validate 函数；normalize 内的相同 guard 可保留为防御兜底但不作为唯一拦截点。 |

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| SHOULD FIX-1 | `routers/commits.py:233` `_expand_tree_recursive` | async 递归无最大深度保护。Python 默认 `sys.getrecursionlimit()=1000`；每层 async 递归约占 2-3 个帧。正常使用（5-10 层）无问题，但构造 400+ 层嵌套的恶意提交可触发 `RecursionError` 使整个 worker 崩溃，不会被 FastAPI 的 500 handler 捕获（RecursionError 不是 Exception 子类）。 | 加 `max_depth: int = 64` 参数，超限时 raise `HTTPException(400, "tree depth exceeded")` 或直接 return。64 层对合法用例（含复杂代码仓库）绰绰有余。 |
| SHOULD FIX-2 | `coding_report_v1.md` "偏离 spec" 节 | 3 个 pre-existing flake（test_f/g/h）的 deselect 理由仅为 generator 自述，无客观验证材料（如 main 分支 CI 截图、git bisect 记录、或 pytest --collect-only 输出）。Stage 4 reviewer 无法独立复核。 | 在 coding_report 或 summary.md 补充：用 `git stash` 回到 main baseline 跑 `pytest tests/test_processor.py -k test_f_... -v` 的截图或输出片段，证明这 3 个用例在 main 上同样失败。这不需要修代码，只需补证据。 |
| SHOULD FIX-3 | `coding_report_v1.md` frontmatter | `head_commit: TBD（commit 后填）` 未补填，实际 commit SHA 为 `72a33fe`。summary.md 阶段进度也应记录该 SHA（coding-style §4.0 "summary.md 的阶段进度必须记录该阶段最新 commit SHA，便于后续 reviewer 精准复核增量"）。 | 将 `head_commit` 改为 `72a33fe`；并在 `summary.md` coding 阶段行补 commit SHA。 |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| NICE TO HAVE-1 | `routers/commits.py:220` `_load_subtree_entries` | `from sqlalchemy import select` 为局部 import，而 `select` 已在 `services/commit.py` 模块级 import，且其他 router（`get_tree` 间接依赖 `selectinload`）均在模块顶部统一 import。局部 import 仅有 "减少 module-level deps" 的微弱理由（import 系统有缓存，无性能差异）。 | 将 `from sqlalchemy import select` 移到 `commits.py` 模块顶部，与 `from sqlalchemy.orm import selectinload` 放一起。 |
| NICE TO HAVE-2 | `routers/commits.py:282-283` `get_tree` | `recursive=True` 时调用 `_expand_tree_recursive(session, repo.id, tree.hash)` 重新查询根 tree，但 `tree` 对象（含 entries）已由 `CommitService.get_tree_by_commit` 通过 `selectinload` 预加载进内存。根节点多一次冗余 SELECT。 | 可将 `recursive=True` 路径改为：先用内存中已加载的 `tree.entries` 处理根层，只对 `type=tree` 的子项递归查询。需重构辅助函数签名。可与 MUST FIX-1 的 batch 改造合并处理。 |
| NICE TO HAVE-3 | `services/commit.py:178,192` `_normalize_to_nested` / `_walk` | 两处 `assert isinstance(blobs, list)` 用于类型收窄（`dict[str, object]` → `list`）。`assert` 在 `python -O` 模式下被静默跳过，可能导致后续 `for leaf in blobs` 不安全迭代（但实际不会触发，因 `_blobs` 总是 list）。 | 改为 `if not isinstance(blobs, list): raise TypeError(...)` 或改变 trie 节点类型定义（如用 `TypedDict`）让 mypy 静态保证不需要运行时 check。后者更优但改动稍大。 |

---

## 正确性确认（关键边界，无需修复）

以下是 prompt 中要求评审的高风险点，逐一验证后确认无误：

**1. _normalize_to_nested 单段名（`name="paper.md"`）**
分析：`segments = ["paper.md"]`，前 N-1 段循环不执行，直接在 `root_node` 中作为 blob 处理。`_walk(root_node)` 返回含 1 个 blob entry 的 root tree。结论：正确。

**2. 同目录 mixed blob+subtree（`images/a.jpg` + `paper.md`）**
分析：`root_node = {"_blobs": [paper.md-leaf], "images": {...blobs: [a.jpg-leaf]}}`. `_walk(root_node)` 收集 1 blob + 1 subtree = 2 entries。结论：正确。

**3. 空 entries**
分析：`root_node = {"_blobs": []}`, `_walk` 返回 `_tree_hash([])`, `all_trees = [(root_hash, [])]`。结论：与 spec 完全一致。

**4. blob-dir 冲突检测顺序（`["a/b", "a"]` 或 `["a", "a/b"]`）**
分析：第二重循环对所有 entries 求真前缀，与 `seen_full_names`（含所有完整 name）比对。两种顺序均能被捕获（`"a/b"` 的真前缀 `"a"` 在 `seen_full_names` 中）。结论：正确。

**5. all_trees 子→父顺序**
分析：`_walk` 是 DFS，先 recurse 子节点（`sub_hash = _walk(child)` 返回后才 append 子 tree entry 到本层），再 `all_trees.append((h, level_entries))` 本层。所以子树先入 list，root 最后。结论：顺序保证正确，FK 持久化安全。

**6. 重复 hash 在 all_trees 内（如两个相同内容的子目录）**
分析：`session.get(TreeORM, hash)` 使用 SQLAlchemy identity map；第一次 `session.add(TreeORM(hash=X))` 后，第二次 `session.get(TreeORM, X)` 命中 identity map 返非 None，跳过。结论：幂等，正确。TreeORM.hash 是单列 PK（非 composite）。

**7. spec AC-9 backward compat（旧扁平 commit）**
旧扁平 commit 的 TreeORM 只有一行（root），entries 的 `name` 含 `/`。GET 默认不 recursive：直接返 `tree.entries`，name 形态与写入时完全一样。GET `?recursive=True`：`_expand_tree_recursive` 对根 tree 取 entries，均是 blob（无 type=tree entry），直接 emit，输出与默认相同。结论：向后兼容，符合 spec AC-9。

**8. AC-6 dedup per-repo 描述 vs 模型实际**
spec AC-6 说"dedup 仅 per-repo（TreeORM PK=(hash, repo_id)）"。但 `models/tree.py` 实际 PK 是单列 `hash`。这是预存在设计决策（`commit-api-mvp-20260517`），本 change 未修改模型。`session.get(TreeORM, sub_tree_hash)` 对单列 PK 是正确调用。spec 对 PK 的描述不准确，但不影响本 change 的正确性。不开 MUST FIX（pre-existing issue）。

---

## Verdict

**REVISION REQUIRED**

2 条 MUST FIX 阻塞：

1. **MUST FIX-1（N+1 查询）**：`_expand_tree_recursive` 对每个子 tree 节点单独 SELECT，违反 `coding-style.md §7.1` "N+1 查询是评审硬性打回项"的字面硬约束。即使当前 PDF 场景（最多 2-3 层）影响有限，规则不允许推迟。需用 BFS+batch 或递归 CTE 替换。
2. **MUST FIX-2（校验边界不一致）**：`_validate_tree_paths` 文档承诺是唯一校验边界，但 `entry_type="tree"` + 合法 mode 的 entry 可以通过 validate（不被拒），在 normalize 才被拒。违反"系统边界单一 validator"原则，造成 error message 来源不可预期。

3 条 SHOULD FIX 不阻塞本轮：递归深度保护 / deselect 证据补充 / head_commit 补填。

---

## 复检指引（Generator 修 v2 后自查）

```bash
# MUST FIX-1 修复验证：确认 _expand_tree_recursive 不再单 SELECT per node
grep -n "_load_subtree_entries\|session.execute\|session.get" \
  apps/api/dataplat_api/routers/commits.py
# 期望：_expand_tree_recursive 内不再出现循环调用 _load_subtree_entries 的模式
# 或者改为 BFS batch 版本后只有常数次 DB 交互

# MUST FIX-2 修复验证：validate 函数统一拒 entry_type=tree
cd apps/api && uv run python -c "
from dataplat_api.services.commit import _validate_tree_paths
from dataplat_api.schemas.tree import TreeEntryCreate as T
try:
    _validate_tree_paths([T(name='x', mode=16384, entry_type='tree', target_hash='a'*64)])
    print('BUG: should have raised ValueError')
except ValueError as e:
    print('FIXED:', e)
"

# SHOULD FIX-1 递归深度保护验证（如加了 max_depth 参数）
grep -n "max_depth\|RecursionError\|depth" apps/api/dataplat_api/routers/commits.py

# SHOULD FIX-3 head_commit 补填
grep "head_commit" .harness/changes/tree-nested-domain-20260520/coding/coding_report_v1.md
# 期望：不再是 TBD

# 全量 lint + smoke
uv run ruff check apps/api packages/core worker/src
uv run mypy apps/api/dataplat_api packages/core/src worker/src
cd apps/api && uv run python -c "
from dataplat_api.services.commit import _normalize_to_nested, _validate_tree_paths
from dataplat_api.schemas.tree import TreeEntryCreate as T
root, trees = _normalize_to_nested([
    T(name='images/a.jpg', mode=33188, entry_type='blob', target_hash='a'*64),
    T(name='paper.md', mode=33188, entry_type='blob', target_hash='b'*64)
])
assert len(trees) == 2
print('smoke OK, trees:', len(trees))
"
```
