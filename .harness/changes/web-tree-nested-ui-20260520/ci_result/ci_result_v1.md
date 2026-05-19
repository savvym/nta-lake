---
change_id: web-tree-nested-ui-20260520
version: 1
run_id: local-self_check-2026-05-19
run_url: local:self_check/current
branch: change/web-tree-nested-ui-20260520
commit_sha: TBD（commit 后填）
triggered_at: 2026-05-19T19:00:00Z
finished_at: 2026-05-19T19:02:00Z
status: SUCCESS
---

# CI Result v1

## 结构化字段

```yaml
total_tests: 10            # repos.files-section 5 + queries.tree-nested 5
passed_tests: 10
failed_tests: 0
skipped_tests: 0
duration_seconds: 3.2
self_check_command: bash scripts/_self_check.sh current web-tree-nested-ui-20260520
```

## 本变更 AC block 结果

```
=== web-tree-nested-ui-20260520 :: 11 AC ===
PASS AC-1   useSubtree 函数
PASS AC-2   useSubtreeByPath 函数
PASS AC-3   validateSearch 含 path
PASS AC-4   FilesSection 用 useSubtreeByPath
PASS AC-5   区分 entry_type tree/blob
PASS AC-6   vitest ≥ 5 + 0 fail（JSON reporter）
PASS AC-7   全 web vitest 不回归
PASS AC-8   pnpm lint + typecheck
PASS AC-9   self_check 含本 block
PASS AC-10  tree-nested-domain 不回归
PASS AC-11  path .default("") 锚定

==> 11/11 PASS
```

current 模式总 20/20 PASS（11 AC + 9 stage-preflight）；全 web vitest 31 passed (14 files)。

## Verdict

**PASS**：11 AC 全绿；7 轮 reviewer spawn 共抓 10+ MUST FIX 全部 RESOLVED。
