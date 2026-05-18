---
change_id: <feature-slug>-<yyyymmdd>
version: 1
run_id: <gh run id>
run_url: <link>
branch: <author>/<change-id>
commit_sha: <sha>
triggered_at: <YYYY-MM-DDTHH:MM:SSZ>
finished_at: <YYYY-MM-DDTHH:MM:SSZ>
status: SUCCESS         # SUCCESS | FAILURE | CANCELLED
---

# CI Result v1

## 结构化字段

```yaml
total_tests: 0
passed_tests: 0
failed_tests: 0
skipped_tests: 0
duration_seconds: 0
coverage_percent: n/a
```

> 阶段 8 门禁判定：
> ```
> status == SUCCESS
> total_tests > 0
> passed_tests == total_tests
> ```

## Job 概览

| Job | 状态 | 用时 | 备注 |
|---|---|---|---|
| python-lint-type | success | 1m20s | |
| python-test | success | 4m11s | junit-api.xml uploaded |
| web-lint-type | success | 0m45s | |
| web-test | success | 1m05s | junit-web.xml uploaded |
| codegen-check | success | 0m30s | |
| docker-build | success | 5m02s | api / web / worker tagged |

## 失败详情

> status != SUCCESS 时填这里。

```text
(失败用例名 + 失败信息摘录，≤ 200 行)
```

## Verdict

PASS / FAIL

## 处理动作

- PASS → 进入阶段 9 部署验证（或阶段 10，如无部署面）。
- FAIL → 按以下逻辑回退：
  - 代码 bug：回阶段 3 编码
  - 测试 bug：回阶段 5 单测编写
  - CI 配置 bug：开独立小变更走 `ci-generate` Skill
- 在 `summary.md` 标记回退原因与目标阶段。
