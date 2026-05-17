---
change_id: cas-storage-20260517
version: 1
authored_at: 2026-05-17T03:10:00Z
---

# Tasks

## 任务清单

```yaml
tasks:
  - id: T-1
    title: packages/core protocols/storage.py - BlobStore Protocol + BlobPutResult
    description: |
      `@typing.runtime_checkable` 装饰的 `Protocol`（spec MUST FIX-1：必须让 `BlobStore._is_runtime_protocol == True` 为 True）；
      async 方法签名 `async def put(self, stream: BinaryIO, *, declared_size: int | None = None) -> BlobPutResult`（spec MUST FIX-3：stream 显式 BinaryIO）
      / `async def get(self, sha256: str) -> AsyncIterator[bytes]` / `async def exists(self, sha256: str) -> bool` /
      `async def get_size(self, sha256: str) -> int | None` / `async def delete(self, sha256: str) -> bool`；
      BlobPutResult Pydantic BaseModel(sha256, size, storage_key, deduplicated)。
      **5 个方法（无 iter_keys）**，与 spec 一致。
    depends_on: []
    estimated_stage: coding
    covers_ac: [AC-1]
    status: pending

  - id: T-2
    title: packages/core protocols/__init__.py 暴露 BlobStore + BlobPutResult
    description: __all__ 加 BlobStore / BlobPutResult；不破坏已有 8 个 protocol
    depends_on: [T-1]
    estimated_stage: coding
    covers_ac: [AC-2]
    status: pending

  - id: T-3
    title: apps/api/pyproject.toml + boto3 / botocore 依赖
    description: 加 boto3>=1.34 / botocore>=1.34
    depends_on: []
    estimated_stage: coding
    covers_ac: [AC-6]
    status: pending

  - id: T-4
    title: apps/api/dataplat_api/storage/keys.py
    description: storage_key_for(sha256) -> str；输入校验 ^[0-9a-f]{64}$，否则 raise ValueError
    depends_on: []
    estimated_stage: coding
    covers_ac: [AC-3, AC-4]
    status: pending

  - id: T-5
    title: apps/api/dataplat_api/storage/__init__.py - 工厂 get_blob_store()
    description: 从 env 读 endpoint / access / secret / bucket / region；module-level lazy 单例
    depends_on: [T-6]
    estimated_stage: coding
    covers_ac: [AC-3, AC-5]
    status: pending

  - id: T-6
    title: apps/api/dataplat_api/storage/minio_store.py - MinioBlobStore 实现
    description: |
      构造参数 endpoint_url / access_key / secret_key / bucket / region；_ensure_bucket() 启动时 head + 按需 create。
      **put 严格按 spec AC-7 6 步算法**（spec MUST FIX-2）：
        (1) tmp_key=`_tmp/{uuid4()}.part`
        (2) HashingStream 包装 BinaryIO（read 同步 update sha256 + size）
        (3) to_thread(s3.upload_fileobj, hashing_stream, bucket, tmp_key)
        (4) final_key=storage_key_for(hex_sha256)
        (5) head_object(final_key)：成功→delete_object(tmp_key)+deduplicated=True；ClientError 404/NoSuchKey→copy_object(src=tmp_key,dst=final_key)+delete_object(tmp_key)+deduplicated=False
        (6) 异常路径 best-effort delete_object(tmp_key) 不吞 caller exception
      get：async generator，from `get_object['Body'].iter_chunks(...)` yield；首次 __anext__ 若 ClientError 404/NoSuchKey raise KeyError。
      exists：head_object 捕 404/NoSuchKey 返 False；NoSuchBucket / 其他 ClientError bubble up。
      get_size：head_object ContentLength；不存在返 None。
      delete：head_object 决定返回值；delete_object（idempotent）。
      所有 sync boto3 调用包 asyncio.to_thread。
    depends_on: [T-1, T-3, T-4]
    estimated_stage: coding
    covers_ac: [AC-5, AC-7, AC-8, AC-9, AC-10, AC-11, AC-12, AC-13]
    status: pending

  - id: T-7
    title: packages/core/tests/test_storage_protocol.py（≥ 3 测试）
    description: |
      test_blobstore_protocol_runtime_checkable / test_blobput_result_roundtrip /
      test_blobput_result_storage_key_matches_helper
    depends_on: [T-1]
    estimated_stage: unit_test
    covers_ac: [AC-14]
    status: pending

  - id: T-8
    title: apps/api/tests/test_minio_store.py（≥ 5 集成测试）
    description: |
      put + get round-trip（小对象） / put 同字节去重 / exists / get_size /
      put 2MB 随机字节 + sha256 与 hashlib 一致 + key pattern；
      fixture 每测一个 MinioBlobStore（fresh），用 uuid 前缀 bucket 避免污染
    depends_on: [T-6]
    estimated_stage: unit_test
    covers_ac: [AC-15]
    status: pending

  - id: T-9
    title: scripts/_self_check.sh 追加 cas-storage block
    description: |
      17 AC self-check；MinIO 探针 socket connect ${DATAPLAT_MINIO_PORT:-9000}；
      探针失败整 block SKIP；保留 PASS/FAIL/SKIP 汇总
    depends_on: [T-7, T-8]
    estimated_stage: unit_test
    covers_ac: [AC-17]
    status: pending
```

## 阶段任务

```yaml
process_tasks:
  - id: P-spec-review
    estimated_stage: request_analysis_review
    status: pending
  - id: P-code-review
    estimated_stage: coding_review
    status: pending
  - id: P-test-review
    estimated_stage: unit_test_review
    status: pending
  - id: P-push
    estimated_stage: push
    status: pending
    reason: 本地 commit
  - id: P-ci
    estimated_stage: ci_result
    status: pending
    reason: 本地等价 self_check.sh + ruff + mypy + pytest
  - id: P-deploy
    estimated_stage: deployment
    status: skipped
    reason: 无运行时部署面
  - id: P-user-confirm
    estimated_stage: user_confirmation
    status: pending
    reason: 用户会话级授权由 Generator 自我确认
```

## DAG 健全性

- T-2 → T-1
- T-5 → T-6
- T-6 → T-1, T-3, T-4
- T-7 → T-1
- T-8 → T-6
- T-9 → T-7, T-8

无循环。

## 验收覆盖矩阵

| AC | 关联任务 |
|---|---|
| AC-1 | T-1 |
| AC-2 | T-2 |
| AC-3 | T-4, T-5 |
| AC-4 | T-4 |
| AC-5 | T-6（实现）；T-5 仅暴露 import path 间接关联 |
| AC-6 | T-3 |
| AC-7 | T-6 |
| AC-8 | T-6 |
| AC-9 | T-6 |
| AC-10 | T-6 |
| AC-11 | T-6 |
| AC-12 | T-6 |
| AC-13 | T-6 |
| AC-14 | T-7 |
| AC-15 | T-8 |
| AC-16 | 全部 |
| AC-17 | T-9 |
