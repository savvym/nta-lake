---
change_id: auth-scaffold-20260517
version: 1
authored_at: 2026-05-17T05:20:00Z
---

# Tasks

## 任务清单

```yaml
tasks:
  - id: T-1
    title: apps/api/pyproject.toml +argon2-cffi +PyJWT
    depends_on: []
    covers_ac: [AC-13]
    status: pending

  - id: T-2
    title: apps/api/dataplat_api/models/user.py - UserORM 表
    description: |
      Mapped[uuid.UUID] id PK / Mapped[str] username unique NOT NULL /
      Mapped[str|None] email unique / password_hash str|None /
      role str default 'user' / is_active bool default True / external_id str|None unique
      TimestampMixin 复用
    depends_on: [T-1]
    covers_ac: [AC-1]
    status: pending

  - id: T-3
    title: apps/api/dataplat_api/models/__init__.py 暴露 UserORM
    depends_on: [T-2]
    covers_ac: [AC-1]
    status: pending

  - id: T-4
    title: apps/api/alembic/versions/0002_users.py
    description: |
      手写 migration：create_table users + 3 unique index（username/email/external_id）+ 外键无
      down() drop_table
    depends_on: [T-2]
    covers_ac: [AC-2]
    status: pending

  - id: T-5
    title: packages/core protocols/auth.py - AuthProvider + AuthenticatedUser
    description: |
      AuthenticatedUser BaseModel(user_id, username, email|None, role, is_active)
      @runtime_checkable AuthProvider Protocol：async def authenticate(username, password) -> AuthenticatedUser | None
    depends_on: []
    covers_ac: [AC-3]
    status: pending

  - id: T-6
    title: packages/core protocols/__init__.py 暴露 AuthProvider / AuthenticatedUser
    depends_on: [T-5]
    covers_ac: [AC-4]
    status: pending

  - id: T-7
    title: apps/api/dataplat_api/auth/password.py
    description: |
      hash_password / verify_password 用 argon2_cffi.PasswordHasher 单例（线程安全）
      verify_password 捕 VerifyMismatchError -> False；其他异常 bubble up
    depends_on: [T-1]
    covers_ac: [AC-5]
    status: pending

  - id: T-8
    title: apps/api/dataplat_api/auth/tokens.py
    description: |
      ACCESS_TTL_SECONDS=900 / REFRESH_TTL_SECONDS=604800 常量
      encode_access_token(user_id, role) -> JWT HS256，payload 含 sub / role / exp / typ='access'
      encode_refresh_token(user_id) -> JWT HS256，payload 含 sub / exp / typ='refresh'
      decode_token(token) -> dict（jwt.decode + verify_exp）；TokenError 包 PyJWTError
      JWT secret 从 DATAPLAT_JWT_SECRET 读；lazy（第一次 encode 时 raise if missing），不 import-time
    depends_on: [T-1]
    covers_ac: [AC-6]
    status: pending

  - id: T-9
    title: apps/api/dataplat_api/auth/cookies.py
    description: |
      set_auth_cookies(response, access, refresh)：set_cookie name=access_token/refresh_token,
      httponly=True, secure=True, samesite='lax', max_age=ACCESS_TTL/REFRESH_TTL, path='/'
      clear_auth_cookies(response)：delete_cookie 两个
    depends_on: [T-8]
    covers_ac: [AC-7]
    status: pending

  - id: T-10
    title: apps/api/dataplat_api/auth/local_provider.py - LocalAuthProvider
    description: |
      构造 (async_sessionmaker)；async authenticate(username, password)：
        - select user where username = ? and is_active = True
        - 若 password_hash IS NULL → 返回 None（SSO 用户无密码）
        - verify_password(password, user.password_hash) → 通过则返 AuthenticatedUser(...)
        - 不通过返 None
      使 isinstance(instance, AuthProvider) 检测通过（@runtime_checkable Protocol）
    depends_on: [T-2, T-5, T-7]
    covers_ac: [AC-8]
    status: pending

  - id: T-11
    title: apps/api/dataplat_api/auth/deps.py - get_current_user
    description: |
      async def get_current_user(request: Request, session: AsyncSession = Depends(get_session))
        -> AuthenticatedUser
      从 request.cookies['access_token'] 读 token
        - 缺 → 401
        - decode TokenError → 401
        - 查 users 表（UserORM） → 不在 / 非活跃 → 401
        - 返 AuthenticatedUser
    depends_on: [T-2, T-5, T-8]      # tasks MUST FIX-1：显式补 T-2（UserORM）+ T-5（AuthenticatedUser）
    covers_ac: [AC-9]
    status: pending

  - id: T-12
    title: apps/api/dataplat_api/auth/__init__.py 暴露
    depends_on: [T-7, T-8, T-9, T-10, T-11]
    covers_ac: [AC-9]
    status: pending

  - id: T-13
    title: apps/api/dataplat_api/routers/auth.py - 4 路由
    description: |
      POST /auth/login: 接受 LoginRequest BaseModel(username, password) → LocalAuthProvider →
        set_auth_cookies → 200 AuthenticatedUser
      POST /auth/logout: clear_auth_cookies → 204
      POST /auth/refresh: 从 cookies['refresh_token'] decode_token → 重发 access_token (set cookie)
      GET /auth/me: Depends(get_current_user) → return AuthenticatedUser
    depends_on: [T-9, T-10, T-11]
    covers_ac: [AC-10, AC-12]
    status: pending

  - id: T-14
    title: apps/api/dataplat_api/routers/__init__.py 占位 + admin.py
    description: |
      __init__.py 空
      admin.py: APIRouter(prefix='/admin')，POST /admin/users + PATCH /admin/users/{id}
      **CreateUserRequest** Pydantic BaseModel 字段（tasks MUST FIX-3）：
        - username: str
        - password: str | None（None 表示 SSO 用户，password_hash 存 NULL）
        - email: str | None
        - role: Literal['admin','user']（默认 'user'）
        - external_id: str | None
      POST 写 password 则 hash 后存 password_hash
      **UpdateUserRequest** 字段：role / new_password / is_active 全部 Optional
      用 Depends(get_current_user) 然后断言 current_user.role == 'admin' 否则 raise HTTPException(403)
    depends_on: [T-11]
    covers_ac: [AC-11, AC-15]      # AC-15 (h) 普通用户 403 由本任务的 admin 路由 + T-17 测试覆盖
    status: pending

  - id: T-15
    title: apps/api/dataplat_api/main.py 集成 router
    description: |
      app.include_router(auth_router) + app.include_router(admin_router)
      验证 OpenAPI schema 包含 /auth/login + /auth/me
    depends_on: [T-13, T-14]
    covers_ac: [AC-12]
    status: pending

  - id: T-16
    title: packages/core/tests/test_auth_protocol.py（≥ 3）
    description: test_auth_provider_runtime_checkable / test_authenticated_user_roundtrip / test_authenticated_user_rejects_invalid
    depends_on: [T-5]
    covers_ac: [AC-14]
    status: pending

  - id: T-17
    title: apps/api/tests/test_auth.py（≥ 7 集成）
    description: |
      hash/verify round-trip / JWT encode-decode / login 成功 cookies（httponly+secure+lax）/
      login 错密码 401 / /auth/me 通过 / /auth/me 缺 cookies 401 / /auth/refresh 重发 access /
      **普通 user 角色访问 POST /admin/users 返 403**（tasks MUST FIX-3 + spec AC-15 (h)）
      Fixture scope（tasks MUST FIX-2）：
        - `@pytest.fixture(scope='session')` 跑 `alembic upgrade head` **一次**（避免 6-12s 反复）
        - 测试用户记录用 `@pytest.fixture(scope='function')` + teardown delete row（不 drop table）
      JWT secret：conftest.py 顶层 `os.environ.setdefault('DATAPLAT_JWT_SECRET', 'test-secret-not-prod-x32-bytes-xxxxx')`
        在任何 dataplat_api 模块 import 之前，保证 lazy os.getenv 在测试期间一致
    depends_on: [T-13, T-14]
    covers_ac: [AC-15]
    status: pending

  - id: T-18
    title: scripts/_self_check.sh 追加 auth-scaffold block
    description: 17 AC self-check；Postgres 探针前置；AC-2/AC-15 SKIP 通道
    depends_on: [T-16, T-17]
    covers_ac: [AC-17]
    status: pending
```

## 阶段任务

```yaml
process_tasks:
  - id: P-spec-review
    estimated_stage: request_analysis_review
    status: pending
  - id: P-code-review
    estimated_stage: coding_review
    status: pending
  - id: P-test-review
    estimated_stage: unit_test_review
    status: pending
  - id: P-push
    estimated_stage: push
    status: pending
  - id: P-ci
    estimated_stage: ci_result
    status: pending
    reason: 本地等价 self_check.sh + ruff + mypy + pytest
  - id: P-deploy
    estimated_stage: deployment
    status: skipped
  - id: P-user-confirm
    estimated_stage: user_confirmation
    status: pending
```

## DAG 健全性

T-2/T-7/T-8 → T-1（依赖装好）；T-3/T-4 → T-2；T-6 → T-5；T-9 → T-8；T-10 → T-2/T-5/T-7；T-11 → T-8；T-12 → T-7..T-11；T-13 → T-9/T-10/T-11；T-14 → T-11；T-15 → T-13/T-14；T-16 → T-5；T-17 → T-13/T-14；T-18 → T-16/T-17。无循环。

## 验收覆盖矩阵

| AC | 关联 |
|---|---|
| AC-1 | T-2, T-3 |
| AC-2 | T-4 |
| AC-3 | T-5 |
| AC-4 | T-6 |
| AC-5 | T-7 |
| AC-6 | T-8 |
| AC-7 | T-9 |
| AC-8 | T-10 |
| AC-9 | T-11, T-12 |
| AC-10 | T-13 |
| AC-11 | T-14 |
| AC-12 | T-13, T-15 |
| AC-13 | T-1 |
| AC-14 | T-16 |
| AC-15 | T-17 |
| AC-16 | 全部 |
| AC-17 | T-18 |
