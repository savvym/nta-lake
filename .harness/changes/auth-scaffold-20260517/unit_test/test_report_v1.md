---
change_id: auth-scaffold-20260517
version: 1
authored_at: 2026-05-17T06:10:00Z
status: waiting_review
---

# Test Report v1

## 验收项 ↔ 测试映射

| AC | 测试 | 文件 |
|---|---|---|
| AC-1 | self_check AC-1 + UserORM 加载（test_auth fixture 用） | scripts/_self_check.sh + apps/api/tests/test_auth.py |
| AC-2 | self_check AC-2（alembic upgrade head 0002） | shell |
| AC-3 | `test_auth_provider_is_runtime_checkable_protocol` | packages/core/tests/test_auth_protocol.py |
| AC-4 | self_check AC-4（from dataplat_core.protocols import ...） | shell |
| AC-5 | `test_a_password_hash_verify_roundtrip` | apps/api/tests/test_auth.py |
| AC-6 | `test_b_jwt_encode_decode_roundtrip` | apps/api/tests/test_auth.py |
| AC-7 | self_check AC-7（cookies httponly+secure+samesite=lax）+ `test_c_login_sets_cookies_with_security_flags` | shell + test |
| AC-8 | self_check AC-8（isinstance(LocalAuthProvider, AuthProvider)） | shell |
| AC-9 | self_check AC-9（iscoroutinefunction(get_current_user)） + `test_e_me_passes` / `test_f_me_without_cookies_401` | shell + test |
| AC-10 | self_check AC-10（4 路由 path 集合 + prefix='/auth' 钉死） | shell |
| AC-11 | self_check AC-11（admin router 含 /admin/users） + `test_h_user_role_cannot_access_admin_users` | shell + test |
| AC-12 | self_check AC-12（OpenAPI 含 /auth/login + /auth/me；make codegen 后 openapi.json 同步） | shell |
| AC-13 | self_check AC-13（pyproject 依赖） | shell |
| AC-14 | `test_authenticated_user_roundtrip` / `test_authenticated_user_allows_null_email` / `test_authenticated_user_rejects_extra_field` | packages/core/tests/test_auth_protocol.py |
| AC-15 (a)~(h) | `test_a` ~ `test_h_user_role_cannot_access_admin_users` | apps/api/tests/test_auth.py |
| AC-16 | self_check AC-16（ruff + mypy） | shell |
| AC-17 | self_check 自递归 | shell |

每条 AC 至少一个具体断言；spec 17 AC 无孤立项。

## 测试文件清单

| 文件 | 类型 | 用例数 |
|---|---|---|
| `packages/core/tests/test_auth_protocol.py` | 单元（Protocol + Pydantic 校验） | 4 |
| `apps/api/tests/test_auth.py` | 集成（依赖 Postgres） | 8 |
| `apps/api/tests/conftest.py` | 配置（JWT secret + NullPool 早于 import） | n/a |
| `scripts/_self_check.sh` auth-scaffold block | shell | 17 |

**总有效断言：4 + 8 + 17 = 29 条**（含 stage 4 reviewer PoC 独立复跑确认的 typ 校验 / role 实时查 / openapi 更新 3 项）。

## Mock 范围声明

- packages/core：**无 mock**（Pydantic + Protocol 形态校验）
- apps/api：**无 mock**——直连 docker-compose Postgres + 真实 argon2 hash + 真实 JWT encode/decode。与 unit-test-write SKILL §1.7 一致。
- shell self_check：直跑真实模块 + 真实 pytest。

## 本地运行结果

```text
=== packages/core ===
33 passed in 0.5s （含 4 个 auth_protocol 单测）

=== apps/api 测试 ===
11 passed, 5 skipped in 2.14s （含 8 auth 集成；MinIO 5 个 skipped）

=== ruff + mypy ===
All checks passed!
Success: no issues found in 38 source files

=== alembic ===
0001 → 0002 (head)

=== self_check 全仓 ===
PASS: 69 / FAIL: 0 / SKIP: 0
```

## 已知 flaky / 跳过

- 无 flaky
- MinIO 集成在 `DATAPLAT_MINIO_ENDPOINT` 未设时 skip（探针前置）
- self_check AC-2 / AC-15 在 PG 不可达时 SKIP（探针前置）；当前 docker-compose 起 `dataplat-pg-test` 在 5433 时全 PASS

## 偏离 SKILL 标准

| 偏离 | 说明 |
|---|---|
| fixture 不 dispose engine | asyncpg 跨 event-loop 关闭后 cancel pending raise；测试结束 GC 兜底；review 已标 SHOULD FIX → follow-up |
| db.py 用 PYTEST_CURRENT_TEST 触发 NullPool | 测试隔离 vs 生产性能权衡；生产 default pool；测试 NullPool |
| test_auth.py 用 https://test 让 secure cookies 携带 | httpx ASGITransport 不真起 TLS；只是协议字符串匹配 cookie secure 标志 |

## 下一步

进入 Stage 6：独立 reviewer 子会话评审 test_report + 8 集成测试 + 4 单测的真实质量（恢复完整 Generator/Reviewer 分离）。
