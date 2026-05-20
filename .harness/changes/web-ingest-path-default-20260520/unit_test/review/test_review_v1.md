---
change_id: web-ingest-path-default-20260520
target: unit_test/test_report_v1.md + apps/web/src/routes/repos.ingest-section.test.tsx
target_version: 1
review_version: 1
reviewer: claude-agent:web-ingest-path-default-20260520-stage4and6-reviewer-v1
reviewed_at: 2026-05-20T12:05:00Z
verdict: APPROVED
---

# Test Review v1

## 检查清单结论（artifact 模式）

### 1. spec 验收标准 → 测试映射完整性

| AC | kind | 测试归宿 | 覆盖判断 |
|---|---|---|---|
| AC-1 | static | self_check AC-1 grep（行 1295-1296）；非 vitest 用例 | ✅ static AC 无需 vitest 用例 |
| AC-3a | behavioral | `repos.ingest-section.test.tsx` 2 个用例 | ✅ 直接覆盖 |
| AC-3b | behavioral | `pnpm test -- --run`（全 33 passed）| ✅ 回归全过 |
| AC-4 | behavioral | `pnpm --filter web typecheck 0 errors` | ✅ |
| AC-5 | static | self_check 自递归 grep | ✅ |

所有 5 个 AC 均有归宿，无漏项。

### 2. 无空跑断言

- 用例 1：`expect(pathInput).toBeInTheDocument()` + `expect(screen.queryByDisplayValue("content/a.pdf")).not.toBeInTheDocument()`——两个有意义断言，正向 + 反向双保险，非空跑。
- 用例 2：`expect(screen.getByDisplayValue("papers/2026/b.pdf")).toBeInTheDocument()`——有意义，验证 updatePath 后状态持久化。

### 3. mock 范围合规性

- mock 整个 `../lib/api/queries` 模块（vi.mock），涵盖 `useEnqueueIngest` / `useUploadBlob`（都返回 `{ mutateAsync: vi.fn(), isPending: false }`）。
- **数据访问层 mock 合规性**：本测试为纯前端组件测试（React + routing），`useEnqueueIngest` / `useUploadBlob` 是前端 React Query hooks，不是服务端 `RepositoryService` / `BlobStore`——`unit-test-write SKILL §质量门禁` 的"禁 mock 数据访问层"指后端 Python 层，此处 mock 合规。
- 未 mock `fetch` 自身，符合 `unit-test-write SKILL §3 TS` "API 调用用 msw 拦截，不要 mock fetch 自身"——本组件测试不触及网络（submit 未触发），此处 fetch 无需拦截，合规。

### 4. 测试名可读性

- `"default path equals filename (no content/ prefix)"`——场景清晰。
- `"user edited path is preserved (not overwritten)"`——场景清晰。
- 符合 `unit-test-write SKILL` "测试名能反映场景" 要求。

### 5. 核心技术问题逐项评估

**Q1：`getByLabelText(/选文件/)` 能命中 `<Input id="ingest-files">` 吗？**

- 代码：`<Label htmlFor="ingest-files">选文件（可多选）</Label>` + `<Input id="ingest-files" ...>`（line 684-690）。
- `@testing-library/react` 的 `getByLabelText` 通过 `htmlFor` → `id` 关联找到 Input，✅ 正确。

**Q2：`Object.defineProperty(fileInput, "files", { value: [file] })` 是否标准做法？**

- JSDOM（vitest/jest 环境）中 `<input type="file">` 的 `files` 属性只读，无法通过 `fileInput.files = ...` 直接赋值；`Object.defineProperty` 覆盖 descriptor 是测试社区的标准 workaround（React Testing Library 文档与众多 vitest/jest 教程均采用此方式）。
- 注意：未传 `configurable: true`——若同一 test（或同一 input 元素实例）内需要第二次 `defineProperty` 同一属性，会抛 `Cannot redefine property`。当前两个 `it` 各自 `renderIngest(...)` 生成独立 DOM 实例，不共享 `fileInput` 对象，不触发该问题。✅ 合规，SHOULD FIX 见下。

**Q3：`getByDisplayValue("a.pdf")` 锚定 path Input value——UI 是 `<span>` 还是 `<Input value={f.path}>`？**

- 代码 line 702-705：`<Input value={f.path} onChange={(e) => updatePath(i, e.target.value) ...>`。
- `f.path` 在 `onFiles` 赋值时为 `f.name`（即 `"a.pdf"`）。
- `getByDisplayValue("a.pdf")` 精准命中该 Input 的 value 属性。
- 旁边的 `<span className="text-gray-500 truncate w-40">{f.file.name}</span>` 显示的是 `f.file.name`，但这是 `<span>` 而非表单控件，`getByDisplayValue` 不会命中 span——无误判风险。✅

**Q4：第 2 个用例（"用户编辑保留"）是否真测了 state machine（updatePath）？**

- 流程：`fireEvent.change(fileInput)` → `onFiles` → `setFiles([{ path: "b.pdf", ... }])`（React state）→ UI 渲染 `<Input value="b.pdf">`。
- `findByDisplayValue("b.pdf")` 等到 React 重渲染后拿到 Input。
- `fireEvent.change(pathInput, { target: { value: "papers/2026/b.pdf" } })` → `onChange` → `updatePath(0, "papers/2026/b.pdf")` → `setFiles` → `{ path: "papers/2026/b.pdf" }`。
- `getByDisplayValue("papers/2026/b.pdf")` 验证 Input value 已更新。
- 这确实走了 `updatePath → setFiles` 的真实 state 路径，非 React internal state 劫持。✅

**Q5：AC-3a JSON reporter banner 剥离（`grep -E "^{"` 能否 catch JSON）？**

- 命令：`pnpm test -- --run --reporter json ... > /tmp/ingest.raw 2>&1 && grep -E "^{" /tmp/ingest.raw > /tmp/ingest.json`。
- vitest `--reporter json` 输出：pnpm banner 行（`> web@...` 等）位于开头且不以 `{` 开头；JSON 报告体是一个单行 `{...}` 以 `{` 开头（vitest JSON reporter 的 `numFailedTests` / `numTotalTests` 字段均在顶层对象）。
- `grep -E "^{"` 精确剥离 banner，结果写入 `/tmp/ingest.json`，python3 `json.load` 解析，✅ 有效。

### 6. 测试文件存在且 vitest 通过

- `test_report_v1.md` 记录：`33 passed (15 files)`（含新 2 用例），`typecheck 0 errors`，`self_check 14/14 PASS`。
- 报告说明本地全通过，符合质量门禁。

## 问题列表

### MUST FIX

无。

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| SHOULD-1 | `repos.ingest-section.test.tsx` line 93 / line 110 | `Object.defineProperty(fileInput, "files", { value: [file] })` 未设 `configurable: true`。当前两 `it` 各自独立 DOM 无问题，但若未来在同一用例内多次模拟文件选择（或同一 input 对象被复用），将报 `Cannot redefine property`，造成难以追查的测试 crash。 | 改为 `Object.defineProperty(fileInput, "files", { value: [file], configurable: true })`，防御性更强，且为社区推荐写法。 |

### NICE TO HAVE

| # | 位置 | 建议 |
|---|---|---|
| NTH-1 | `repos.ingest-section.test.tsx` | 第 2 个用例仅断言正向路径（改后 value = `"papers/2026/b.pdf"`），可补一条反向断言 `expect(screen.queryByDisplayValue("b.pdf")).not.toBeInTheDocument()` 确认旧 value 不残留，但非必须——Input 只有一个 `value`，不存在双值并存问题，当前断言已充分。 |
| NTH-2 | `test_report_v1.md` | AC 映射表未列出测试函数名称（只写了"2 用例"），后续若用例数增加，难以通过报告追溯哪个函数覆盖哪个 AC。建议下次报告加一列"测试函数"。 |

## Verdict

**APPROVED**

MUST FIX = 0。2 个 vitest 用例真实覆盖 AC-3a 的正向（默认 path = filename）和 state machine（updatePath 保留用户编辑）行为；mock 范围合规；JSON reporter banner 剥离逻辑正确；`getByDisplayValue` 锚点与 `<Input value={f.path}>` 精准对应，无误判；反向断言 `queryByDisplayValue("content/a.pdf")` 有效防止前缀回归。SHOULD-1 为防御性改进，不阻塞。

## 复检指引

若 generator 修 SHOULD-1（defineProperty 加 configurable）：
```bash
grep -n "configurable" apps/web/src/routes/repos.ingest-section.test.tsx
# 期望: 2 处 configurable: true

cd apps/web && pnpm test -- --run src/routes/repos.ingest-section.test.tsx
# 期望: 2 passed
```

下一阶段：stage 7 CI（等同于本地 self_check current 全过 + vitest 33 passed 已验证，可直接推进 CI 确认）。
