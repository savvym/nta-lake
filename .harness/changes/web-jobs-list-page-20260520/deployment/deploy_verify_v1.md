---
change_id: web-jobs-list-page-20260520
version: 1
env: dev
deployed_at: 2026-05-20T06:15:00Z
verifier: application-owner-agent
status: PASS
---

# Deploy Verify v1 (dev)

## 部署方式

- 同源 monorepo 本地服务：FastAPI uvicorn 0.0.0.0:8080 + vite 0.0.0.0:5173 + RQ worker
- 重启动作：kill 旧 uvicorn pids 2798885/2798888，重启同命令（pickup main 上新合入的 routers/jobs.py）
- 前端 vite dev server HMR 自动 pick up 新 `routes/jobs/index.tsx` + `__root.tsx` 改动

## 验证步骤 / 结果

### 1) OpenAPI schema 含新端点 ✅
```
$ curl -s http://localhost:8080/openapi.json | jq -r '.paths | keys[]' | grep "^/jobs"
/jobs
/jobs/{job_id}
/jobs/ingest
```
新 `/jobs` 出现在 schema 中。

### 2) admin login → GET /jobs 200 ✅
```
$ curl -X POST /auth/login {admin/admin123} → 200 + set-cookie access_token
$ curl -H "Cookie: $COOKIE" /jobs?limit=3
{"items":[3 项],"total":823,"limit":3,"offset":0}
```
真实数据：823 条 job，分页生效，items 含完整 payload/result 字段。

### 3) 401 未登录 ✅
```
$ curl /jobs → 401
```

### 4) 400 非白名单 status ✅
```
$ curl -H "Cookie: $COOKIE" /jobs?status=bogus → 400
{"detail":"status 'bogus' 非白名单；允许：['failed', 'queued', 'running', 'succeeded']"}
```

### 5) status filter 实际收窄 ✅
```
$ curl -H "Cookie: $COOKIE" /jobs?status=succeeded&limit=2
{total: 347, first.status: 'succeeded'}
```
823 条总数下 succeeded 子集 347；首项 status 确实为 succeeded。

### 6) Web UI（手动）— 待用户确认

- 入口：登录 admin 后 nav 出现 "Jobs" 链接（非 admin 不出现）
- /jobs 页：filter (status/type/page size) + 表格 + 上一页/下一页/Refresh
- 表格列：created（相对时间）/ id（前 8 位，链到 /jobs/{job_id}）/ type / status badge / payload 摘要 / 用时
- 翻页：limit 切换重置 offset=0

## 失败 / 回滚

无失败。回滚路径：`git revert 45407ed`（merge commit），重启 uvicorn。

## 后续指引

- stage 10：用户确认 UI 体验（filter / 翻页 / Refresh 即时生效；非 admin 看不到入口）
- follow-up：
  - `web-jobs-list-live-poll-*`：列表自动 5s 轮询（当前仅手动 Refresh）
  - `jobs-owner-acl-*`：JobORM 加 owner_id 后开放给普通 user 看自己的
  - `jobs-cancel-*`：cancel/retry 按钮
  - 上层提醒：用户最初请求的 follow-up `web-pdf-mineru-ui-*`（PDF→MD 按钮）仍未启动
