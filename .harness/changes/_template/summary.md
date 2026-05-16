---
change_id: <feature-slug>-<yyyymmdd>     # 与目录名一致
title: <一句话概括>
owner: <负责人>
started_at: <YYYY-MM-DDTHH:MM:SSZ>
stage: request_analysis                  # 当前所处阶段
status: in_progress                      # in_progress | waiting_review | blocked | done | abandoned
last_updated: <YYYY-MM-DDTHH:MM:SSZ>
related_changes: []                      # 依赖或被依赖的其他 change id
---

# Summary

> 这是本变更的 Single Source of Truth。任何阶段开始 / 通过 / 失败都必须同步更新这里。

## 一句话目标

<复述用户诉求，不展开。>

## 范围摘要

- **In scope**：<bullet list>
- **Out of scope**：<bullet list>

## 阶段进度

| 阶段 | 状态 | 最新版本 | verdict | 产物 / 报告 |
|---|---|---|---|---|
| 1 需求分析 | _pending / in_progress / done_ | _v1_ | _APPROVED / REVISION REQUIRED / —_ | [spec.md](request_analysis/spec.md) · [tasks.md](request_analysis/tasks.md) |
| 2 需求评审 | | | | [spec_review_v1.md](request_analysis/review/spec_review_v1.md) · [tasks_review_v1.md](request_analysis/review/tasks_review_v1.md) |
| 3 编码实现 | | | | [coding_report_v1.md](coding/coding_report_v1.md) |
| 4 编码评审 | | | | [code_review_v1.md](coding/review/code_review_v1.md) |
| 5 单测编写 | | | | [test_report_v1.md](unit_test/test_report_v1.md) |
| 6 单测评审 | | | | [test_review_v1.md](unit_test/review/test_review_v1.md) |
| 7 代码推送 | | | | _branch / commit SHA_ |
| 8 CI 验证 | | | | [ci_result_v1.md](ci_result/ci_result_v1.md) |
| 9 部署验证 | | | | [deploy_verify_v1.md](deployment/deploy_verify_v1.md) |
| 10 用户确认 | | | | _确认人 / 时间_ |

## 关键决策

| 时间 | 决策 | 理由 / 取舍 | 关联文件 |
|---|---|---|---|
| _YYYY-MM-DD_ | _e.g. 选择 A 方案而非 B_ | _原因_ | _spec.md §x_ |

## 当前阻塞

- <如有阻塞，列在这里：等待谁的输入 / 待哪个上游 change 完成 / 待某个 ADR 决议>

## Deferred 项（已 review 通过但未在本 change 内修）

| 类型 | 描述 | 跟进位置 |
|---|---|---|
| SHOULD FIX | _e.g. 加更细的并发测试_ | _follow-up change <id> 或 task <id>_ |

## 交付

> 关闭本变更时填写。

- Branch：`<author>/<change-id>`
- PR：<链接>
- Merge commit：`<sha>`
- 部署版本（如有）：`<image tag / release tag>`
- 用户确认：<人 / 时间>
- 关闭时间：<YYYY-MM-DDTHH:MM:SSZ>

## 复盘（可选）

- 哪些步骤超预期顺利
- 哪些步骤踩坑：根因 + 防复发机制（一定要落到 rules / skills 的修订）
