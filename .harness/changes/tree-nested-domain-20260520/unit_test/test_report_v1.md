---
change_id: tree-nested-domain-20260520
version: 1
authored_at: 2026-05-19T15:50:00Z
status: waiting_review
---

# Test Report v1

## 验收项 ↔ 测试映射

| AC ID | 测试文件 | 测试函数 |
|---|---|---|
| AC-3 (路径校验) | test_tree_nested.py | test_path_validation_rejects（9 类失败 fixture：空 / 起头 / / 结尾 / / 连续 / / . / .. / 空白 segment / blob-dir conflict / type=tree input） |
| AC-6 (子 tree dedup) | test_tree_nested.py | test_dedup_same_subtree_across_commits |
| AC-7 (default GET 含 subtree) | test_tree_nested.py | test_get_tree_default_shows_subtree |
| AC-8 (GET /trees/{hash}) | test_tree_nested.py | test_get_subtree_by_hash |
| AC-9 (legacy 不回归) | test_tree_nested.py | test_get_tree_legacy_flat_unchanged · test_recursive_no_op_on_flat |
| AC-10 (扁平 → recursive 还原) | test_tree_nested.py | test_post_flat_input_round_trip |
| AC-11 (≥ 8 用例全 PASS) | test_tree_nested.py | 9 个用例 |
| AC-13 (上游不回归) | tests/test_commits.py / tests/test_processor.py / tests/test_pdf_mineru.py | -k deselect 3 pre-existing flake，35 PASS |

## 测试文件清单

| 文件 | 类型 | 用例数 |
|---|---|---|
| apps/api/tests/test_tree_nested.py | 集成（ASGI + PG + MinIO） | 9 |

## Mock 范围

- 不 mock CommitService / _validate_tree_paths / _normalize_to_nested / GET 路由（被测对象）
- 测试 (d) test_get_tree_legacy_flat_unchanged 与 (i) test_recursive_no_op_on_flat **直接 INSERT TreeORM** 模拟历史扁平 commit（绕过 service normalize 入库）；显式声明 `session.flush()` 让 FK 检查能看到 ORM-staged rows，然后 raw SQL INSERT commits

## 本地运行

```text
$ cd apps/api && uv run pytest -q tests/test_tree_nested.py
.........  9 passed in 6.38s

$ uv run ruff check apps/api packages/core worker/src
All checks passed!

$ uv run mypy apps/api/dataplat_api packages/core/src worker/src
Success: no issues found in 96 source files

$ source .env.local && cd apps/api && uv run pytest -q --tb=no \
    -k "not test_f_end_to_end_process_succeeded and not test_g_unknown_processor_marks_failed and not test_h_source_ref_missing_marks_failed" \
    tests/test_commits.py tests/test_processor.py tests/test_pdf_mineru.py tests/test_tree_nested.py
44 passed, 3 deselected in 18.16s
```

## 已知 flaky / 跳过

- 3 个 pre-existing flake（spec v4 § Deferred + AC-13 -k deselect）：
  - `tests/test_processor.py::test_f_end_to_end_process_succeeded`
  - `tests/test_processor.py::test_g_unknown_processor_marks_failed`
  - `tests/test_processor.py::test_h_source_ref_missing_marks_failed`
- 根因：worker 进程读不到 ASGI 测试 session 未提交的 repo；非本 change 引入，main baseline 同样 fail。
- 跟进：follow-up `tests-worker-session-isolation-*`。

## 覆盖率

未跑 coverage（spec 未要求）。9 测试覆盖：
- 扁平 → nested round-trip
- 默认 GET 含子 tree
- /trees/{hash} 取子层 + 404
- 历史 flat 不回归 + recursive no-op
- 子 tree dedup per repo
- 9 类路径校验失败（含 type=tree input）
- 3 层深嵌套
- 空 tree

未覆盖（接受）：
- 真实 64+ 层超深嵌套触发 _MAX_TREE_RECURSION_DEPTH（实际不会触发；rate limit 性质）
- 跨 repo same hash 隔离（spec 显式承诺 by repo_id；可加单测但优先级低）

## 下一步

stage 6：spawn 独立 sonnet test reviewer 复检。
