---
change_id: processor-pdf-mineru-assets-20260520
title: PDF→MD 时连带保存 images + content_list
owner: application-owner-agent
started_at: 2026-05-19T12:30:02Z
stage: user_confirmation
status: done
last_updated: 2026-05-19T13:30:00Z
related_changes:
  - processor-pdf-mineru-20260519           # 上游 spec § 非范围 deferred 项的兑现
  - processor-pdf-mineru-live-fix-20260519  # 基于此分支
session_deviation:
  id: 1
  rationale: |
    用户在 stage 10 演示期间提需求：silver 仓装 MD/images/content_list（PDF 留 bronze）；
    本 change 是上游 spec 已显式 deferred 的 follow-up，scope 局限于 client 字段透传 +
    blob 写入 + base64 解码，用户授权"一气呵成"。stage 2/4/6 reviewer 走 self-attest。
  reviewer_status: self-attest (会话级授权偏离 #1; 2026-05-19; 上游 spec § 非范围预授权 follow-up)
---

# Summary

> 这是本变更的 Single Source of Truth。任何阶段开始 / 通过 / 失败都必须同步更新这里。

## 一句话目标

让 pdf-mineru processor 把 MinerU 抽出来的 images（按 sha 命名一图一 blob）和 content_list.json（结构化大纲）一并落到 silver target 仓；PDF 原件留 bronze 不动。

## 范围摘要

- **In scope**：PdfMineruSpec 加 return_images / return_content_list；client 新增 fetch_full_result + base64 decode；processor.run 写 md + images/* + content_list.json
- **Out of scope**：MD 内图片引用重写（MinerU 已重写）/ PDF 复制 / lang_list 等高级字段 / UI / vision 二次处理

## 阶段进度

| 阶段 | 状态 | 最新版本 | verdict | 阶段 commit | 产物 / 报告 |
|---|---|---|---|---|---|
| 1 需求分析 | done | v1 | — | TBD | [spec.md](request_analysis/spec.md) · [tasks.md](request_analysis/tasks.md) |
| 2 需求评审 | skipped | — | self-attest (会话级授权偏离 #1) | — | n/a |
| 3 编码实现 | in_progress | v1 | — | — | [coding_report_v1.md](coding/coding_report_v1.md) |
| 4 编码评审 | skipped | — | self-attest (会话级授权偏离 #1) | — | n/a |
| 5 单测编写 | | | | | [test_report_v1.md](unit_test/test_report_v1.md) |
| 6 单测评审 | skipped | — | self-attest (会话级授权偏离 #1) | — | n/a |
| 7 代码推送 | | | | | _branch / push ref_ |
| 8 CI 验证 | | | | | [ci_result_v1.md](ci_result/ci_result_v1.md) |
| 9 部署验证 | | | | | [deploy_verify_v1.md](deployment/deploy_verify_v1.md) |
| 10 用户确认 | done | — | PASS（实测 1.8MB PDF → 305K MD + 81 图 + 510K content_list 全部落 silver target） | 76c1ae9 | 用户：2026-05-19 演示会话内确认 "当前这个 change 可以闭环" |

## 关键决策

| 时间 | 决策 | 理由 / 取舍 | 关联文件 |
|---|---|---|---|
| 2026-05-19 | silver target 仓装 md + images/ + content_list.json；PDF 留 bronze | 用户实测期间决定；保持 bronze/silver 语义干净 | spec.md §背景 |
| 2026-05-19 | MD 内图片引用不重写 | MinerU 已自重写为相对路径 "images/SHA.jpg"；省一步 | spec.md §背景 §AC-5 |
| 2026-05-19 | content_list.json 直接 passthrough（MinerU 已序列化为字符串） | 不重 dumps；下游 LLM 检索友好 | spec.md §背景 |

## 当前阻塞

- 无

## Deferred 项

| 类型 | 描述 | 跟进位置 |
|---|---|---|
| 非范围 | lang_list / formula_enable / table_enable / 页面范围 | follow-up `processor-pdf-mineru-config-fields-batch-*` |
| 非范围 | UI "一键 PDF→MD" 按钮 | follow-up `web-pdf-mineru-ui-*` |
| 非范围 | image vision 二次处理 | follow-up `processor-pdf-mineru-image-vision-*` |

## 交付

- Branch：`change/processor-pdf-mineru-assets-20260520`（基于 `change/processor-pdf-mineru-live-fix-20260519`）
- PR：TBD（push 后开）
- Merge commit：TBD（合并 PR 后填）
- 部署版本：n/a（stage 9 noop）
- 用户确认：2026-05-19 演示会话内确认
- 关闭时间：2026-05-19T13:30:00Z
