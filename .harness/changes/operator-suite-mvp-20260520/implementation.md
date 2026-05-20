---
change_id: operator-suite-mvp-20260520
phase: implementation
status: done
authored_at: 2026-05-20T22:00:00Z
author: sonnet-phase2-implementer
model_used: sonnet
branch: change/operator-suite-mvp-20260520
base_commit: 614ce1363138ab1f71a3410fcf84e3aff0b206c5
head_commit: a4e5779ef5590a6c09be3a603d5f0d94a547c3ad
pr_url: n/a (gh PAT 缺 pr:write)
---

# Implementation

## 做了什么

按 design.md In Scope 清单，新增 FilterOperator / DedupOperator / ScoreOperator 三个算子，并更新 `__init__.py` 完成 4 个内置算子（含已有的 IdentityOperator）的模块级自动注册。

- **FilterOperator**：按 `min_chars` 丢弃短行；len(text) < min_chars 返空列表，否则返追加 lineage_ops 的新 row。
- **DedupOperator**：在 `ctx._dedup_seen` set 上维护已见 hash_key；支持 `text`（sha256）与 `source_blob`（blob_sha 直接取）两种 key；重复返空列表。
- **ScoreOperator**：支持 `text_chars`（字符数）与 `alpha_ratio`（字母占比，4 位小数）两种 metric；计分写入 `stats[f"score_{metric}"]`。
- `__init__.py`：try/except 包裹的 for 循环完成 4 次 register，防止模块重复 import 时抛 ValueError。

## 改动文件清单

| 路径 | 类型 | 一句话说明 |
|---|---|---|
| `packages/core/src/dataplat_core/operators/filter.py` | new | FilterOperator |
| `packages/core/src/dataplat_core/operators/dedup.py` | new | DedupOperator |
| `packages/core/src/dataplat_core/operators/score.py` | new | ScoreOperator |
| `packages/core/src/dataplat_core/operators/__init__.py` | edit | import 4 个 class + auto-register |
| `packages/core/tests/test_operator_suite_mvp.py` | new | AC-1..AC-4 测试 |

## 任务完成情况

| Task | 状态 | commit | 备注 |
|---|---|---|---|
| FilterOperator 实现 | done | a4e5779 | |
| DedupOperator 实现 | done | a4e5779 | |
| ScoreOperator 实现 | done | a4e5779 | |
| __init__.py auto-register | done | a4e5779 | |
| test_operator_suite_mvp.py | done | a4e5779 | 4 AC 全 pass |

## 测试通过证据

```text
# W2-1 专项测试（AC-1..AC-4）
$ cd packages/core && uv run pytest tests/test_operator_suite_mvp.py -x -q
....
4 passed in 0.15s

# 全套（含 W1-2 W1-3 W1-4，共 42 tests）
$ cd packages/core && uv run pytest tests/ -q
..........................................
42 passed in 0.23s

# pyright 类型检查
$ cd packages/core && uv run pyright src/ tests/test_operator_suite_mvp.py 2>&1 | tail -3
0 errors, 0 warnings, 0 informations
```

W1-2 test_operator_protocol.py 中 `test_registry_register_and_lookup` 使用唯一 key `"identity_test_ac2"`，与自动注册的 `"identity"` 不冲突，仍 PASS。

## 偏离 design.md（如有）

无偏离。严格按 design.md § In scope 落地，未扩展 scope。

## 下一步

进入 Phase 3：Application Owner spawn opus reviewer 对照 design.md 验 PR。
