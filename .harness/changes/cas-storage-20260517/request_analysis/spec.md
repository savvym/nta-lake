---
change_id: cas-storage-20260517
version: 1
authored_at: 2026-05-17T03:05:00Z
status: draft
---

# Spec：BlobStore Protocol + MinioBlobStore + sha256 去重

## 背景

`core-domain-model-20260516` 已落 `BlobRef` Pydantic 与 `blobs` ORM 表（含 sha256 主键 / size / storage_key 列）。但**实际字节内容如何写入对象存储 / 如何寻址 / 如何去重**还没有代码实现。

dataplat 的核心承诺之一是"相同字节内容跨 Repository 只存一份"（design.md §1.2 #5 + §4.4 §好处第 1 条）。这需要：

1. 一个抽象的 `BlobStore` Protocol（让 worker / api / SDK 共用同一接口）
2. 一个具体的 `MinioBlobStore` 实现（boto3 S3 兼容）
3. 严格的 key 规范 `blobs/{sha256[0:2]}/{sha256}`（design.md §5.2）
4. server 端计算 sha256（不信任 caller）+ 去重（已存在则跳过 put）

本变更只做 storage 操作层；ORM blob 行写入与 storage 操作的事务一致留给 `repo-api-mvp`。

## 问题陈述

当前缺：

1. `packages/core/src/dataplat_core/protocols/` 没有 `storage.py`——Adapter / Processor 想 put blob 没有接口可调
2. `apps/api/dataplat_api/storage/` 目录不存在
3. 没有 `storage_key_for(sha256)` 工具，"key 拼接"会散落在各处
4. 没有 boto3 依赖；MinIO 客户端没法用

## 范围

In scope（每条对应可机械化验证）：

- **AC-1**：`packages/core/src/dataplat_core/protocols/storage.py` 存在，定义 `BlobStore` 为 `@runtime_checkable` Protocol，含 async 方法签名 `async def put(self, stream: BinaryIO, *, declared_size: int | None = None) -> BlobPutResult` / `async def get(self, sha256: str) -> AsyncIterator[bytes]` / `async def exists(self, sha256: str) -> bool` / `async def get_size(self, sha256: str) -> int | None` / `async def delete(self, sha256: str) -> bool`；`stream` 类型显式 `typing.BinaryIO`（sync 二进制可读流）—— HashingStream 包装也是 sync 包装；boto3 调用整体在 `asyncio.to_thread()` 内。导出 `BlobPutResult` Pydantic BaseModel（sha256 / size / storage_key / deduplicated）。
- **AC-2**：`packages/core/src/dataplat_core/protocols/__init__.py` 暴露 `BlobStore` 与 `BlobPutResult`；可被 `from dataplat_core.protocols import BlobStore, BlobPutResult` 引入。
- **AC-3**：`apps/api/dataplat_api/storage/__init__.py` + `keys.py` + `minio_store.py` 三文件齐全；`keys.py` 提供 `storage_key_for(sha256: str) -> str` 函数（拒绝非 64-hex 输入 raise `ValueError`）。
- **AC-4**：`storage_key_for("a"*64) == "blobs/aa/aaaa...aaaa"`（共 64 个 a）；`storage_key_for("aB"*32)` 在 sha256 校验未通过时 raise ValueError（大写不允许，与 SHA256 类型一致）。
- **AC-5**：`MinioBlobStore` 实现 `BlobStore` Protocol（`isinstance(store, BlobStore)` 通过 `runtime_checkable` 检测）；构造参数 `endpoint_url / access_key / secret_key / bucket / region`；从环境变量读默认（`DATAPLAT_MINIO_ENDPOINT` / `DATAPLAT_MINIO_ACCESS_KEY` / `DATAPLAT_MINIO_SECRET_KEY` / `DATAPLAT_BLOB_BUCKET`）。
- **AC-6**：`apps/api/pyproject.toml` 新增依赖 `boto3>=1.34` 与 `botocore>=1.34`；`uv sync` 后 `import boto3` 成功。
- **AC-7**：`MinioBlobStore.put(stream)` server 端流式计算 sha256（不读全量到内存），**采用临时 key + copy 算法**解决"upload_fileobj 需要 Key 先知道，但 sha256 流式才有"冲突：
  1. 生成 `tmp_key = _tmp/{uuid4}.part`
  2. 用 `HashingStream` 包装 caller 传入的 `BinaryIO`，每次 read 同步 update `hashlib.sha256()` + 累计 size
  3. `s3.upload_fileobj(hashing_stream, bucket, tmp_key)`（单次扫流；upload_fileobj 内部自动 multipart）
  4. 算出 sha256；构造 final_key = `storage_key_for(sha256)`
  5. `s3.head_object(bucket, final_key)` 查重：
     - 已存在 → `s3.delete_object(bucket, tmp_key)`；返回 `BlobPutResult(..., deduplicated=True)`
     - 不存在 → `s3.copy_object(bucket, source=tmp_key, dest=final_key)` + `s3.delete_object(bucket, tmp_key)`；返回 `deduplicated=False`
  6. 任何步骤异常 → best-effort `s3.delete_object(bucket, tmp_key)`，孤儿对象由 retention follow-up 兜底

  返回 `BlobPutResult(sha256, size, storage_key=final_key, deduplicated)`。
- **AC-8**：去重：同一字节内容 put 两次，第二次 `result.deduplicated == True`，且 storage 只占用一个对象（list objects 数量不增）。
- **AC-9**：`exists(sha256)` 在 blob 存在时返回 True，不存在时 False。
- **AC-10**：`get(sha256)` 返回 AsyncIterator，迭代字节流；读出内容与 put 输入字节完全一致；对不存在 blob 调用 `get` **首次 `async for` / `__anext__` 时** raise `KeyError`（不要求 helper 工厂调用瞬间 raise；async generator 在首 yield 前执行 body）。boto3 `ClientError` code 分类：`404` / `NoSuchKey` → 视作不存在 raise KeyError；`NoSuchBucket` / 其他 ClientError → 不吞，bubble up 让 caller 知道是基础设施错而非业务"不存在"。
- **AC-11**：`get_size(sha256)` 对存在的 blob 返回字节数；对不存在的 blob 返回 None。
- **AC-12**：所有 put 写入 storage 的 key 严格匹配 `^blobs/[0-9a-f]{2}/[0-9a-f]{64}$`；list bucket 抽样验证。
- **AC-13**：大对象 put（≥ 2MB 随机字节）成功且 sha256 与本地 hashlib.sha256 计算一致；`MinioBlobStore.put` 不应一次性把全部字节加载到内存（用 boto3 `upload_fileobj` 或类似流式 API）。
- **AC-14**：`packages/core/tests/test_storage_protocol.py` 含 ≥ 3 个测试：(a) Protocol 可被 import 与 `runtime_checkable`；(b) `BlobPutResult` Pydantic 序列化往返；(c) `storage_key_for(sha)` 与 `BlobPutResult.storage_key` 一致（用 dummy hash）。
- **AC-15**：`apps/api/tests/test_minio_store.py` 含 ≥ 5 个集成测试（依赖 MinIO 容器）：(a) put + get round-trip + 不存在 blob 首次 async for 抛 KeyError；(b) put 同字节内容两次去重；(c) exists 真假；(d) get_size 真假；(e) put ≥ 2MB 大对象 + sha256 与 hashlib 一致 + key pattern 匹配 `^blobs/[0-9a-f]{2}/[0-9a-f]{64}$`。**测试 fixture bucket 命名**：`dataplat-test-{uuid4().hex[:8]}`（lowercase / 长度 < 63 / 无下划线，符合 MinIO 规则）；setup `_ensure_bucket()` + teardown delete 所有对象后 `delete_bucket`；MinioBlobStore 构造时 override `bucket` 参数（不读 env 默认 bucket，避免污染）。
- **AC-16**：`uv run ruff check apps/api packages/core` 与 `uv run mypy apps/api/dataplat_api packages/core/src` 全 PASS。
- **AC-17**：`scripts/_self_check.sh cas-storage` 17/17 PASS（含 MinIO SKIP 通道，本机不可达时整 block 跳过非阻塞）。

## 非范围

- 不引入 HTTP 路由（POST /blobs 等）—— 留给 `repo-api-mvp`
- 不实现 ORM blobs 行写入与 storage put 的事务一致—— 留给 `repo-api-mvp` 的 service 层
- 不实现 retention / GC / purge / 多版本垃圾回收—— 单独 follow-up
- **`BlobStore.delete` 在 Protocol 中声明**（供调用者类型推断 + 后续 retention 用），但**本变更不要求集成测试覆盖**——retention follow-up 将引入级联删除一致性测试
- **`BlobStore.iter_keys` 不在本变更范围**（list / pagination 由 retention follow-up 引入；本变更内 list bucket 只在 test fixture 用 boto3 直接调用，不暴露 Protocol 方法）
- **临时 key 孤儿对象 GC**：put 异常路径用 best-effort delete；超过 24h 残留对象由 retention follow-up 兜底
- 不实现 streaming chunked / multi-part upload—— 单文件 ≤ 100MB 范围用 boto3 默认 `upload_fileobj` 即可
- 不实现 audit log / cost accounting / rate limit—— Phase 2+ 单独
- 不支持 S3 / 其他 provider—— 仅 MinIO；S3 兼容 boto3 即可后续切换

## 验收标准

| ID | 描述 | 验证方式 | 期望 |
|---|---|---|---|
| AC-1 | storage.py + BlobStore 是 runtime_checkable Protocol + BlobPutResult 是 BaseModel | `test -f packages/core/src/dataplat_core/protocols/storage.py && cd packages/core && uv run python -c "from typing import Protocol; from pydantic import BaseModel; from dataplat_core.protocols.storage import BlobStore, BlobPutResult; assert issubclass(BlobStore, Protocol); assert getattr(BlobStore, '_is_runtime_protocol', False) is True, 'BlobStore 必须 @runtime_checkable'; assert issubclass(BlobPutResult, BaseModel)"` | exit 0 |
| AC-2 | protocols/__init__.py 暴露 | `cd packages/core && uv run python -c "from dataplat_core.protocols import BlobStore, BlobPutResult"` | exit 0 |
| AC-3 | apps/api/storage/ 三文件齐全 | `for f in __init__.py keys.py minio_store.py; do test -f "apps/api/dataplat_api/storage/$f" \|\| exit 1; done` | exit 0 |
| AC-4 | storage_key_for 正确性 + sha256 校验 | `(cd apps/api && uv run python -c "from dataplat_api.storage.keys import storage_key_for; assert storage_key_for('a'*64)=='blobs/aa/' + 'a'*64") && ! (cd apps/api && uv run python -c "from dataplat_api.storage.keys import storage_key_for; storage_key_for('NOTHEX' + 'a'*58)") 2>/dev/null` | exit 0 |
| AC-5 | MinioBlobStore 实现 BlobStore Protocol | `cd apps/api && uv run python -c "from dataplat_api.storage.minio_store import MinioBlobStore; from dataplat_core.protocols.storage import BlobStore; s=MinioBlobStore.__new__(MinioBlobStore); assert isinstance(s, BlobStore)"` | exit 0 |
| AC-6 | apps/api 依赖 +boto3 +botocore | `python3 -c "import tomllib; d=tomllib.load(open('apps/api/pyproject.toml','rb')); deps=d['project']['dependencies']; assert any('boto3' in x for x in deps) and any('botocore' in x for x in deps)"` | exit 0 |
| AC-7 | put 返回 BlobPutResult + 内部计算 sha256 | 由 AC-15 (a) round-trip 测试覆盖 | exit 0 |
| AC-8 | 去重 | 由 AC-15 (b) 覆盖 | exit 0 |
| AC-9 | exists | 由 AC-15 (c) 覆盖 | exit 0 |
| AC-10 | get + KeyError | 由 AC-15 (a) + 单独负向用例覆盖 | exit 0 |
| AC-11 | get_size | 由 AC-15 (d) 覆盖 | exit 0 |
| AC-12 | key 严格规范 | 由 AC-15 list bucket key pattern 校验覆盖 | exit 0 |
| AC-13 | ≥ 2MB 大对象 + sha256 一致 | 由 AC-15 (e) 覆盖 | exit 0 |
| AC-14 | packages/core 单测 ≥ 3 | `(cd packages/core && uv run pytest -q --tb=no tests/test_storage_protocol.py) && [ "$(cd packages/core && uv run pytest --collect-only -q tests/test_storage_protocol.py 2>&1 \| grep -cE "::")" -ge 3 ]` | exit 0 |
| AC-15 | apps/api 集成测试 ≥ 5 + MinIO 真连 | `python3 -c "import socket; s=socket.socket(); s.settimeout(1); s.connect(('localhost', int('${DATAPLAT_MINIO_PORT:-9000}'))); s.close()" 2>/dev/null && (cd apps/api && uv run pytest -q --tb=no tests/test_minio_store.py) && [ "$(cd apps/api && uv run pytest --collect-only -q tests/test_minio_store.py 2>&1 \| grep -cE "::")" -ge 5 ]`（探针失败 → SKIP 不 FAIL）| exit 0 或 SKIP |
| AC-16 | ruff + mypy | `uv run ruff check apps/api packages/core && uv run mypy apps/api/dataplat_api packages/core/src` | exit 0 |
| AC-17 | self_check cas-storage block | `bash scripts/_self_check.sh cas-storage` 退出码 0（含 SKIP 通道）| exit 0 |

## 风险

| 风险 | 概率 | 影响 | 缓解 |
|---|---|---|---|
| MinIO 容器未起 / 端口冲突 | 高（本机已 5432 占用经验）| AC-15 / AC-17 FAIL | 用 `DATAPLAT_MINIO_PORT` 环境变量；socket 探针 SKIP；spec 显式允许 SKIP |
| boto3 异步：S3 客户端是 sync，不能直接在 async 路由调 | 中 | 阻塞 async 路由 | 用 `asyncio.to_thread()` 包装 sync 调用；`MinioBlobStore.put / get` 暴露 async 接口、内部 to_thread；这是 boto3 + asyncio 标准做法 |
| 流式 sha256 + boto3 upload_fileobj 二次扫流 | 中 | 大对象慢 / 内存 | 自定义 `HashingStream` 包装：read 时同步 update hash；boto3 upload 接 wrapper，单次扫流 |
| MinioBlobStore 与 Protocol 形态错配（async vs sync 方法）| 中 | isinstance 通不过 | Protocol 定义 async 方法签名；MinioBlobStore 用 `async def` + to_thread；测试用 `runtime_checkable` 协议 + `isinstance` |
| storage_key 计算逻辑漂移（多处拼接）| 低 | key 不一致 | 强制单源 `storage_key_for()` 工具；ruff lint 后期可加禁字符串字面 `blobs/` 拼接（follow-up）|
| pytest-asyncio + boto3 thread 跨 loop event loop 关闭时序 | 中 | 测试 flaky | 复用 core-domain-model 经验：fresh client per test + 显式 close；同源 conftest |
| MinIO bucket 不存在 | 中 | 第一个 put 失败 | MinioBlobStore 启动时 head_bucket → 不存在则 create；测试 fixture 也保证 bucket 在 |
| 临时 key 孤儿对象（put 成功但 copy 或 delete 失败）| 低 | bucket 残留 `_tmp/{uuid}/*` 对象，占用空间 | 所有临时 key 强制 `_tmp/{uuid}/` 前缀；retention follow-up 周期清理超 24h 对象；短期接受残留 |
| aioboto3 / aiobotocore 原生 async 替代未启用 | 低 | 若 to_thread 队列堆积 → API 延迟上升 | **已评估**：维持 boto3 + to_thread 不切。理由：减少依赖体积 + worker/SDK/api 共享调用栈一致 + Phase 1 流量低（< 100 QPS 估）+ 任何性能问题 follow-up 切 aiobotocore；switch 成本 ≈ 重写 MinioBlobStore 即可，不外溢 |

## 受影响模块

- `packages/core/src/dataplat_core/protocols/storage.py`（新建）+ `__init__.py`（修改）
- `packages/core/tests/test_storage_protocol.py`（新建）
- `apps/api/dataplat_api/storage/{__init__.py,keys.py,minio_store.py}`（新建）
- `apps/api/tests/test_minio_store.py`（新建）
- `apps/api/pyproject.toml`（新增依赖）
- `scripts/_self_check.sh`（追加 block）

## 不受影响

- `.harness/`、`wiki/`、`apps/web/`、`apps/api/dataplat_api/main.py`、`models/` 全部不变
- `apps/api/dataplat_api/db.py` 不变（仅在后续 service 层用到）

## 待澄清问题

- [x] sha256 是 client 还是 server 计算？答：server（CAS 语义要求；不信任 caller）
- [x] 同字节内容已存在再 put：返回成功（idempotent）还是 raise？答：返回成功 + `deduplicated=True`
- [x] BlobStore 方法是 async 还是 sync？答：async（与 FastAPI / aiosqlalchemy 一致；内部用 to_thread 包 boto3）
- [x] MinIO endpoint 是否要 TLS？答：本变更不强制；endpoint URL 接受 http/https 由 caller 决定
- [x] Q6 boto3 ClientError code 分类：`404` / `NoSuchKey` → 不存在；`NoSuchBucket` / 其他 → bubble up（见 AC-10）
- [x] Q7 0 字节 stream put：允许；sha256(empty)=`e3b0c4...855`；BlobRef.size `ge=0` 已经容许；走 dedup 路径与非空一致；AC-15 (e) 用 2MB 充分覆盖大对象路径，0 字节边界由后续 NICE TO HAVE follow-up 补

## 引用

- `.harness/design.md` §1.2 #5（CAS 去重）/ §4.4（CAS 模型）/ §5.2（key 规范）/ §11.2（boto3 选型）
- `.harness/changes/core-domain-model-20260516/`：BlobRef + blobs ORM 表已落
