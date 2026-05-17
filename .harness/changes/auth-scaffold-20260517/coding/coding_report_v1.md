---
change_id: auth-scaffold-20260517
version: 1
authored_at: 2026-05-17T06:00:00Z
branch: main
base_commit: fc73193
head_commit: (stage 7 回填)
status: review_approved_v2
---

# Coding Report v1

## 一句话总览

按 spec v2 17 AC + tasks 18 个 T-*，落地 dataplat MVP 认证基础设施。**18 个改动文件**（15 new + 3 mod）。Stage 4 reviewer 抓到 3 个真实安全/正确性 MUST FIX（已全部就地修闭环并 PoC 实证）。

**最终成绩**：cas-storage 17 AC 全 PASS、auth-scaffold 17 AC 全 PASS、全仓 69/69 全 PASS、ruff + mypy 38 sources Success、8 auth 集成测试 PASS。

## 改动文件清单

| 路径 | 类型 | 说明 | T-* |
|---|---|---|---|
| `apps/api/pyproject.toml` | mod | +argon2-cffi>=23.1 / +PyJWT>=2.8 | T-1 |
| `apps/api/dataplat_api/models/user.py` | new | UserORM 表 + 3 unique constraint | T-2 |
| `apps/api/dataplat_api/models/__init__.py` | mod | 暴露 UserORM | T-3 |
| `apps/api/alembic/versions/0002_users.py` | new | 0002 migration + 3 unique index | T-4 |
| `packages/core/src/dataplat_core/protocols/auth.py` | new | AuthProvider @runtime_checkable Protocol + AuthenticatedUser BaseModel | T-5 |
| `packages/core/src/dataplat_core/protocols/__init__.py` | mod | 暴露 AuthProvider / AuthenticatedUser | T-6 |
| `apps/api/dataplat_api/auth/password.py` | new | hash_password / verify_password（argon2-cffi）| T-7 |
| `apps/api/dataplat_api/auth/tokens.py` | new | encode_access/refresh + decode + TokenError；lazy os.getenv（每次调用）| T-8 |
| `apps/api/dataplat_api/auth/cookies.py` | new | set/clear cookies（httponly + secure + samesite=lax） | T-9 |
| `apps/api/dataplat_api/auth/local_provider.py` | new | LocalAuthProvider 实现 AuthProvider；查 users 表 + verify_password + 检查 password_hash NULL & is_active | T-10 |
| `apps/api/dataplat_api/auth/deps.py` | new + **mod (stage 4)** | get_current_user + require_admin；**stage 4 加 typ=='access' 校验（MUST FIX #1）** | T-11 |
| `apps/api/dataplat_api/auth/__init__.py` | new | 暴露 auth 模块 | T-12 |
| `apps/api/dataplat_api/routers/auth.py` | new + **mod (stage 4)** | 4 路由（prefix='/auth'）；**stage 4 refresh 改为 DB 查实时 role + is_active（MUST FIX #2）** | T-13 |
| `apps/api/dataplat_api/routers/__init__.py` | new | 包占位 | T-14 |
| `apps/api/dataplat_api/routers/admin.py` | new | /admin/users POST/PATCH + require_admin 守卫 | T-14 |
| `apps/api/dataplat_api/main.py` | mod | include 2 router（不再传 prefix——prefix 在 router 自带）| T-15 |
| `apps/api/dataplat_api/db.py` | mod | NullPool 测试支持（避免 asyncpg 跨 event-loop stale connection）| T-11 副产物 |
| `apps/api/tests/conftest.py` | mod | conftest 顶层 setdefault JWT_SECRET + USE_NULL_POOL 早于 import | T-17 |
| `packages/core/tests/test_auth_protocol.py` | new | 4 Protocol/Pydantic 单测 | T-16 |
| `apps/api/tests/test_auth.py` | new + **mod (stage 4)** | 8 集成测试（含 (h) user→admin 路由 403）；base_url https://test 让 secure cookies 携带；fixture 不 dispose engine | T-17 |
| `scripts/_self_check.sh` | mod | 追加 auth-scaffold 17 AC block；core-domain-model AC-13 从 alembic current 改为 alembic history（兼容后续 migration）| T-18 |
| `packages/api-types/openapi.json` | mod (生成) | **stage 4 后 make codegen 更新**，含 /auth/login, /auth/me, /admin/users（MUST FIX #3）| 副产物 |
| 顶层 `pyproject.toml` | mod | ruff B008 例外清单加 FastAPI Depends/Query/Path/Body/Header | 副产物 |

**总计 15 new + 8 mod = 23 项改动**。

## Stage 4 reviewer 抓到的 3 个 MUST FIX（全闭环 + PoC 实证）

1. **MUST FIX #1 安全降级**：`get_current_user` 没校验 `typ == 'access'`，refresh token 复制到 access cookie 可被认证。**修**：deps.py 加 `if payload.get("typ") != "access": raise _UNAUTHORIZED`。reviewer PoC：`refresh rejected → 401 ✓`。
2. **MUST FIX #2 admin 静默降权**：refresh 取 `payload.get("role", "user")` 但 refresh token 不带 role。**修**：refresh 路径查实时 DB role + is_active（副效益：停用用户的 refresh 窗口一并闭环）。
3. **MUST FIX #3 openapi.json 未更新**：AC-12 没真闭环。**修**：跑 `make codegen`，openapi.json 现含 `/auth/login`, `/auth/me`, `/admin/users`。

## 偏离 spec / trade-off

1. **测试 fixture 不显式 `engine.dispose()`**：asyncpg + pytest-asyncio 跨用例 event-loop 关闭后 cancel pending 会 raise。Generator 选择"测试结束进程退出 GC 兜底"——production 不受影响。Stage 4 reviewer 标 SHOULD FIX，已记入 §Deferred。
2. **db.py 启用 NullPool**：通过 `PYTEST_CURRENT_TEST` 或 `DATAPLAT_USE_NULL_POOL=1` 触发。conftest 早设环境变量。生产用默认 pool（性能高），测试隔离用 NullPool（避免 stale connection）。
3. **base_url https://test**：cookies secure 标志要求 https；测试用 https://test (httpx ASGITransport 不真起 TLS) 让 secure cookies 在跨请求间携带。
4. **core-domain-model AC-13 改 grep alembic history 而非 current**：原命令 grep "0001" 在 0002 引入后失败。改为查 alembic history 含 0001——这是跨 change 累积自检脚本的合理修订。
5. **routers/auth.py refresh 不再走 spec v1 注释的 "MVP 简化保留旧 role"**：stage 4 reviewer 指出会导致 admin 静默降权，重写为查 DB。

## 本地校验结果

```text
=== ruff ===           All checks passed!
=== mypy ===           Success: no issues found in 38 source files
=== packages/core ===  29 + 4 = 33 passed
=== apps/api ===       11 passed (含 8 auth 集成) + 5 skipped (MinIO)
=== make codegen ===   openapi.json 已含 /auth/login + /auth/me + /admin/users
=== alembic ===        0001 → 0002 (head)，6+1=7 张表
=== self_check 全仓 === PASS: 69 / FAIL: 0 / SKIP: 0
```

## 已知未解决问题（Deferred）

| 问题 | 处理 |
|---|---|
| Stage 4 SHOULD FIX：fixture 不 dispose connection leak 风险 | follow-up：dependency override + 共享 engine fixture |
| Stage 4 SHOULD FIX：base_url https://test 与 production cookie secure flag 一致性 | follow-up：在 cookies.py 加 env-var 控制 secure，dev/test 可关 |
| Stage 4 SHOULD FIX：refresh 每次查 DB——性能开销 vs 安全 | 接受；MVP 流量 < 100 QPS 可承受；高 QPS 时加 cache |
| Stage 4 NICE：JWT secret 弱密钥长度（< 32 字节）未校验 | follow-up：tokens.py `_get_secret()` 加 `len(secret) >= 32` 断言 |
| Stage 4 NICE：CreateUserRequest 不校验 password 强度 | follow-up：admin 创建账号时由 admin 自检；MVP 可接受 |
| self_check SKIP 通道仅探端口未探凭证 | follow-up `harness-tighten-skip-channel-credentials-*`（reviewer 标的） |

## 下一步

Stage 5（test_report 归档）+ Stage 6（独立 reviewer）+ Stage 7（commit）+ Stage 10（closure）。
