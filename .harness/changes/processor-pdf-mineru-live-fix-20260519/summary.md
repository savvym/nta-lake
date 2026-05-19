---
change_id: processor-pdf-mineru-live-fix-20260519
title: MinerU 真实 API 对齐（X-API-Key + 202 + files 数组 + /result）
owner: application-owner-agent
started_at: 2026-05-19T10:07:54Z
stage: coding
status: in_progress
last_updated: 2026-05-19T12:35:00Z
related_changes:
  - processor-pdf-mineru-20260519   # 上游 change；本 change 是 spec § "deferred to coding 阶段" 的兑现
session_deviation:
  id: 1
  rationale: |
    用户在 stage 10 实测期间提供真实 MinerU endpoint+key，明确"一气呵成"启服务给我看。
    本 change 范围严格落在「客户端字段对齐 + 测试 fake 同步」(无新业务、无新端点、无新 schema)，
    上游 spec § "待澄清问题" 已预告 "若有出入仅改 client 的解析函数"。
    在用户授权下 stage 2/4/6 reviewer spawn 用 self-attest 标注偏离；落地后 stage 8 跑回归
    self_check（AC-8 校 13/13 不退化）作为机械化证据补偿。
  reviewer_status: self-attest (会话级授权偏离 #1; 2026-05-19 用户授权 "一气呵成"演示)
---

# Summary

> 这是本变更的 Single Source of Truth。任何阶段开始 / 通过 / 失败都必须同步更新这里。

## 一句话目标

把 `_mineru_client.py` 适配真实 MinerU 3.1.14 API（X-API-Key / 202 / files 数组 / 单独 /result 端点），同步更新测试 fake；上游 change 上线后 live 即可跑通。

## 范围摘要

- **In scope**：4 处 API 对齐 + PdfMineruSpec.backend 字段 + 测试 fake 同步 + 新 self_check AC block（9 条）
- **Out of scope**：UI / Pipeline / 部署 / 图片表格公式 / 高级 MinerU 字段 / 上游 change history

## 阶段进度

| 阶段 | 状态 | 最新版本 | verdict | 阶段 commit | 产物 / 报告 |
|---|---|---|---|---|---|
| 1 需求分析 | done | v1 | — | TBD | [spec.md](request_analysis/spec.md) · [tasks.md](request_analysis/tasks.md) |
| 2 需求评审 | skipped | — | self-attest (会话级授权偏离 #1; 2026-05-19 用户授权 "一气呵成"演示; 上游 spec § deferred 预授权 client 改) | — | n/a |
| 3 编码实现 | | | | | [coding_report_v1.md](coding/coding_report_v1.md) |
| 4 编码评审 | skipped | — | self-attest (会话级授权偏离 #1) | — | n/a |
| 5 单测编写 | | | | | [test_report_v1.md](unit_test/test_report_v1.md) |
| 6 单测评审 | skipped | — | self-attest (会话级授权偏离 #1) | — | n/a |
| 7 代码推送 | | | | | _branch / push ref_ |
| 8 CI 验证 | | | | | [ci_result_v1.md](ci_result/ci_result_v1.md) |
| 9 部署验证 | | | | | [deploy_verify_v1.md](deployment/deploy_verify_v1.md) |
| 10 用户确认 | | | | | _确认人 / 时间_ |

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

- Branch：`change/processor-pdf-mineru-live-fix-20260519`
- PR：<链接>
- Merge commit：TBD（合并 PR 后填）
- 部署版本（如有）：`<image tag / release tag>`
- 用户确认：<人 / 时间>
- 关闭时间：TBD（stage 10 用户确认后填）

## 复盘（可选）

- 哪些步骤超预期顺利
- 哪些步骤踩坑：根因 + 防复发机制（一定要落到 rules / skills 的修订）
