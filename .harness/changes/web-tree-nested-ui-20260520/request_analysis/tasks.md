---
change_id: web-tree-nested-ui-20260520
version: 2
authored_at: 2026-05-19T16:50:00Z
revised_at: 2026-05-19T17:15:00Z
revision_notes: |
  v2 修 stage 2 reviewer v1 报的 2 条 tasks MUST FIX：
  - MUST FIX-1（T-3 超大）：拆 T-3a（数据层：useSubtreeByPath 接入 + path search 钩子）+
    T-3b（表现层：面包屑 + folder/blob 行 + loading/error UI）
  - MUST FIX-2（AC-9 无 task 归宿）：spec v2 删旧 AC-9（手测）；新 AC-9 = self_check 含
    run_web_tree_nested_ui，归 T-5；AC 表全列任务覆盖
---

# Tasks

```yaml
tasks:
  - id: T-1
    title: queries.ts 加 useSubtree + useSubtreeByPath
    description: |
      apps/web/src/lib/api/queries.ts。
      新增：
      - useSubtree(owner, name, tree_hash) 调 GET /api/repos/{owner}/{name}/trees/{tree_hash}
        返 TreeRead；enabled 检查 tree_hash 是 sha256
      - useSubtreeByPath(owner, name, commit_hash, path) 单 queryFn 串行 fetch：
        1. 先 fetch /tree/{commit_hash} 拿 root tree
        2. path == "" → 返 root
        3. 否则 path.split("/").filter(Boolean) 走每段：
           cur.entries.find(e => e.name == seg && e.entry_type == "tree")
           不存在 / 非 tree → throw new Error(详细消息)
           存在 → fetch /trees/{found.target_hash}
        4. 返最终层 TreeRead
        queryKey: ["subtree-by-path", owner, name, commit_hash, path]
        enabled: !!commit_hash && /^[0-9a-f]{64}$/.test(commit_hash)
    depends_on: []
    estimated_stage: coding
    covers_ac: [AC-1, AC-2]
    status: pending

  - id: T-2
    title: 路由 validateSearch 加 path 字段
    description: |
      apps/web/src/routes/repos/$owner.$name.tsx。
      现有 validateSearch（来自 createFileRoute）含 tab；加 path 字段：
        - path: z.string().optional() 或 路由生成代码格式
        - 默认值 ""
      _searchSchema 同步更新（如果有 schema variable）
      Link / navigate 调用点同步：tab 切换时保留 path（或重置到 ""），看交互期望
    depends_on: [T-1]
    estimated_stage: coding
    covers_ac: [AC-3]
    status: pending

  - id: T-3a
    title: FilesSection 数据层接入（useSubtreeByPath + path search 钩子）
    description: |
      apps/web/src/routes/repos/$owner.$name.tsx::FilesSection。
      - 通过 useSearch({ from: route }) 拿 path (default "")
      - 用 useSubtreeByPath(owner, name, commit_hash, path) 取当前层 entries
      - 用 useNavigate({ from: route }) 拿 navigate；封装 setPath(newPath)
        helper（保留其他 search 字段如 tab）
      - useSubtreeByPath isError 时把 error 透出，由 T-3b 渲染
      - 不动现有 commit / ref query，loading / 空 tree 状态保留
      颗粒度估算：~1.5h（含 hook 接入 + setPath helper + error 透出）
    depends_on: [T-2]
    estimated_stage: coding
    covers_ac: [AC-4]
    status: pending

  - id: T-3b
    title: FilesSection 表现层（面包屑 + folder/blob 行 + loading/error UI）
    description: |
      apps/web/src/routes/repos/$owner.$name.tsx::FilesSection。
      - 面包屑组件（inline 实现）：repo 链接（→ setPath("")）+ 当前 path 各段（→ setPath("a/b")）
      - "返回上一级" 按钮：path != "" 时显示；click → setPath(path 去掉最后段)
      - entries 行渲染区分 entry_type：
        - type=tree：📁 icon（或 svg）+ `{name}/` + 整行 button onClick → setPath(path ? `${path}/${e.name}` : e.name)；
          不展示 sha256 / 下载按钮；保证可访问性（role="button" + tabIndex + onKeyDown Enter）
        - type=blob：保持现有 Link to /blob/$owner/$name/$hash + sha256 + 下载按钮；
          search.path 记录该 blob 在仓内全路径
      - 头部计数："{entries.length} entries"（含 folder + file 总数）
      - useSubtreeByPath isError：渲染错误 message + "返 root" 按钮 → setPath("")
      - 空 tree（entries.length==0 但非 error）：保留现有"commit 为空 tree"提示
      颗粒度估算：~2.5h（含面包屑组件 + a11y + error UI + 调试）
    depends_on: [T-3a]
    estimated_stage: coding
    covers_ac: [AC-4, AC-5]
    status: pending

  - id: T-4
    title: 单测 vitest 用例 ≥ 4 + 调整现有 legacy 断言
    description: |
      apps/web/src/routes/repos.files-section.test.tsx。
      mock useSearch + useSubtreeByPath（或直接 fetch fixture）。
      新用例：
        a. test_default_root_shows_mixed_entries：root commit 含 type=tree + type=blob → 渲染显 folder icon 与文件
        b. test_click_folder_updates_path：模拟点 folder 行 → setSearch({ path: ... }) 被调
        c. test_breadcrumb_navigate：path != "" 时渲染面包屑 ≥ 2 段；点中间段 → setSearch 回退
        d. test_legacy_flat_commit：useSubtreeByPath 返全 type=blob entries (name 含 /) → 不显面包屑（path == ""）+ 不显 folder icon；正常 link 到 /blob
        e（可选）. test_path_not_found_error：useSubtreeByPath 抛错 → 渲染 error message + "返 root" 按钮
      现有 test_files_section_renders_table 等 legacy 断言：保留并明示是 legacy commit 路径
    depends_on: [T-3b]
    estimated_stage: unit_test
    covers_ac: [AC-6, AC-7, AC-10]
    status: pending

  - id: T-5
    title: scripts/_self_check.sh 加 run_web_tree_nested_ui 11 AC
    description: |
      在 run_tree_nested_domain 后插入 run_web_tree_nested_ui（11 AC，
      不再含 AC-12 自递归——v2 删了，AC-9 兼任）。
      AC-6/7/10 跑 `pnpm --filter web test -- --run`（不依赖 PG/MinIO/Redis）；
      AC-8 跑 pnpm lint + typecheck。
      filter case + 全跑入口 list 都加上。
    depends_on: [T-4]
    estimated_stage: ci_result
    covers_ac: [AC-9]
    status: pending

  - id: T-6
    title: 本地 lint / typecheck / vitest / self_check current 全绿
    description: |
      pnpm --filter web lint && pnpm --filter web typecheck
      cd apps/web && pnpm test -- --run
      bash scripts/_self_check.sh current web-tree-nested-ui-20260520
      bash scripts/_self_check.sh current tree-nested-domain-20260520（不回归）
    depends_on: [T-5]
    estimated_stage: ci_result
    covers_ac: [AC-7, AC-8, AC-10, AC-11]
    status: pending
```

## 阶段任务

```yaml
process_tasks:
  - id: P-spec-review
    estimated_stage: request_analysis_review
    status: pending       # 走完整 reviewer spawn（沿 tree-nested-domain 模式不偏离）
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
    status: pending        # noop（仅前端，无 schema 改动；vite 重 build 即可）
  - id: P-user-confirm
    estimated_stage: user_confirmation
    status: pending
```

## DAG

T-1 → T-2 → T-3a → T-3b → T-4 → T-5 → T-6（无环）

## 验收覆盖

| AC | 任务 |
|---|---|
| AC-1 | T-1 |
| AC-2 | T-1 |
| AC-3 | T-2 |
| AC-4 | T-3a, T-3b |
| AC-5 | T-3b |
| AC-6 | T-4 |
| AC-7 | T-4, T-6 |
| AC-8 | T-6 |
| AC-9 | T-5 |
| AC-10 | T-4, T-6 |
| AC-11 | T-2（path default ""） |
