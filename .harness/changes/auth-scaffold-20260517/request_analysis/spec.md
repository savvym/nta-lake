---
change_id: auth-scaffold-20260517
version: 1
authored_at: 2026-05-17T05:10:00Z
status: draft
---

# Spec：users 表 + argon2 + JWT 双 token + AuthProvider Protocol

## 背景

dataplat 是内部工具，需要从 day 1 起就有可工作的认证。design.md §11.6 已明确 MVP 选型：
- argon2-cffi 密码哈希
- JWT 双 token（access 15min + refresh 7d）放 httpOnly cookie
- AuthProvider 接口预留 SSO

前 4 个变更已落 monorepo 骨架 + 领域模型 + ORM + CAS storage，但**还没有任何用户表 / 路由 / 权限**——后续 `repo-api-mvp` 的 CRUD 路由要做权限控制必须先有 auth 基础设施。

## 问题陈述

当前缺：
1. 没有 `users` 表 / `UserORM` / 0002 migration
2. 没有 argon2 密码哈希工具
3. 没有 JWT encode/decode 工具
4. 没有 `AuthProvider` Protocol（LocalAuthProvider / 未来 OIDCAuthProvider 共用接口）
5. 没有 `/auth/login` / `/auth/logout` / `/auth/refresh` / `/auth/me` 路由
6. 没有 `get_current_user` FastAPI 依赖
7. 没有 admin 路由创建用户（spec §non-范围明示不做注册流程，admin 后台建账号）

## 范围

In scope（每条对应可机械化验证）：

- **AC-1**：`apps/api/dataplat_api/models/user.py` 存在；`UserORM` 表 SQLAlchemy 2.0 Mapped[] 风格；字段：`id (UUID PK)` / `username (str, unique, NOT NULL)` / `email (str, unique, nullable)` / `password_hash (str, nullable)` / `role (str NOT NULL, default 'user')` / `is_active (bool NOT NULL default true)` / `external_id (str, unique, nullable)` / `created_at` / `updated_at`。
- **AC-2**：`apps/api/alembic/versions/0002_*.py` 存在；`alembic upgrade head` 在已运行 0001 的库上能成功添加 `users` 表（含 unique index username + email + external_id）。
- **AC-3**：`packages/core/src/dataplat_core/protocols/auth.py` 存在；`AuthProvider` Protocol（async）含方法 `async def authenticate(self, username: str, password: str) -> AuthenticatedUser | None`；`AuthenticatedUser` Pydantic BaseModel 含 `user_id: str` / `username: str` / `email: str | None` / `role: str` / `is_active: bool`。`@runtime_checkable` + `_is_runtime_protocol == True`。
- **AC-4**：`packages/core/src/dataplat_core/protocols/__init__.py` 暴露 `AuthProvider` + `AuthenticatedUser`。
- **AC-5**：`apps/api/dataplat_api/auth/password.py` 存在，导出 `hash_password(plain: str) -> str` + `verify_password(plain: str, hashed: str) -> bool`；用 argon2-cffi `PasswordHasher`；同 plain 输入产生不同 hash（含 salt）；verify 跨 hash 一致。
- **AC-6**：`apps/api/dataplat_api/auth/tokens.py` 存在，导出 `encode_access_token(user_id, role) -> str` / `encode_refresh_token(user_id) -> str` / `decode_token(token) -> dict` / `TokenError` 异常；access TTL 15min，refresh TTL 7d；HS256 算法。**Secret 读取明确**：`encode_*` / `decode_*` 函数体内**每次**调用 `os.environ.get("DATAPLAT_JWT_SECRET")` 读取，**不得 cache 在模块级常量**（避免 conftest `monkeypatch.setenv` 失效）；若读到 None / 空串 raise `TokenError`（不在 import time）。
- **AC-7**：`apps/api/dataplat_api/auth/cookies.py` 存在，导出 `set_auth_cookies(response, access, refresh)` / `clear_auth_cookies(response)`；cookies 必有 `httponly=True` + `secure=True` + `samesite='lax'`；max_age 对应 token TTL。
- **AC-8**：`apps/api/dataplat_api/auth/local_provider.py` 存在；`LocalAuthProvider(session_factory)` 构造；实现 `AuthProvider` Protocol（`isinstance(p, AuthProvider)` PASS）；`authenticate("admin", "wrong")` 返 None；`authenticate("admin", correct_password)` 返 AuthenticatedUser；非活跃用户（is_active=False）返 None。
- **AC-9**：`apps/api/dataplat_api/auth/deps.py` 存在，导出 `get_current_user` async generator/coroutine 依赖；从 request cookies 读 access token → decode → 查 users 表 → 返回 AuthenticatedUser；token 缺失 / 非法 / 过期 → raise HTTPException 401。
- **AC-10**：`apps/api/dataplat_api/routers/auth.py` 含 4 路由：`POST /auth/login`（接受 username/password JSON → 校验 → set cookies → 返回 AuthenticatedUser）/ `POST /auth/logout`（clear cookies → 204）/ `POST /auth/refresh`（从 refresh cookie → 解码 → 重发 access → set 新 access cookie）/ `GET /auth/me`（用 `Depends(get_current_user)`）。**Prefix 钉死**：必须用 `router = APIRouter(prefix="/auth")` + main 用 `app.include_router(router)` **不再传 prefix**——这是让 AC-10 `router.routes` 与 AC-12 `app.openapi()['paths']` 同时含 `/auth/login` 的唯一组合。
- **AC-11**：`apps/api/dataplat_api/routers/admin.py` 含 `POST /admin/users`（仅 admin 角色，创建用户）+ `PATCH /admin/users/{id}`（admin 改 role / 重置密码 / 停用）。普通用户访问返 403。
- **AC-12**：`apps/api/dataplat_api/main.py` include 新 router；`/auth/login` 与 `/auth/me` 在 OpenAPI schema 中出现（make codegen 后 openapi.json 含这两个 path）。
- **AC-13**：`apps/api/pyproject.toml` 新增 `argon2-cffi>=23.1` + `PyJWT>=2.8`；`uv sync` 后 `import argon2` + `import jwt` 成功。
- **AC-14**：`packages/core/tests/test_auth_protocol.py` 含 ≥ 3 单测：(a) `AuthProvider` `_is_runtime_protocol == True`；(b) `AuthenticatedUser` round-trip；(c) `AuthenticatedUser` 校验非法字段。
- **AC-15**：`apps/api/tests/test_auth.py` 含 ≥ 10 集成测试（依赖 Postgres，用 0001 + 0002 schema）：(a) hash/verify password round-trip；(b) JWT encode/decode round-trip；(c) `/auth/login` 成功后 cookies 设置（httponly + secure + samesite=lax）；(d) `/auth/login` 错密码返 401；(e) `/auth/me` 用 cookies 通过；(f) `/auth/me` 缺 cookies 返 401；(g) `/auth/refresh` 从 refresh cookie 重发 access；**(h) 普通 user 角色访问 `POST /admin/users` 返 403**（spec MUST FIX-3 + tasks MUST 3 同步）。
- **AC-16**：`uv run ruff check apps/api packages/core` + `uv run mypy apps/api/dataplat_api packages/core/src` 全 PASS。
- **AC-17**：`scripts/_self_check.sh auth-scaffold` 17/17 PASS（含 Postgres SKIP 通道）。

## 非范围

- 不实现注册路由 / 邮件验证 / 密码重置邮件
- 不实现 MFA / OAuth / 社交登录
- 不实现 OIDC / SAML AuthProvider 实现（接口预留）
- 不实现 Repository 级 ACL（Phase 2）
- 不实现 rate limit / brute-force 防护（follow-up）

## 验收标准

| ID | 描述 | 验证方式 | 期望 |
|---|---|---|---|
| AC-1 | UserORM 模块 | `test -f apps/api/dataplat_api/models/user.py && grep -q "class UserORM" apps/api/dataplat_api/models/user.py` | exit 0 |
| AC-2 | 0002 migration | `ls apps/api/alembic/versions/0002_*.py >/dev/null && (export DATAPLAT_DATABASE_URL=postgresql+asyncpg://dataplat:dataplat@localhost:${DATAPLAT_PG_PORT:-5432}/dataplat && cd apps/api && uv run alembic upgrade head && uv run alembic current 2>&1 \| grep -q "0002")` | exit 0（pg 探针失败 → SKIP）|
| AC-3 | AuthProvider Protocol + AuthenticatedUser | `cd packages/core && uv run python -c "from typing import Protocol; from pydantic import BaseModel; from dataplat_core.protocols.auth import AuthProvider, AuthenticatedUser; assert issubclass(AuthProvider, Protocol); assert getattr(AuthProvider, '_is_runtime_protocol', False) is True; assert issubclass(AuthenticatedUser, BaseModel)"` | exit 0 |
| AC-4 | protocols __init__ 暴露 | `cd packages/core && uv run python -c "from dataplat_core.protocols import AuthProvider, AuthenticatedUser"` | exit 0 |
| AC-5 | password hash/verify round-trip + 随机 salt | `cd apps/api && uv run python -c "from dataplat_api.auth.password import hash_password, verify_password; h1=hash_password('x'); h2=hash_password('x'); assert h1!=h2; assert verify_password('x',h1) and verify_password('x',h2) and not verify_password('y',h1)"` | exit 0 |
| AC-6 | JWT encode/decode | `cd apps/api && DATAPLAT_JWT_SECRET=test-secret-32-bytes-long-xxxxx uv run python -c "from dataplat_api.auth.tokens import encode_access_token, decode_token; t=encode_access_token('u1','user'); d=decode_token(t); assert d['sub']=='u1' and d['role']=='user'"` | exit 0 |
| AC-7 | cookies httponly + secure + samesite | `cd apps/api && uv run python -c "from fastapi import Response; from dataplat_api.auth.cookies import set_auth_cookies; r=Response(); set_auth_cookies(r,'a','b'); c=[c for c in r.raw_headers if b'set-cookie' in c[0].lower()]; raw=b'\\n'.join(c[1] for c in c).lower(); assert b'httponly' in raw and b'secure' in raw and b'samesite=lax' in raw"` | exit 0 |
| AC-8 | LocalAuthProvider isinstance | `cd apps/api && uv run python -c "from dataplat_api.auth.local_provider import LocalAuthProvider; from dataplat_core.protocols.auth import AuthProvider; p=LocalAuthProvider.__new__(LocalAuthProvider); assert isinstance(p, AuthProvider)"` | exit 0 |
| AC-9 | get_current_user 存在 | `cd apps/api && uv run python -c "from dataplat_api.auth.deps import get_current_user; import inspect; assert inspect.iscoroutinefunction(get_current_user)"` | exit 0 |
| AC-10 | auth router 含 4 路由 | `cd apps/api && uv run python -c "from dataplat_api.routers.auth import router; paths={r.path for r in router.routes}; assert {'/auth/login','/auth/logout','/auth/refresh','/auth/me'} <= paths"` | exit 0 |
| AC-11 | admin router 含 2 路由 | `cd apps/api && uv run python -c "from dataplat_api.routers.admin import router; paths={r.path for r in router.routes}; assert any('/admin/users' in p for p in paths)"` | exit 0 |
| AC-12 | main 集成 + OpenAPI 含 /auth/* | `cd apps/api && uv run python -c "from dataplat_api.main import app; spec=app.openapi(); assert '/auth/login' in spec['paths'] and '/auth/me' in spec['paths']"` | exit 0 |
| AC-13 | argon2 + PyJWT 依赖 | `python3 -c "import tomllib; d=tomllib.load(open('apps/api/pyproject.toml','rb')); deps=d['project']['dependencies']; assert any('argon2-cffi' in x for x in deps) and any('PyJWT' in x or 'pyjwt' in x.lower() for x in deps)"` | exit 0 |
| AC-14 | packages/core auth 单测 ≥ 3 + 全 PASS | `(cd packages/core && uv run pytest -q --tb=no tests/test_auth_protocol.py) && [ "$(cd packages/core && uv run pytest --collect-only -q tests/test_auth_protocol.py 2>&1 \| grep -cE "::")" -ge 3 ]` | exit 0 |
| AC-15 | apps/api auth 集成 ≥ 10 + 全 PASS（含普通用户访问 /admin/users 返 403）| `python3 -c "import socket; s=socket.socket(); s.settimeout(1); s.connect(('localhost', int('${DATAPLAT_PG_PORT:-5432}'))); s.close()" 2>/dev/null && (export DATAPLAT_DATABASE_URL=postgresql+asyncpg://dataplat:dataplat@localhost:${DATAPLAT_PG_PORT:-5432}/dataplat && export DATAPLAT_JWT_SECRET=test-secret-not-prod-x32-bytes-xxxxx && cd apps/api && uv run pytest -q --tb=no tests/test_auth.py) && [ "$(cd apps/api && uv run pytest --collect-only -q tests/test_auth.py 2>&1 \| grep -cE "::")" -ge 10 ]` | **PG up → exit 0；PG down → 本命令 exit 1，AC-17 内由 `_self_check.sh` SKIP 通道转 exit 0**（spec MUST FIX-3 澄清）|
| AC-16 | ruff + mypy | `uv run ruff check apps/api packages/core && uv run mypy apps/api/dataplat_api packages/core/src` | exit 0 |
| AC-17 | self_check auth-scaffold block | `bash scripts/_self_check.sh auth-scaffold` 退出 0（含 SKIP 通道）| exit 0 |

## 风险

| 风险 | 概率 | 影响 | 缓解 |
|---|---|---|---|
| `DATAPLAT_JWT_SECRET` 未设置时模块 import 失败 | 中 | 测试启动崩 | tokens.py 用 lazy check：encode 时才 raise（不在 import time）；测试 conftest 显式 set env |
| argon2-cffi 在 alpine / musl 环境编译失败 | 低 | CI 阻塞 | 用 wheels；本变更不切 alpine 镜像 |
| Cookie SameSite=Lax 在跨域 POST 失败 | 中 | 前端登录失败 | dev/test 同域代理；prod 同域部署 |
| JWT secret 在测试用弱密钥 | 低 | 测试无影响 | 测试 secret 显式 prefix `test-secret-...`，与生产用 secrets manager 区分 |
| Cookie max_age 与 JWT exp 不一致 | 中 | 用户体验断点 | tokens.py 与 cookies.py 共享常量 `ACCESS_TTL_SECONDS` / `REFRESH_TTL_SECONDS` |
| password_hash NULL 列允许 SSO 用户无密码 | 低 | LocalAuthProvider 必查 password_hash IS NOT NULL | 实现里显式判 |
| 0002 migration 与 0001 类型冲突（外键 / 重复 column）| 低 | upgrade 失败 | users 表与 0001 表无外键关系；本变更后续 follow-up 才引入 repos.author_id → users.id |

## 受影响模块

- `apps/api/dataplat_api/models/{__init__,user}.py`（新 + 修）
- `apps/api/dataplat_api/auth/`（全新目录）
- `apps/api/dataplat_api/routers/{auth,admin}.py`（新；首次有 routers 子目录文件）
- `apps/api/dataplat_api/main.py`（修改：include router）
- `apps/api/alembic/versions/0002_*.py`（新）
- `apps/api/pyproject.toml`（+2 依赖）
- `packages/core/src/dataplat_core/protocols/{auth.py,__init__.py}`（新 + 修）
- `packages/core/tests/test_auth_protocol.py`（新）
- `apps/api/tests/test_auth.py`（新）
- `scripts/_self_check.sh`（追加 block）

## 不受影响

- `.harness/`、`wiki/`、`apps/web/`、`packages/core/src/dataplat_core/domain/`、CAS storage 全部不动

## 待澄清问题

- [x] `users.role` 用 enum 还是 str？答：MVP 用 str（'admin' / 'user'），后续可换 enum table
- [x] external_id 是 unique 还是非 unique？答：unique（同 SSO 用户唯一）；NULL 允许多
- [x] JWT secret 缺失行为：lazy at first encode（不 import-time crash）
- [x] Cookie 域 / path：默认 `path=/`，无 domain（同域）

## 引用

- `.harness/design.md` §11.6 + §11.7 #1（async session）
- `.harness/changes/core-domain-model-20260516/`：Base + TimestampMixin + db.py 已落
