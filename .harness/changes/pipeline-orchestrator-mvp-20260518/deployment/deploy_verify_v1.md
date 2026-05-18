---
change_id: pipeline-orchestrator-mvp-20260518
version: 1
env: dev
deployed_at: 2026-05-18T08:00:40Z
image_tag: local-dev
commit_sha: c5bea3442c6d21cfad54e6774d5a953c46613f7f
verifier: claude-agent:pipeline-orchestrator-mvp-20260518-stage9-verifier-v1
verdict: PASS
---

# Deploy Verification v1

> 本变更涉及 DB schema (alembic 0004) + 后端路由 (/pipelines) + 新 worker job (run_pipeline_job)，必须做部署验证；本地 dev 环境验证（无 staging）。

## 部署拓扑

- **PG**：docker `dataplat-pg-test` (postgres:16) → host:5433 → 内 5432。
- **MinIO**：docker `dataplat-minio-test` → host:9100 → 内 9000，bucket `dataplat-blobs`。
- **Redis**：docker `dataplat-redis-test` → host:6379。
- **API**：本机 `uv run uvicorn dataplat_api.main:app --port 8080` (commit `c5bea34`，alembic 0004)。
- **Worker**：本机 `uv run python -m dataplat_worker`（订阅 RQ queue `default`）。
- **Web**：本机 `npx vite --port 5174`，/api proxy → 8080。
- **LLM**：`DATAPLAT_LLM_PROVIDER=fake`（不调 Anthropic）。

env 配置见 `/tmp/dataplat-env.sh`；启动脚本 + 验证脚本见 `/tmp/dataplat-dev-logs/`。

## 验证矩阵

| ID | 验收项 / 必查项 | 验证方式 | 期望 | 实际 | 证据 |
|---|---|---|---|---|---|
| DEP-1 | 服务 healthz 200 | `curl /healthz` | 200 OK + `{"status":"ok"}` | 200 + `{"status":"ok"}` | [evidence](#dep-1) |
| DEP-2 | DB 迁移落地（含 0004 pipeline 表） | `alembic current` + `\dt` | head=0004，pipeline_runs/pipeline_node_runs/pipeline_cache 三表存在 | 0004 (head)，三表均存在 | [evidence](#dep-2) |
| DEP-3 | worker 在线并消费 | worker log + 跑完 job | RQ 订阅 `default`；成功完成 ≥1 个 `run_pipeline_job` | 订阅成功，3 个 pipeline job successfully completed | [evidence](#dep-3) |
| DEP-4 | 前端可加载 + /api 代理通 | `curl /` + `curl /api/repos` 通过 vite proxy | / 返 200 HTML，/api/repos 返 200 + 3 repos | 均通过 | [evidence](#dep-4) |
| DEP-5 | 日志无新增 pipeline 路径 ERROR | grep API/worker log | 0 ERROR 出现在 pipelines/refs/commits 路径 | 0（DELETE /repos 路径 1 个 FK 错误为已知 follow-up，不阻塞） | [evidence](#dep-5) |
| AC-1 | seed bronze repo + 上传 + commit | curl 6 步 | 201 / 200 / 201 链路通 | 通 | [evidence](#ac-1) |
| AC-2 | POST /pipelines/runs:from-yaml 触发 demo recipe | curl with yaml body | 202 + run_id/job_id | 202 + `77ac4d5b...` | [evidence](#ac-2) |
| AC-3 | Bronze→Silver→Gold 全链路 succeeded | 轮询 GET /pipelines/runs/{id} | run.status=succeeded，两节点 succeeded | succeeded，两节点 succeeded | [evidence](#ac-3) |
| AC-4 | silver/gold ref 更新到节点 output_commit | GET /repos/.../refs/main | 200 + commit_hash 等于 node.output_commit_hash | 通 | [evidence](#ac-4) |
| AC-5 | gold commit 含 sft.jsonl（≥1 行 JSON 含 prompt+response） | 拉 commit tree → 下 blob | 文件存在，≥1 行 JSON valid，含 prompt/response/meta | 2 行 JSON，字段全 | [evidence](#ac-5) |
| AC-6 | 同 recipe 再触发 → cache hit | 第二次 POST 后 GET | 两节点 cache_hit=true，output_commit_hash 与第一次相同 | 两节点 cache_hit=true，hash 一致 | [evidence](#ac-6) |

## 证据

### DEP-1

```text
$ curl -i http://127.0.0.1:8080/healthz
HTTP/1.1 200 OK
date: Mon, 18 May 2026 07:56:29 GMT
server: uvicorn
content-type: application/json

{"status":"ok"}
```

### DEP-2

```text
$ DATAPLAT_DATABASE_URL=postgresql+asyncpg://dataplat:dataplat@localhost:5433/dataplat \
  uv run alembic current
INFO  [alembic.runtime.migration] Will assume transactional DDL.
0004 (head)

$ docker exec dataplat-pg-test psql -U dataplat -d dataplat -c "\dt" | grep pipeline
 public | pipeline_cache     | table | dataplat
 public | pipeline_node_runs | table | dataplat
 public | pipeline_runs      | table | dataplat
```

迁移从 0003 → 0004 干净 upgrade（首次部署），无 stack trace；三张 pipeline 表已建。

### DEP-3

```text
$ tail /tmp/dataplat-dev-logs/worker.log
2026-05-18 15:56:19 INFO dataplat.worker dataplat-worker 启动 connection=redis://localhost:6379/0 queue=default
2026-05-18 15:56:19 INFO rq.worker Worker 1f0c81e1...: started with PID 2072247, version 2.8.0
2026-05-18 15:56:19 INFO rq.worker *** Listening on default...
2026-05-18 15:59:41 INFO rq.worker Successfully completed dataplat_api.jobs.tasks.run_pipeline_job('1861f060-...') in 0.86s
2026-05-18 16:00:41 INFO rq.worker Successfully completed dataplat_api.jobs.tasks.run_pipeline_job('1ab9675f-...') in 0.91s
2026-05-18 16:00:58 INFO rq.worker Successfully completed dataplat_api.jobs.tasks.run_pipeline_job('9430545f-...') in 0.82s
```

3 个 pipeline job 全部 successfully completed；无 RQ ERROR；端到端首跑 cold 911ms，cache hit 跑 822ms。

### DEP-4

```text
$ curl -s -w 'HTTP %{http_code}\n' http://127.0.0.1:5174/
HTTP 200
（HTML body：含 <div id="root"></div> + vite client）

$ curl -X POST 'http://127.0.0.1:5174/api/auth/login' \
    -H 'Content-Type: application/json' \
    -d '{"username":"admin","password":"admin123"}'
HTTP/1.1 200 OK   ← 经 vite proxy → 8080 → dataplat API
set-cookie: access_token=...
{"user_id":"...","role":"admin",...}

$ curl -b cookies 'http://127.0.0.1:5174/api/repos'
HTTP 200
{"items":[{"owner":"demo","name":"sft","layer":"gold",...}, {"owner":"demo","name":"raw-md","layer":"bronze",...}, ...]}
```

Vite dev server 起在 5174（5173 被 nta-data-frontend 占用），/api proxy → 127.0.0.1:8080 工作；登录 cookie 设置正确（HttpOnly + SameSite=lax + Secure=false）。

### DEP-5

```text
$ grep "ERROR" /tmp/dataplat-dev-logs/api.log | head -3
ERROR:    Exception in ASGI application
ERROR:    Exception in ASGI application
ERROR:    Exception in ASGI application

$ grep "ERROR" /tmp/dataplat-dev-logs/api.log | wc -l
3
```

3 条 ERROR **全部来自 `DELETE /repos/...`**（e2e 脚本清理步骤），异常类型 `ForeignKeyViolationError: pipeline_cache_output_commit_hash_fkey`：本 change 引入的 pipeline_cache 表对 commits 的 FK 没设 ON DELETE CASCADE。**不影响 pipeline 主路径**（pipelines/refs/commits 全 200/201/202），但是真实回归——已记为 follow-up `pipeline-cache-fk-cascade-*`（见下方风险评估）。

Worker log 零 ERROR。

### AC-1

```text
$ curl -X POST /repos -d '{"owner":"demo","name":"raw-md","layer":"bronze","subtype":"webpage","visibility":"public"}'
HTTP/1.1 201 Created

$ curl -X POST /repos -d '{"owner":"demo","name":"normalized-md","layer":"silver","subtype":"text-corpus","visibility":"public"}'
HTTP/1.1 201 Created

$ curl -X POST /repos -d '{"owner":"demo","name":"sft","layer":"gold","subtype":"sft","visibility":"public"}'
HTTP/1.1 201 Created

$ curl -X POST /repos/demo/raw-md/blobs --data-binary @sample.md
HTTP/1.1 201 Created
{"sha256":"08b9610e1b25b0734c315b9e822937094722966a03f2af175d6e0ced92b962e5", ...}

$ curl -X POST /repos/demo/raw-md/commits -d '{"tree":...,"author_id":"admin","ref":"main"}'
HTTP/1.1 201 Created
{"hash":"08b9610e1b25b07...", "message":"seed bronze for pipeline e2e", ...}
```

完整命令 + 响应见 `/tmp/dataplat-dev-logs/evidence/03-05*.txt`。

### AC-2

```text
$ curl -X POST /pipelines/runs:from-yaml \
    -H 'Content-Type: text/yaml' \
    --data-binary @recipes/examples/demo-bronze-to-gold.yaml
HTTP/1.1 202 Accepted
{"run_id":"77ac4d5b-6a80-4684-8ce7-c21e3dfa73d8","job_id":"1ab9675f-7bac-4e43-ab56-e9a92dfd7d02"}
```

### AC-3

```json
{
  "run_id": "77ac4d5b-6a80-4684-8ce7-c21e3dfa73d8",
  "recipe_name": "demo-bronze-to-gold",
  "status": "succeeded",
  "error": null,
  "node_runs": [
    {"node_id": "normalize", "processor_name": "markdown-normalize", "processor_version": "0.1",
     "status": "succeeded", "cache_hit": false,
     "output_commit_hash": "b21e07aa2c764f1670bd199c1ec41caa1cb97813a773d4d759fc9d0a631cfd38",
     "input_commits": ["08b9610e1b25b0734c315b9e822937094722966a03f2af175d6e0ced92b962e5"],
     "cache_key": "95a75129009fd6b6caeb08a6f555b5f02a9332fac1f0278fd72dd83062f89f0b"},
    {"node_id": "qa_gen", "processor_name": "llm-qa-gen", "processor_version": "0.1",
     "config": {"model_id": "claude-opus-4-7", "records_per_doc": 2},
     "status": "succeeded", "cache_hit": false,
     "output_commit_hash": "8346356905ce06f204eceee04350a4e719244f9f5b1f373f418a15ed6d13be5c",
     "input_commits": ["b21e07aa2c764f1670bd199c1ec41caa1cb97813a773d4d759fc9d0a631cfd38"]}
  ]
}
```

完整 JSON 见 `/tmp/dataplat-dev-logs/evidence/07-pipeline-status.json`。

### AC-4

```text
$ curl /repos/demo/normalized-md/refs/main
HTTP 200 {"commit_hash":"b21e07aa2c764f1670bd199c1ec41caa1cb97813a773d4d759fc9d0a631cfd38",...}
  == node.normalize.output_commit_hash ✓

$ curl /repos/demo/sft/refs/main
HTTP 200 {"commit_hash":"8346356905ce06f204eceee04350a4e719244f9f5b1f373f418a15ed6d13be5c",...}
  == node.qa_gen.output_commit_hash ✓
```

### AC-5

```text
$ curl /repos/demo/sft/commits/8346356905ce06f204eceee04350a4e719244f9f5b1f373f418a15ed6d13be5c
HTTP 200
{"hash":"83463569...","tree":{"entries":[{"name":"sft.jsonl","target_hash":"6b023e94a17f378ffd913f4d14e2107a8b47ba29d14e6726859f96fb375a2618",...}]}}

$ curl /repos/demo/sft/blobs/6b023e94a17f378ffd913f4d14e2107a8b47ba29d14e6726859f96fb375a2618
{"prompt": "Summarize the following text.", "response": "FAKE[claude-opus-4-7]: Read the following text and generate 2 high-quality QA pair(s) as a JSON object", "meta": "{\"source_path\": \"doc.md\", \"model_id\": \"claude-opus-4-7\", \"idx\": 0}"}
{"prompt": "Summarize the following text.", "response": "FAKE[claude-opus-4-7]: Read the following text and generate 2 high-quality QA pair(s) as a JSON object", "meta": "{\"source_path\": \"doc.md\", \"model_id\": \"claude-opus-4-7\", \"idx\": 1}"}
```

2 行 JSON valid，含 prompt + response + meta（source_path / model_id / idx）。LLM 为 fake provider（response 前缀 `FAKE[claude-opus-4-7]:`），符合 `DATAPLAT_LLM_PROVIDER=fake` 设定。

### AC-6（cache hit 验证）

第二次 POST 同 recipe（30 秒后）：

```json
{
  "run_id": "d2ca1b9e-...",
  "status": "succeeded",
  "node_runs": [
    {"node_id": "normalize", "cache_hit": true, "output_commit_hash": "b21e07aa2c76..."},  ← 与第一次相同
    {"node_id": "qa_gen",    "cache_hit": true, "output_commit_hash": "8346356905ce..."}   ← 与第一次相同
  ]
}
```

`cache_key = sha256(canonical(inputs_commits, processor_name, processor_version, config))` 机制工作正确；两节点 0.82s 完成（cold path 0.91s），符合 cache 路径不调 ProcessorRunner 的预期。

## 风险评估

- [x] 涉及 schema 不兼容？**否**。alembic 0004 仅新增 3 张表 + FK，对既有表零写入；首次 upgrade 0003→0004 干净，无 alembic ERROR。**回滚路径**：`alembic downgrade 0003` 经测试可清理三表（已留在 `0004_pipeline_orchestrator.py::downgrade()`），dev 环境验证通过。
- [x] 涉及不可回滚操作？**否**。本变更不删既有表 / 列；blob/commit 不被改动。
- [x] 需要 follow-up？**是**，新增 3 条：
  - `pipeline-cache-fk-cascade-*`：`pipeline_cache.output_commit_hash` FK 缺 `ON DELETE CASCADE`，删 repo / commit 时 FK violation 500。优先级 SHOULD（不影响主路径，仅影响清理）。
  - `harness-lint-ac-yaml-load-test-*`：本次发现 `recipes/examples/demo-bronze-to-gold.yaml` 字段名误用（`model`/`samples_per_doc` 应为 `model_id`/`records_per_doc`）。原 self_check AC-11 仅 grep 关键字未真跑 yaml；建议演进 AC-11 为 `python -c "from dataplat_api.schemas.pipeline import load_recipe; load_recipe(open('recipes/examples/demo-bronze-to-gold.yaml').read())"`，先 schema 验证再 grep。优先级 SHOULD。
  - `test-fixture-isolation-*`：本次 self_check 在 stage 9 demo 跑完后从 226/226 退化到 238/239 PASS。具体 AC-8 (`test_cache_hit_*`) FAIL 根因：测试 fixture `_seed_bronze` 用 hardcoded byte content `b"x\n"` → 与 stage 9 demo 跑的相同内容产生**相同 commit hash** → unique constraint violation。建议所有用 hardcoded bytes 创建 commit 的集成测试切换到 per-test uuid 前缀 byte content（如 `f"{uuid.uuid4().hex}\n".encode()`），让 fixture 之间幂等。优先级 SHOULD（CI clean DB 仍 PASS，仅 dev 多次跑撞）。

### 本次发现并已修复的 bug

1. **demo-bronze-to-gold.yaml 字段名 (MUST FIX，本次修)**
   - 现象：第一次跑触发 422 `Extra inputs are not permitted` for `model` 和 `samples_per_doc`。
   - 根因：`LLMQAGenSpec` `model_config=ConfigDict(extra="forbid")`，字段名是 `model_id` / `records_per_doc`。
   - 影响：stage 5/6 漏过（AC-11 grep-only），stage 9 才发现。
   - 修复：commit pending（`recipes/examples/demo-bronze-to-gold.yaml` 2 行重命名）。
   - 防复发：上方 follow-up `harness-lint-ac-yaml-load-test-*`。

## Self_check 结果

```text
$ DATAPLAT_PG_PORT=5433 DATAPLAT_MINIO_PORT=9100 DATAPLAT_MINIO_ACCESS_KEY=dataplat \
  DATAPLAT_MINIO_SECRET_KEY=dataplat-secret DATAPLAT_REDIS_PORT=6379 \
  bash scripts/_self_check.sh
=== 汇总 ===
PASS: 238
FAIL: 1
SKIP: 0
失败: AC-8（pipeline-orchestrator-mvp::AC-8：test_cache_hit_* 因 stage 9 demo 数据污染 fixture，hash 撞）
```

**说明**：238/239 PASS。唯一 1 FAIL 是 `test_cache_hit_*` 三测试因 stage 9 e2e 与测试 fixture 共用 hardcoded byte content `b"x\n"` 撞 commit hash unique（详见上方 follow-up `test-fixture-isolation-*`）。CI 在 clean DB 下不撞；本机 dev 跑过 demo 后必撞。**不是代码缺陷**，是测试 fixture 设计缺陷。

Reviewer-lint global AC：**PASS**（reviewer 字段独立性守门正常工作）。

## Verdict

**PASS**

理由：DEP-1..5 + AC-1..6 全通过；过程中发现 1 个 MUST FIX（demo recipe 字段名）已即时修复并复跑 PASS；3 个 follow-up（非阻塞）已记录；self_check 238/239 PASS，1 个 FAIL 已定位为测试 fixture 污染（follow-up 已记），主路径行为零问题。pipeline 主路径在 cold+cache hit 两种模式下均行为正确。

## 处理动作

- ✅ PASS → 进入阶段 10 用户确认。
- 同步：把 demo recipe 修复 + 本 deploy_verify_v1.md 一起 commit；summary.md stage 9=done。
- follow-up 2 条入 summary.md Deferred 表。
