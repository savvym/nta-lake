---
change_id: repo-api-mvp-20260517
title: Repository CRUD MVP 路由（POST/GET/PATCH/DELETE 含 visibility 隔离）
owner: zhhdzhang
started_at: 2026-05-17T07:00:00Z
closed_at: 2026-05-17T09:20:00Z
stage: closed
status: closed
last_updated: 2026-05-17T09:20:00Z
related_changes:
  - core-domain-model-20260516
  - auth-scaffold-20260517
---

# Summary

## 一句话目标

按 [.harness/design.md](../../design.md) §4.4 / §7.1 / §11.6 落地 Repository CRUD 路由：用 `auth-scaffold` 的 `get_current_user` / `require_admin` 守卫；private/internal/public 三档 visibility 隔离；OpenAPI 自动含 `/repos/*` paths；让前端开始联调 Repository 列表 / 详情。

## 范围摘要

- **In scope**：
  - `apps/api/dataplat_api/schemas/__init__.py` + `repo.py`：`RepositoryCreate` / `RepositoryRead` / `RepositoryListItem` / `RepositoryUpdate` Pydantic
  - `apps/api/dataplat_api/services/__init__.py` + `repo.py`：业务逻辑（CRUD + visibility 过滤）
  - `apps/api/dataplat_api/routers/repos.py`：5 路由 `POST /repos` / `GET /repos` / `GET /repos/{owner}/{name}` / `PATCH /repos/{owner}/{name}` / `DELETE /repos/{owner}/{name}`
  - `main.py` include repos router
  - 集成测试 ≥ 8 个 + visibility 矩阵覆盖（admin / user / 匿名 三类调用方 × private/internal/public 三档 = 部分核心组合）
  - `scripts/_self_check.sh` 追加 repo-api-mvp block
- **Out of scope**：
  - 不实现 commit / tree / blob 上传路由（commit-api-mvp 单独 follow-up）
  - 不实现 dataset card 解析（card-schema follow-up）
  - 不实现 lineage 查询（lineage-query-graph follow-up）
  - 不实现 Repository 级 ACL（Phase 2；visibility 字段足够 MVP）
  - 不实现 search（全文 / tag filter）—— Phase 2

## 关键决策

| 时间 | 决策 | 理由 |
|---|---|---|
| 2026-05-17 | visibility 矩阵：private 仅 admin / internal 已登录 / public 匿名 | design.md §11.6 MVP 简化（OWNER 字段后续 ACL 引入再细化） |
| 2026-05-17 | service 层放 `services/repo.py`，路由只做 HTTP 转 service | design.md §11.3 / coding-style.md §1.3 分层 |
| 2026-05-17 | 不引入 owner-permission：admin 全权；普通用户只读 | MVP；后续 `repo-owner-permission-*` follow-up |
| 2026-05-17 | 范围严格限定 repo CRUD（无 commit）| 隔离变更，让 reviewer 焦点单一；commit 路由依赖 BlobStore 写入 + tree + 事务，体量更大 |

## 阶段进度

| 阶段 | 状态 |
|---|---|
| 1 需求分析 | done（spec v2） |
| 2 需求评审 | done（reviewer v1 REVISION REQUIRED → v2 APPROVED） |
| 3 编码实现 | done（7 个 T-* + schemas/__init__ 暴露 fix） |
| 4 编码评审 | done（reviewer v1 APPROVED，0 MUST FIX） |
| 5 单测编写 | done（14 集成测试 a~n + 13 self_check） |
| 6 单测评审 | done（reviewer v1 1 MUST FIX → v2 APPROVED） |
| 7 代码推送 | done（session 直推 main 等价；commit 落地） |
| 8 CI 验证 | done（本地 self_check 等价：repo-api-mvp 13/13 PASS；全仓 81/82，仅 cas-storage AC-15 MinIO env-drift） |
| 9 部署验证 | skipped: 无运行时部署面（deployment/deploy_verify_v1.md 决策记录） |
| 10 用户确认 | done（会话级授权 Generator 自我确认） |

## 当前阻塞

- 无功能性阻塞。环境层 MinIO 凭据漂移（cas-storage AC-15）pre-existing，不影响本变更代码。

## Follow-ups（spec 内 deferred + 评审 deferred SHOULD FIX/NICE TO HAVE）

- `commit-api-mvp-*`：commit/blob/tree/lineage 路由（本变更明确不实现）
- `repo-owner-permission-*`：owner-level ACL 取代 admin 全权
- `repo-visibility-anon-internal-coverage-*`：补 (anon, internal) detail HTTP 端到端用例（stage 6 v1 SHOULD FIX）
- `coverage-instrumentation-*`：pytest-cov 量化覆盖率
- `domain-errors-introduce-*`：service 层不直 raise HTTPException，引入 domain error → 路由层翻译
- `main-py-comment-update-*`：main.py:31 注释里 "cas-storage" 应纠正为 "auth-scaffold"（stage 4 NICE TO HAVE）
