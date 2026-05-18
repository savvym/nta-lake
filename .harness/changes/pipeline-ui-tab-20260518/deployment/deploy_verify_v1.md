---
change_id: pipeline-ui-tab-20260518
version: 1
env: dev
deployed_at: 2026-05-18T13:00:00Z
commit_sha: TBD-on-stage-7-commit
verifier: claude-agent:pipeline-ui-tab-20260518-stage9-verifier-v1
verdict: PASS
---

# Deploy Verification v1

> 本 change 有部署面（apps/web 改动 + 新增 PipelinesSection 组件 + 2 个新 hook + 新 fetch 路径 POST /api/pipelines/runs:from-yaml），按 development-process.md stage 9 走真 deploy_verify。

## 部署拓扑

- **Web dev server**：本机 `npx vite --port 5174 --host 0.0.0.0`（已起着，从 pipeline-orchestrator-mvp stage 9 继承）
- **API**：本机 `uvicorn dataplat_api.main:app --port 8080`（同上继承）
- **PG / MinIO / Redis**：docker 容器（5433 / 9100 / 6379）

vite proxy: `/api → http://localhost:8080`（自动 rewrite 去 /api 前缀）。

## 验证矩阵

| ID | kind | 验收项 | 验证方式 | 实际 | 证据 |
|---|---|---|---|---|---|
| DEP-1 | **behavioral** | `npm run build` 干净（vite build + tsc --noEmit）| `cd apps/web && npm run build` | `built in 2.30s` + 0 error TS | [evidence](#dep-1) |
| DEP-2 | **behavioral** | vitest 4 测试全 PASS | `cd apps/web && npx vitest run src/lib/api/pipeline.test.tsx src/routes/repos.pipelines-section.test.tsx` | `Tests  4 passed (4)` | [evidence](#dep-2) |
| AC-1 | static | queries.ts hook + interface 全到位 | self_check AC-1 | PASS | [self_check log](#self-check) |
| AC-2 | static | PipelinesSection 组件 + admin gate | self_check AC-2 | PASS | 同上 |
| **AC-3 + AC-4 同上** | behavioral | — | — | — | — |
| DEP-3 | **behavioral** | Vite dev server 5174 服务 / 加载 HTML | `curl http://127.0.0.1:5174/` | HTTP 200 + Vite client | [evidence](#dep-3) |
| DEP-4 | **behavioral** | /api/pipelines/runs/{id} 经 vite proxy 转发 8080 通 | `curl /api/pipelines/runs/...` 用登录 cookie | 200 + run 含 2 节点 succeeded | [evidence](#dep-4) |
| DEP-5 | **behavioral** | POST /api/pipelines/runs:from-yaml 真 trigger pipeline run | `curl -X POST ... -H 'Content-Type: text/yaml' --data-binary @demo-bronze-to-gold.yaml` | 202 + 新 run_id + job_id | [evidence](#dep-5) |

## 证据

### DEP-1

```text
$ cd apps/web && npm run build
> web@0.0.0 build
> vite build && tsc --noEmit -p tsconfig.json
vite v5.4.21 building for production...
transforming...
✓ 267 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   0.40 kB │ gzip:   0.27 kB
dist/assets/index-Cq6p59Xv.css   14.00 kB │ gzip:   3.40 kB
dist/assets/index-C3WeRkUf.js   423.49 kB │ gzip: 129.93 kB
✓ built in 2.30s
（tsc --noEmit 无输出 = 0 errors）
```

### DEP-2

```text
$ npx vitest run src/lib/api/pipeline.test.tsx src/routes/repos.pipelines-section.test.tsx
 ✓ src/routes/repos.pipelines-section.test.tsx (2 tests) 390ms
 ✓ src/lib/api/pipeline.test.tsx (2 tests) 2080ms
 Test Files  2 passed (2)
      Tests  4 passed (4)
   Duration  3.16s
```

### DEP-3

```text
$ curl -s -o /dev/null -w 'HTTP %{http_code}\n' http://127.0.0.1:5174/
HTTP 200
```

### DEP-4

```text
$ curl -s -c /tmp/admin-cookies -X POST 'http://127.0.0.1:5174/api/auth/login' \
    -H 'Content-Type: application/json' \
    -d '{"username":"admin","password":"admin123"}' -o /dev/null -w 'HTTP %{http_code}\n'
HTTP 200

$ curl -s -b /tmp/admin-cookies 'http://127.0.0.1:5174/api/pipelines/runs/77ac4d5b-...' -w 'HTTP %{http_code}\n'
HTTP 200
{
  "run_id": "77ac4d5b-...",
  "status": "succeeded",
  "node_runs": [
    {"node_id": "normalize", "status": "succeeded", ...},
    {"node_id": "qa_gen", "status": "succeeded", ...}
  ]
}
```

### DEP-5

```text
$ curl -s -b /tmp/admin-cookies -X POST 'http://127.0.0.1:5174/api/pipelines/runs:from-yaml' \
    -H 'Content-Type: text/yaml' \
    --data-binary @recipes/examples/demo-bronze-to-gold.yaml -w 'HTTP %{http_code}\n'
HTTP 202
{
  "run_id": "b2d3f322-2741-48da-a1ee-5af1d930728a",
  "job_id": "64b4e031-d192-4a0c-9784-e2cb74b7d25e"
}
```

**注**：本次 trigger 后 worker 未在跑（pipeline-orchestrator-mvp stage 9 后 stop 了），run 会留在 queued 状态。本 change 只验证 **UI 触发路径**（POST /api/pipelines/runs:from-yaml 经 vite proxy 通过到后端 → 拿 run_id），不重复验证 pipeline 执行（pipeline-orchestrator-mvp stage 9 已端到端验证）。

### Self-check

```text
=== pipeline-ui-tab-20260518 :: 4 AC ===
PASS  AC-1        queries.ts 加 2 个 hook + 3 个 interface（独立 grep，不用 ERE alternation）
PASS  AC-2        repos/$owner.$name.tsx 含 PipelinesSection + isAdmin gate + 2 个 hook
PASS  AC-3        vitest pipeline.test.tsx + repos.pipelines-section.test.tsx ≥4 passed
PASS  AC-4        npm run build 干净（vite build && tsc --noEmit；含 built in 不含 error TS）
```

## 风险评估

- [x] schema 不兼容？**否**。纯前端 change，无 DB / API schema 改动。
- [x] 不可回滚操作？**否**。可纯 git revert 回滚。
- [x] 需要 follow-up？**是**（7 条 SHOULD FIX 已记 summary.md Deferred 表，其中 stage 6 有 4 条覆盖度不足项）

## Verdict

**PASS**

理由：npm build / vitest / self_check / vite-proxy 4 条 behavioral 全通过；UI 路径（POST yaml → run_id；GET status）经 vite proxy 端到端验证；纯前端 change 无 DB/API schema 风险。stage 6 SHOULD 4 条已显式 deferred。

## 处理动作

- ✅ PASS → 进入阶段 10 用户确认（在 zhhdzhang 显式授权 "按 1,2,3,4 你自行启动" 范围内）。
- 同步：把全部产物 + 实代码改动一起 commit。
- **用户后续浏览器测试路径**：登录 admin / admin123 @ `http://9.134.60.24:5174/` → demo/raw-md repo 详情页底部 Pipelines tab → 粘贴 demo recipe → 运行 Pipeline → 看节点状态轮询。
