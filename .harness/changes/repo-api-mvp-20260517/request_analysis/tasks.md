---
change_id: repo-api-mvp-20260517
version: 1
authored_at: 2026-05-17T07:10:00Z
---

# Tasks

## 任务清单

```yaml
tasks:
  - id: T-1
    title: apps/api/dataplat_api/schemas/{__init__,repo}.py - 4 Pydantic
    description: |
      RepositoryCreate(owner, name, layer, subtype, visibility='private', description=None)
      RepositoryRead(id, owner, name, layer, subtype, visibility, description, created_at, updated_at)
      RepositoryListItem(同 Read 子集；用于 list 响应)
      RepositoryUpdate(visibility?, description?) 全 Optional
      __init__.py 暴露 4 类
    depends_on: []
    covers_ac: [AC-1]
    status: pending

  - id: T-2
    title: apps/api/dataplat_api/auth/deps.py 扩展（tasks MUST FIX-1：硬契约）
    description: |
      新增 `_decode_user_from_cookie(request: Request, session: AsyncSession) -> AuthenticatedUser | None`
        七路径全返 None（不 raise）：无 cookie / token 解码失败 / typ != 'access' /
        sub 缺 / sub 非 UUID / user 不存在 / user inactive
      重构 get_current_user：调 _decode_user_from_cookie；None → raise _UNAUTHORIZED
      新增 get_optional_user：调 _decode_user_from_cookie；直接 return（None 不 raise）
      **硬契约**：
        (a) get_current_user 仍是七路径全 raise 401（auth-scaffold 既有行为不破）
        (b) get_optional_user 七路径全返 None（含 user inactive 也返 None 不 raise）
        (c) apps/api/tests/test_auth.py 既有 11 个测试（test_a ~ test_k）全 PASS（回归）
    depends_on: []
    covers_ac: [AC-5]
    status: pending

  - id: T-3
    title: apps/api/dataplat_api/services/{__init__,repo}.py - RepoService（职责分离明示）
    description: |
      RepoService class（不持 state，方法接 AsyncSession + 必要时 current_user）
      **service 职责（tasks MUST FIX-3）**：
        - service **不查 role / 不调 require_admin**——admin 权限校验由 router 的
          Depends(require_admin) 保证，service 假设 caller 已通过守卫
        - service 处理：(a) get_by_owner_name / list 的 visibility 过滤（current_user
          为 None / user / admin 三档）；(b) create 的 IntegrityError → 409；
          (c) update / delete 的 not-found → 404
      方法签名：
        create(session, payload) → RepositoryORM；捕 IntegrityError → raise HTTPException 409
        get_by_owner_name(session, owner, name, current_user) → RepositoryORM | None；
          visibility 矩阵：public 任何人；internal current_user is not None；private current_user.role=='admin'
        list(session, *, limit, offset, layer, current_user) → tuple[list, total]；同矩阵过滤
        update(session, owner, name, payload) → RepositoryORM；不存在 raise HTTPException 404；
          只更新非 None 字段（避免误清）
        delete(session, owner, name) → bool；返 True/False 表示是否真删
      __init__.py 暴露 RepoService
    depends_on: [T-1]
    covers_ac: [AC-2, AC-6, AC-7, AC-8, AC-9, AC-10]
    status: pending

  - id: T-4
    title: apps/api/dataplat_api/routers/repos.py - 5 路由
    description: |
      APIRouter(prefix='/repos', tags=['repos'])
      POST /repos: Depends(require_admin) → service.create → 201 RepositoryRead
      GET /repos: Depends(get_optional_user) + Query(limit/offset/layer) → service.list → {items, total}
      GET /repos/{owner}/{name}: Depends(get_optional_user) → service.get_by_owner_name；None → 404
      PATCH /repos/{owner}/{name}: Depends(require_admin) → service.update → 200
      DELETE /repos/{owner}/{name}: Depends(require_admin) → service.delete；False → 404；True → 204
    depends_on: [T-2, T-3]
    covers_ac: [AC-3, AC-4]
    status: pending

  - id: T-5
    title: main.py include_router(repos_router)
    description: app.include_router(repos_router) 不加 prefix（router 自带）
    depends_on: [T-4]
    covers_ac: [AC-4]
    status: pending

  - id: T-6
    title: apps/api/tests/test_repos.py（≥ 13 集成，含 list visibility 矩阵）
    description: |
      13 集成测试（AC-11 a~m）覆盖 admin/user/匿名 × public/internal/private 矩阵
      - a~k 同 spec AC-11 a~k（detail 矩阵 + 创建 + 重复 + PATCH + delete）
      - l: 匿名 list 仅含 public（spec MUST FIX-3：list 矩阵机械化覆盖）
      - m: user list 不含 private（同）
      fixture：复用 auth-scaffold 的 created_admin / created_user 模式（fresh engine + delete row teardown）
      conftest 已早设 JWT_SECRET + USE_NULL_POOL，无需新加
    depends_on: [T-4, T-5]
    covers_ac: [AC-6, AC-7, AC-8, AC-9, AC-10, AC-11]
    status: pending

  - id: T-7
    title: scripts/_self_check.sh 追加 repo-api-mvp block
    description: 13 AC self-check；Postgres 探针前置；AC-11 SKIP 通道
    depends_on: [T-6]
    covers_ac: [AC-13]
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
    reason: 本地等价 self_check + ruff + mypy + pytest
  - id: P-deploy
    estimated_stage: deployment
    status: skipped
  - id: P-user-confirm
    estimated_stage: user_confirmation
    status: pending
```

## DAG 健全性

T-3 → T-1（schema 引用）；T-4 → T-2/T-3；T-5 → T-4；T-6 → T-4/T-5；T-7 → T-6。无循环。

## 验收覆盖矩阵

| AC | 关联 |
|---|---|
| AC-1 | T-1 |
| AC-2 | T-3 |
| AC-3 | T-4 |
| AC-4 | T-4, T-5 |
| AC-5 | T-2 |
| AC-6 ~ AC-10 | T-3 (service 实现) + T-6 (测试覆盖) |
| AC-11 | T-6 |
| AC-12 | 全部 |
| AC-13 | T-7 |
