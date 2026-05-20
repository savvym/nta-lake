---
change_id: loader-docx-pptx-20260520
title: docx/pptx loader (W3-5)
owner: application-owner-agent
started_at: 2026-05-21T05:50:00Z
phase: verify
status: verify_approved
last_updated: 2026-05-21T06:30:00Z
related_changes:
  - loader-html-md-20260520 (W3-4, packages/core loader 模板)
  - loader-refactor-pdf-mineru-20260520 (W1-4, 图片写 blob_store 模板)
  - operator-protocol-20260520 (W1-2, Loader Protocol)
process_variant: v3-mini-design
---

# Summary

> v3 mini-design 流程（D-13）。Wave 3 首次引入第三方依赖（python-docx + python-pptx）；测试 fixture 运行时构造，不引入二进制资源。

## 一句话目标

新增 `DocxLoader` + `PptxLoader`：从 bronze blob 读 .docx / .pptx，输出 1 SilverRow；正文文本 + 图片提取写 blob_store；stats 含 format/paragraph_count or slide_count/image_count/char_count。

## 范围摘要

- **In scope**：loaders/docx.py + loaders/pptx.py + __init__.py auto-register + pyproject.toml 加 2 依赖 + 6 个 behavioral pytest（3 docx + 3 pptx）
- **Out of scope**：不接 apps/api；不做 docx 表格/footnote/tracked-changes；不做 pptx 备注页/动画；不做 OCR；不做 .doc/.ppt OLE；不抓 video/audio；不做 manifest.yaml（D-1）

## 阶段进度

| 阶段 | 模型 | 状态 | verdict | commit | 产物 |
|---|---|---|---|---|---|
| Phase 1 Design | opus (application-owner 自写) | done | n/a (v3 无 Phase 1 reviewer) | 57bf70a | [design.md](design.md) |
| Phase 2 Implementation | sonnet | done | n/a | 91b215f / c0cb178 | [implementation.md](implementation.md) |
| Phase 3 Verify | opus | done | APPROVED | _待 merge 后回填_ | [verify_review.md](verify_review.md) |

## 关键决策

| 时间 | 决策 | 理由 | 关联 |
|---|---|---|---|
| 2026-05-21 05:50 | 两个独立 Loader 类 + 独立文件 | docx/pptx schema 完全不同 | design.md § 决策 1 |
| 2026-05-21 05:50 | 图片真抓不占位（vs W3-4 占位）| roadmap "图片提取到 images column" | design.md § 决策 2 |
| 2026-05-21 05:50 | 引入 python-docx + python-pptx | Wave 3 第一次新增第三方依赖；pure-Python | design.md § 决策 3 |
| 2026-05-21 05:50 | 测试 fixture 运行时构造 | 不引入二进制资源；用库本身现场生成 | design.md § 决策 4 |
| 2026-05-21 05:50 | content_type 写到 images 列元数据 | caller 按 jpg/png 分支处理 | design.md § 决策 8 |
| 2026-05-21 05:50 | 不做 manifest.yaml | D-1 永不做清单 | design.md § 决策 9 |

## Deferred 项

| 类型 | 描述 | 跟进位置 |
|---|---|---|
| follow-up (design) | apps/api routes | `loader-docx-route-*` / `loader-pptx-route-*` |
| follow-up (design) | docx 表格 / pptx 备注页 | `loader-docx-pptx-tables-*` |
| follow-up (design) | .doc / .ppt OLE 格式 | `loader-doc-ppt-ole-*` |
| follow-up (design) | track changes | `loader-docx-pptx-track-changes-*` |
| follow-up (design) | Loader Protocol async | `loader-async-protocol-*` |

## 交付（merge 时回填）

- Branch：`change/loader-docx-pptx-20260520`
- Merge commit：_待 merge 后填_
- 关闭时间：_待填_
