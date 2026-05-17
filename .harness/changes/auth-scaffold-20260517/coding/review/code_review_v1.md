---
change_id: auth-scaffold-20260517
target: coding/main (working tree, pre-commit)
target_head: untracked working tree（Generator 尚未写 coding_report；本评审走"先评审后归档"路径）
review_version: 1
reviewer: claude-agent:auth-scaffold-stage4-reviewer
reviewed_at: 2026-05-17T07:00:00Z
verdict: REVISION REQUIRED
---

# Code Review v1

## 范围与作者声明对照

- `git status -s` 与 `find apps/api/dataplat_api/auth -type f` 落地文件：
  - 新增：`models/user.py`、`alembic/versions/0002_users.py`、`auth/{__init__,password,tokens,cookies,local_provider,deps}.py`、`routers/{__init__,auth,admin}.py`、`tests/test_auth.py`、`packages/core/src/dataplat_core/protocols/auth.py`、`packages/core/tests/test_auth_protocol.py`。
  - 修改：`apps/api/dataplat_api/{db.py,main.py,models/__init__.py,pyproject.toml,tests/conftest.py}`、`packages/core/src/dataplat_core/protocols/__init__.py`、`scripts/_self_check.sh`、`pyproject.toml`、`uv.lock`。
- 与 spec §受影响模块 / §非范围比对：注册路由、MFA、OIDC 实现、Repository ACL、rate limit 均未引入；范围合规。
- spec v2 4 条 MUST FIX 全部体现：(1) `APIRouter(prefix="/auth")` + main `include_router` 不传 prefix（routers/auth.py L29，main.py L31）；(2) tokens.py 无 module-level secret cache，`_get_secret()` 在 encode/decode 每次调用（PoC：env 切换后旧 token 立即失效）；(3) `_self_check.sh` 用 `run_ac_skipif_no_pg` 包裹 AC-2 / AC-15；(4) AC-15 (h) `test_h_user_role_cannot_access_admin_users` 已落。

## 实证复跑

| 项 | 结果 | 备注 |
|---|---|---|
| `uv run ruff check apps/api packages/core` | All checks passed | 与 Generator 一致 |
| `uv run mypy apps/api/dataplat_api packages/core/src` | Success: 38 source files | 与 Generator 一致 |
| `cd packages/core && uv run pytest tests/test_auth_protocol.py` | 4 passed | spec AC-14 ≥ 3 PASS |
| `bash scripts/_self_check.sh auth-scaffold` | PASS 15 / FAIL 2 / SKIP 0 | AC-2 / AC-15 在本会话 FAIL（见下） |
| AC-2 / AC-15 复现 | `password authentication failed for user "dataplat"` | 本机 5432 监听非 dataplat 实例；SKIP 通道只探端口未探凭证；Generator 跑过 dataplat docker-compose 后 PASS 可信 |

纯静态 + 非 DB 部分（13/17 AC + ruff + mypy + core 单测）独立复现 PASS；DB 集成（AC-2 / AC-15）未能在本会话独立复现，按 Generator 自陈采信。

## 安全审查（最关键）

### MUST 1 — `get_current_user` 不校验 `typ == 'access'`，refresh token 可冒充 access token

`apps/api/dataplat_api/auth/deps.py` L36-50 解码 token 后只读 `sub`，未检查 `payload['typ']`。PoC：将 `encode_refresh_token(uid)` 直接放入 `request.cookies['access_token']`，`get_current_user` 返回完整 AuthenticatedUser（含 role='admin'）。修复：decode 后立即 `if payload.get("typ") != "access": raise _UNAUTHORIZED`。利用面要先攻破 httpOnly（XSS）将 refresh 拷到 access cookie，但分层防御立场下必须封堵——这是 spec §11.6 双 token 设计的基本不变量。

### MUST 2 — `/auth/refresh` 静默降权 admin → user（功能 bug，影响安全语义）

`routers/auth.py` L92 用 `payload.get("role", "user")` 重新签 access token，但 `encode_refresh_token`（tokens.py L43-51）的 payload 不含 `role`。结果：admin 用户 access 过期触发 refresh 后，新 access token 的 role='user'，直到下次完整 login。方向"降权而非提权"安全友好，但是 correctness bug、用户体验断裂、与 spec AC-10 "重发 access" 的意图不一致。修复二选一：(a) refresh token 也带 role；(b) refresh 路由查 users 表读最新 role（顺带闭环 SHOULD 1）。注释 L89-91 已承认这是 MVP 简化但实际现状是"无论谁都被降为 user"，注释与代码不一致。

### MUST 3 — `packages/api-types/openapi.json` 未更新

`grep -c "/auth/login\|/auth/me\|/admin/users" packages/api-types/openapi.json` → 0，且 `git status -s` 该文件无修改。spec AC-12 文字"make codegen 后 openapi.json 含这两个 path"未真正闭环（AC 机器验证只看 `app.openapi()` in-memory，是 spec 留缝；用户评审重点 E 已点名）。修复：跑 `make codegen` 后 `git add packages/api-types/openapi.json`。

### SHOULD 1 — `/auth/refresh` 不查 users 表，已停用账户在 access 过期前仍可获新 access

`is_active=False` 的用户在 access 未过期时 `/auth/me` 仍通过（token 未过期）；access 过期后调 refresh 仍能拿新 access（refresh 路由不查 DB）。直至 refresh 7d 过期才彻底失效。spec 风险表 #6 与 MVP trade-off 一致，但应在 spec follow-up / 注释里显式记账，并把"7d 撤销窗口"作为已知风险落库。

### SHOULD 2 — JWT secret 弱密钥生产环境无代码层防护

`_get_secret()` 只判空、未判长度。PyJWT 在密钥 < 32 字节时只 warn（PoC 已观察 `InsecureKeyLengthWarning`）。spec 风险表 #4 把这条交给运维 secrets manager，可接受；但加 8 行 `if len(secret) < 32: raise TokenError(...)` 是廉价的纵深防御。

### SHOULD 3 — `test_g_refresh_issues_new_access` 测试盲区

test_g 只断 `b"access_token=" in raw`，未解码新 access token 验证 `typ == 'access'` + `role == 已登录用户 role`。MUST 1 / MUST 2 都是该盲区漏过的；建议增加 `decode_token(new_access)["typ"] == "access"` 与 role 同步性断言。

### SHOULD 4 — admin gate 缺正向集成测试

test_h 只断负向（user → 403）。建议加 `test_admin_can_create_user` 用 `created_admin` fixture（已存在）登录 → POST /admin/users → 201 + body 验证。spec AC-11 与 AC-15 (h) 文字未要求，但生产前应有正向覆盖；fixture 都已铺好，加测试 ~15 行。

## 代码质量

- **timing attack**：argon2-cffi `PasswordHasher.verify` 内部常量时间比较；但 `LocalAuthProvider.authenticate` 在 user 不存在时立即 return None（不跑 verify），存在 user-existence timing oracle。MVP 可接受，未来可考虑 dummy verify。
- **`db.py` 双探针**：`PYTEST_CURRENT_TEST` 由 pytest 自动注入，安全；`DATAPLAT_USE_NULL_POOL=1` 若误设至生产则走 NullPool（性能差但功能正确）。NICE：docstring 加显式警告"仅测试环境"。
- **`routers/auth.py` L89-91 注释**与实际行为不一致（见 MUST 2），需同步修订。
- **`UserORM.password_hash` `String(255)`**：argon2id 默认参数下 hash 串 ~100 字节，远低于 255 OK；若未来调高 `memory_cost`/`time_cost` 风险有限。NICE：升 String(512) 或 Text 防参数升级。
- **`require_admin`** 用法正确，admin.py 两个 endpoint 都挂；无遗漏。
- **`AuthenticatedUser` `extra="forbid"`** 在 protocol 模块设置，与 deps.py / local_provider.py 显式枚举字段构造一致——OK。
- **conftest.py** `os.environ.setdefault` 在模块顶层（任何 dataplat_api 子模块 import 之前），PoC 验证 `_USE_NULL_POOL=True` 生效——OK。

## 测试质量

- 8 集成测试覆盖 AC-15 (a)~(h) 全部要求；test_h `created_user`（role='user'）先 login 拿到合法 access cookie，再访问 `POST /admin/users`，必然走到 `require_admin` 的 role check 而非 401（验证路径正确）。
- 4 单测覆盖 AC-14 (a)~(c) + 1 个 extra 字段拒绝；超 spec 最低要求。
- fixture 用 `delete row` 不 drop table、不 dispose engine——Generator 在 docstring 自陈"测试结束进程退出 GC 兜底"。短期 OK；`pytest -x --lf` 反复跑同一文件时若 connection 泄漏可能耗尽 pg 连接池。NICE：用 module-scope engine + teardown dispose 一次。

## 工程缺口

- **openapi.json 未更新**：MUST 3。
- **0002 migration**：本会话因 PG 凭证不匹配未能 `alembic upgrade` 复现；表结构（unique constraints + UUID PK + server_default）与 UserORM 一致，静态审查通过。Generator 自陈 `alembic current` 含 0002，可信。
- **依赖锁**：`apps/api/pyproject.toml` +`argon2-cffi>=23.1` +`PyJWT>=2.8` 与 spec AC-13 一致；`uv.lock` 已重生。
- **ruff B008 例外**配在顶层 `pyproject.toml`（L31-33），全仓共享；与 cas-storage MUST FIX-2 决策一致。

## 评审结论

verdict: **REVISION REQUIRED**

| 类别 | 数量 | 项 |
|---|---|---|
| MUST | 3 | (1) `get_current_user` 校验 typ；(2) `/auth/refresh` role 处理 + 注释同步；(3) openapi.json 同步入 commit |
| SHOULD | 4 | (1) refresh 撤销窗口落账；(2) JWT secret 长度防护；(3) test_g 加 typ/role 断言；(4) admin gate 正向测试 |
| NICE | 3 | (1) timing-oracle dummy verify；(2) `DATAPLAT_USE_NULL_POOL` 警告 docstring；(3) `password_hash` 列扩为 String(512)/Text |

## 复检指引

Generator 修完后，把以下证据贴进 `coding_report_v1.md`（或 v2 重生）：

1. **MUST 1 验证**：复跑 reviewer PoC（将 refresh token 放入 `access_token` cookie 调 `get_current_user`），预期 `HTTPException 401`；同时在 `test_auth.py` 加 `test_refresh_token_cannot_be_used_as_access` 断 401。
2. **MUST 2 验证**：admin login → 调 `/auth/refresh` → decode 新 access token → 断 `typ == 'access'` + `role == 'admin'`；注释 L89-91 同步修订。
3. **MUST 3 验证**：`make codegen && grep -c "/auth/login" packages/api-types/openapi.json` → ≥ 1；`git status -s packages/api-types/openapi.json` → ` M ...`，并入本变更 commit。
4. SHOULD 4 项任选 ≥ 2 项闭环；未闭环的明列 follow-up issue。
5. 复跑 `bash scripts/_self_check.sh auth-scaffold`（PG 凭证正确环境下）→ PASS 17 / FAIL 0 / SKIP 0；并复跑 `uv run ruff check apps/api packages/core && uv run mypy apps/api/dataplat_api packages/core/src` → 全 PASS。

复检通过后本评审升 v2 verdict=APPROVED；MUST 全闭、SHOULD ≥ 2 闭即可放行 Stage 5。
