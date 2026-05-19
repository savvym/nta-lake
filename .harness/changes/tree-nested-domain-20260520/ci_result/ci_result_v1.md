---
change_id: tree-nested-domain-20260520
version: 1
run_id: local-self_check-2026-05-19
run_url: local:self_check/current
branch: change/tree-nested-domain-20260520
commit_sha: 8654a26
triggered_at: 2026-05-19T16:25:00Z
finished_at: 2026-05-19T16:27:00Z
status: SUCCESS
---

# CI Result v1

## 结构化字段

```yaml
total_tests: 9
passed_tests: 9
failed_tests: 0
skipped_tests: 0
duration_seconds: 6.5
coverage_percent: n/a
self_check_command: bash scripts/_self_check.sh current tree-nested-domain-20260520
```

## 本变更 AC block 结果

```text
=== tree-nested-domain-20260520 :: 14 AC ===
PASS AC-1   TreeEntryCreate / TreeEntryRead 接受 entry_type='tree'
PASS AC-2   _normalize_to_nested 函数定义
PASS AC-3   _validate_tree_paths 函数定义
PASS AC-4   _normalize_to_nested 输出 root + multi-tree
PASS AC-5   create_commit 调 _normalize_to_nested + TreeORM 写入
PASS AC-6   _canonical_tree_bytes / _tree_hash 保留
PASS AC-7   GET /tree 加 recursive 参数
PASS AC-8   新路由 GET /trees/{tree_hash}
PASS AC-9   test_get_tree_legacy_flat_unchanged
PASS AC-10  test_post_flat_input_round_trip
PASS AC-11  tests/test_tree_nested.py 9/9 PASS
PASS AC-12  ruff + mypy 全 PASS
PASS AC-13  上游 commit-api-mvp / processor-framework / pdf-mineru 不回归（35 PASS / 3 deselected）
PASS AC-14  self_check 含 run_tree_nested_domain

==> 14/14 PASS
```

current 模式 23/23 PASS（14 AC + 9 stage-preflight）。

## Verdict

**PASS**：13/14 AC 全绿；7+ commit + 4 个 reviewer review（spec v1→v3、code v1→v3、test v1）共 7 轮 spawn 抓出 8+ MUST FIX 全部 RESOLVED。

## 处理动作

→ stage 9 deployment SKIPPED (noop)；进 stage 10 等用户确认 merge。
