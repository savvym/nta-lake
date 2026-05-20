---
change_id: loader-jsonl-20260520
title: jsonl loader (W3-6)
owner: application-owner-agent
started_at: 2026-05-21T06:35:00Z
phase: verify
status: verify_approved
last_updated: 2026-05-20T13:11:18Z
related_changes:
  - adapter-jsonl-import-20260520 (W3-3, 上游 adapter)
  - loader-html-md-20260520 (W3-4, packages/core loader 模板)
  - loader-docx-pptx-20260520 (W3-5, 多 loader auto-register 模板)
  - operator-protocol-20260520 (W1-2, Loader Protocol)
process_variant: v3-mini-design
---

# Summary

> v3 mini-design 流程（D-13）。第 4 个 packages/core loader；W3-3 上下游配对（adapter 整文件入 bronze → loader 拆行成 silver rows）。

## 一句话目标

新增 `JsonlLoader`：从 bronze blob 读 .jsonl / .jsonl.gz，每行 JSON object → 1 个 SilverRow；坏行跳过 + error_count 计数不抛；stats 含 format / char_count；全局 notes 含 line_count / error_count。

## 范围摘要

- **In scope**：loaders/jsonl.py + loaders/__init__.py auto-register + 4 个 behavioral pytest（auto-register + 明文 happy + gz happy + no blob_store）
- **Out of scope**：不接 apps/api；不做 prompt/completion 对模式；不抓行内嵌图片；不做嵌套字段；不流式；不引入新依赖（stdlib json + gzip）；不做 manifest.yaml（D-1）

## 阶段进度

| 阶段 | 模型 | 状态 | verdict | commit | 产物 |
|---|---|---|---|---|---|
| Phase 1 Design | opus (application-owner 自写) | done | n/a (v3 无 Phase 1 reviewer) | _待回填_ | [design.md](design.md) |
| Phase 2 Implementation | sonnet | done | — | 894c059 + 6d14f58 | [implementation.md](implementation.md) |
| Phase 3 Verify | opus | done | APPROVED | _待回填_ | [verify_review.md](verify_review.md) |

## 关键决策

| 时间 | 决策 | 理由 | 关联 |
|---|---|---|---|
| 2026-05-21 06:35 | 每行 1 row（行级 1→N）| jsonl 天然每行 1 训练样本 | design.md § 决策 1 |
| 2026-05-21 06:35 | 坏行跳过 + error_count 计数不抛 | jsonl 训练集常含少量 malformed 行；fail-fast 不友好 | design.md § 决策 2 |
| 2026-05-21 06:35 | default text_field="text" 可由 config 覆盖 | HF SFTTrainer 标准 | design.md § 决策 3 |
| 2026-05-21 06:35 | stdlib json + gzip | 不引入新依赖 | design.md § 决策 4 |
| 2026-05-21 06:35 | per-row stats 极简 + 全局放 notes | 避免 row stats 冗余 | design.md § 决策 6 |
| 2026-05-21 06:35 | source_ref 加 line_no（1-based）| 多 row 场景需追溯到 bronze 原行 | design.md § 决策 7 |
| 2026-05-21 06:35 | 不做 manifest.yaml | D-1 永不做清单 | design.md § 决策 10 |

## Deferred 项

| 类型 | 描述 | 跟进位置 |
|---|---|---|
| follow-up (design) | apps/api routes | `loader-jsonl-route-*` |
| follow-up (design) | prompt/completion 对模式 | `loader-jsonl-prompt-completion-*` |
| follow-up (design) | 行内嵌图片 URL / base64 抓取 | `loader-jsonl-image-extract-*` |
| follow-up (design) | 嵌套字段提取 | `loader-jsonl-nested-field-*` |
| follow-up (design) | 流式 Loader Protocol | `loader-async-stream-protocol-*` |

## 交付（merge 时回填）

- Branch：`change/loader-jsonl-20260520`
- Merge commit：_待 merge 后填_
- 关闭时间：_待填_
