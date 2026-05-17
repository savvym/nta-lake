---
change_id: commit-api-mvp-20260517
target: unit_test/test_report_v1.md
target_version: 1
review_version: 1
reviewer: claude-stage6-reviewer
reviewed_at: 2026-05-17T10:45:00Z
verdict: APPROVED
must_fix_count: 0
should_fix_count: 0
nice_to_have_count: 2
---

# Stage 6 Test Review v1 — commit-api-mvp-20260517

## 被评对象

- `apps/api/tests/test_commits.py`（18 测试：g1 纯单元 + 17 集成 a~q）
- `scripts/_self_check.sh` 中 `run_commit_api_mvp`（13 AC）
- `unit_test/test_report_v1.md`（映射表 + 运行结果 + mock 范围声明）

## 验证动作（reviewer 亲自执行，机械化证据）

```bash
# 1. self_check 13 AC
DATAPLAT_PG_PORT=5433 DATAPLAT_MINIO_PORT=9100 \
  DATAPLAT_MINIO_ACCESS_KEY=dataplat DATAPLAT_MINIO_SECRET_KEY=dataplat-secret \
  bash scripts/_self_check.sh commit-api-mvp
# → PASS=13 FAIL=0 SKIP=0

# 2. pytest 18 测试
cd apps/api && \
  DATAPLAT_DATABASE_URL=postgresql+asyncpg://dataplat:dataplat@localhost:5433/dataplat \
  DATAPLAT_JWT_SECRET=test-secret-not-prod-x32-bytes-xxxxx \
  DATAPLAT_MINIO_ENDPOINT=http://localhost:9100 \
  DATAPLAT_MINIO_ACCESS_KEY=dataplat DATAPLAT_MINIO_SECRET_KEY=dataplat-secret \
  uv run pytest -v tests/test_commits.py
# → 18 passed in 9.23s（无 flaky、无 skip、无 xfail）
```

## 检查清单结论（expert-reviewer SKILL §1 artifact 模式）

- [x] 每条 spec AC 在映射表中至少出现一次（13 AC 全有归宿；详见下方目标 1）
- [x] 没有空跑断言：`grep -nE "assert\s+True|assert\s+1\s*==\s*1|assert\s+None\s+is\s+None" tests/test_commits.py` rc=1（空）
- [x] mock 范围与 `coding-style.md` §1.7 一致：唯一 `dependency_overrides[get_blob_store]` 注入 per-test bucket 隔离的真实 `MinioBlobStore`；DB / BlobStore 算法均真实
- [x] 测试名反映场景：`test_a_admin_post_blob_200_sha256_correct`、`test_l_anonymous_private_repo_returns_404`、`test_n_2mb_streaming_roundtrip` 等；无 `test_1`/`test_works`
- [x] flaky / skip 显式说明：test_report §"已知 flaky / 跳过" 注明无 flaky + PG/MinIO 未通时 self_check SKIP（pytest 用 module 级 skipif 跳整文件）

## 评审目标逐项核对

### 目标 1：AC ↔ 测试映射诚实性（不要用 self_check shell 糊弄关键 AC）

逐条审计 test_report v1 §映射表 vs 实际测试断言：

| AC | 声明覆盖 | 审计结论 |
|---|---|---|
| AC-1 | 仅 self_check shell | 命令断言精确：`'created_at' not in CommitCreate.model_fields` + `extra=='forbid'`（7 schema 全检）；非空跑；**可接受** |
| AC-2 | 仅 self_check shell | `inspect.getsource(BlobService)` 检查 `'AsyncSession' not in src` + `'role' not in src`；精确字符串；**可接受** |
| AC-3 | 仅 self_check shell | hasattr 检查 8 个属性名（3 公共 + 5 私有）；精确；**可接受** |
| AC-4~AC-5 | self_check + 18 测试隐式 | OpenAPI 5 paths 集合断言 + 18 测试触达全部 5 路由 |
| AC-6 | self_check grep + test_l + test_m/p/q | grep 副本不存在 + 4 真测试覆盖三视角（anon/user/admin × public/internal/private）|
| AC-7 | self_check + test_a + test_b | test_a 用本地 `hashlib.sha256(data).hexdigest()` 与服务端响应双向核对；test_b 断 dedup；**非空跑** |
| AC-8 | self_check grep + test_e | test_e 断 `400` + `fake_sha in detail["missing_hashes"]`；精确字段 |
| AC-9 | self_check + test_g1 | 见目标 2（**纯单元测试**，非 shell 糊弄）|
| AC-10 | self_check + test_g2 | test_g2 断 `r1.hash == r2.hash` + `r2.deduplicated == True`；精确 |
| AC-11 | self_check + 18 测试 | 18 ≥ 16；逐用例审计无空壳 |
| AC-12 | self_check | ruff + mypy；外部工具 0 错误 |
| AC-13 | self_check 自递归 | 约定，可接受 |

**结论**：未发现"用 self_check shell 一行式糊弄关键 AC"。AC-1/AC-2/AC-3 仅 shell 但都断言精确属性/精确字符串（非泛 `import xxx`）。关键行为 AC（AC-6/7/8/9/10）均有真实 pytest 断言支撑。

### 目标 2：(g1) hash 单元测试是否真覆盖 spec AC-9 canonical 不变性

源码 `test_commits.py:203-223`（纯单元，无 PG/MinIO 依赖）：

- **entries 排序不变性** ✓
  `_canonical_tree_bytes([e1, e2]) == _canonical_tree_bytes([e2, e1])`（用 name 倒序输入 b/a）
  `_tree_hash([e1, e2]) == _tree_hash([e2, e1])`
- **parents 排序不变性** ✓
  `_commit_hash(th, [p1, p2], "u1", "msg", None) == _commit_hash(th, [p2, p1], "u1", "msg", None)`
- **message 影响 hash**（bonus，覆盖 spec AC-9 第 3 步 message 入 canonical）✓
  `_commit_hash(th, [p1, p2], "u1", "msg2", None) != _commit_hash(th, [p1, p2], "u1", "msg", None)`

spec AC-11 (g1) 原文：`_canonical_tree_bytes(unordered) == _canonical_tree_bytes(sorted)` + `_commit_hash(t, [p1, p2], ...) == _commit_hash(t, [p2, p1], ...)`——测试逐字对应。**这是真正的纯单元测试，不是 self_check shell 一行式。**

### 目标 3：(n) 2MB 是否真覆盖 spec 风险 #2 大文件流式

源码 `test_commits.py:587-606`：

```python
data = secrets.token_bytes(2 * 1024 * 1024 + 17)
expected_sha = hashlib.sha256(data).hexdigest()
...
r_blob = await c.post(f"/repos/test/{repo_name}/blobs", content=data)
assert r_blob.json()["sha256"] == expected_sha          # 上传方向 sha256
assert r_blob.json()["size"] == len(data)               # size
r_get = await c.get(f"/repos/test/{repo_name}/blobs/{expected_sha}")
assert hashlib.sha256(r_get.content).hexdigest() == expected_sha   # 下载方向 sha256
assert len(r_get.content) == len(data)                  # size
```

**不只 size 检查**——而是：
1. 上传方向：客户端本地 hashlib vs 服务端响应 sha256
2. 下载方向：客户端 GET 后再算 hashlib vs 期望 sha256
3. 长度双向核对

覆盖 spec 风险 #2「`UploadFile.read()` 全量到内存 → 用 SpooledTemporaryFile 流式」要求的 round-trip 不丢字节、不变形。**充分。**

### 目标 4：(o) lineage round-trip 是否真覆盖 spec 风险 #5

源码 `test_commits.py:612-659`：

POST 含完整嵌套 `Lineage`：
- `produced_by`: kind + name + version + config_hash（4 字段全）
- `inputs`: `[InputRef(repo, commit)]`（嵌套列表 + 嵌套对象 2 字段）
- `run_id` + `env` 字典

GET 后断言：
```python
ln = body["lineage"]
assert ln is not None
assert ln["produced_by"]["kind"] == "processor"
assert ln["produced_by"]["name"] == "llm-qa-gen"
assert ln["inputs"][0]["repo"] == "silver/cn-lit/normalized-text-v1"
assert ln["inputs"][0]["commit"] == "a" * 64
```

**不是只断 `lineage != None`**——而是展开 `produced_by.kind` / `produced_by.name` / `inputs[0].repo` / `inputs[0].commit` 多层级精确断言。覆盖 spec 风险 #5 + AC-11 (o) 原文要求"produced_by.kind / inputs[0].repo / inputs[0].commit 字段全在"。**充分。**

（见 NICE TO HAVE N-1：可加 `Lineage.model_validate(ln)` 一行更直接锁 Pydantic schema——非阻塞）

### 目标 5：(l) 是否真覆盖三路由 (blob/commit/tree) 都 404

源码 `test_commits.py:544-559`：

```python
r_blob = await anon.get(f"/repos/test/{repo_name}/blobs/{'a' * 64}")
r_commit = await anon.get(f"/repos/test/{repo_name}/commits/{'a' * 64}")
r_tree = await anon.get(f"/repos/test/{repo_name}/tree/{'a' * 64}")
assert r_blob.status_code == 404
assert r_commit.status_code == 404
assert r_tree.status_code == 404
```

**三路由全检 + 三 assert 全在**——不止其中一个。覆盖 spec AC-6 visibility 矩阵中"私有 repo 对匿名 → 三 GET 全部 404 不区分"语义。**充分。**

### 目标 6：mock 范围声明是否诚实（确认 dependency_overrides 只覆盖 BlobStore 不覆盖 DB）

`_override_blob_store` fixture（`test_commits.py:119-155`）实际行为：
- 唯一 override：`app.dependency_overrides[get_blob_store] = lambda: store`（store = 真实 `MinioBlobStore` 类实例，仅换 bucket 名）
- DB 一律真实：`_make_user` / `_delete_user` / `_delete_repo_cascade`（共 4 处）/ test_f 查 refs 全用 `create_async_engine + async_sessionmaker` 直连 PG
- 不 patch `BlobService` / `CommitService` / `RepoService` / SQLAlchemy session / dependency `get_session`
- teardown 严格 `pop + delete_bucket` + 异常吞掉（避免测试失败时 bucket 泄漏）

test_report v1 §"Mock 范围声明"原文：
> 无 mock：直连 docker-compose Postgres ... + 真实 BlobStore CAS 算法
> 唯一的 dependency_overrides：`app.dependency_overrides[get_blob_store]` 注入 per-test bucket 隔离

**声明与代码完全一致**——bucket 隔离不构成数据访问层 mock。符合 `unit-test-write` SKILL §"核心数据访问层禁用无条件 mock"。

## 问题列表

### MUST FIX

无。

| # | 文件:行 | 问题 | 建议 |
|---|---|---|---|

### SHOULD FIX

无。

| # | 文件:行 | 问题 | 建议 |
|---|---|---|---|

### NICE TO HAVE

| # | 文件:行 | 问题 | 建议 |
|---|---|---|---|
| N-1 | apps/api/tests/test_commits.py:651-657 | test_o 只断 dict 字段，未触发 Pydantic `Lineage.model_validate`；若未来 `CommitRead.lineage` 被改为 `dict[str, Any]`，dict 断言会通过但 schema 退化无觉察 | 加一行 `from dataplat_core.domain.lineage import Lineage; Lineage.model_validate(ln)` 锁 schema 不变 |
| N-2 | apps/api/tests/test_commits.py:203-223 | test_g1 未直接断 lineage 入 `_commit_hash` 的不变性（spec AC-9 第 3 步 lineage 入 canonical 仅由集成 (o) 隐式覆盖） | 补一行 `assert _commit_hash(th, [p1,p2], "u", None, lineage_dict) != _commit_hash(th, [p1,p2], "u", None, None)` |

## Verdict

**APPROVED**

判据（expert-reviewer SKILL §3）：MUST FIX 计数 = 0。

## 复检指引

NICE TO HAVE 不阻塞 stage 6 通过；若 Generator 选做后自查：

```bash
# 1. self_check 13 AC
DATAPLAT_PG_PORT=5433 DATAPLAT_MINIO_PORT=9100 \
  DATAPLAT_MINIO_ACCESS_KEY=dataplat DATAPLAT_MINIO_SECRET_KEY=dataplat-secret \
  bash scripts/_self_check.sh commit-api-mvp
# 期望：PASS=13 FAIL=0 SKIP=0

# 2. pytest 18 测试
cd apps/api && \
  DATAPLAT_DATABASE_URL=postgresql+asyncpg://dataplat:dataplat@localhost:5433/dataplat \
  DATAPLAT_JWT_SECRET=test-secret-not-prod-x32-bytes-xxxxx \
  DATAPLAT_MINIO_ENDPOINT=http://localhost:9100 \
  DATAPLAT_MINIO_ACCESS_KEY=dataplat DATAPLAT_MINIO_SECRET_KEY=dataplat-secret \
  uv run pytest -v tests/test_commits.py
# 期望：18 passed

# 3. 若做了 N-1：grep 验证 Lineage 反序列化锚点
grep -nE "Lineage\.model_validate" apps/api/tests/test_commits.py
# 期望：在 test_o 体内出现至少 1 处
```

进入 stage 7（集成/CI）前确认：
- `summary.md` stage=`unit_test` 标 status=`approved`
- 把本 review 路径 `unit_test/review/test_review_v1.md` 追加到 summary.md 阶段索引
- NICE TO HAVE 如不选做，可在 summary.md 写 deferred 说明 + 跟进项（可挂 follow-up `commit-api-mvp-test-tighten-*`）
