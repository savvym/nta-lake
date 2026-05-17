---
change_id: cas-storage-20260517
reviewer: claude-agent:cas-storage-stage2-reviewer
target: request_analysis/spec.md
target_version: v1
reviewed_at: 2026-05-17T04:00:00Z
mode: plan
verdict: REVISION REQUIRED
must_fix_count: 5
should_fix_count: 6
nice_count: 3
---

# Spec Review v1 — cas-storage-20260517

## 检查清单结论

- 背景 / 问题陈述 / 范围-非范围 / 待澄清问题（4 个全 [x] 已答）：PASS
- AC 可演示且可机械化：**FAIL**（AC-1 永真 + AC-13 难直接断言）
- 风险有缓解：部分 PASS（缺 dedup 路径冲突、async 替代评估、临时孤儿对象风险）
- 没把 design.md 当新提案：PASS

## bash -n 验证（17 AC，sandbox=/tmp/cas-storage-bash-n 空仓库）

补跑 Generator 未自跑的 13 条 + 复跑 4 条：**全部 syntax OK**。但发现两条语义陷阱：

- **AC-1**：`hasattr(BlobStore, '__call__') or typing.runtime_checkable(type(BlobStore))`—— `hasattr(any_class, '__call__')` 永真（class 自身是 callable），OR 短路使 assert 失效。沙箱 Python 3.13 实测 `hasattr(P, '__call__')==True` 即使 P 是 Protocol。`runtime_checkable(type(P))` 反而 raise TypeError。
- **AC-13**："不一次性载入内存" 难以机械化断言（tracemalloc 脆，需 mock upload_fileobj 验证）。

其他 11 条 AC bash -n 通过且无语义陷阱（AC-4 `'NOTHEX'+'a'*58` 长度 64 含非 hex 字符，校验正确；AC-15 `${DATAPLAT_MINIO_PORT:-9000}` 在双引号 `-c` 内可正常 expand）。

## 分级问题列表

### MUST FIX

1. **AC-1 命令断言失效**（line 67）：`hasattr(BlobStore,'__call__')` 对任意 class 永真，OR 短路连 Protocol 是否存在都不验。改用 `assert getattr(BlobStore,'_is_runtime_protocol', False)`，或写 dummy class 验 `not isinstance(_Empty(), BlobStore)`。

2. **dedup 工程路径未定，与 AC-13 隐性冲突**（AC-7+8+13）：spec 同时要求 server 端流式 hash + 同字节去重 + ≥2MB 不全量内存。但 `upload_fileobj(Body,Bucket,Key)` 调用前 Key 必须已知；sha256 仅在流读完后有。Generator 必然在 (A) 临时 key + copy_object 路径 / (B) 全量 buffer（违反 AC-13）之间自由选择。须在 spec 明示采用 (A)：`_tmp/{uuid}` → upload_fileobj → head_object 查重 → 已存在则 delete 临时返 dedup=True / 否则 copy_object 临时→目标 + delete 临时；accept 并发同字节产生临时孤儿。

3. **`put(stream)` 类型签名缺失**（AC-1 line 36）：未声明 `stream` 是 `BinaryIO` / `IO[bytes]` / `AsyncIterator[bytes]` / `Iterable[bytes]`。tasks T-6 隐含 sync `read(size)` 即 `BinaryIO`，但未在 spec 固化。改为 `put(stream: typing.BinaryIO, *, declared_size: int|None=None) -> BlobPutResult`。

4. **summary.md 与 spec.md 方法清单不一致**（summary line 23 vs spec AC-1 line 36）：summary 列 6 方法含 `iter_keys`，spec/tasks 仅 5 个无 `iter_keys`。Generator 不知是否实现。建议删 summary 的 `iter_keys`（与 §非范围 "不实现 GC/retention" 一致；iter_keys 主服务 GC）。

5. **`delete` 方法无 AC 验证 / 也未 §非范围 deferred**：Protocol 声明 delete 但 AC-7~15 / §非范围都未提。Generator 可写空实现也能 PASS。建议从 Protocol 移除 delete 留给 retention follow-up；或加 AC-15(f) "delete 后 exists 返 False"。倾向前者。

### SHOULD FIX

1. **aioboto3 / aiobotocore 原生 async 替代未评估**（风险表第 2 行）：两者为 Python async S3 主流方案。spec 直接拍板 `asyncio.to_thread` 包 sync boto3，无评估记录。风险表追加："评估过 aiobotocore/aioboto3，维持 boto3 + to_thread，理由：减少依赖 + worker/SDK/api 共享调用栈 + Phase 1 流量低；如 to_thread 队列堆积后续切换 follow-up。"

2. **临时 key 孤儿对象风险未列**（风险表）：MUST FIX-2 闭环后，upload 成功但 copy/delete 失败会产生孤儿 `_tmp/*`。追加风险行："所有临时 key 用 `_tmp/{uuid}/` 前缀；retention follow-up 周期清理超 24h 对象；短期接受残留。"

3. **boto3 ClientError code 分类不全**（AC-9/10/11 + 风险表）：head_object 不存在通常返 HTTP 404；get_object 失败 code `NoSuchKey`；bucket 缺失 `NoSuchBucket`。新增澄清问题 Q6："`404`/`NoSuchKey` → 视作不存在；`NoSuchBucket` 与其他 ClientError → bubble up 不吞。"

4. **0 字节 blob 边界未澄清**：sha256(empty)=`e3b0c4...855` 合法；BlobRef.size `ge=0` 允许 0。新增 Q7 "0 字节 stream put 允许，dedup 按已存在状态返"；或 AC-15(f) 加 0 字节 round-trip 测试。

5. **AC-10 KeyError raise 时机不明**（line 45）："进入异步上下文时"含糊。async generator 在首 `__anext__` 才执行 body；helper 工厂可在 `get()` 调用瞬间 raise。固化为 "首次 `async for`/`__anext__` 时 raise KeyError，不要求调用瞬间"；AC-15(a) 配套负向 `pytest.raises(KeyError)` 用例。

6. **测试 fixture bucket 命名规则未明 / 与 §范围段 env 单 bucket 冲突**（AC-5+15 + T-8）：MinIO bucket name 严格（lowercase/3-63/无下划线）；fixture 需 create+delete bucket；不依赖 env 默认。AC-15 追加："fixture bucket=`dataplat-test-{uuid4().hex[:8]}`；setup `_ensure_bucket` + teardown 清空后 `delete_bucket`；MinioBlobStore 构造参数 override，不读 env 默认。"

### NICE TO HAVE

1. **AC-13 大对象可测性**：建议 AC-15(e) 加 `with patch.object(boto3.client,'upload_fileobj') as m: ...; assert m.called` 证明走流式 API。
2. **storage_key 字面拼接 lint follow-up**（风险表第 5 行已记）：可在 wiki/coding-style.md 写纯文档约束 "禁止 `f\"blobs/{...}\"`"，与 follow-up 同步落实。
3. **§引用未含 wiki 入口**：扫一次 wiki/，若有 CAS 词条加入。

## Verdict

**REVISION REQUIRED**（5 条 MUST FIX 未关闭）

## 复检指引

Generator 修完 spec_v2.md 后自查：

```bash
# 1) AC-1 不再永真
! grep -F "hasattr(BlobStore, '__call__')" \
    .harness/changes/cas-storage-20260517/request_analysis/spec.md \
  && echo OK || echo "AC-1 still uses永真"

# 2) dedup 路径已写明
grep -E "_tmp/|tmp_key|copy_object|临时 key" \
    .harness/changes/cas-storage-20260517/request_analysis/spec.md && echo OK

# 3) stream 类型固化
grep -E "stream:\s*(typing\.)?BinaryIO|stream:\s*IO\[bytes\]" \
    .harness/changes/cas-storage-20260517/request_analysis/spec.md && echo OK

# 4) summary 与 spec 方法清单一致（两边都无 iter_keys 或都有）
diff <(grep -c iter_keys .harness/changes/cas-storage-20260517/summary.md) \
     <(grep -c iter_keys .harness/changes/cas-storage-20260517/request_analysis/spec.md)

# 5) delete 有 AC 验证或 §非范围 deferred
grep -E "delete.*AC-1[5-9]|delete.*非范围|delete.*follow-up|delete.*defer" \
    .harness/changes/cas-storage-20260517/request_analysis/spec.md && echo OK

# 6) 在 /tmp 空仓库重跑 17 AC bash -n
```

修完后在 summary.md stage 2 追加 `v2 / verdict pending`，启 reviewer 子会话评 v2。
