---
change_id: cas-storage-20260517
title: BlobStore Protocol + MinioBlobStore 实现 + sha256 去重 / CAS 寻址
owner: zhhdzhang
started_at: 2026-05-17T03:00:00Z
stage: request_analysis
status: in_progress
last_updated: 2026-05-17T03:00:00Z
related_changes:
  - bootstrap-monorepo-20260516
  - core-domain-model-20260516
---

# Summary

## 一句话目标

按 [.harness/design.md](../../design.md) §4.4 / §5.2 落地 CAS（内容寻址存储）：`packages/core` 定义 `BlobStore` Protocol；`apps/api` 提供 `MinioBlobStore` 实现（基于 boto3 S3 客户端兼容 MinIO）；blob key 严格遵循 `blobs/{sha256[0:2]}/{sha256}` 规范；同字节内容 put 两次只产生一个 storage 对象（sha256 去重）；blobs ORM 表写入与 storage 写入保持一致。

## 范围摘要

- **In scope**：
  - `packages/core/src/dataplat_core/protocols/storage.py`：`BlobStore` Protocol（**5 个方法**：put / get / exists / get_size / delete）+ `BlobPutResult` 数据类。**`iter_keys` 不在本变更范围**（list / pagination 留 retention follow-up）
  - `apps/api/dataplat_api/storage/__init__.py` + `minio_store.py`：`MinioBlobStore` 实现（boto3-based）+ 工厂 `get_blob_store()`
  - `apps/api/dataplat_api/storage/keys.py`：`storage_key_for(sha256: str) -> str` 工具，统一返回 `blobs/{sha256[0:2]}/{sha256}`
  - apps/api/pyproject.toml：+`boto3>=1.34`、+`botocore>=1.34`
  - 单测：`packages/core/tests/test_storage_protocol.py`（Protocol 形式正确性）+ `apps/api/tests/test_minio_store.py`（集成：MinIO 真连 put/get/exists/dedup/key 规范 + 大对象流式 ≥ 2MB）
  - `scripts/_self_check.sh` 追加 cas-storage block
- **Out of scope**：
  - **不引入 HTTP 路由**（上传 / 下载留给 `repo-api-mvp`）
  - **不实现 BlobORM 写入与 BlobStore 写入的事务一致**（仍由后续 service 层做；本变更只把 storage 操作做出来）
  - 不实现 retention / GC / purge（design.md §10 #3 单独 follow-up）
  - 不实现 streaming chunked upload（直接 put_object；多 part 留给后续）
  - 不接入认证 / per-bucket ACL

## 阶段进度

| 阶段 | 状态 | 最新版本 | verdict | 产物 / 报告 |
|---|---|---|---|---|
| 1 需求分析 | in_progress | v1 | — | [spec.md](request_analysis/spec.md) · [tasks.md](request_analysis/tasks.md) |
| 2 需求评审 | pending（独立 reviewer 子会话）| — | — | — |
| 3 编码实现 | pending | — | — | — |
| 4 编码评审 | pending（独立 reviewer 子会话）| — | — | — |
| 5 单测编写 | pending | — | — | — |
| 6 单测评审 | pending（独立 reviewer 子会话）| — | — | — |
| 7 代码推送 | pending | — | — | — |
| 8 CI 验证 | 本地等价 | — | — | — |
| 9 部署验证 | skipped: 无运行时部署面 | — | — | — |
| 10 用户确认 | 用户会话级授权 Generator 自我确认 | — | — | — |

## 关键决策

| 时间 | 决策 | 理由 |
|---|---|---|
| 2026-05-17 | 用 boto3 作 MinIO S3 客户端 | design.md §11.2 已选 boto3；MinIO S3 兼容协议官方支持 |
| 2026-05-17 | blob key 严格 `blobs/{sha256[0:2]}/{sha256}` 在 `storage_key_for(sha256)` 工具中实现 | 与 design.md §5.2 一致；让所有 producer / consumer 共用单源 |
| 2026-05-17 | sha256 在 client 侧计算（put 接受 bytes 或 file-like，put 内部 hashlib.sha256 流式）| 不信任 caller 提供的 hash；CAS 语义要求 server 自己算 |
| 2026-05-17 | 已存在的 blob put 直接返回成功（idempotent）| 去重是 CAS 的核心价值 |
| 2026-05-17 | 流式 put（≥ 2MB 测试）用 boto3 upload_fileobj | 大对象避免全量加载内存 |
| 2026-05-17 | 恢复完整 Generator/Reviewer 分离 | core-domain-model 的 self-attest 是一次性偏离；本变更 stage 2/4/6 启独立 reviewer 子会话 |

## 当前阻塞

- Stage 1 进行中。

## Deferred 项

> 评审通过后填。
