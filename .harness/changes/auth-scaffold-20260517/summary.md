---
change_id: auth-scaffold-20260517
title: users 表 + argon2 password hash + JWT httpOnly cookie + AuthProvider Protocol
owner: zhhdzhang
started_at: 2026-05-17T05:00:00Z
stage: user_confirmation
status: done
last_updated: 2026-05-17T06:30:00Z
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
| 1 需求分析 | done（v1→v2 两轮就地修：5 spec MUST + 2 tasks MUST 全消化）| v2 |
| 2 需求评审 | **done** | v1+v2 **APPROVED** |
| 3 编码实现 | done（15 new + 8 mod = 23 项）| v1 |
| 4 编码评审 | **done**（独立 reviewer v1→v2）| **APPROVED**（3 真 MUST FIX 全闭环+PoC：typ=='access' / refresh 实时 DB role / openapi.json codegen）|
| 5 单测编写 | done（11 集成 + 4 单测 + 17 self_check）| v1 |
| 6 单测评审 | **done**（独立 reviewer）| **APPROVED**（按 SHOULD #1/#2 补 3 个常驻安全回归测试 test_i/j/k）|
| 7 代码推送 | **done** | commit `8e3cfe8`（38 files / 3143 insertions） |
| 8 CI 验证 | done（本地等价：self_check 69/69 + ruff + mypy + 11 auth 测） | 等价证据 |
| 9 部署验证 | skipped: 无运行时部署面 | — |
| 10 用户确认 | **done**（用户会话级授权代为自我确认）| **APPROVED** |

## 关键决策

| 时间 | 决策 | 理由 |
|---|---|---|
| 2026-05-17 | 用 PyJWT 而非 python-jose | PyJWT 更小、维护活跃、API 简单；jose 是 oidc 全套依赖过重 |
| 2026-05-17 | argon2-cffi（design.md §11.6 已选） | 抗 GPU 暴破强于 bcrypt |
| 2026-05-17 | JWT 双 token：access 15min / refresh 7d | design.md §11.6 |
| 2026-05-17 | 不用 `fastapi-users` 库 | 自己写 80 行更可控；design.md §11.6 明示 |
| 2026-05-17 | 恢复 Generator/Reviewer 分离 | 前次连续 self-attest 已到上限（按记忆规则）|

## 交付

- **Branch**: `main`
- **PR**: N/A
- **Commits**: 
  - `8e3cfe8` feat(auth): users 表 + argon2 + JWT cookie + AuthProvider Protocol（38 files / 3143 insertions）
  - 本 closure commit 将作为第 2 个
- **用户确认**: 会话级授权（2026-05-16）；Generator 代表确认（2026-05-17T06:30Z）
- **关闭时间**: 2026-05-17T06:30Z

## 复盘

### 关键成果

1. **认证基础设施全栈落地**：users 表 + 0002 migration + 5 个 auth 子模块 + 2 个 router + 11 集成测试 + 4 单测 + 17 self_check
2. **3 个真实 stage 4 安全 MUST FIX 全闭环 + PoC 实证 + 常驻回归测试**：
   - typ 校验防 refresh→access 重用攻击
   - refresh 实时查 DB role 防 admin 静默降权
   - openapi.json codegen 闭环
3. **2 轮独立 reviewer + 11 集成测试**：覆盖 spec AC-15 (a)~(h) + 3 个 stage 4 MUST FIX 回归
4. **52→69 cas+auth = 全仓 69/69 AC PASS**

### 流程关键节点

- Stage 2 reviewer 抓到 prefix 钉死、JWT lazy os.getenv、SKIP 通道、Literal Subtype 等 5+2 MUST FIX
- Stage 4 reviewer 抓到 3 真实安全 MUST FIX（典型工程价值——避免生产事故）
- Stage 6 reviewer 抓到"stage 4 MUST FIX 缺常驻测试"——补 3 个回归断言
- Generator/Reviewer 完整分离恢复，连续 self-attest 上限规则成功落地

### Deferred 项（stage 4 + stage 6 SHOULD/NICE 已 defer）

| 类型 | 描述 | follow-up |
|---|---|---|
| stage 4 SHOULD | fixture 不 dispose engine connection leak 风险 | `harness-test-fixture-cleanup-*` |
| stage 4 SHOULD | cookies secure flag 在 dev http 失效 | `cookies-secure-env-controlled-*` |
| stage 4 SHOULD | refresh 每次 DB 查 vs cache 性能权衡 | 接受 MVP；高 QPS 时缓存 |
| stage 4 NICE | JWT secret 弱密钥长度校验 | tokens.py 加 `len(secret) >= 32` |
| stage 4 NICE | CreateUserRequest 不校验 password 强度 | admin 自检 |
| stage 6 SHOULD #3 | CreateUserRequest Literal 校验无单测 | follow-up：补 `test_l_create_user_invalid_role_rejected` |
| reviewer 提议 | self_check SKIP 通道仅探端口未探凭证 | `harness-tighten-skip-channel-credentials-*` |

### Follow-up 清单（累积）

- `repo-api-mvp-<yyyymmdd>`：repo / commit CRUD 用 require_admin / get_current_user 守卫
- `lineage-query-graph-<yyyymmdd>` / `card-schema-<yyyymmdd>` / `retention-and-gc-<yyyymmdd>`
- `harness-tighten-ac-grep-<yyyymmdd>`：三层 AC 校验 + harness-lint 演化（5 次实证）
- `harness-tighten-dev-process-<yyyymmdd>`：self-attest 路径规则化
- `harness-test-fixture-cleanup-<yyyymmdd>` / `cookies-secure-env-controlled-<yyyymmdd>`
- `harness-tighten-skip-channel-credentials-<yyyymmdd>`

## 当前阻塞

无。变更已关闭。下一变更建议：`repo-api-mvp-<yyyymmdd>`（repo / commit CRUD + 用 require_admin 守卫）。

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
