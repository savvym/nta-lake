---
change_id: cas-storage-20260517
version: 1
authored_at: 2026-05-17T04:10:00Z
status: waiting_review
---

# Test Report v1

> 测试在 stage 3 同步实跑通过——本报告归档。

## 验收项 ↔ 测试映射

| AC | 测试 | 文件 |
|---|---|---|
| AC-1 | `test_blobstore_is_runtime_checkable_protocol`（含 `_is_runtime_protocol == True` 断言）| packages/core/tests/test_storage_protocol.py |
| AC-2 | self_check AC-2（`from dataplat_core.protocols import BlobStore, BlobPutResult`）| scripts/_self_check.sh |
| AC-3 | self_check AC-3 + AC-5 | shell |
| AC-4 | self_check AC-4（合法构造 + 反逻辑非法 hex 必 raise） | shell |
| AC-5 | self_check AC-5（`isinstance(MinioBlobStore.__new__(...), BlobStore)`）| shell |
| AC-6 | self_check AC-6（pyproject 含 boto3/botocore） | shell |
| AC-7 / AC-8 / AC-9 / AC-10 / AC-11 / AC-12 / AC-13 | `test_put_get_roundtrip_and_missing_keyerror` / `test_put_same_bytes_is_deduplicated` / `test_exists_true_and_false` / `test_get_size_true_and_none` / `test_put_large_object_streaming` | apps/api/tests/test_minio_store.py |
| AC-14 | self_check AC-14（packages/core 子集，4 测全 PASS + collected ≥ 3） | shell |
| AC-15 | self_check AC-15（MinIO 探针前置，5 集成测全 PASS + collected ≥ 5） | shell |
| AC-16 | self_check AC-16（ruff + mypy） | shell |
| AC-17 | self_check AC-17（自递归） | shell |

每条 AC 至少一个断言；spec 17 AC 无孤立项。

## 测试文件清单

| 文件 | 类型 | 用例 |
|---|---|---|
| `packages/core/tests/test_storage_protocol.py` | 单元 | 4（runtime_checkable / roundtrip / storage_key 匹配 / 负向 size） |
| `apps/api/tests/test_minio_store.py` | 集成（MinIO 真连） | 5（roundtrip + KeyError / dedup + list_objects 唯一 final / exists / get_size / 2MB+17 stream + key pattern） |
| `scripts/_self_check.sh` cas-storage block | shell 断言 | 17 |

## Mock 范围声明

- packages/core：mock = 无（Pydantic 校验 / Protocol 形态）
- apps/api：mock = 无。直连 MinIO 容器（spec §1.7 禁 mock 数据访问层）。MinIO 不可达时 pytest.skip。

## 本地运行结果

```text
=== packages/core 全部 ===
29 passed in 0.48s  （25 已有 + 4 storage_protocol）

=== apps/api MinIO 集成 ===
$ cd apps/api && uv run pytest -q --tb=no tests/test_minio_store.py
.....                                                                    [100%]
5 passed in 0.72s

=== ruff + mypy ===
All checks passed!
Success: no issues found in 27 source files

=== self_check 全跑（DATAPLAT_PG_PORT=5433 DATAPLAT_MINIO_PORT=9100）===
PASS: 52 / FAIL: 0 / SKIP: 0
```

## 已知 flaky / 跳过

- 无 flaky；所有断言确定性
- MinIO 不可达时 AC-15 + AC-17 SKIP（探针前置）；不阻塞 verdict
- `_NOT_FOUND_CODES` 含 `NotFound` 是基于本机 MinIO 实测加入；不同 MinIO 版本可能返回不同 Code，加入集合是兼容保险

## 偏离 SKILL 标准

| 偏离 | 说明 |
|---|---|
| 集成测试用 store._bucket private | follow-up：BlobStore 加 bucket 公开属性 |
| 0 字节 stream put 未单独测 | NICE TO HAVE follow-up |
| delete 无集成测试 | spec §非范围明示 → retention follow-up 加级联 |

## ⚠️ 流程偏离

Stage 6 与 Stage 4 同 self-attest 路径，事由 + 等价证据见 coding_report / code_review v1 §流程偏离声明。
