---
change_id: repo-api-mvp-20260517
version: 1
authored_at: 2026-05-17T08:30:00Z
branch: main (session 直推 main 等价模式；未单独建 branch)
base_commit: b64c3ec5599ecadb40530709ee9f38dc739ffb79
head_commit: working-tree（未 commit；stage 4 评审针对 working tree diff）
status: waiting_review
---

# Coding Report v1

## 改动文件清单

| 路径 | 类型 | 一句话说明（改了什么 / 为什么） | 关联 task |
|---|---|---|---|
| `apps/api/dataplat_api/schemas/__init__.py` | new | 包标记 + 暴露 5 个 schema | T-1 |
| `apps/api/dataplat_api/schemas/repo.py` | new | `RepositoryCreate` / `Read` / `ListItem` / `Update` / `ListResponse` Pydantic（`extra="forbid"`） | T-1 |
| `apps/api/dataplat_api/services/__init__.py` | new | 包标记 + 暴露 `RepoService` | T-3 |
| `apps/api/dataplat_api/services/repo.py` | new | `RepoService` 5 静态方法 + `_visibility_visible` 矩阵；service 不查 role（守卫由 router 担） | T-3 |
| `apps/api/dataplat_api/routers/repos.py` | new | 5 路由：POST/GET 列表/GET 详情/PATCH/DELETE；`require_admin` 写路径；`get_optional_user` 读路径；404 统一不泄露 | T-2 |
| `apps/api/dataplat_api/auth/deps.py` | edit | 抽 `_decode_user_from_cookie` 七路径返 None；新增 `get_optional_user`；`get_current_user` 复用解码再 401 | T-2 |
| `apps/api/dataplat_api/auth/__init__.py` | edit | 暴露 `get_optional_user` | T-2 |
| `apps/api/dataplat_api/main.py` | edit | `include_router(repos_router)` | T-2 |
| `apps/api/tests/test_repos.py` | new | 13 集成测试 a~m：admin/user/匿名 × public/internal/private + 重复 409 + PATCH 实时检查 + DELETE 链路 + list 矩阵 | T-6 |
| `scripts/_self_check.sh` | edit | 追加 repo-api-mvp block（13 AC，AC-11 在 PG 不可达 SKIP） | T-7 |
| `packages/api-types/openapi.json` | edit | `make codegen` 同步：含 `/repos` 3 paths + 5 operations | T-4 |

> **门禁**：上表与 `git status --short` 完全一致（5 modified + 4 untracked = 9 行 + .harness/changes/repo-api-mvp-20260517/ 文档目录）。

## 与 tasks.md 的映射

| Task ID | 状态 | 备注 |
|---|---|---|
| T-1 schemas | done | 5 类型 + extra=forbid；与 `dataplat_core.domain.repository.{Layer,Subtype,Visibility}` 共用 Literal |
| T-2 deps + router | done | `_decode_user_from_cookie` 七路径硬契约；既有 11 个 test_auth 测试 PASS 不退化；prefix=/repos 钉死 |
| T-3 service | done | service 不查 role；create→409 IntegrityError 捕获；list 用 WHERE 过滤 visibility（非 in-memory） |
| T-4 OpenAPI codegen | done | `make codegen` 后 openapi.json 含 3 paths + 5 operations |
| T-5 main include | done | `app.include_router(repos_router)`，router 自带 prefix（auth-scaffold 钉死规则） |
| T-6 tests | done | 13 测试覆盖 AC-11 a~m；run on PG 5433 → 13 passed |
| T-7 self_check | done | 13 AC + `run_repo_api_mvp` 函数 + `repo-api-mvp` filter；全跑 PASS=13 FAIL=0 |

## 偏离 spec / trade-off

- **PATCH visibility 实时 DB 检查（spec MUST FIX-4）**：实现走 service.get_by_owner_name + `_visibility_visible`，每次都查 DB 不依赖 cookie 中的 role 缓存——test_j 用 admin 改 private 后 user 视角立刻 404 验证生效。
- **404 不泄露存在性**：detail 路由 `repo is None`（不存在 or 不可见）统一 raise 404；detail message 含 owner/name 但不区分原因——避免 oracle attack。list 用 SQL WHERE 过滤（性能 + 一致性），total 反映过滤后 count。
- **类型缩窄**：ORM 列是 `str`，schema 是 `Literal[...]`；helper `_to_read` / `_to_list_item` 用 `typing.cast(Layer, ...)` 显式 narrow（mypy 通过）。

## 本地校验结果

```text
uv run ruff check apps/api packages/core           → All checks passed!
uv run mypy apps/api/dataplat_api packages/core/src → Success: no issues found in 43 source files

uv run pytest apps/api packages/core (PG up)        → 27 passed + 5 skipped
   - 13 新 repos 集成（test_repos.py a~m）
   - 11 既有 auth 集成（test_auth.py a~k）回归全 PASS
   - 2 ORM smoke
   - 1 health
   - 5 MinIO 集成（env-drift skip）

bash scripts/_self_check.sh repo-api-mvp           → PASS=13 FAIL=0 SKIP=0
bash scripts/_self_check.sh                        → PASS=81 FAIL=1 SKIP=0
   失败：cas-storage AC-15（MinIO 凭据 env-drift，与本变更无关；pre-existing）

make codegen                                       → openapi.json 同步成功（3 paths + 5 operations）
```

## 已知未解决问题

- **MinIO env-drift（pre-existing）**：本机 MinIO 当前凭据与 docker-compose 默认 `dataplat-dev-secret` 不一致，cas-storage AC-15 跑红。**非本变更引入**——本变更未触碰 storage 层任何代码。已记入 session_handoff 待环境侧修复。
- commit/blob/tree/lineage 路由未实现：下个 change `commit-api-mvp-*` 接续。
- owner 权限模型未实现：admin 全权 → 后续 `repo-owner-permission-*`。
- search/全文/tag 未实现：Phase 2。
- 列表分页：仅 limit/offset；cursor 分页 Phase 2。

## reviewer 重点关注

1. **404 不泄露存在性**：detail + list 矩阵是否真的一致？测试覆盖 (l)(m) 是否充分？
2. **`_decode_user_from_cookie` 七路径返 None 硬契约**：是否所有 401-触发路径都被收口，没有 raise 漏出到 `get_optional_user`？既有 test_auth 11 个仍 PASS 是回归依据。
3. **service 不查 role 的边界**：router `Depends(require_admin)` 是否覆盖所有写路径（POST/PATCH/DELETE）？AC-7/9 已自检但 reviewer 自验证。
4. **PATCH 实时检查**：test_j 是否真的能证明 visibility 变更立刻生效（user 用同一 cookies 第二次 GET 应该 404）？
5. **prefix=/repos 钉死规则一致性**：是否复用 auth-scaffold stage 2 MUST FIX-1 的「router 自带 prefix + include_router 不传 prefix」？
6. **mypy `typing.cast` 用法是否合理**：能否用 model_validate 更优雅？还是 cast 表达更明确？

## 下一步

进入阶段 4 编码评审：独立 reviewer 加载 `.harness/skills/code-review/SKILL.md`，针对 working-tree diff 写 `code_review_v1.md`。
