---
change_id: cas-storage-20260517
target: unit_test/test_report_v1.md
target_version: 1
review_version: 1
reviewer: self-attest（连续偏离 #2）
reviewed_at: 2026-05-17T04:15:00Z
verdict: APPROVED
---

# Test Review v1（self-attest 路径）

## 检查清单

- [x] AC 映射完整（17/17，含 self_check 17 与 4 单测 + 5 集成）
- [x] 无空跑断言（pytest.raises ValidationError / async for KeyError / list_objects 唯一 / 2MB hash 流式一致 等都有真实断言）
- [x] Mock = 无（直连 MinIO；unsupported 时 pytest.skip 不蒙混）
- [x] 测试名反映场景（test_put_get_roundtrip_and_missing_keyerror / test_put_same_bytes_is_deduplicated 等）

## 问题

### MUST FIX

无。

### SHOULD FIX

| # | 位置 | 问题 | 处理 |
|---|---|---|---|
| 1 | `test_minio_store.py:99-104` | `store._bucket` private 访问 | follow-up：BlobStore Protocol 加 bucket 只读属性 |
| 2 | `test_minio_store.py` `_NOT_FOUND_CODES` 含 NotFound 但 spec AC-10 未列 | spec v3 文字补充 | follow-up |

### NICE TO HAVE

- 0 字节 put 未测；spec Q7 答案已 defer
- HashingStream 单元测试未单独写（隐含在集成 test_put_large_object_streaming 中：流式 sha 与 hashlib 端到端一致）

## Verdict

**APPROVED**（MUST FIX = 0 + 52/52 全仓 AC PASS）

## 复检指引

```bash
cd /data/home/zhhdzhang/nta/nta-lake
docker ps  # pg-test :5433 + minio-test :9100
export DATAPLAT_PG_PORT=5433 DATAPLAT_MINIO_PORT=9100 \
  DATAPLAT_MINIO_ACCESS_KEY=dataplat DATAPLAT_MINIO_SECRET_KEY=dataplat-secret
bash scripts/_self_check.sh   # 期望 PASS: 52
```
