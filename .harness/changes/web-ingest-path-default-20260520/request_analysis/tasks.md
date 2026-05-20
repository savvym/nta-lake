---
change_id: web-ingest-path-default-20260520
version: 2
authored_at: 2026-05-20T10:40:00Z
revised_at: 2026-05-20T11:10:00Z
revision_notes: |
  v2 修 stage 2 reviewer v1 报的 1 条 tasks MUST FIX：
  - MUST-1（T-2 缺新单测动作）：拆 T-2 为 T-2a（新增 IngestSection 单测文件
    repos.ingest-section.test.tsx）+ T-2b（确认 6 处现有 "content/" display
    fixture 保留不动）；与 spec v2 新 AC-3a 对齐
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

  - id: T-2a
    title: 新增 repos.ingest-section.test.tsx，覆盖 onFiles 默认 path 行为
    description: |
      apps/web/src/routes/repos.ingest-section.test.tsx（与 repos.tabs / repos.files-section 并列）。
      mock '../lib/api/queries' 含 useMe/useRepoRef/useCommit/useSubtreeByPath/useEnqueueIngest/useUploadBlob 等
      （沿 repos.tabs.test.tsx fixture 风格）；
      渲染 repo 详情页 ?tab=ingest；用 React Testing Library 模拟拖文件 / 点 input[type=file]：
        - File 对象 name='a.pdf'
        - 模拟 onChange/onFiles 后渲染应当显示 path 输入框 value='a.pdf'（不是 'content/a.pdf'）
        - 或直接 assert 上传后 enqueueIngest mock 收到 spec.files[0].path === 'a.pdf'
      ≥ 1 用例（断言 path 不含 content/ 前缀）；推荐 2 用例（默认 + 用户编辑后保留）。
    depends_on: [T-1]
    estimated_stage: unit_test
    covers_ac: [AC-3a]
    status: pending

  - id: T-2b
    title: 确认现有 6 处 "content/" display fixture 保留不动
    description: |
      grep -rE 'content/' apps/web/src/routes/*.test.tsx
      预期 6 处：repos.files-section.test.tsx (4) + commits.$owner.$name.$hash.test.tsx (2)
      它们模拟 legacy 扁平 commit 形态的显示断言（与 ingest 默认 path 行为无关）。
      不改这些 fixture；spec v2 § AC-3a 已显式声明。
      如 grep 结果 ≠ 6，调查新增/丢失原因并 stage 4 复审。
    depends_on: [T-1]
    estimated_stage: unit_test
    covers_ac: [AC-3b]
    status: pending

  - id: T-3
    title: scripts/_self_check.sh 加 run_web_ingest_path_default 5 AC
    description: |
      在 run_web_tree_nested_ui 后插入 run_web_ingest_path_default（5 AC：AC-1 /
      AC-3a / AC-3b / AC-4 / AC-5；不再含 AC-6——已合到 AC-5）；
      filter case + 全跑入口 list 都加上。
      AC-3a 跑 JSON reporter 单文件 vitest；AC-3b 跑全 vitest；AC-4 跑 typecheck。
    depends_on: [T-2a, T-2b]
    estimated_stage: coding
    covers_ac: [AC-5]
    status: pending

  - id: T-4
    title: 本地 typecheck / test / self_check current 全绿
    description: |
      pnpm --filter web typecheck
      pnpm --filter web test -- --run
      bash scripts/_self_check.sh current web-ingest-path-default-20260520
    depends_on: [T-3]
    estimated_stage: ci_result
    covers_ac: [AC-3a, AC-3b, AC-4]
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

T-1 → T-2a + T-2b（并行）→ T-3 → T-4（无环）

## 验收覆盖

| AC | 任务 |
|---|---|
| AC-1 | T-1 |
| AC-3a | T-2a, T-4 |
| AC-3b | T-2b, T-4 |
| AC-4 | T-4 |
| AC-5 | T-3 |
