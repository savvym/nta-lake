---
change_id: pipeline-ui-tab-20260518
target: unit_test/test_report_v1.md
target_version: 1
review_version: 1
reviewer: claude-agent:pipeline-ui-tab-20260518-stage6-reviewer-v1
reviewed_at: 2026-05-18T12:07:30Z
verdict: APPROVED
---

# Test Review v1（artifact 模式）

## 真跑验证（reviewer 独立执行）

```text
$ cd apps/web && npx vitest run src/lib/api/pipeline.test.tsx src/routes/repos.pipelines-section.test.tsx
 ✓ src/routes/repos.pipelines-section.test.tsx (2 tests) 386ms
   ✓ PipelinesSection > disables run button when yaml is empty and enables when filled; click triggers mutation 358ms
   ✓ PipelinesSection > renders node table with 2 rows when run.status=succeeded
 ✓ src/lib/api/pipeline.test.tsx (2 tests) 2083ms
   ✓ usePipelineRun > polls until status reaches succeeded 2077ms
   ✓ useCreatePipelineRun > POSTs yaml with text/yaml content-type and returns run_id

 Test Files  2 passed (2)
      Tests  4 passed (4)
   Start at  20:06:34
   Duration  3.16s
```

- 4/4 PASS，独立复跑确认 test_report 数字真实。
- 总耗时 3.16s（hook 2.08s + 组件 0.39s + setup/transform/env ~0.7s）；hook 文件慢是因 usePipelineRun 真等 ≥1 次 1000ms refetchInterval 才能从 queued → running → succeeded。
- 控制台一个 `act(...)` warning（PipelinesSection 内部 mutateAsync 异步 setActiveRunId 未包 act），不阻塞断言；测试仍稳定 PASS。

## 检查清单结论（artifact 模式 §1.7）

| 项 | 结论 | 证据 |
|---|---|---|
| 每条 spec AC 映射到具体测试用例 | ✓ | AC-1/AC-2 静态由 self_check `run_pipeline_ui_tab` grep；AC-3 由 vitest 4 项；AC-4 由 `npm run build`（stage 9 验） |
| 没有空跑断言（`assert True` / `!= None`） | ✓ | 4 测试断言都有真实 value（`toBe("succeeded")` / `toBe("text/yaml")` / `toHaveBeenCalledWith(...)` / `findByText("normalize")`） |
| mock 范围符合 coding-style §1.7 / `unit-test-write` SKILL | ✓ | hook 测试仅 spy `globalThis.fetch`（入口层）；组件测试仅 `vi.mock("../lib/api/queries")`（入口 hook 层），组件本体 + DOM + Card/Button/Textarea/Table 真渲染。无数据访问层 mock |
| 测试名能反映场景 | ✓ | "polls until status reaches succeeded" / "POSTs yaml with text/yaml content-type and returns run_id" / "disables run button when yaml is empty and enables when filled; click triggers mutation" / "renders node table with 2 rows when run.status=succeeded"——均场景化 |
| 真跑命令落地（reviewer 独立复跑） | ✓ | 见本节顶部 |
| behavioral AC 真有行为断言（非 grep） | ✓ | AC-3 vitest 真渲染 + 真 fetch spy + 真 fireEvent；AC-4 vite build 真编译 |

## 重点核查（任务点 a/b/c）

### (a) Hook 测试 spy fetch 行为可信吗

- **fake timer 没用**：实读 `pipeline.test.tsx` 没有 `vi.useFakeTimers()`；用真 timer + `waitFor({ timeout: 5000 })` 等 TanStack v5 默认 refetchInterval=1000ms 真实推进 → fetch 被自然调到第 3 次返 succeeded。
- **响应序列触发轮询**：`responses[Math.min(callCount, responses.length-1)]` callCount 单调递增 + Math.min 兜底；fetchSpy 调用 ≥2 是 strict 断言，证明至少经过 queued→running 一次轮询 + 拿到 succeeded 一次（实际 callCount≥3）。可信。
- **refetchInterval callback 真停止？** 这是关键漏测点：测试仅等到 `data?.status === "succeeded"` 后立刻断言 fetchSpy ≥2 退出；**没断言此后 fetch 不再被调**。理想做法是 succeeded 后 `await new Promise(r => setTimeout(r, 1500))` 再断言 `fetchSpy.mock.calls.length` 不增长。当前测试无法防范"refetchInterval 错误返 1000 而非 false"的回归。**降一档 SHOULD FIX**（不阻塞，因 hook 实现已读、callback 内 `data.status === "succeeded" || "failed" → return false` 静态正确；regression risk 由 npm run build tsc 守门 + AC-1 grep `refetchInterval` 文字守门，仅是不进入运行期行为断言）。

### (b) 组件测试 mock 边界

- `vi.mock("../lib/api/queries", () => ({ useCreatePipelineRun: () => ..., usePipelineRun: () => ... }))` 整模块 mock 是 vitest hoisting-safe 模式，与既有 `apps/web/src/routes/repos.test.tsx` 一致；reviewer 实读后者证实同 pattern。
- 默认 `mockRunData.mockReturnValue(undefined)` 在 beforeEach 设定 → 等价 activeRunId=null（query 未启）状态，自然覆盖"未运行 pipeline"分支，避免污染 button disabled/enabled 测试。合理。
- 边界：仅 mock 这 2 个 hook，**没 mock `useViewerSession` / `useRepoDetail`**——本组件不依赖（只接 `owner, name` props，且函数内 `void owner; void name`），不会触发其他 hook，所以 mock 范围正确。

### (c) Run 面板节点表 5 列覆盖

实读 `$owner.$name.tsx:687-704` 节点表 5 列 = `node` / `processor` / `status` / `cache` / `output_commit`。组件测试断言覆盖：

| 列 | 测试断言 | 是否覆盖 |
|---|---|---|
| `node` (node_id 文本) | `findByText("normalize")` + `getByText("qa_gen")` | ✓ |
| `processor` (`processor_name@processor_version`) | `getByText(/markdown-normalize@0.1/)` + `getByText(/llm-qa-gen@0.1/)` | ✓ |
| `status` 文字 | `getAllByText("succeeded").length >= 2`（含 2 行节点 status） | ✓（文字） |
| `status` 颜色 className（green/red/blue） | 无 | ✗（漏） |
| `cache_hit` → "hit" / "miss" 显示 | 无 `getByText("hit")` / "miss" 断言 | ✗（漏） |
| `output_commit_hash` 截 12 字符显示 | 无 `getByText(/aaaaaaaaaaaa…/)` / "—" 断言 | ✗（漏） |

3 列被"提到 mock 数据里但没断言显示"——见 SHOULD FIX-2。

## 问题列表

### MUST FIX

无。所有 spec AC（4 项）都映射到真跑测试，没有空跑断言，mock 范围合规，4/4 PASS 真复现，npm run build 在 stage 9 真验，behavioral 自约束 ≥1 满足。

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| SHOULD-1 | `pipeline.test.tsx::usePipelineRun > polls until status reaches succeeded` | succeeded 后未断言 refetchInterval 真停止——无法防范"callback 错误返 1000 而非 false"的回归 | 测试结尾增加：`const finalCount = fetchSpy.mock.calls.length; await new Promise(r => setTimeout(r, 1500)); expect(fetchSpy.mock.calls.length).toBe(finalCount);` 显式断言停止轮询 |
| SHOULD-2 | `repos.pipelines-section.test.tsx::renders node table with 2 rows when run.status=succeeded` | 节点表 5 列中 3 列（`cache_hit`→hit/miss、`output_commit_hash` 截 12 字符、status 颜色 className）只提供 mock 数据但未断言渲染结果——回归不安全 | 增加：`expect(screen.getByText("hit")).toBeInTheDocument(); expect(screen.getByText("miss")).toBeInTheDocument(); expect(screen.getByText(/aaaaaaaaaaaa…/)).toBeInTheDocument();` |
| SHOULD-3 | 两个测试文件 | 测试覆盖缺 5 个边界分支：(1) status="failed" 走 red badge + red 文字；(2) run.error <pre> 块显示；(3) node_runs.length===0 时表不渲染；(4) output_commit_hash=null 显示 "—"；(5) mutateAsync 失败 setError 文案 | 至少补 1 条 failed 路径用例（mockRunData 返 `{status:"failed", error:"oops", node_runs:[]}` → 断言 "failed" 文字 + "oops" 出现 + 表不渲染） |
| SHOULD-4 | `repos.pipelines-section.test.tsx::disables run button...` | `fireEvent.click(button)` 后 mutateAsync 异步 setActiveRunId 未包 `act(...)` → 控制台 warning。当前测试通过仅因后续断言不依赖 activeRunId state | 包 `await act(async () => { fireEvent.click(button); })` 或用 `userEvent.click`（已内置 act）。修后 warning 消失，测试更稳 |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| NICE-1 | `pipeline.test.tsx::useCreatePipelineRun` | `captured!` 非空断言；可改用类型守卫更类型安全 | 改 `if (!captured) throw new Error("fetch not called");` 后用 captured.url 等。微调，不阻塞 |
| NICE-2 | test_report_v1.md "测试文件清单"行 `用例数` | hook 文件标 2 但 describe 数 2、it 数 2；OK。组件文件标 2 也正确 | 无操作 |
| NICE-3 | test_report_v1.md "覆盖维度"表 | "组件 Run 状态面板 2 节点表渲染 ✓" 把 cache_hit/output_commit_hash/status 颜色一起算覆盖；与本 review SHOULD-2 现状有偏差 | follow-up 补完 SHOULD-2 后再回填表准确性 |

## 性能/资源评估

- vitest 2 文件 4 测试 3.16s（hook 2.08s + 组件 0.39s + setup 0.7s）合理：hook 文件 2s 是真等 ≥2 次 1000ms refetchInterval 的下限（不可压缩，除非引 fake timer）；组件文件 390ms 与 repos 既有测试同量级。
- 无文件 I/O、无 docker、无后端连接；纯 jsdom + spy。CI 资源开销极低。
- 单 PASS 测试 ≤ 2.1s，远低于 vitest 默认 5000ms timeout；hook 测试显式设 timeout=10000ms / waitFor timeout=5000ms 是合理冗余。

## Verdict

**APPROVED**。

理由：
1. 真跑 vitest 独立复现 4/4 PASS（本 reviewer 第 2 次跑，3.16s）。
2. 4 条 spec AC 全部映射到具体测试用例：AC-1/AC-2 self_check grep 在 stage 9 守门；AC-3 vitest 4 项真行为；AC-4 npm run build 在 stage 9 stage 收口。
3. Mock 范围严格合规：hook 测试只 spy fetch（入口层），组件测试只 mock queries 模块（入口层）；无数据访问 / 业务层 mock。
4. Behavioral AC（AC-3 + AC-4）满足 ≥1 自约束。
5. SHOULD FIX 4 项都是"覆盖深度可加强"——属于 stage 5 测试质量持续改进，不构成阻塞下一阶段的根本缺陷；按 SKILL §2 "verdict 唯一判据：是否还有未关闭的 MUST FIX" 应放行。

## 后续指引

- **APPROVED** → 进入 stage 7（代码推送）/ stage 9（部署验证）。
- **SHOULD FIX 处置**：若在 stage 7 commit 前修补 SHOULD-1/2/3/4 → 直接补到现有 `pipeline.test.tsx` / `repos.pipelines-section.test.tsx` 然后 stage 5 出 v2 test_report；若延后 → 必须在 `summary.md` "Deferred 项" 显式列出 SHOULD-1..4 + 关联到 follow-up（建议合并到 `pipeline-ui-recipe-editor-*` 或新开 `pipeline-ui-test-coverage-strengthen-*`）。
- **复检指引（如 generator 修后想自检 v2）**：
  1. `cd apps/web && npx vitest run src/lib/api/pipeline.test.tsx src/routes/repos.pipelines-section.test.tsx 2>&1 | tail -10` → 期望 `Tests  ≥4 passed`（修 SHOULD 后可能涨到 6+）
  2. 控制台无 `act(...)` warning（修 SHOULD-4 后）
  3. 节点表 5 列全部有 `expect(screen.getByText(...))` 断言（修 SHOULD-2 后 grep `cache_hit` / `hit` / `miss` 在测试文件中至少各 1 次）
  4. failed 路径有专门 it 块（修 SHOULD-3 后 grep `failed` 在 test 文件中 ≥ 2 次）
