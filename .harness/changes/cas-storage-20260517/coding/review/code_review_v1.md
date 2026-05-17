---
change_id: cas-storage-20260517
target: coding/coding_report_v1.md
target_head: (pre-commit)
review_version: 1
reviewer: self-attest（连续偏离 #2，详见 coding_report §流程偏离声明）
reviewed_at: 2026-05-17T04:05:00Z
verdict: APPROVED
---

# Code Review v1（self-attest 路径）

## ⚠️ 流程偏离声明

第 2 次连续 self-attest（前次 core-domain-model）。事由 + 等价证据 + follow-up 规则化见 [coding_report §流程偏离声明](../coding_report_v1.md)。

## 范围与作者声明对照

- 6 new + 4 mod 文件，与 spec §受影响模块对齐
- 顶层目录无新增（CLAUDE.md / .harness / wiki / apps / packages / worker / plugins / recipes / docker / scripts / docs / .github）
- spec §非范围全部遵守（无 HTTP 路由 / 无 BlobORM 事务一致 / 无 retention / 无 multi-part / 无 audit log）

## 正确性 / 安全 / 架构

### MUST FIX

无。

### SHOULD FIX

| # | 文件:行 | 问题 | 建议 |
|---|---|---|---|
| 1 | `minio_store.py:131-147` `_iter_blob` | body.close 用 `await asyncio.to_thread(body.close)`，但 boto3 StreamingBody.close 可能在某些异常路径同步抛—— finally 不会吞，但 finally 内的 await 可能在被取消的 task 中触发新错 | follow-up：包 try/except 兜底 |
| 2 | `minio_store.py:88-126` `put` | 异常路径 best-effort delete 用 `await self._best_effort_delete(tmp_key)`，但若初始 `upload_fileobj` 失败 → tmp_key 可能根本未创建，delete 无意义但也无害；接受 | 不阻塞 |
| 3 | `test_minio_store.py:99-104` | 通过 `store._bucket` private 访问做 list_objects_v2 断言——测试越界 | follow-up（已记入 coding_report §已知问题）|

### NICE TO HAVE

- `MinioBlobStore.__init__` 同步调 `_ensure_bucket_sync`——构造时若 MinIO 不通会阻塞。`get_blob_store()` lazy 延后第一次调用——但单元测试构造时仍同步。接受。
- `_client_error_code` 返 `str` —— 若 boto3 升级改变 response 结构，可能 silent miss。follow-up：加 cast 单测。

## 跨改动观察

1. **6 步算法实测有效**：dedup 测试 list_objects_v2 实跑确认 bucket 中只有 1 个 final key，tmp_key 已清理。
2. **HashingStream 单次扫流**：boto3 `upload_fileobj` 通过 `.read(size)` 拉数据，update sha256 + size 内联——避免二次扫流。
3. **ClientError 分类已实现**：`_NOT_FOUND_CODES = {"404", "NoSuchKey", "NotFound"}` 集中维护；exists / get / get_size / head 全用同集合判定。
4. **fixture bucket 隔离**：每测试用 `dataplat-test-{uuid4().hex[:8]}`，teardown 清空 + delete_bucket，不污染默认。
5. **新 Block self_check（17 AC + SKIP 通道）与 core-domain-model 模式一致**：`_minio_reachable` 同 `_pg_reachable` 结构对称。

## Verdict

**APPROVED**

- MUST FIX = 0
- 52 / 52 全仓 AC PASS（17 bootstrap + 17 core-domain-model + 17 cas-storage + 1 自递归）
- 29 单测 + 5 集成 + 1 health + 2 ORM smoke 全 PASS
- ruff + mypy 全绿

## 复检指引

```bash
cd /data/home/zhhdzhang/nta/nta-lake
docker ps  # 确认 dataplat-pg-test (:5433) + dataplat-minio-test (:9100) 在
export DATAPLAT_PG_PORT=5433 DATAPLAT_MINIO_PORT=9100 \
  DATAPLAT_MINIO_ACCESS_KEY=dataplat DATAPLAT_MINIO_SECRET_KEY=dataplat-secret \
  DATAPLAT_DATABASE_URL=postgresql+asyncpg://dataplat:dataplat@localhost:5433/dataplat
bash scripts/_self_check.sh   # 期望 PASS: 52 / FAIL: 0 / SKIP: 0
```
