---
change_id: tree-nested-domain-20260520
target: tasks.md
target_version: 1
review_version: 1
reviewer: claude-agent:tree-nested-domain-20260520-stage2-reviewer-v1
reviewed_at: 2026-05-19T15:00:00Z
verdict: REVISION REQUIRED
---

# Tasks Review v1

## 检查清单结论

| 条目 | 状态 | 备注 |
|---|---|---|
| 每个任务粒度合理（1-3 小时） | PARTIAL（详见 MUST FIX-1） | T-2 包含 trie 构造 + 递归 hash + validate 三个独立算法，合并风险高 |
| depends_on 形成 DAG，没有循环 | PASS | T-1→T-2→T-3→T-4→T-5→T-6→T-7 线性 DAG，无环 |
| 评审 / 单测 / CI 阶段对应任务都存在 | PASS | process_tasks 含 P-spec-review / P-code-review / P-test-review；T-5/T-6 对应单测和 CI |
| 没有"做完整个系统"类目标性任务 | PASS | 每个任务有具体产物和 AC 映射 |
| 验收覆盖表 14 AC 全覆盖 | PASS | AC-1 至 AC-14 均有对应任务 |
| spec ↔ tasks ↔ self_check 一致 | PARTIAL（SHOULD FIX-1：AC-13 覆盖）| |

---

## 问题列表

### MUST FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| MUST FIX-1 | tasks.md T-2 | T-2 合并了两个独立算法单元：`_validate_tree_paths`（路径校验）和 `_normalize_to_nested`（trie 构造 + 递归 hash 计算）。两者逻辑相互独立，都是非平凡算法；合并后 1-3 小时估算不现实（trie 构造 + 自底向上递归 hash 单独就超 3h）；且若 _validate 出 bug，会掩盖 _normalize 的实现状态。按 development-process.md §阶段 1 "每个任务能在 1-3 小时内完成"要求，T-2 违规。 | 拆为 T-2a（`_validate_tree_paths`；covers AC-3；1-2h）和 T-2b（`_normalize_to_nested`；covers AC-2/AC-4；2-3h）；DAG: T-1→T-2a→T-2b→T-3；验收覆盖表同步更新 |
| MUST FIX-2 | tasks.md T-3 description + spec AC-4 | T-3 description 中 `create_commit` 步骤 1（blob 存在性校验）未更新。现行代码 `target_hashes = {e.target_hash for e in payload.tree.entries}`——当 entries 全是 blob（soft mode 输入）时 target_hash 全是 blob hash，正确。但 T-3 description 说"步骤 2（算 tree_hash）先 `_validate_tree_paths` → `_normalize_to_nested`"，并没有提步骤 1 是否需改。若 generator 在改步骤 2 之前误解"步骤 1 不变"，可能在嵌套入参（含 entry_type=tree 的手工传参）情境下把子 tree hash 当 blob hash 校验，引发 400 误拒（见 spec SHOULD FIX-3）。T-3 应明确步骤 1 适用范围：仅取 `entry_type == "blob"` 的 entries 的 target_hash。 | 在 T-3 description 步骤 2 之前加说明："步骤 1 blob 存在性校验：仅检查 `entry_type == 'blob'` 的 entry 的 target_hash；entry_type='tree' 的 target_hash 是子 tree hash，不在 BlobStore" |

---

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| SHOULD FIX-1 | tasks.md §验收覆盖 + T-5 + T-6 | T-6 covers_ac 为 `[AC-14, AC-12, AC-13]`，但 T-7 也 covers `[AC-11, AC-12, AC-13]`。AC-12（ruff+mypy）和 AC-13（上游回归）被两个任务重复覆盖但关系不同：T-6 是"把 AC-13 命令加进 self_check.sh"，T-7 是"实际跑通 AC-13"。这种"注册 vs 执行"的语义差异在任务描述里不够清晰，可能导致 T-6 完成后 generator 误认为 AC-13 已 done 而不跑 T-7。 | T-6 的 covers_ac 改为仅 `[AC-14]`（注册 self_check block）；T-7 的 covers_ac 保留 `[AC-11, AC-12, AC-13]`（实际执行验证）；或在 T-6 description 加注"T-6 仅注册命令，执行验证在 T-7" |
| SHOULD FIX-2 | tasks.md T-5 description | test_dedup_same_subtree_across_commits（用例 5）的说明是"两个不同 commit 都含 images/{a.jpg,b.jpg} → 同 subtree_hash；DB 只有一行 images-tree TreeORM"。但如 SHOULD FIX-1（spec 层）所分析，TreeORM 主键是 hash（全局唯一），非 (hash, repo_id)；若是跨 repo 测试则 repo_id 不同但 hash 主键会冲突（IntegrityError 或 upsert 幂等）。用例 5 应明确是**同 repo 两次 commit 共享 subtree**，而非跨 repo 测试；否则 generator 可能写出跨 repo 测试，遇到 DB 约束问题后误判为 bug。 | T-5 用例 5 描述改为"**同 repo** 两个不同 commit 都含 images/{a.jpg,b.jpg} → 同 subtree_hash；`trees` 表该 hash 行只有一条"；如需测跨 repo 不共享行为，拆一个独立用例并说明预期（INSERT 第二行 vs IntegrityError） |
| SHOULD FIX-3 | tasks.md T-5 description + T-4 | T-5 用例 8（test_empty_tree）"POST commit with tree.entries=[]"——空 entries 是合法输入（spec §非范围"空根 tree 是合法的全空仓语义"），但 spec AC-3 及 _validate_tree_paths 逻辑没有显式处理空 entries（empty list 不需任何校验即通过，_normalize_to_nested 应返回空 root tree）。T-5 只列了用例，没有说明 T-4 的 `get_tree` 默认模式对空 root tree 的预期响应（TreeRead.entries=[]，200 OK）。建议 T-4 description 加一行"空 tree（entries=[]）GET 返 200 + entries=[]" | 在 T-4 description 末尾加"边界：空 root tree → 返 TreeRead(hash=..., entries=[])" |

---

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| NTH-1 | tasks.md T-5 | test_path_validation_rejects（用例 6）列了 5 个 case：`""` / `"//a"` / `"a//b"` / `"a/../b"` / `"a"` 同 `"a/b"`（冲突）。若采纳 spec MUST FIX-2（末尾 `/`、空白 segment），此用例需补 2 条 case：`"a/"` 和 `" a"`。 | 随 spec v2 同步补用例 |
| NTH-2 | tasks.md T-2 | _normalize_to_nested 算法描述里说"all_trees 顺序：子 tree 在前，root 在后（持久化时按顺序 upsert 不会断引用）"。但 TreeORM 的 FK 引用在 tree_entries.tree_hash → trees.hash，不是 tree 引用 subtree。子 tree upsert 顺序对 FK 完整性没有实际约束（子 tree entry 里 target_hash 是 String，没有 FK 约束）。这个顺序说明是多余的，但不影响正确性，仅可能误导 generator 过度关注顺序。 | 可注"顺序仅为可读性；非 FK 约束要求" |
| NTH-3 | tasks.md T-7 | T-7 description 里引用 `processor-pdf-mineru-20260519` 和 `processor-pdf-mineru-assets-20260520`，但 summary.md 的 related_changes 中只列了 `processor-pdf-mineru-assets-20260520`，未列 `processor-pdf-mineru-20260519`。两者不完全一致（可能只是 typo 或确实有两个独立 change）。 | 核实上游 change id；若只有一个则 T-7 删掉多余那条 |

---

## Verdict

**REVISION REQUIRED**

未关闭 MUST FIX 共 2 条：

1. **MUST FIX-1**：T-2 颗粒度违反 1-3 小时规则，validate + normalize 应拆为 T-2a + T-2b。
2. **MUST FIX-2**：T-3 对步骤 1（blob 存在性校验）范围未更新，存在 generator 误包含子 tree hash 导致 400 误拒的实现风险。

---

## 后续指引（Generator 修 v2 后自查）

```bash
# 1. 确认 T-2 已拆为 T-2a / T-2b（或等价拆分）
grep -E "T-2[ab]|_validate_tree_paths|_normalize_to_nested" \
  .harness/changes/tree-nested-domain-20260520/request_analysis/tasks.md

# 2. 确认 T-3 description 含 entry_type=='blob' 限制 blob hash 校验范围
grep -A20 "id: T-3" .harness/changes/tree-nested-domain-20260520/request_analysis/tasks.md | \
  grep -E "blob.*hash|entry_type.*blob"

# 3. 确认验收覆盖表已同步（若 T-2 拆分则 AC-3 挂 T-2a，AC-2 挂 T-2b）
grep -A20 "## 验收覆盖" .harness/changes/tree-nested-domain-20260520/request_analysis/tasks.md
```

v2 review 时将以上输出作为 MUST FIX 复检证据。
