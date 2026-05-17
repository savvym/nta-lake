---
change_id: repo-api-mvp-20260517
target_head: working-tree (base b64c3ec5)
review_version: 1
reviewer: claude-stage4-reviewer
reviewed_at: 2026-05-17T08:35:00Z
verdict: APPROVED
---

# Code Review v1

## 范围与作者声明对照

作者 coding_report v1 声明 9 个改动条目，实际 `git status --short` + working tree 比对：

| 路径 | coding_report 声明 | 实际 | 一致 |
|---|---|---|---|
| `apps/api/dataplat_api/schemas/__init__.py` | new | new | OK |
| `apps/api/dataplat_api/schemas/repo.py` | new | new（含 5 个 Pydantic：`RepositoryCreate/Read/ListItem/Update/ListResponse`） | OK |
| `apps/api/dataplat_api/services/__init__.py` | new | new | OK |
| `apps/api/dataplat_api/services/repo.py` | new | new | OK |
| `apps/api/dataplat_api/routers/repos.py` | new | new | OK |
| `apps/api/dataplat_api/auth/deps.py` | edit | edit（抽 `_decode_user_from_cookie` + 新增 `get_optional_user`） | OK |
| `apps/api/dataplat_api/auth/__init__.py` | edit | edit（export `get_optional_user`） | OK |
| `apps/api/dataplat_api/main.py` | edit | edit（`include_router(repos_router)`） | OK |
| `apps/api/tests/test_repos.py` | new（13 集成） | new（13 集成，a~m） | OK |
| `scripts/_self_check.sh` | edit | edit（追加 `run_repo_api_mvp` 13 AC block） | OK |
| `packages/api-types/openapi.json` | edit（codegen） | edit（3 paths + 5 operations + 5 schema components） | OK |

11/11 行 = coding_report 表格 11 行（9 表述项被作者展开到 11 个文件，但范围一致）。

**作者声明 vs 实际一致**：无 ghost artifacts、无遗漏。

## scope 合规

| spec 受影响模块 | 实际改动 |
|---|---|
| `schemas/{__init__,repo}.py` | 命中 |
| `services/{__init__,repo}.py` | 命中 |
| `routers/repos.py` | 命中 |
| `auth/deps.py` + `auth/__init__.py` | 命中 |
| `main.py` | 命中 |
| `tests/test_repos.py` | 命中（13 测试） |
| `scripts/_self_check.sh` | 命中（13 AC block） |
| `packages/api-types/openapi.json` | 命中 |

**无 scope creep**。`schemas/repo.py` 新增的 `RepositoryListResponse` 未列入 AC-1（AC-1 只钉死 4 个 Create/Read/ListItem/Update），但作为 GET /repos 响应包装器是 AC-10 的 `{items, total}` 形状所必须——属合理派生而非 creep。

## AC 实跑验证

逐条机械化跑 spec 表的命令（PG 5433 端口，凭据 `dataplat/dataplat`）：

| AC | 状态 | 备注 |
|---|---|---|
| AC-1 schemas 4 类齐全 | PASS | `from dataplat_api.schemas.repo import ... ; issubclass(BaseModel)` |
| AC-2 RepoService 5 method | PASS | `inspect.getmembers` 集合 ≥ `{create, get_by_owner_name, list, update, delete}` |
| AC-3 router 5 路由 + prefix=/repos | PASS | paths == `{/repos, /repos/{owner}/{name}}` |
| AC-4 main 集成 + OpenAPI 含 /repos | PASS | `app.openapi()['paths']` 含两 path |
| AC-5 get_optional_user 异步 | PASS | `inspect.iscoroutinefunction` True |
| AC-6 visibility 矩阵 | PASS（self_check AC-6 9 断言全过） | public/internal/private × None/user/admin = 9 组合 |
| AC-7 POST require_admin | PASS（self_check AC-7） | `route.dependant.dependencies` 含 `require_admin` |
| AC-8 GET get_optional_user | PASS（self_check AC-8） | GET 仅挂 optional 不挂 current |
| AC-9 PATCH/DELETE require_admin | PASS（self_check AC-9） |  |
| AC-10 extra=forbid | PASS（self_check AC-10） | 传 `bogus=x` 抛 ValidationError |
| AC-11 repos 集成 ≥ 13 全 PASS | **PASS（13 passed in 6.07s）** | `pytest tests/test_repos.py` PG 5433 |
| AC-12 ruff + mypy | PASS | `All checks passed!` + `Success: no issues found in 43 source files` |
| AC-13 self_check repo-api-mvp 13/13 | PASS | `DATAPLAT_PG_PORT=5433 bash scripts/_self_check.sh repo-api-mvp` → PASS=13 FAIL=0 |

**回归**：

- `tests/test_auth.py` 11 passed（既有 `_decode_user_from_cookie` 抽出后没有破坏 `get_current_user` 七路径硬契约——auth-scaffold 11 测试全 PASS）。
- 全仓 `bash scripts/_self_check.sh`（默认 PG 5432）：cas-storage AC-15 MinIO 凭据 env-drift 是 pre-existing；repo-api-mvp AC-11 在默认 5432 端口因 PG 凭据 `dataplat/dataplat` 与本机 5432 实例不一致而 FAIL（**非代码缺陷**，环境侧 docker-compose 默认端口与开发机本地实例冲突；coding_report 已说明）。`DATAPLAT_PG_PORT=5433` 显式跑 13/13 PASS。

## 正确性 / 安全 / 架构问题

### MUST FIX

无。

### SHOULD FIX

| # | 文件:行 | 问题 | 建议 |
|---|---|---|---|
| 1 | `apps/api/dataplat_api/schemas/__init__.py:3-15` 与 `coding/coding_report_v1.md` 表第一行 | coding_report 声称"暴露 5 个 schema"，但 `__init__.py.__all__` 只有 4 个（`RepositoryCreate / Read / ListItem / Update`），缺 `RepositoryListResponse`。下游目前都从 `dataplat_api.schemas.repo` 直接 import（`grep -rn "from dataplat_api.schemas import" apps/api/` 返回空），所以功能不破，但**作者声明与实物不一致**违反 coding-style §0.4「删干净」精神（声明面与代码面应一致）。 | 二选一：(a) 把 `RepositoryListResponse` 加进 `__init__.py` 的 `from ... import` + `__all__`；(b) 修 coding_report 表格"暴露 5 个 schema" → "暴露 4 个 schema（ListResponse 仅 routers 内用）"。 |
| 2 | `apps/api/dataplat_api/services/repo.py:60-63, 136-139` | `service.create` / `service.update` 直接 `raise HTTPException(409/404, ...)`——HTTP 关切渗入 service 层，违反 coding-style §1.5「业务错误用项目内自定义异常层级（如 DataplatError → RepositoryNotFound 等）」。spec tasks T-3 明确允许（"service 处理 not-found → 404"），所以是 spec 钉的 trade-off 而非个人风格违背；但项目长远应有 `RepositoryNotFoundError` / `RepositoryAlreadyExistsError`，router 边界统一转 HTTP。当前 spec 没强制，列为 **deferred SHOULD FIX**。 | 不阻塞本变更。下个 change（建议 `domain-errors-introduce-*` 或挂在 `commit-api-mvp` 引入相同模式时一起做）落 `DataplatError` 基类 + 路由 exception_handler 转换。Repo 服务的两处 `raise HTTPException` 重构为 `raise RepositoryAlreadyExistsError` / `RepositoryNotFoundError`。 |

### NICE TO HAVE

| # | 文件:行 | 问题 | 建议 |
|---|---|---|---|
| 1 | `apps/api/dataplat_api/services/repo.py:46-47` | `service.create` 显式 `id=uuid.uuid4()`，而 `RepositoryORM.id` 已 `default=uuid.uuid4`（见 `models/repository.py:23`）——冗余。 | 删掉 `id=uuid.uuid4()` 那行，让 ORM default 接手。不阻塞。 |
| 2 | `apps/api/dataplat_api/services/repo.py:122-148, 150-166` | `service.update / delete` 不做 visibility 矩阵——目前 router `Depends(require_admin)` 守住没问题，但失去 defense-in-depth：若将来误把 `require_admin` 改成 `require_user`，user PATCH 私有 repo 会返 200 / PATCH 不存在的私有 repo 会返 404，从而暴露存在性（404 vs 200 oracle）。 | 不阻塞——spec 明确 admin 全权，业务层不重复门禁也是一致选择。若引入 `RepositoryNotFoundError`（SHOULD FIX #2）一起做时可补 visibility 校验。 |
| 3 | `apps/api/dataplat_api/main.py:31` | 注释 `# 见 cas-storage spec MUST FIX-1 与 stage 4 reviewer 钉死的唯一组合` 误指——prefix 钉死规则实际首次出现在 **auth-scaffold-20260517 stage 2 MUST FIX-1**（cas-storage 不涉及 router）。`routers/repos.py:3-4` 的 module docstring 写"auth-scaffold-20260517 stage 2 MUST FIX 已规则化"是正确归属。`git blame main.py` 显示该注释来自 commit `8e3cfe8 feat(auth): ...`——**非本变更引入**，不在本评审职责范围内。 | 下个变更顺手 `s/cas-storage/auth-scaffold/` 即可。 |
| 4 | `apps/api/tests/test_repos.py:38-79` | `_make_user / _delete_user / _delete_repo` 每次都新建 engine（auth-scaffold 风险表点名要求的"fresh engine per fixture"模式），慢但符合 spec。 | 不阻塞。若后续测试套显著拖慢 CI，可考虑 module-scope engine + per-test session。 |

## 风格 / 性能 / 可观测性

按 `.harness/rules/coding-style.md` 逐节核查：

| 章节 | 覆盖 | 检查 |
|---|---|---|
| §0.1 不造抽象 | OK | `RepositoryRead` 与 `RepositoryListItem` 字段相同但 spec AC-1 钉死两类型（演化轴），不抽 |
| §0.4 删干净 | 有 SHOULD FIX #1（`__init__.py` vs coding_report 不一致） | 否则 OK |
| §1.3 类型完整性 | OK | 所有 public 函数全类型注解；router/service 签名完整；用 `Literal` 不用 `Any` |
| §1.4 异步 | OK | service/router 全 `async def`；session 用 `AsyncSession`；count/list 都走 `await session.execute(...)`；无 sync IO |
| §1.5 错误处理 | SHOULD FIX #2（HTTPException 在 service） | 余 OK——`IntegrityError` 显式 `from exc`，无 `except: pass` |
| §1.6 注释 | OK | docstring 写 contract（WHY/约束）不写 WHAT；service module docstring 简洁 |
| §1.7 测试 | OK | 13 集成走真实 PG（无 mock 数据访问层）；fixture 复用 auth-scaffold 模式；测试名 `test_<letter>_<scenario>_<expectation>` |
| §1.8 日志 | OK | 本变更未引日志，无违规 |
| §6 安全 | OK | 404 不泄露存在性（detail + list 一致）；admin 守卫 + 实时 DB 检查防 cookie 缓存窗口（test_j） |
| §7 性能 | OK | list 用 SQL WHERE 过滤（非 in-memory），count 单独 query 总数 1+1=2 queries 非 N+1；layer/offset/limit 走 Query 参数；max=200 已钉 |

**性能**：list 接口走 SQL filter + 单独 `func.count()`——2 queries 完成 list + total，符合 §7 "N+1 是硬性打回项" 无违规。

**可观测性**：本变更未涉及 telemetry / span，spec 不要求，OK。

## 跨改动观察

1. **prefix 规则三处一致**（`auth.py:33` / `admin.py:22` / `repos.py:32` 都 `APIRouter(prefix="/xxx")`；`main.py:32-34` 都 `app.include_router(xxx_router)` 不传 prefix）。auth-scaffold MUST FIX-1 已规则化的硬约束在本变更继续遵守，OK。
2. **`_decode_user_from_cookie` 七路径返 None 硬契约**：手验代码（`deps.py:31-70`）——七路径 `return None` 全到位；`get_current_user` 仅在外层 `is None` 时统一 `raise _UNAUTHORIZED`；`get_optional_user` 直 return——双依赖共享同一解码不漂移。test_auth 11 个 PASS 是回归证据。
3. **404 echo 输入但不区分原因**：detail 路由 `Repository {owner}/{name} 不存在`（router L106 + service L138）——echo 用户输入而非数据库实际存在性，不泄露 oracle。list 用 SQL WHERE 过滤——total 也是过滤后的数（spec AC-10 钉死），不暴露 private 数量。test_l / test_m 机械化覆盖了 list 矩阵。
4. **service 不查 role 边界**：grep `service/repo.py` 无 `current_user.role`（除 `_visibility_visible` 内 `=="admin"` 用于 visibility 而非授权）——service 完全不调用 `require_admin`，admin 权限由 router Depends 担保。AC-7/AC-9 (self_check) 机械化校验 POST/PATCH/DELETE 三写路径全挂 `require_admin`。
5. **test_j PATCH 实时检查证据**：user 在 client `u` 第一次 GET 200 → admin 在 client `a` PATCH → user 在**同一** client `u`（同一 cookies）再 GET → 404。这证明 visibility 检查每次查 DB 行（不缓存于 access token claim），符合 spec MUST FIX #4。

## Deferred SHOULD FIX

| # | 描述 | 建议跟进位置 |
|---|---|---|
| #1 | `schemas/__init__.py` 暴露与 coding_report 表述不一致 | 本 change stage 5 收尾时修，二选一即可（不开新 change） |
| #2 | service 直接 raise HTTPException（违 §1.5 业务异常分层期望） | follow-up change `domain-errors-introduce-*`，或挂在 `commit-api-mvp` 引入相同问题时一并落 `DataplatError` + handler |

## Verdict

**APPROVED**

判据：MUST FIX = 0。所有 13 AC（含 self_check repo-api-mvp 13/13）机械化 PASS；test_auth 11 个回归 PASS；ruff + mypy 全绿；scope / 架构 / 安全 / 性能 / 风格无阻塞性偏离。两条 SHOULD FIX 走 deferred（一条本 change 收尾顺手修；一条 follow-up change 引入异常分层时统一做）。

## 复检指引

作者无需为本评审改代码即可推进 stage 5。若处理 SHOULD FIX #1（推荐顺手做）：

1. 二选一改动后，重跑 `bash scripts/_self_check.sh repo-api-mvp`（默认 PG 端口；若端口不是 5432 加 `DATAPLAT_PG_PORT=5433` 前缀）→ PASS=13。
2. 重跑 `uv run ruff check apps/api packages/core && uv run mypy apps/api/dataplat_api packages/core/src` → 全绿。
3. 若改的是 coding_report 表，进入 stage 5 前在 `coding/coding_report_v1.md`（或开 v2）注明更正。

进入 stage 5（单元测试编写）：13 集成测试已在 `tests/test_repos.py` a~m 落地——stage 5 主要工作是 `unit_test/test_report.md` 汇总 + 评审产物，不必再写新测试。

SHOULD FIX #2（service 异常分层）按 deferred 走，不阻塞 stage 5/6/7。
