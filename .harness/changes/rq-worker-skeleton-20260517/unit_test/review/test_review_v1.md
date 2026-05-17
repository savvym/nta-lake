---
change_id: rq-worker-skeleton-20260517
target: unit_test/test_report_v1.md
target_version: 1
review_version: 1
reviewer: claude-stage6-reviewer
reviewed_at: 2026-05-17T14:55:00Z
verdict: APPROVED
---

# Test Review v1 — rq-worker-skeleton-20260517

> 评审对象：`unit_test/test_report_v1.md` + `apps/api/tests/test_jobs.py`（10 用例 a~j）+ `scripts/_self_check.sh::run_rq_worker_skeleton`（13 AC）。
>
> 评审范围限于本 change spec.md v2 的 13 条 AC（AC-1 ~ AC-13）。fork worker E2E + 覆盖率工具化按 owner 通告**显式 deferred 到 follow-up，不在本轮 MUST FIX 范围**。

## 1. 检查清单结论

> 依据 `.harness/skills/expert-reviewer/SKILL.md` artifact 模式 + `.harness/skills/unit-test-write/SKILL.md`。

- [x] 每条 spec AC（AC-1 ~ AC-13）在映射表中至少出现一次（见 §1.1）。
- [x] 没有空跑断言：`grep -nE "assert\s+True|assert\s+1\s*==\s*1" tests/test_jobs.py` → 0 命中（实测）。
- [x] mock 范围符合 `coding-style.md §1.7`（不允许无条件 mock 核心数据访问层）：`grep -nE "Mock\(|MagicMock|patch\(|monkeypatch.setattr.*Service" tests/test_jobs.py` → 0 命中。
- [x] 测试名场景化：`test_<letter>_<scenario>_<expected>` 格式（如 `test_g_end_to_end_succeeded`、`test_h_parent_chain_through_ref`、`test_j_idempotent_dedup_true`），无 `test_xxx_1` 反模式。
- [x] flaky/skip 显式：test_report v1 §"已知 flaky" 段明确 "无 flaky"；Redis 队列 fixture 用 `queue.empty()` 防跨测试污染。三探针 PG/MinIO/Redis 任一不可达整文件 skip，**没有局部 skip**。

### 1.1 AC ↔ 测试映射诚实性

| AC | spec 要求 | test_report 声明 | 实际产物核对（文件:行） | 结论 |
|---|---|---|---|---|
| AC-1 JobORM 9 字段 | `cols >= {id,type,status,payload,result,error,created_at,started_at,completed_at}` | self_check AC-1 | `scripts/_self_check.sh:783-789` 直接 introspect `JobORM.__table__.columns` | 真断言 |
| AC-2 alembic 0003 | `ls 0003_*.py && grep "jobs"` | self_check AC-2 | `scripts/_self_check.sh:791-792` 文件 + grep 双重 | 真断言 |
| AC-3 redis_client 双 callable | `get_redis + get_queue` 可调 | self_check AC-3 | `scripts/_self_check.sh:794-795` import + `callable()` | 真断言 |
| AC-4 JobsService 5 方法 | `hasattr` all 5 | self_check AC-4 | `scripts/_self_check.sh:797-798` `all(hasattr(...))` generator（v2 已修 stage 2 v1 SyntaxError） | 真断言 |
| AC-5 run_ingest_job 签名 | `job_id` ∈ signature | self_check AC-5 | `scripts/_self_check.sh:800-801` inspect.signature | 真断言 |
| AC-6 schemas extra=forbid | JobIngestRequest + JobRead | self_check AC-6 + 测试隐式 | `scripts/_self_check.sh:803-804` model_config 直查；test_a~j 的 payload 全部通过 schema | 真断言（结构 + 行为联动） |
| AC-7 jobs router 2 paths | `/jobs/ingest + /jobs/{job_id}` | self_check AC-7 | `scripts/_self_check.sh:806-807` paths set 包含 | 真断言 |
| AC-8 main + OpenAPI | 2 paths in `app.openapi()` | self_check AC-8 | `scripts/_self_check.sh:809-810` | 真断言 |
| AC-9 不重复 `_visibility_visible` | 正向 grep `_resolve_repo\|RepoService.get_by_owner_name` + 反向 `! grep _visibility_visible` | self_check AC-9 | `scripts/_self_check.sh:812-813` test -f 前置 + 正向 + 反向（spec §跨 AC 模板正确应用） | 真断言 |
| AC-10 worker/main.py Worker.work | grep `Worker\|work\(` | self_check AC-10 | `scripts/_self_check.sh:815-816` test -f + grep | 真断言 |
| AC-11(a)~(j) 集成 ≥ 10 | 10 子用例覆盖 a~j | self_check AC-11 + `test_jobs.py` 10 函数 | 见 §1.2 逐条核对 | **真断言**（见 §1.2） |
| AC-12 ruff + mypy | 含 worker/src | self_check AC-12 | `scripts/_self_check.sh:821-822` 加入 worker/src | 真断言 |
| AC-13 自递归 | true | self_check AC-13 | trivial pass | OK |

**映射诚实**：13 AC 全部落到具体可机械化的命令；AC-11 进一步分解到 10 个有名测试函数；test_report v1 §"AC ↔ 测试映射" 与实际脚本块一一对应，没有空映射或"测试覆盖说"。

### 1.2 AC-11 子用例 (a)~(j) 行为正确性逐条核对

| 子用例 | 验证目标 | 实际断言（test_jobs.py 行号） | 评审结论 |
|---|---|---|---|
| (a) admin POST → 201 queued | 入队成功 + 类型/ID | `297 status==201; 299 status=="queued"; 300 type=="ingest"; 301 "id" in body` | **真覆盖** |
| (b) GET 已有 job | 200 + 同 id | `333 status==200; 334 json["id"]==job_id` | **真覆盖** |
| (c) GET 不存在 → 404 | 404 | `348 r.status_code==404` | **真覆盖** |
| (d) user POST → 403 | role 拒绝 | `379 r.status_code==403`（admin 建 repo + user 登录 POST） | **真覆盖** |
| (e) anon POST → 401 | 未登录拒绝 | `409 r.status_code==401`（admin 建 repo + 全新 client 不登录 POST） | **真覆盖** |
| (f) 缺 blob → failed | worker 内 AdapterRunner 触发 missing_hashes → swallow → mark_failed | `452 status=="failed"; 453 error is not None` | **真覆盖**（与 (i) 互补：错误来源不同） |
| (g) **E2E succeeded + commit_hash + dedup=False**（reviewer 重点 #1） | 真跑通整个 ingest pipeline | `492 status=="succeeded"; 493 commit_hash truthy; 494 len(commit_hash)==64; 495 deduplicated is False` | **真覆盖**（四断言齐全；不仅"非空"还断言 64 hex 长度 + 首次非去重） |
| (h) **parent 链 C2.parents=[C1]**（reviewer 重点 #2） | 两次 ingest 同 ref 接链 | `557 c2!=c1; 558 GET /repos/.../commits/{c2_hash}; 560 commit2["parents"]==[c1_hash]` | **真覆盖**（不是直接读 DB，而是通过 commits GET API 回读，链路覆盖 commit-api-mvp 接链） |
| (i) **worker 异常 → failed**（reviewer 重点 #3） | unknown adapter 触发 swallow 路径 | `598 status=="failed"; 599 error is not None`（使用 `adapter_name="no-such-adapter"`） | **真覆盖**（见 §1.2.1） |
| (j) **幂等 dedup=true**（reviewer 重点 #4） | 两次同 spec enqueue 各跑通 + 第二次 dedup | `637-642 r1.status=succeeded; r2.status=succeeded; commit_hash 相等; r1.dedup=False; r2.dedup=True` | **真覆盖**（5 断言齐全；两个 job 在同一 burst 内顺序跑通） |

#### 1.2.1 关于 (i) 用 unknown adapter 作为 worker 异常代理

- `apps/api/dataplat_api/runner/adapter_runner.py:57-62` 显示：未注册 adapter 抛 `HTTPException(404)`；
- `apps/api/dataplat_api/jobs/tasks.py:110-112` 显示：`_run_ingest_job_async` 用 `except Exception` swallow，调 `mark_failed(str(exc))`；
- 因此 (i) 实际跑过的代码路径就是 spec AC-11 (i) "worker 异常 swallow → status=failed"；HTTPException 是 Exception 子类，被 swallow 路径正确捕获。
- 这是**合理代理**，比刻意 force-raise 更接近现实——adapter 不存在是真实生产事故场景。
- 与 (f) 形成互补：(f) 是 adapter 存在但 blob 缺失（400-equivalent 来自 BlobStore.exists() 检查链）；(i) 是 adapter 根本不存在。两条都跑通 swallow → mark_failed 路径，覆盖度足够。

### 1.3 Mock 范围声明诚实性

测试**没有**违反 `coding-style.md §1.7`：

- `grep -nE "Mock\(|MagicMock|patch\(|monkeypatch.setattr.*Service" tests/test_jobs.py` → 0 命中（实测）；
- `app.dependency_overrides[get_blob_store] = lambda: store`：注入一个**真实** `MinioBlobStore`（指向真 MinIO）+ per-test bucket 隔离，**不是** mock；
- `monkeypatch.setattr(storage_mod, "_blob_store", None) + setenv DATAPLAT_BLOB_BUCKET=...`：让 worker 端 singleton 在每次测试新建一个指向**同**真 MinIO 同 bucket 的 store。worker 与 FastAPI handler 两条路径都打真实组件，只是 bucket 隔离。

唯一的"变形"是 `_run_worker_burst()`（test_jobs.py:231-269）：

- **诚实声明**：函数 docstring 232-238 行 "绕过 RQ Worker，直接 dequeue → 调用 task 函数" + test_report v1 § Mock 范围 "唯一变形：测试用 thread + 直接 dequeue 取代 SimpleWorker（绕开 signal handler 限制）；本质仍调真 task 函数" 已经把替换事实写到位。
- **本质**：从 `get_queue()` 弹 `pop_job_id()` → `Job.fetch(job_id, connection=conn)` → import + call `job.func_name` → 走真实 `run_ingest_job(job_id)` → 真 engine + 真 BlobStore + 真 AdapterRunner.
- **未覆盖**：RQ Worker 自身的 SIGINT/SIGTERM/SIGALRM handler + fork 子进程边界 + 多消费者 race。**已 deferred 到 follow-up**（owner 在 reviewer 任务通告中明确说明，不构成本轮 MUST FIX）。

## 2. 验证动作执行结果

| 验证 | 命令 | 结果 |
|---|---|---|
| pytest test_jobs.py | `cd apps/api && DATAPLAT_DATABASE_URL=postgresql+asyncpg://dataplat:dataplat@localhost:5433/dataplat DATAPLAT_JWT_SECRET=test-secret-not-prod-x32-bytes-xxxxx DATAPLAT_MINIO_ENDPOINT=http://localhost:9100 DATAPLAT_MINIO_ACCESS_KEY=dataplat DATAPLAT_MINIO_SECRET_KEY=dataplat-secret DATAPLAT_REDIS_URL=redis://localhost:6379/0 uv run pytest -q tests/test_jobs.py` | **10 passed in 6.75s** |
| self_check rq-worker-skeleton | `DATAPLAT_PG_PORT=5433 DATAPLAT_MINIO_PORT=9100 DATAPLAT_MINIO_ACCESS_KEY=dataplat DATAPLAT_MINIO_SECRET_KEY=dataplat-secret bash scripts/_self_check.sh rq-worker-skeleton` | **PASS 13 / FAIL 0 / SKIP 0** |

> 注：本环境上跑测试的容器是 `dataplat-pg-test:5433 / dataplat-minio-test:9100 / dataplat-redis-test:6379`，账号 `dataplat / dataplat / dataplat-secret`，与 reviewer 任务通告 env 一致。

## 3. 问题列表

### MUST FIX

无（0 条）。

### SHOULD FIX

| # | 文件:位置 | 问题 | 建议 |
|---|---|---|---|
| S-1 | `unit_test/test_report_v1.md` § Mock 范围 | "无 mock：直连 PG + MinIO + Redis" 与 "唯一变形：RQ Worker 被替换" 并列，读起来割裂；严格按字面解读"无 mock"不准确（RQ Worker 层确实被替换） | 拆为两条："**无数据访问层 mock**：PG / MinIO / Redis 直连；BlobStore 用 `dependency_overrides` 注 per-test bucket 隔离的真实 `MinioBlobStore`。" + "**唯一替换**：RQ Worker 用 thread + 直接 dequeue 取代（绕开 signal handler / SIGALRM；fork worker E2E 已 deferred 到 follow-up）。" 不阻塞本轮 verdict。 |

### NICE TO HAVE

| # | 文件:行 | 问题 | 建议 |
|---|---|---|---|
| N-1 | `tests/test_jobs.py:141-170` `_override_blob_store` fixture | bucket 清理逻辑写了**两遍**（141-155 与 156-170 完全相同的 boto3 paginator + delete + delete_bucket 块） | 删除重复块。不影响正确性（第二次 list_objects_v2 返 0 个对象，delete_bucket 已被第一块删过后 swallow 异常）；只是 dead code。 |
| N-2 | `tests/test_jobs.py:9, 648` | `import hashlib` 仅被 `_ = hashlib` 占位防 ruff F401 | 删除 `import hashlib` 和文末 `_ = hashlib`。当前用法只是应付 ruff，不是真实依赖。 |

## 4. Verdict

**APPROVED**

判据：

- MUST FIX = 0；
- 所有 spec AC（13 条）映射到具体可机械化的命令或测试函数；
- AC-11 (a)~(j) 10 个子用例全部真断言（含 reviewer 重点 g / h / i / j 四条）；
- pytest 10/10 PASS、self_check rq-worker-skeleton 13/13 PASS（实测）；
- 无数据访问层 mock 违规；
- worker E2E（fork SimpleWorker）+ 覆盖率工具按 owner 通告已显式 deferred；不在本轮 MUST FIX 范围。

## 5. 复检指引

verdict 为 APPROVED；本 review **不要求** generator 必须再开 v2 后回评。若 owner 选择在 close 前顺手处理 SHOULD / NICE：

```bash
# 1. 测试仍全 PASS
cd apps/api && \
  DATAPLAT_DATABASE_URL=postgresql+asyncpg://dataplat:dataplat@localhost:5433/dataplat \
  DATAPLAT_JWT_SECRET=test-secret-not-prod-x32-bytes-xxxxx \
  DATAPLAT_MINIO_ENDPOINT=http://localhost:9100 \
  DATAPLAT_MINIO_ACCESS_KEY=dataplat \
  DATAPLAT_MINIO_SECRET_KEY=dataplat-secret \
  DATAPLAT_REDIS_URL=redis://localhost:6379/0 \
  uv run pytest -q tests/test_jobs.py    # 期望 10 passed

# 2. ruff/mypy clean
uv run ruff check apps/api packages/core worker/src && \
  uv run mypy apps/api/dataplat_api packages/core/src worker/src

# 3. self_check 全块仍 13/13 PASS
DATAPLAT_PG_PORT=5433 DATAPLAT_MINIO_PORT=9100 \
  DATAPLAT_MINIO_ACCESS_KEY=dataplat DATAPLAT_MINIO_SECRET_KEY=dataplat-secret \
  bash scripts/_self_check.sh rq-worker-skeleton

# 4. 若改 N-2 删 hashlib import，确保 ruff 不抓 F401（同时删文末 `_ = hashlib`）
# 5. 若改 S-1，确认 Mock 范围段拆分后仍诚实描述：BlobStore 注入 + RQ 替换两件事
```

SHOULD / NICE 由 owner 决定是否本 change 关闭前清掉或落到 follow-up（如 `harness-test-report-clarity-*`）。
