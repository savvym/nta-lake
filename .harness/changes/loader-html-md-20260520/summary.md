---
change_id: loader-html-md-20260520
title: html/md loader (W3-4)
owner: application-owner-agent
started_at: 2026-05-21T05:00:00Z
phase: verify
status: verify_approved
last_updated: 2026-05-20T12:42:13Z
related_changes:
  - loader-refactor-pdf-mineru-20260520 (W1-4, Loader 实现模板)
  - operator-protocol-20260520 (W1-2, Loader Protocol + SilverRow)
  - adapter-raw-upload-20260520 (W3-1, auto-register 模式)
process_variant: v3-mini-design
---

# Summary

> v3 mini-design 流程（D-13）。packages/core 内首个真正 Loader 落地，为 W3-5 / W3-6 立模板。

## 一句话目标

新增 `HtmlMdLoader`：从 bronze blob 读 .md / .html，输出 1 SilverRow；stats 含 format / heading_count / char_count / image_ref_count；图片占位（不抓 blob）。

## 范围摘要

- **In scope**：loaders/html_md.py + loaders/__init__.py 加 auto-register + 4 个 behavioral pytest（含 stub BlobStore）
- **Out of scope**：不接 apps/api routes；不做 HTML 净化 / frontmatter；不抓真图片；不引入 markdown-it-py / bs4 依赖（stdlib re + html.parser）；不做 manifest.yaml（D-1）

## 阶段进度

| 阶段 | 模型 | 状态 | verdict | commit | 产物 |
|---|---|---|---|---|---|
| Phase 1 Design | opus (application-owner 自写) | done | n/a (v3 无 Phase 1 reviewer) | 7051395 | [design.md](design.md) |
| Phase 2 Implementation | sonnet | done | — | 8d71277 / 6d7030f | [implementation.md](implementation.md) |
| Phase 3 Verify | opus | done | APPROVED | _本次 commit_ | [verify_review.md](verify_review.md) |

## 关键决策

| 时间 | 决策 | 理由 | 关联 |
|---|---|---|---|
| 2026-05-21 05:00 | packages/core 内落 loader | 与 W3-1..3 同节奏；为 W3-5/W3-6 立模板 | design.md § 决策 1 |
| 2026-05-21 05:00 | 单文件 → 单 row | chunker operator 做拆分 | design.md § 决策 2 |
| 2026-05-21 05:00 | stdlib re + html.parser 解析 | 不引入新依赖 | design.md § 决策 4 |
| 2026-05-21 05:00 | 图片占位（image_ref_count + images=[]）| 不抓 blob；遵循 loader 不做强算子 | design.md § 决策 5 |
| 2026-05-21 05:00 | asyncio.run 内嵌 | 与 W1-4 PdfMineruLoader 同模式 | design.md § 决策 8 |
| 2026-05-21 05:00 | 不做 manifest.yaml | D-1 永不做清单 | design.md § 决策 9 |

## Deferred 项

| 类型 | 描述 | 跟进位置 |
|---|---|---|
| follow-up (design) | apps/api routes / worker | `loader-html-md-route-*` |
| follow-up (design) | HTML XSS 净化 | `loader-html-md-sanitize-*` |
| follow-up (design) | jekyll/hugo frontmatter 解析 | `loader-html-md-frontmatter-*` |
| follow-up (design) | Loader Protocol async 版本 | `loader-async-protocol-*` |
| follow-up (design) | 抓取相对/绝对图片 URL | `loader-html-md-image-fetch-*` |

## 交付（merge 时回填）

- Branch：`change/loader-html-md-20260520`
- Merge commit：_待 merge 后填_
- 关闭时间：_待填_
