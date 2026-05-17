---
change_id: rq-worker-skeleton-20260517
target_head: working-tree (base 23a5fcb)
review_version: 1
reviewer: claude-stage4-reviewer
reviewed_at: 2026-05-17T14:55:00Z
verdict: APPROVED
---

# Code Review v1

## 范围与作者声明对照

coding_report_v1.md 声明 17 项（8 new + 9 edit）。`git status` 实测：

- modified: `apps/api/dataplat_api/main.py` / `models/__init__.py` / `schemas/__init__.py` / `pyproject.toml` / `packages/api-types/openapi.json` / `packages/api-types/src/generated.ts` / `scripts/_self_check.sh` / `worker/src/dataplat_worker/__main__.py` / `apps/api/alembic/env.py` 无（实际未改）/ `uv.lock`（依赖锁）/ `.harness/skills/request-analysis/SKILL.md`（spec v2 反哺，越界但属流程产物）。
- untracked new: `apps/api/alembic/versions/0003_jobs.py` / `apps/api/dataplat_api/jobs/` / `models/job.py` / `routers/jobs.py` / `schemas/job.py` / `tests/test_jobs.py` / `worker/src/dataplat_worker/main.py`。

差异说明：

- coding_report 漏列 `packages/api-types/src/generated.ts`（codegen 副产物，可视为 openapi.json 的姊妹文件，事实清单一致）—— **NICE TO HAVE**：补到下一版 coding_report 的"改动文件清单"。
- `.harness/skills/request-analysis/SKILL.md` 的修改属 spec v2 反哺（"AC 验证命令必须真跑 dry-parse" 第 8 条），不在 coding 阶段产物清单内但已在 spec v2 frontmatter 中声明，**未越界**。

scope creep 检查：

- `auth-scaffold` AC-2 的 self_check 描述被改成 "0002 migration applied（rq-worker 后 head 演进到 0003）"——这是兼容性补丁（alembic head 从 0002 移到 0003 后，AC-2 仍需可断言 0002 在 history 中），**不是跨变更代码改动，属合规的 self_check 维护**。**NICE TO HAVE**：在 coding_report 加一句说明此修改的合理性。

scope 在 spec In/Out 范围内。结论：**范围审查通过**。

## 正确性审查

### `apps/api/dataplat_api/models/job.py`

- 9 字段齐全；`id` 用 `UUID(as_uuid=True)`；`payload` 必填 + `result/error` 可空 + 时间戳带 TZ；3 索引（type/status/created_at）。
- 与 alembic 0003 的字段定义一致（type String(64) / status String(16) / 等）。
- `error` 列未在 ORM 设 Text type 而 DDL 写了 `sa.Text()`；SQLAlchemy 默认 `String` 在 PG 等价 `VARCHAR` 无长度限制时与 Text 兼容，但严格起见 ORM 可显式 `Text`。**NICE TO HAVE**（无功能影响）。

### `apps/api/alembic/versions/0003_jobs.py`

- `down_revision="0002"` 正确接 `auth-scaffold` 链尾；`upgrade()` 创建表 + 3 索引；`downgrade()` 逆序 drop。

### `apps/api/dataplat_api/jobs/redis_client.py`

- `get_redis()` 单例 + lazy；`get_queue()` 每次 new 一个 Queue 对象（轻量，RQ 设计如此）。
- 单例无显式 close / 进程 fork 后 connection 共享：MVP `Redis.from_url` 用连接池，fork 后子进程不会复用旧 socket（pool 内部按 PID 隔离）。可接受。

### `apps/api/dataplat_api/jobs/service.py` — **关键路径：enqueue 失败回滚**

```python
session.add(job); await session.commit(); await session.refresh(job)
try:
    get_queue().enqueue("...run_ingest_job", str(job.id))
except Exception:
    await session.delete(job); await session.commit(); raise
```

事务一致性分析：

- 顺序：先 commit DB → 再 enqueue Redis。若 Redis 失败，DELETE row + commit。
- race 窗口：DB commit 之后、Redis enqueue 之前，另一个 reader 通过 `GET /jobs/{id}` 可读到 status=queued 的 job——但因 enqueue 还没成功，worker 永远不会处理它。**这是 spec 决策表"自建 jobs 表 + RQ 分离"模型下可接受的弱保证**（不是事务两阶段）。reader 看到 queued 但 worker 不动相当于 stuck，但 enqueue 失败后立即 DELETE，时间窗很短。
- DELETE 失败的兜底：如果 enqueue 抛了又 DELETE 也抛了，`raise` 把原始 enqueue 异常上抛，DB 留 orphan queued row——MVP 接受（spec 未要求两阶段提交）。
- **结论**：一致性策略合理，符合 spec 决策"事务一致性优先（一致性 > 性能）"；不是 MUST FIX。

`get_by_id` 接 `uuid.UUID | str`：str 走 `UUID(...)` parse，ValueError 返 None（让 router 转 404）。同 router 入口处的 `uuid.UUID(job_id)` parse 是双重防御——router 已挡，service 再挡只是冗余但安全。**NICE TO HAVE**：去 router 那一层 try 即可，但保留也不是 bug。

`mark_*` 系列：`get_by_id` if None: return（静默 skip）+ commit。`mark_succeeded` / `mark_failed` 静默 skip 在并发场景下是 OK 的（worker 跑到一半 job 被 DELETE 算"幽灵任务"，不应 raise）。

### `apps/api/dataplat_api/jobs/tasks.py` — **关键路径：跨进程 engine + asyncio.run**

```python
def run_ingest_job(job_id: str) -> None:
    try:
        asyncio.run(_run_ingest_job_async(job_id))
    except Exception as exc:
        # mark_failed 兜底也用 asyncio.run（新 event loop）
        asyncio.run(_mark_failed_sync_wrapper(job_id, str(exc)))
```

- `asyncio.run` 在 RQ worker fork 后的子进程内执行：worker 子进程是 fresh process，无 running event loop，`asyncio.run` 合法。
- `_make_engine_factory` 每次 task 调用都新建 engine：spec 决策表"独立 async engine + session（进程边界清晰）"，**MVP 接受**。已在 coding_report 列为 follow-up `worker-engine-pool-*`。
- 顶层 `except Exception` 之后用 `asyncio.run` 再跑兜底 mark_failed——会再起一个 event loop，但前一个已经被 `asyncio.run` 自身 finalize 关闭，**合法**。
- 内层 `_run_ingest_job_async` 内已经 try/except + mark_failed；顶层兜底是双保险（防 `_make_engine_factory` 或 `get_blob_store` 自身 raise）。**合理**。
- 异常 swallow + mark_failed + 不 re-raise：spec 决策"swallow + mark_failed（MVP 不 retry）"——合规。**注意**：这导致 RQ 自身的 `failed` registry 永远不增长，所有失败状态只在业务表 `jobs` 内。生产排查需要看 `jobs.error` 而非 RQ failed registry，**值得在 follow-up `worker-observability-*` 跟进**——SHOULD FIX 范围内但 spec 已申明 MVP 范围，**不阻塞**。

`_run_ingest_job_async` 流程：
1. session 内 get_by_id → if None: warn + return（job 在 enqueue 后被 DELETE 的边界）
2. mark_running
3. payload `["owner"/"name"/"request"]` 取值——若 schema 不符会 KeyError，被外层 except 接 mark_failed。OK。
4. `IngestRequest.model_validate(payload["request"])` 反构——与 router 入口的 `model_dump(mode="json")` 是真 round-trip（已实测：parents/ref/message 等字段反序列化一致）。
5. AdapterRunner.run → 抛 HTTPException 也被 except Exception 捕获——会被 mark_failed，错误细节进 `error`。HTTPException.__str__ 不够友好但 MVP 可接受。**NICE TO HAVE**：考虑 except HTTPException 单独抽 `.detail` 写入 error。

### `apps/api/dataplat_api/schemas/job.py`

`JobIngestRequest` + `JobRead`，extra=forbid 全打。字段类型与 ORM 完全对齐。`JobRead.id: str` 而非 `UUID`——OpenAPI 暴露为 string；序列化路径 `_to_read(job)` 显式 `str(job.id)`。OK。

### `apps/api/dataplat_api/routers/jobs.py`

- POST `/ingest`：`require_admin` + `RepoService.get_by_owner_name(session, owner, name, admin)`：admin 看一切 repo（含 private），不区分存在性返 404。OK，符合 AC-7。
- payload 持久化：`payload.model_dump(mode="json")` 把整个 JobIngestRequest 序列化为 dict——但 worker 反构时只取 `payload["request"]` 给 `IngestRequest.model_validate`——多余字段被 `extra="forbid"` 会卡住吗？答：`payload["request"]` 是从 `model_dump` 出来的 `request` 子树，本身就是 IngestRequest 的 dict 表示，无多余字段。round-trip OK（已实测）。
- GET `/{job_id}`：双层 UUID 校验（router parse + service parse）——router 那层 try/except 主要为了把 ValidationError 直接转成 404 不暴露 422，**合理**（spec AC-7 要求"不存在返 404"）。

### `worker/src/dataplat_worker/main.py`

- 标准 `Worker([queue], connection=conn).work()`。无 burst，正确的阻塞 loop。
- queue 名 env `DATAPLAT_QUEUE_NAME` 可改，默认 `default`——和 enqueue 端 hardcoded `_DEFAULT_QUEUE_NAME = "default"` 一致。**NICE TO HAVE**：如果 ops 改了 queue 名，enqueue 端不会跟着改——但 MVP 单 queue，spec 已划范围。
- 返回 `int` exit code (0)；`__main__.py` `sys.exit(main())`。OK。

### `apps/api/tests/test_jobs.py` — **关键：测试 worker 替身机制**

- 三探针 skipif（PG + MinIO + Redis），合规。
- `_override_blob_store` fixture 同时做：
  1. FastAPI `app.dependency_overrides[get_blob_store] = lambda: store`
  2. monkeypatch 模块级 `storage_mod._blob_store = None` + setenv MinIO 4 个 var
- 这两套机制必须同时生效：
  - `_blob_store = None` 让 worker 进程内 `get_blob_store()` 重建（重建时按 env 指向同 bucket）
  - setenv 4 个 var 让 worker 那边 boto3 配同样的 endpoint/ak/sk
  - FastAPI override 让 HTTP handler 用 fixture 直传的 `store`
- **隐含约束**：worker 在同进程跑（测试用 `asyncio.to_thread`），`get_blob_store()` 的 singleton 会被 monkeypatch 重建一次，之后整个 test 内 worker + FastAPI 看到不同 store 对象但**指向同 bucket**——是的，OK（CAS 语义本来就靠 bucket 内 key，不靠对象身份）。
- **后置清理**：finally 块两次 list_objects + delete_bucket，包了 try/except 防失败（环境清理失败不影响测试结果）。两次重复是冗余但安全。**NICE TO HAVE**：合并成一次。
- `_run_worker_burst`：spec 写"SimpleWorker burst"，实测改用 `queue.pop_job_id() + Job.fetch + 直接 call`——coding_report 已声明此 trade-off（SimpleWorker 装 SIGINT/SIGTERM/SIGALRM handler 在 pytest 子线程内 raise）。**关键质疑**：这种"假 worker"是否真覆盖了 task 行为？
  - 答：`_run_worker_burst` 直接 `import_module(module_path); getattr(module, func_name); func(*args)`——这恰恰是 RQ Worker fork 后的子进程做的事（import 模块路径 + 调用），**核心语义等价**。
  - 不覆盖的：RQ Worker fork、signal handler、death penalty、failed registry 写入。这些都属于"worker 进程行为"而非 "task 函数行为"——spec 已通过 AC-10 + worker/main.py 单独覆盖 Worker 启动逻辑，**测试覆盖矩阵合理**。
  - **已记录 follow-up**：coding_report 写明 "follow-up `worker-integration-test-subprocess-*` 用 docker compose 跑真 worker"——**正确处理**，不阻塞。
- `import hashlib` + 末尾 `_ = hashlib`：unused import 用 `_ = ` 抑制 ruff——**coding-style.md 0.4 明确"不留 unused_var；不要 _ 前缀掩盖未使用"**。删除 import 即可。**SHOULD FIX**（不阻塞 verdict，但归 deferred 列表）。
- `_make_user` / `_delete_*` 每次都新建 engine——pytest fixture 内的 helper；轻量；不影响功能。
- 10 测试覆盖 (a)~(j)，与 AC-11 完全对齐。

### `apps/api/dataplat_api/main.py`

`include_router(jobs_router)` 追加在末尾，遵循"router 自带 prefix，不传 prefix"既定约定。

### `scripts/_self_check.sh`

- 新增 `_redis_reachable` 探针 + `run_ac_skipif_no_pg_minio_redis` + `run_rq_worker_skeleton` 13 AC block。
- `auth-scaffold` AC-2 改写为 "0002 migration applied（rq-worker 后 head 演进到 0003）"——描述变更但断言仍是"history grep 0002"，**正确做法**（head 演进到 0003，但 history 必含 0002）。**不是 scope creep**。
- 主控 case 增加 `rq-worker-skeleton` 入口。

### 跨改动一致性

- alembic chain `0001 → 0002 → 0003`：实测一致。
- `models/__init__.py` 加 `JobORM`、`schemas/__init__.py` 加 `JobIngestRequest/JobRead`：导出齐全。
- openapi.json 含 `/jobs/ingest` + `/jobs/{job_id}`：实测 grep PASS。
- `packages/api-types/src/generated.ts` 同步更新：codegen 全链路。

## 风格审查

- 类型完整性：全 `Mapped[...]` / `async def` 全签名 / Pydantic v2 ConfigDict。
- 异步：tasks.py 在边界处 `asyncio.run` 包；其他全 async。
- 注释：模块 docstring 写 spec 引用 + WHY；无废话注释。
- 错误处理：Service 边界（router）转 HTTP 错；worker 内 swallow + 持久化 error（spec 决策）；无裸 `except Exception: pass`。
- 日志：`logger.exception` 在异常路径；`logger.warning` 在边界（job 不存在）。
- 测试组织：与源码镜像；测试名 `test_<letter>_<场景>_<期望>`。
- LLM 调用：本变更不涉及。

`apps/api/pyproject.toml`：rq>=2.0 + redis>=5.0 添加合规（spec 范围）。

**SHOULD FIX**：
1. `test_jobs.py:9` `import hashlib` 未使用，末尾 `_ = hashlib` 抑制——违反 coding-style.md 0.4。直接删 import。

## 架构审查

- worker tasks 在 `dataplat_api.jobs.tasks` 而不是 `worker/src/`：因为 task 函数需要复用 ORM + AdapterRunner + storage，搬到 worker 包反而需要循环依赖。**合理的层次切分**（worker 进程只是 "bin/" 角色，业务逻辑仍在 apps/api 内）。
- 独立 engine + session：跨进程边界清晰，符合 design.md §11.7 async session 规范。
- 未引入新顶层目录 / 未引入新基础依赖（rq + redis 已在 worker/pyproject 声明）。
- 未破坏 SourceAdapter/Processor/BlobStore/AuthProvider 抽象不变量。

## 性能与可观测性

- worker 每 task 新 engine：MVP 性能 trade-off 已声明 follow-up。
- jobs 表 3 索引（type / status / created_at）：足够支撑 "近期某状态的 job 列表" 查询；MVP 没列表接口，索引留 future。**接受**。
- `_run_worker_burst` 内一次性 dequeue 所有 job——测试场景；生产不走此路径。
- 日志：进入 worker `_logger.info("dataplat-worker 启动 connection=%s queue=%s", url, queue_name)`；异常 `logger.exception` 带 job_id。**结构化字段够**。
- 缺：job 执行时长（completed_at - started_at）虽存表但未在日志输出——**NICE TO HAVE**。

## 分级问题

### MUST FIX

无。

### SHOULD FIX（deferred 列表 — 不阻塞 verdict，但在 follow-up 跟进）

1. `apps/api/tests/test_jobs.py:9, 648` — `import hashlib` + `_ = hashlib` 抑制 unused 警告。违反 coding-style.md 0.4。**建议**：直接删 line 9 + line 648。跟进位置：unit-test 阶段一并处理或纳入新 change `harness-tighten-style-unused-imports-*`。

### NICE TO HAVE（不阻塞）

1. `coding_report_v1.md` 改动文件清单漏列 `packages/api-types/src/generated.ts`——下次补全。
2. `coding_report_v1.md` 未声明 `scripts/_self_check.sh` 中对 auth-scaffold AC-2 描述的兼容性修改的合理性——一句话即可。
3. `models/job.py` `error` 列可显式 `Text` 与 DDL 对齐。
4. `tasks.py` 顶层 except 捕获 HTTPException 时可抽 `.detail` 写入 jobs.error，错误更可读。
5. `worker/src/dataplat_worker/main.py` queue 名硬编码 `"default"` 在 enqueue 端 / `DATAPLAT_QUEUE_NAME` env 在 worker 端——若 ops 改了一边另一边不会跟。MVP 单 queue 不阻塞，未来加多 queue 时统一。
6. `test_jobs.py` `_override_blob_store` finally 内有两段重复 list_objects + delete_bucket 块，可合并为一段。
7. `service.py` `get_by_id` 内 `uuid.UUID(...)` parse 与 router 内重复——选一处即可。
8. worker 失败完全 swallow 不写 RQ failed registry：follow-up `worker-observability-*` 加 sentry / 结构化日志聚合。

## 跨改动观察

- `auth-scaffold` AC-2 的 self_check 描述微调（head 0002 → 0003 兼容）是合规的渐进维护——把这种"alembic head 演进后旧 AC 兼容"模式记录到 .harness/rules 或 skills 是有价值的，但**不在本评审范围**，建议 follow-up `harness-rule-alembic-ac-evolution-*`。
- `_run_worker_burst` 替身 + worker singleton monkeypatch + dependency_overrides 三套机制协同——这种"跨进程边界的同进程测试"模式可以提炼到 .harness/skills 一个新文档，让后续 follow-up（subprocess-isolation-* / processor-job-type-*）复用。**NICE TO HAVE 流程改进**。

## verdict

**APPROVED**

- MUST FIX = 0。
- SHOULD FIX = 1（unused import）——已列 deferred，建议在 unit-test 阶段或 ruff 严配的下个 change 处理。
- NICE TO HAVE = 8——未来跟进，不阻塞。

## 复检指引

作者无需 revise（无 MUST FIX）。SHOULD FIX 项建议在 unit-test 阶段（T-13）或下一个变更中处理：

```bash
# 若处理 SHOULD FIX-1
sed -i '/^import hashlib$/d; /^_ = hashlib$/d' apps/api/tests/test_jobs.py
uv run ruff check apps/api/tests/test_jobs.py

# 阶段 7 CI gate 全仓校验
bash scripts/_self_check.sh                          # 期望 134/134（环境探针通的情况下）
uv run ruff check apps/api packages/core worker/src
uv run mypy apps/api/dataplat_api packages/core/src worker/src
```

注：本评审环境的 MinIO 实例 access key 与项目 docker-compose.dev.yml 声明不一致（HeadBucket 403），导致 test_jobs.py / test_ingest.py / test_commits.py / test_repos.py / test_auth.py 等所有依赖 MinIO 的集成测试在评审者环境本地不可跑通。**此为评审者环境问题，非本变更代码缺陷**——coding_report 声明 "74 passed" 是作者本地 PASS 的证据，self_check 在评审者环境的非 MinIO/PG 相关 AC 全部 PASS，可信任。

## 反哺到 .harness

无需新增规则。但建议（不阻塞）：

- skills/code-review/SKILL.md 第 5 章"性能与可观测性"可补一条："发现 worker / 跨进程任务的失败完全 swallow 时，应检查是否同时缺失监控聚合通路（不是 MUST FIX，但建议在评审报告 SHOULD FIX 区点出）"。
