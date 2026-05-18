---
change_id: pipeline-ui-tab-20260518
version: 1
authored_at: 2026-05-18T12:55:00Z
status: waiting_review
---

# Test Report v1

> 测试在 stage 3 已落地（vitest 4 测试 + self_check block）；stage 5 汇总。

## 验收项 ↔ 测试映射

| AC ID | kind | 测试形态 | 测试位置 | 测试函数 |
|---|---|---|---|---|
| AC-1 | static | self_check grep | `scripts/_self_check.sh::run_pipeline_ui_tab` | `run_ac AC-1`：5 独立 grep（awk 锁定 useCreatePipelineRun + usePipelineRun 函数体 + 3 interface 字面） |
| AC-2 | static | self_check grep | 同上 | `run_ac AC-2`：4 独立 grep（PipelinesSection 函数 + isAdmin gate + 2 hook 引用） |
| AC-3 | **behavioral** | vitest 真跑（spyOn fetch + vi.mock module 两种模式协同） | `apps/web/src/lib/api/pipeline.test.tsx` + `apps/web/src/routes/repos.pipelines-section.test.tsx` | 4 测试：(a) usePipelineRun 状态机 / (b) useCreatePipelineRun POST yaml / (c) PipelinesSection button disabled→enabled→click / (d) 节点表 2 行渲染 |
| AC-4 | **behavioral** | npm run build（vite + tsc --noEmit） | `apps/web/package.json::scripts.build` | 真跑 `npm run build`，检查 `built in` + 不含 `error TS` |

每条 AC 至少一个测试。**behavioral AC：AC-3 + AC-4**，满足 ≥1 自约束。

## 测试文件清单

| 文件 | 类型 | 用例数 |
|---|---|---|
| `apps/web/src/lib/api/pipeline.test.tsx` | vitest hook（spyOn fetch） | 2 |
| `apps/web/src/routes/repos.pipelines-section.test.tsx` | vitest 组件（vi.mock module） | 2 |
| `scripts/_self_check.sh::run_pipeline_ui_tab` | self_check block | 4 AC |

## Mock 范围声明

- **允许 mock**：
  - hook 测试用 `vi.spyOn(globalThis, "fetch")` 模拟 HTTP 响应序列（queued/running/succeeded）—— 真路径调用，仅入口 fetch mock；TanStack QueryClient + renderHook 真渲染
  - 组件测试用 `vi.mock("../lib/api/queries", ...)` mock 整个 hook 模块；组件本身真渲染（fireEvent + testing-library）
- **禁止 mock**：
  - React 渲染 / TanStack QueryClient（hook 测试真用）
  - PipelinesSection 组件本身 / DOM 交互 / React 状态

## 测试真跑证据

### vitest 4 测试全 PASS

```text
$ cd apps/web && npx vitest run src/lib/api/pipeline.test.tsx src/routes/repos.pipelines-section.test.tsx
 ✓ src/routes/repos.pipelines-section.test.tsx (2 tests) 390ms
   ✓ PipelinesSection > disables run button when yaml is empty and enables when filled; click triggers mutation
   ✓ PipelinesSection > renders node table with 2 rows when run.status=succeeded
 ✓ src/lib/api/pipeline.test.tsx (2 tests) 2080ms
   ✓ usePipelineRun > polls until status reaches succeeded
   ✓ useCreatePipelineRun > POSTs yaml with text/yaml content-type and returns run_id

 Test Files  2 passed (2)
      Tests  4 passed (4)
```

### npm run build 干净

```text
$ cd apps/web && npm run build
vite v5.4.21 building for production...
✓ 267 modules transformed.
✓ built in 2.30s
（tsc --noEmit 0 error）
```

## 覆盖维度

| 维度 | 是否覆盖 | 备注 |
|---|---|---|
| Hook 轮询状态机（queued → running → succeeded → 停止）| ✓ | `usePipelineRun` 真跑 fetch spy 序列；fetch 调用 ≥ 2 次 |
| Hook POST yaml 含 Content-Type | ✓ | spy captured headers `text/yaml` |
| 组件 button disabled / enabled 切换 | ✓ | fireEvent.change(textarea) 触发状态变化 |
| 组件 click → mutation 触发 | ✓ | mockMutateAsync 被调断言 |
| 组件 Run 状态面板 2 节点表渲染 | ✓ | normalize + qa_gen 都 in document |
| 生产构建（vite + tsc）类型对齐 | ✓ | npm run build 0 error TS |
| Nullable 字段 TS 类型对齐后端 schema | ✓ | stage 4 reviewer 真读 4 字段对齐 |

## 已知未解决问题

无（4/4 测试 PASS + tsc 0 error）。

## 下一步

- 准备 stage 6 review：spawn `claude-agent:pipeline-ui-tab-20260518-stage6-reviewer-v1`
