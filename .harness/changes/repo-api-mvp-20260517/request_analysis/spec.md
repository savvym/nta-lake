---
change_id: repo-api-mvp-20260517
version: 1
authored_at: 2026-05-17T07:05:00Z
status: draft
---

# Spec：Repository CRUD MVP 路由

## 背景

前 5 个变更已落 monorepo + Pydantic 模型 + ORM + CAS storage + auth。但 dataplat **还没有任何业务 HTTP CRUD 路由**——前端无法开始联调 Repository 列表 / 详情。本变更引入 Repository CRUD 路由（**仅 Repository；commit/blob/tree/lineage 路由留给独立 follow-up**），让前端可工作 + 验证 auth-scaffold 守卫在真实路由上生效。

## 范围

In scope（每条对应可机械化验证）：

- **AC-1**：`apps/api/dataplat_api/schemas/__init__.py` + `schemas/repo.py` 存在；定义 `RepositoryCreate(owner, name, layer, subtype, visibility='private', description: str | None=None)` / `RepositoryRead` / `RepositoryListItem` / `RepositoryUpdate(visibility?, description?)` 共 4 个 Pydantic BaseModel。
- **AC-2**：`apps/api/dataplat_api/services/__init__.py` + `services/repo.py` 存在；`RepoService` class 含 async 方法 `create / get_by_owner_name / list / update / delete`；每个方法接收 `AsyncSession` + `current_user: AuthenticatedUser | None` 用于 visibility 过滤。
- **AC-3**：`apps/api/dataplat_api/routers/repos.py` 存在；`router = APIRouter(prefix="/repos", tags=["repos"])`；5 路由（`POST /repos` / `GET /repos` / `GET /repos/{owner}/{name}` / `PATCH /repos/{owner}/{name}` / `DELETE /repos/{owner}/{name}`）。
- **AC-4**：`main.py` `include_router(repos_router)`；OpenAPI 含 `/repos` + `/repos/{owner}/{name}` 两类 path。
- **AC-5**：`auth/deps.py` 新增 `get_optional_user` async 依赖；无 cookie 返 None；含合法 access cookie 返 AuthenticatedUser；含 typ != 'access' 也返 None（不 raise）。`get_current_user` 与 `get_optional_user` 应共享 `_decode_user_from_cookie` 实现避免漂移。
- **AC-6**：**visibility 矩阵**（**detail + list 一致**；返 404 不 401/403 避免泄露存在性）：
  - `public` repo：匿名 / user / admin —— detail GET 200；list 中可见
  - `internal` repo：user / admin —— detail 200 / list 可见；**匿名 → detail 404 / list 静默缺席不报错**
  - `private` repo：仅 admin —— detail 200 / list 可见；user 与匿名 → detail 404 / list 静默缺席
  - **visibility 检查基于实时 DB 行；access token 仅证身份不证可见性**——PATCH 后旧 cookie 不构成缓存窗口（spec MUST FIX #4）
- **AC-7**：`POST /repos` 仅 admin（`Depends(require_admin)`）；创建成功 → 201 + RepositoryRead；`(owner, name)` 重复 → 409 Conflict；非 admin → 403。
- **AC-8**：`PATCH /repos/{owner}/{name}` 仅 admin；改 `visibility` + `description`；repo 不存在 → 404；返 200 + RepositoryRead。
- **AC-9**：`DELETE /repos/{owner}/{name}` 仅 admin；成功 → 204；不存在 → 404。
- **AC-10**：`GET /repos` 支持 query `limit` (default 50, max 200) + `offset` (default 0) + `layer` (bronze/silver/gold 之一时过滤)；按 AC-6 visibility 矩阵自动过滤；返 `{"items": [...], "total": N}`。**`total` 反映 visibility 过滤后剩余数**（不泄露 private/internal 数量给无权 caller）。
- **AC-11**：`apps/api/tests/test_repos.py` 含 ≥ 13 集成测试（spec MUST FIX #3 加 list × visibility 2 条）：
  - (a) admin POST 创建 → 201
  - (b) user POST → 403
  - (c) 重复 (owner, name) → 409
  - (d) admin GET 已创建 → 200
  - (e) admin list 含新 repo
  - (f) 匿名 GET public repo → 200
  - (g) 匿名 GET private repo → 404
  - (h) user GET internal repo → 200
  - (i) user GET private repo → 404
  - (j) admin PATCH visibility public→private + 验证 user 视角变 404
  - (k) admin DELETE 204 + 再 GET 404
  - **(l) 匿名 list 仅含 public**（spec MUST FIX #3：list visibility 矩阵机械化覆盖）
  - **(m) user list 不含 private**（同上）
- **AC-12**：`uv run ruff check apps/api packages/core` + `uv run mypy apps/api/dataplat_api packages/core/src` 全 PASS。
- **AC-13**：`scripts/_self_check.sh repo-api-mvp` 13/13 PASS（含 Postgres SKIP 通道）。

## 非范围

- 不实现 commit / tree / blob / lineage 路由（独立 commit-api-mvp follow-up）
- 不实现 dataset card 解析
- 不实现 Repository 级 ACL（Phase 2；visibility 字段已够 MVP）
- 不实现 search / tag / full-text
- 不实现 audit log / rate limit
- 不支持 PATCH owner/name 改名

## 验收标准

| ID | 描述 | 验证方式 | 期望 |
|---|---|---|---|
| AC-1 | schemas 4 类齐全 | `cd apps/api && uv run python -c "from dataplat_api.schemas.repo import RepositoryCreate, RepositoryRead, RepositoryListItem, RepositoryUpdate; from pydantic import BaseModel; assert all(issubclass(c, BaseModel) for c in (RepositoryCreate, RepositoryRead, RepositoryListItem, RepositoryUpdate))"` | exit 0 |
| AC-2 | RepoService 5 method | `cd apps/api && uv run python -c "from dataplat_api.services.repo import RepoService; import inspect; m={n for n,_ in inspect.getmembers(RepoService, inspect.isfunction)}; assert {'create','get_by_owner_name','list','update','delete'} <= m"` | exit 0 |
| AC-3 | repos router 5 路由 + prefix='/repos' | `cd apps/api && uv run python -c "from dataplat_api.routers.repos import router; paths={r.path for r in router.routes}; assert '/repos' in paths and '/repos/{owner}/{name}' in paths"` | exit 0 |
| AC-4 | OpenAPI 含 /repos | `cd apps/api && uv run python -c "from dataplat_api.main import app; s=app.openapi(); assert '/repos' in s['paths'] and '/repos/{owner}/{name}' in s['paths']"` | exit 0 |
| AC-5 | get_optional_user 异步依赖 | `cd apps/api && uv run python -c "from dataplat_api.auth.deps import get_optional_user; import inspect; assert inspect.iscoroutinefunction(get_optional_user)"` | exit 0 |
| AC-6 ~ AC-10 | 行为由 AC-11 集成测试覆盖 | 见 AC-11 | exit 0 |
| AC-11 | apps/api repos 集成 ≥ 13 + 全 PASS（含 list visibility 矩阵）| **命令实现移至 scripts/_self_check.sh repo-api-mvp block**（spec MUST FIX #1：markdown 表格内反斜杠转义的竖线是字面字符不是 shell pipe，混在 spec 行内必失败）。脚本内做 (a) socket 探针 SKIP；(b) export DATAPLAT_DATABASE_URL + DATAPLAT_JWT_SECRET；(c) pytest exit 0；(d) collect-only 输出 redirect 到临时文件后 grep -cE "::" 计数 ≥ 13 | PG up → exit 0；PG down → AC-13 SKIP 转 |
| AC-12 | ruff + mypy 全 PASS | `uv run ruff check apps/api packages/core && uv run mypy apps/api/dataplat_api packages/core/src` | exit 0 |
| AC-13 | self_check repo-api-mvp block | `bash scripts/_self_check.sh repo-api-mvp` 退出 0 | exit 0 |

## 风险

| 风险 | 概率 | 影响 | 缓解 |
|---|---|---|---|
| visibility 矩阵返 404 vs 401 vs 403 不统一会泄露存在性 | 中 | 安全 | spec 钉死：无权访问者一律 404；403 仅用于"已认证但角色不够" |
| `get_optional_user` 与 `get_current_user` 解码漂移 | 中 | 维护 | 抽出 `_decode_user_from_cookie`，两依赖共用 |
| service.create 重复 (owner, name) → IntegrityError 未捕获 → 500 | 中 | UX | service try/except IntegrityError → raise HTTPException 409 |
| PATCH partial update 误清字段 | 中 | 数据 | RepositoryUpdate 字段全 Optional 默认 None；service 内 `if v is not None: setattr` |
| list 返回 total 涉及额外 count query | 低 | 性能 | MVP 流量小可接受；高 QPS 时另算 |
| 测试 fixture 跨用例 stale connection（asyncpg event-loop） | 中 | flaky | 复用 auth-scaffold 的 NullPool + fresh engine per fixture + 不 dispose |

## 受影响模块

- `apps/api/dataplat_api/schemas/{__init__,repo}.py`（新）
- `apps/api/dataplat_api/services/{__init__,repo}.py`（新）
- `apps/api/dataplat_api/routers/repos.py`（新）
- `apps/api/dataplat_api/auth/deps.py`（修：+ get_optional_user + 抽 _decode_user_from_cookie）
- `apps/api/dataplat_api/main.py`（修：include repos_router）
- `apps/api/tests/test_repos.py`（新，≥ 13）
- `scripts/_self_check.sh`（追加）
- `packages/api-types/openapi.json`（生成）

## 待澄清问题

- [x] internal/private 返 404 vs 403？答：**404**（避免存在性泄露）
- [x] PATCH 改 owner/name？答：**否**（MVP 不支持）
- [x] DELETE 级联？答：MVP 仅删 repo 行；commit/tree/blob 暂无 FK 到 repo（design 中有 ON DELETE CASCADE 但 commit 还没引入路由），实际级联留给 commit-api 变更

## 引用

- design.md §4.4 / §7.1 / §11.3 / §11.6
- auth-scaffold-20260517 已落 get_current_user / require_admin
