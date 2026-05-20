---
change_id: adapter-folder-md-assets-20260520
title: folder md+assets adapter (W3-2)
owner: application-owner-agent
started_at: 2026-05-21T03:05:00Z
phase: design
status: design_approved
last_updated: 2026-05-21T03:05:00Z
related_changes:
  - adapter-raw-upload-20260520 (W3-1, AdapterRegistry + raw-upload 模板)
  - operator-protocol-20260520 (W1-2, SourceAdapter Protocol)
process_variant: v3-mini-design
---

# Summary

> v3 mini-design 流程（D-13）。按 W3-1 raw-upload 模板复制 + 加 path safety + asset/md 元数据。

## 一句话目标

新增 `FolderMdAssetsAdapter` 到 packages/core/adapters/：把"已上传 zip / 文件夹内 `*.md + ./assets/*`"的 file refs 转 IngestResult，保留相对路径并做 path-safety 校验。

## 范围摘要

- **In scope**：adapters/folder_md_assets.py + adapters/__init__.py 加 auto-register + 4 个 behavioral pytest
- **Out of scope**：不实际解压 zip / 不做 multipart 接收（W3-1 上传链路覆盖）；不改 apps/api（apps/api 接 core registry 留 follow-up）；不做 content-type sniff；不做 manifest.yaml（D-1 永不做清单）

## 阶段进度

| 阶段 | 模型 | 状态 | verdict | commit | 产物 |
|---|---|---|---|---|---|
| Phase 1 Design | opus (application-owner 自写) | done | n/a (v3 无 Phase 1 reviewer) | _待回填_ | [design.md](design.md) |
| Phase 2 Implementation | sonnet | pending | — | — | [implementation.md](implementation.md) |
| Phase 3 Verify | opus | pending | — | — | [verify_review.md](verify_review.md) |

## 关键决策

| 时间 | 决策 | 理由 | 关联 |
|---|---|---|---|
| 2026-05-21 03:05 | 按 W3-1 raw-upload 模板复制 refs-only adapter | Wave 3 adapter 系列标准切口 | design.md § 决策 1 |
| 2026-05-21 03:05 | path safety 用 PurePosixPath.parts 检查 `..` | 跨平台一致；不依赖 OS | design.md § 决策 2 |
| 2026-05-21 03:05 | asset_count = 非 .md 文件数 | 语义直观 | design.md § 决策 3 |
| 2026-05-21 03:05 | 至少 1 个 .md 必需 | 让 adapter 选择有信息量；否则走 raw-upload | design.md § 决策 4 |
| 2026-05-21 03:05 | 不做 manifest.yaml | D-1 永不做清单 | design.md § 决策 7 |

## Deferred 项

| 类型 | 描述 | 跟进位置 |
|---|---|---|
| follow-up (design) | apps/api 加 POST /repos/.../folder-md-assets 路由 + worker | `adapter-folder-md-assets-route-*` |
| follow-up (design) | content-type 推断（png/jpg/webp） | `adapter-folder-md-assets-mime-sniff-*` |
| follow-up (design) | 服务端 zip 流式解压 + 自动 sha256 | `adapter-folder-md-assets-zip-stream-*` |

## 交付（merge 时回填）

- Branch：`change/adapter-folder-md-assets-20260520`
- Merge commit：_待 merge 后填_
- 关闭时间：_待填_
