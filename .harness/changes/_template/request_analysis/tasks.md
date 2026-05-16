---
change_id: <feature-slug>-<yyyymmdd>
version: 1
authored_at: <YYYY-MM-DDTHH:MM:SSZ>
---

# Tasks

> 任务粒度 1-3 小时。每个任务都要标明 `depends_on` 与 `estimated_stage`。

## 任务清单

```yaml
tasks:
  - id: T-1
    title: <e.g. 新增 Repository SQLAlchemy 模型与 Alembic 迁移>
    description: <更详细的内容，3-5 行内>
    depends_on: []
    estimated_stage: coding
    covers_ac: [AC-1]                # 关联的验收项 ID
    status: pending                  # pending | in_progress | done | deferred
    commits: []                      # 关联 commit SHA（完成时填）

  - id: T-2
    title: <e.g. 写 Repository CRUD 路由>
    description: ...
    depends_on: [T-1]
    estimated_stage: coding
    covers_ac: [AC-1]
    status: pending
    commits: []

  - id: T-3
    title: <e.g. 写 Repository CRUD 集成测试>
    description: ...
    depends_on: [T-2]
    estimated_stage: unit_test
    covers_ac: [AC-1, AC-2]
    status: pending
    commits: []
```

## 阶段任务（必备占位，不要漏）

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

  - id: P-ci
    estimated_stage: ci_result
    status: pending

  - id: P-deploy
    estimated_stage: deployment       # 如本 change 无部署面，可删除并在 summary.md 注明
    status: pending

  - id: P-user-confirm
    estimated_stage: user_confirmation
    status: pending
```

## DAG 健全性

依赖图必须无环。本文件提交前自行用一段脚本或人工验证。

## 验收覆盖矩阵

| AC | 关联任务 |
|---|---|
| AC-1 | T-1, T-2, T-3 |
| AC-2 | T-3 |

每条 AC 必须至少有一个非 process_tasks 的任务覆盖。
