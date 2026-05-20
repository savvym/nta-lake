---
change_id: web-ingest-path-default-20260520
version: 1
authored_at: 2026-05-20T10:40:00Z
---

# Tasks

```yaml
tasks:
  - id: T-1
    title: 改 $owner.$name.tsx line 583 默认 path 为 f.name
    description: |
      apps/web/src/routes/repos/$owner.$name.tsx onFiles 函数：
        - 原：`path: \`content/${f.name}\``
        - 改：`path: f.name`
      不动其他逻辑（updatePath、上传链路）。
    depends_on: []
    estimated_stage: coding
    covers_ac: [AC-1]
    status: pending

  - id: T-2
    title: 扫测试断言含 "content/" 字面，按需调整
    description: |
      grep -rE 'content/"' apps/web/src/routes/*.test.tsx
      如有断言依赖默认 content/ 前缀的 fixture，逐个改：
        - 若是测试上传"用户没改 path"的默认行为：改断言为期望 path = filename（不含前缀）
        - 若是断言用户手工填了 content/xxx：保留，标注是手工输入 fixture
      ≤ 5 处预计；预跑 pnpm test 看哪些 break。
    depends_on: [T-1]
    estimated_stage: unit_test
    covers_ac: [AC-2, AC-3]
    status: pending

  - id: T-3
    title: scripts/_self_check.sh 加 run_web_ingest_path_default 6 AC
    description: |
      在 run_web_tree_nested_ui 后插入 run_web_ingest_path_default（6 AC）；
      filter case + 全跑入口 list 都加上。
      AC-3 跑 pnpm --filter web test -- --run；AC-4 跑 typecheck。
    depends_on: [T-2]
    estimated_stage: coding
    covers_ac: [AC-5, AC-6]
    status: pending

  - id: T-4
    title: 本地 typecheck / test / self_check current 全绿
    description: |
      pnpm --filter web typecheck
      pnpm --filter web test -- --run
      bash scripts/_self_check.sh current web-ingest-path-default-20260520
    depends_on: [T-3]
    estimated_stage: ci_result
    covers_ac: [AC-3, AC-4]
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
    estimated_stage: stage-7
    status: pending
  - id: P-ci
    estimated_stage: ci_result
    status: pending
  - id: P-deploy
    estimated_stage: deployment
    status: pending   # noop（仅前端）
  - id: P-user-confirm
    estimated_stage: user_confirmation
    status: pending
```

## DAG

T-1 → T-2 → T-3 → T-4（无环）

## 验收覆盖

| AC | 任务 |
|---|---|
| AC-1 | T-1 |
| AC-2 | T-2 |
| AC-3 | T-2, T-4 |
| AC-4 | T-4 |
| AC-5 | T-3 |
| AC-6 | T-3 |
