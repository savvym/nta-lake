---
change_id: auth-scaffold-20260517
title: users 表 + argon2 password hash + JWT httpOnly cookie + AuthProvider Protocol
owner: zhhdzhang
started_at: 2026-05-17T05:00:00Z
stage: request_analysis
status: in_progress
last_updated: 2026-05-17T05:00:00Z
related_changes:
  - core-domain-model-20260516
---

# Summary

## 一句话目标

按 [.harness/design.md](../../design.md) §11.6 落地 dataplat MVP 认证：`users` 表（含 external_id 预留 SSO）+ argon2-cffi 密码哈希 + JWT 双 token（access 15min / refresh 7d）httpOnly cookie + `AuthProvider` Protocol（`LocalAuthProvider` 实现）+ 4 路由（`/auth/login` / `/auth/logout` / `/auth/refresh` / `/auth/me`）+ `/admin/users` 占位。

## 范围摘要

- **In scope**：
  - `apps/api/dataplat_api/models/user.py`：`UserORM` 表 + 0002 alembic migration（含 `external_id` 列预留 SSO）
  - `packages/core/src/dataplat_core/protocols/auth.py`：`AuthProvider` Protocol（`authenticate(username, password) -> AuthenticatedUser | None`）+ `AuthenticatedUser` Pydantic
  - `apps/api/dataplat_api/auth/__init__.py` + `password.py`（argon2 hash/verify）+ `tokens.py`（JWT encode/decode + access/refresh 工具）+ `local_provider.py`（LocalAuthProvider 实现）+ `cookies.py`（httpOnly + Secure + SameSite 设置）+ `deps.py`（`get_current_user` FastAPI 依赖）
  - `apps/api/dataplat_api/routers/auth.py`：4 路由 `/auth/login` / `/auth/logout` / `/auth/refresh` / `/auth/me`
  - `apps/api/dataplat_api/routers/admin.py`：`/admin/users` POST/PATCH 路由（仅 admin 角色）
  - `apps/api/dataplat_api/main.py`：include 新 router
  - `apps/api/pyproject.toml`：+`argon2-cffi>=23.1` +`PyJWT>=2.8`
  - 单测：argon2 round-trip / JWT encode-decode / AuthenticatedUser 模型；集成：4 auth 路由 + 1 admin/users 路由
  - `scripts/_self_check.sh` 追加 auth-scaffold block
- **Out of scope**：
  - 不实现注册流程（admin 在后台或种子脚本建账号）—— design.md §11.6 MVP 明确不做
  - 不实现密码重置邮件流程
  - 不实现 MFA / OAuth login / 社交登录
  - 不实现 Repository 级 ACL（Phase 2，先用 `visibility` 字段）
  - 不实现 OIDC / SAML AuthProvider（接口预留，实现留给 follow-up）

## 阶段进度

| 阶段 | 状态 |
|---|---|
| 1 需求分析 | in_progress |
| 2 需求评审 | pending（独立 reviewer 子会话）|
| 3 编码实现 | pending |
| 4 编码评审 | pending（**恢复完整 Generator/Reviewer 分离**——按 [[session-handoff-20260517]] 规则，连续 self-attest 上限已到）|
| 5 单测编写 | pending |
| 6 单测评审 | pending（独立 reviewer 子会话）|
| 7 代码推送 | pending |
| 8 CI 验证 | 本地等价 |
| 9 部署验证 | skipped: 无运行时部署面 |
| 10 用户确认 | 用户会话级授权 Generator 自我确认 |

## 关键决策

| 时间 | 决策 | 理由 |
|---|---|---|
| 2026-05-17 | 用 PyJWT 而非 python-jose | PyJWT 更小、维护活跃、API 简单；jose 是 oidc 全套依赖过重 |
| 2026-05-17 | argon2-cffi（design.md §11.6 已选） | 抗 GPU 暴破强于 bcrypt |
| 2026-05-17 | JWT 双 token：access 15min / refresh 7d | design.md §11.6 |
| 2026-05-17 | 不用 `fastapi-users` 库 | 自己写 80 行更可控；design.md §11.6 明示 |
| 2026-05-17 | 恢复 Generator/Reviewer 分离 | 前次连续 self-attest 已到上限（按记忆规则）|

## 当前阻塞

- 无。Stage 2 已 **APPROVED**（spec v2 + tasks v2 双通过，0 MUST 残留）。下一步进入 Stage 3 编码。

## Stage 2 评审记录

| 版本 | reviewer | verdict | MUST | SHOULD | NICE | 报告 |
|---|---|---|---|---|---|---|
| spec v1 | claude-agent:auth-scaffold-stage2-reviewer | REVISION REQUIRED | 3 | 6 | 3 | [spec_review_v1.md](request_analysis/review/spec_review_v1.md) |
| tasks v1 | claude-agent:auth-scaffold-stage2-reviewer | REVISION REQUIRED | 3 | 6 | 3 | [tasks_review_v1.md](request_analysis/review/tasks_review_v1.md) |
| spec v2 | claude-agent:auth-scaffold-stage2-reviewer | **APPROVED** | 0 | 3 | 2 | [spec_review_v2.md](request_analysis/review/spec_review_v2.md) |
| tasks v2 | claude-agent:auth-scaffold-stage2-reviewer | **APPROVED** | 0 | 4 | 2 | [tasks_review_v2.md](request_analysis/review/tasks_review_v2.md) |

v2 关闭的关键 MUST：
1. spec AC-10 钉死 `APIRouter(prefix="/auth")` + main `include_router(r)` 不再传 prefix（与 AC-12 OpenAPI 同时 PASS 的唯一组合）
2. spec AC-6 明示 `encode_*/decode_*` 函数体内每次 `os.environ.get`，不得 cache 模块级（conftest setenv 才有效）
3. spec AC-15 期望列改 "PG up → exit 0；PG down → 命令 exit 1，AC-17 _self_check.sh SKIP 通道转 0"；测试数 ≥6 → ≥7，新增 (h) 普通用户 403
4. tasks T-11 `depends_on: [T-2, T-5, T-8]` 显式补 UserORM + AuthenticatedUser
5. tasks T-17 fixture scope='session'（alembic 一次）+ scope='function'（用户记录）+ conftest.py 顶层 `os.environ.setdefault(...)` 早于 dataplat_api import
6. tasks T-14 CreateUserRequest / UpdateUserRequest 字段固化（username / password|None / email|None / role: Literal / external_id|None）

SHOULD 残留（不阻塞，Stage 3 顺手处理）：
- spec AC-6 测试 secret 31 字节 < 32（AC-15 已 36 字节 OK）；AC-15 描述列文字 "≥6" 与 "≥7" 不一致
- T-10 末行 "isinstance(BlobStore-style)" cas-storage 残留；T-13 未显式重复 prefix；T-12 covers_ac AC-9 严格无贡献
- spec/tasks frontmatter version/last_updated 未跟随 v2 更新
