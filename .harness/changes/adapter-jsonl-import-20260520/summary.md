---
change_id: adapter-jsonl-import-20260520
title: jsonl import adapter (W3-3)
owner: application-owner-agent
started_at: 2026-05-21T04:05:00Z
phase: verify
status: verify_approved
last_updated: 2026-05-21T04:45:00Z
related_changes:
  - adapter-raw-upload-20260520 (W3-1, AdapterRegistry + raw-upload 模板)
  - adapter-folder-md-assets-20260520 (W3-2, refs adapter 模板二次验证)
  - operator-protocol-20260520 (W1-2, SourceAdapter Protocol)
process_variant: v3-mini-design
---

# Summary

> v3 mini-design 流程（D-13）。第三个 refs-only adapter；强制单文件 + .jsonl(.gz) 后缀；line_count 透传 notes。

## 一句话目标

新增 `JsonlImportAdapter`：把"已上传 .jsonl 整文件"的 file refs 转 IngestResult（单文件 spec，整文件入 bronze，loader-jsonl 在 W3-6 拆行）。

## 范围摘要

- **In scope**：adapters/jsonl_import.py + adapters/__init__.py 加 auto-register + 4 个 behavioral pytest
- **Out of scope**：不拆行 / 不读取 JSONL（W3-6 loader 做）；不支持 .ndjson 别名；不接 apps/api；不做 manifest.yaml（D-1）

## 阶段进度

| 阶段 | 模型 | 状态 | verdict | commit | 产物 |
|---|---|---|---|---|---|
| Phase 1 Design | opus (application-owner 自写) | done | n/a (v3 无 Phase 1 reviewer) | c9b8fae | [design.md](design.md) |
| Phase 2 Implementation | sonnet | done | — | caf3d0e (impl) + b1a4de1 (impl.md) | [implementation.md](implementation.md) |
| Phase 3 Verify | opus | done | APPROVED | _本提交回填_ | [verify_review.md](verify_review.md) |

## 关键决策

| 时间 | 决策 | 理由 | 关联 |
|---|---|---|---|
| 2026-05-21 04:05 | 按 W3-1 / W3-2 refs-only adapter 模板复制 | 第三次复用同模式 | design.md § 决策 1 |
| 2026-05-21 04:05 | 整文件入 bronze（不拆行）| 拆行是 loader-jsonl 职责 | design.md § 决策 2 |
| 2026-05-21 04:05 | 强制 maxItems=1 单文件 | 语义清晰；多文件走 raw-upload | design.md § 决策 3 |
| 2026-05-21 04:05 | 支持 .jsonl.gz | 训练数据常用 gzip | design.md § 决策 4 |
| 2026-05-21 04:05 | line_count 透传到 IngestResult.notes | 避免改 Protocol；loader-jsonl 校验用 | design.md § 决策 5 |
| 2026-05-21 04:05 | 不做 manifest.yaml | D-1 永不做清单 | design.md § 决策 8 |

## Deferred 项

| 类型 | 描述 | 跟进位置 |
|---|---|---|
| follow-up (design) | apps/api routes + worker | `adapter-jsonl-import-route-*` |
| follow-up (design) | .ndjson 别名 | `adapter-jsonl-import-ndjson-alias-*` |
| follow-up (design) | magic byte 校验 | `adapter-jsonl-import-magic-byte-*` |
| 上游 | loader-jsonl bronze → silver rows | W3-6 `loader-jsonl-20260520` |

## 交付（merge 时回填）

- Branch：`change/adapter-jsonl-import-20260520`
- Merge commit：_待 merge 后填_
- 关闭时间：_待填_
