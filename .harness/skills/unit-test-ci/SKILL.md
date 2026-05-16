---
name: unit-test-ci
description: 触发并解读 CI 结果，按机械化标准做门禁判定
applicable_stage: 阶段 8（CI 验证）
inputs:
  - 已推送到远端的分支
  - 项目 CI 配置（.github/workflows/）
outputs:
  - ci_result/ci_result_v{N}.md
---

# unit-test-ci Skill

## 进入条件

- 阶段 7 推送完成，远端分支存在。
- CI 已经触发或可被手动触发。

## 步骤

### 1. 触发 / 等待 CI

- 推送通常自动触发；如未触发，用 `gh run rerun` 或 push 一次空 commit。
- 用 Monitor 工具持续观察（每分钟轮询一次状态），不要原地 sleep。

```bash
# 推荐：单一一次性通知
gh run list -b <branch> -L 1 --json status,conclusion,databaseId,name
```

### 2. 收集结果

每个 job 收集：

| 字段 | 来源 |
|---|---|
| `status` | gh run view 的 conclusion |
| `total_tests` | 测试报告 artifact 或 pytest junit xml |
| `passed_tests` | 同上 |
| `failed_tests` | 同上 |
| `skipped_tests` | 同上 |
| `duration` | run 元数据 |
| `coverage`（如启用） | 覆盖率 artifact |

如 CI 没有产出 junit xml，则**先去 ci-generate Skill 把测试结果产物化**，再回来跑这个阶段。门禁判定不能基于 stdout 文本搜索。

### 3. 写 ci_result 报告

按 `ci_result/ci_result_v{N}.md` 模板填：

```yaml
---
run_id: <gh run id>
run_url: <link>
branch: <branch>
commit_sha: <sha>
triggered_at: <iso8601>
finished_at: <iso8601>
status: SUCCESS | FAILURE | CANCELLED
---
```

接结构化字段：

```
total_tests: <int>
passed_tests: <int>
failed_tests: <int>
skipped_tests: <int>
duration_seconds: <int>
coverage_percent: <float | n/a>
```

接失败详情：失败 job 名、失败用例名 + 失败信息摘录（≤ 200 行）。

### 4. 门禁判定

机械化条件：

```text
status == SUCCESS
total_tests > 0
passed_tests == total_tests
```

任何一条不满足 → verdict = FAIL，**禁止进入阶段 9**。

### 5. 更新 summary.md

- 在 CI 阶段子项追加：`v{N}` / run_url / verdict / 触发时间。
- 失败时同步标记 stage=`coding` 或对应回退阶段，附"为什么回退"。

## 产出

- `ci_result/ci_result_v{N}.md`。
- `summary.md` 同步刷新。

## 质量门禁

```text
ci_result_v{latest}.md 存在
报告含必填字段：run_url / status / total_tests / passed_tests / failed_tests
status == SUCCESS
total_tests > 0
passed_tests == total_tests
```

## 失败回退

- 测试失败 = 代码 bug → 回阶段 3 编码。
- 测试失败 = 测试本身 bug → 回阶段 5 单测编写。
- CI 基础设施失败（runner 挂、cache 异常） → 重试一次；连续失败开独立小变更走 `ci-generate` Skill 修。
- skipped_tests 偷偷增多 → 当作 MUST FIX 处理，等同失败。

## 反模式

- 用"重试 5 次只要有一次通过就算过"打补丁。
- 用 `grep "FAILED" stdout` 取代 junit xml 解析。
- 忽略 flaky 测试。flaky 一律算失败，要么修要么删（不允许长期 skip）。
- 在 ci_result 报告里写"应该通过"或贴一张截图代替结构化字段。
