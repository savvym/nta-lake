---
change_id: web-write-flows-20260517
version: 1
env: dev
deployed_at: 2026-05-17T16:00:00Z
status: deployed
---

# Deploy Verify v1

## 部署面

本变更纯前端 + 后端无改动；HMR 已自动热更新到运行中的 Vite dev server。

## 实际部署

- Vite dev server 跑在 `0.0.0.0:5174`（5173 被本机其他进程占用）
- 浏览器外部访问 `http://9.134.60.24:5174/`
- API（FastAPI `127.0.0.1:8080`）+ Worker（RQ 连 Redis）+ PG（5433）+ MinIO（9100）+ Redis（6379）全部运行中

## 用户确认（人工 smoke）

待用户在浏览器跑端到端 admin 工作流确认。
