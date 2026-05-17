---
change_id: adapter-framework-20260517
title: Adapter Framework + RawFileUploadAdapter（MVP in-process）
owner: zhhdzhang
started_at: 2026-05-17T11:00:00Z
closed_at: 2026-05-17T12:10:00Z
stage: closed
status: closed
last_updated: 2026-05-17T12:10:00Z
related_changes:
  - core-domain-model-20260516
  - cas-storage-20260517
  - repo-api-mvp-20260517
  - commit-api-mvp-20260517
---

# Summary

## 一句话目标

落 design.md §4.1 + §6.1 + §9 Phase 1 #2 Adapter 框架最小子集：AdapterRegistry + AdapterRunner + RawFileUploadAdapter + `POST /repos/{o}/{n}/ingest` 路由，让 Bronze 录入路径打通（解锁后续 processor / pipeline / LLM 调用链）。

## 范围摘要

- **In scope**：IngestResult.files schema 升级 / Adapter Registry / StandardRunContext / AdapterRunner（in-process）/ RawFileUploadAdapter / ingest schema + 路由 / 测试 ≥ 12 + self_check 13 AC
- **Out of scope**：RQ 异步执行（next change）/ subprocess L2 隔离 / 第二个 adapter / Adapter Registry 持久化 / ctx.metrics-secrets-llm 实质实现

## 关键决策

| 时间 | 决策 | 理由 |
|---|---|---|
| 2026-05-17 | Adapter 输出契约用 `IngestResult.files` 而非 workspace 文件扫描 | RawFileUpload 不写盘；统一不耦合 BlobStore |
| 2026-05-17 | 注册机制用代码 import 静态注册（非 entrypoints） | MVP 只有 L1 内置；entrypoints 留给 L2 |
| 2026-05-17 | 执行模型 in-process + asyncio.to_thread；非 RQ | RQ 下个 change；本变更聚焦 framework |
| 2026-05-17 | IngestResult 升级走加字段（非新类型） | 既有 33 个 core 测试不破坏 |
| 2026-05-17 | RawFileUpload 不生成 manifest.yaml | 减依赖；manifest 由 client 单独上传作为普通文件 |

## 阶段进度

| 阶段 | 状态 |
|---|---|
| 1 需求分析 | done（spec v2） |
| 2 需求评审 | done（reviewer v1 4 MUST FIX → v2 APPROVED；SKILL 反哺 4→7 条） |
| 3 编码实现 | done（9 个 T-* + SKILL 反哺） |
| 4 编码评审 | done（reviewer v1 APPROVED 0 MUST FIX，5 SHOULD FIX deferred） |
| 5 单测编写 | done（13 测试 a~m，含 m parent 链回归） |
| 6 单测评审 | done（reviewer v1 APPROVED 0 MUST FIX；test_j 命名 SHOULD FIX 已修） |
| 7 代码推送 | done（session 直推 main 等价） |
| 8 CI 验证 | done（self_check adapter-framework 13/13 + 全仓 108/108） |
| 9 部署验证 | skipped: 无运行时部署面 |
| 10 用户确认 | done（会话级授权） |

## 当前阻塞

- 无。

## Follow-ups（spec deferred + stage 4/6 SHOULD FIX）

- `rq-worker-skeleton-*`：异步执行 + RQ queue + thread pool 容量评估（next change）
- `adapter-subprocess-isolation-*`：L2 plugin subprocess 隔离（Phase 2）
- `adapter-firecrawl-*`：第二个 adapter（FirecrawlURL）
- `adapter-pdf-to-text-*` / `adapter-book-archive-*` 等
- `workspace-gc-*`：进程崩溃后 workspace 残留清理
- `adapter-narrow-except-*`（stage 4 S1）：raw_upload `except Exception` 改窄
- `test-teardown-error-propagate-*`（stage 4 S2）：fixture teardown 不再吞 Exception
- `runcontext-run-id-*`（stage 4 S3）：注入 run_id 到 logger / metrics
- `router-helper-extract-*`（stage 4 S4）：_resolve_repo 抽公共 helper（commits + ingest 共用）
- `adapter-lineage-emit-*`（stage 4 S5）：具体 adapter 写入 lineage
