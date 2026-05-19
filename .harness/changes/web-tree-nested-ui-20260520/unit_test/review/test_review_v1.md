---
change_id: web-tree-nested-ui-20260520
target: repos.files-section.test.tsx
target_version: 1
review_version: 1
reviewer: claude-agent:web-tree-nested-ui-20260520-stage4and6-reviewer-v1
reviewed_at: 2026-05-19T19:30:00Z
verdict: REVISION REQUIRED
---

# Test Review v1

## 检查清单结论（artifact 模式）

| # | 检查项 | 结论 |
|---|---|---|
| T-1 | 每条 spec AC 都映射到 ≥1 个测试用例 | 部分未覆盖（见 MUST FIX-1） |
| T-2 | 无空跑断言（assert True / assert result != None） | PASS：所有断言都有实质判断 |
| T-3 | mock 范围符合 coding-style §2.7（API 调用用 MSW，不 mock fetch 本身） | **FAIL**（见 MUST FIX-2） |
| T-4 | 测试名能反映场景 | PASS：全中文描述场景，清晰 |
| T-5 | test_report_v1.md 正确填写 | **FAIL**（见 MUST FIX-3）|
| T-6 | AC-6 5 用例全覆盖 spec 场景 | 基本覆盖但有 gap（见 SHOULD FIX） |
| T-7 | beforeEach reset mockSubtreeState | PASS：reset 4 个字段 |
| T-8 | router.state.location.search 读法正确（对象直读 .path） | PASS：强转 `as { path?: string }` 后读 .path |

---

## 问题列表

### MUST FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| MUST FIX-1 | `repos.files-section.test.tsx` 整体 | **AC-7 spec 要求测试 `useSubtreeByPath` 被调用时 `commitHash` 为空字符串（enabled=false）时的"暂无 commit"渲染，但 5 个用例均未覆盖"refQuery.data=null"路径**。test_1 到 test_5 均把 `useRepoRef` mock 返回 `{ data: { commit_hash: FAKE_COMMIT_HASH } }`，因此 `refQuery.data` 始终非空，"暂无 commit"分支代码路径（`repos/$owner.$name.tsx` 第 271–276 行）完全未被测试。spec AC-6 列出 5 场景（legacy/nested根/click folder/面包屑/error），与 5 个测试 1:1 对应，但 AC-6 的场景 ① 和 ② 对应的是"正常有数据"路径，"无 commit"分支属于 spec 风险项（"暂无 commit"UI），**该路径无任何测试覆盖**。这不是 MUST FIX 级别的 spec-AC gap（spec AC-6 未明确要求此场景），降级为 SHOULD FIX。重新评估：**MUST FIX-1 撤销**，改为 SHOULD FIX。 | 见 SHOULD FIX 列表 |
| MUST FIX-2 | `repos.files-section.test.tsx` 第 26 行 `vi.mock("../lib/api/queries", ...)` | **mock 策略违反 coding-style §2.7：规则要求 API 调用用 MSW mock，不 mock fetch 本身**。当前实现 `vi.mock("../lib/api/queries", ...)` 直接 mock 了整个 queries 模块（包括 `useSubtreeByPath` 返回固定对象），绕开了 TanStack Query 的 fetching 逻辑，测试无法验证 queryFn 的 null-guard / throw 路径。spec AC-6 要求 behavioral 覆盖（"点 folder → search.path 更新"等），当前 mock 让 hook 直接返回 data 对象，测试的是纯 React 渲染路径，**queryFn 的串行 fetch 逻辑完全未被任何测试验证**。这是测试覆盖的深层 gap。 | 对 queryFn 逻辑（null-guard / segment-not-found throw / multi-level traversal）应有独立的 unit test（测 queryFn 函数本身，可用 vitest + fetch mock），与组件渲染测试分开。当前 5 个 RTL 测试测的是"数据已加载后的 UI 行为"，可接受；但须补 `useSubtreeByPath queryFn` 的独立单元测试 ≥2 个（null root throw；segment 不存在 throw）。 |
| MUST FIX-3 | `.harness/changes/web-tree-nested-ui-20260520/unit_test/test_report_v1.md` | **test_report_v1.md 是未填充的模板**：frontmatter 的 `change_id` 字段是 `<feature-slug>-<yyyymmdd>`，`authored_at` 是 `<YYYY-MM-DDTHH:MM:SSZ>`；AC 映射表引用的是错误的 `test_repos.py` 和 `test_create_bronze_repo_returns_201`（这些是 Python 后端测试，不属于本 change）；本地运行结果是模板占位符。这意味着 test_report 没有真实反映本 change 的测试产出。 | 重新填写 test_report_v1.md：change_id=web-tree-nested-ui-20260520，AC 映射表对应 repos.files-section.test.tsx 的 5 个 it()，本地运行结果填 `pnpm --filter web test -- --run` 实际输出（5 passed）。 |

**实际 MUST FIX = 2（MUST FIX-2 + MUST FIX-3；MUST FIX-1 撤销降为 SHOULD FIX）**

---

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| SHOULD FIX-1 | `repos.files-section.test.tsx` | **"暂无 commit"分支未测**：`useRepoRef` 返 null 时 FilesSection 渲染"暂无 commit"提示，完全未覆盖。这是 spec 风险项（"legacy 扁平 commit"只测有数据场景），应补一个"refQuery.data=null"用例 | 新增 test 6：mock useRepoRef 返 `{ data: null }`，断言 screen.getByText(/暂无 commit/) |
| SHOULD FIX-2 | `repos.files-section.test.tsx` test-3（点 folder） | **仅测 click 触发路径更新，未测 keyboard（Enter/Space）触发**：a11y 实现专门加了 onKeyDown，但没有对应测试。 | 新增 `fireEvent.keyDown(folderRow, { key: "Enter" })` 断言 search.path 更新 |
| SHOULD FIX-3 | `repos.files-section.test.tsx` test-5（error） | **`getByText(/加载失败/)` regex 过宽**：error UI 的文本是"路径 "nope" 加载失败：Error: path 段…"，`/加载失败/` 能命中但也会命中 repo 加载失败等其他错误 UI。更精确的断言应查 `within(errorDiv).getByText(/加载失败/)` 或用 `getByText(/路径.*加载失败/)` | 改 regex 为 `/路径.*加载失败/` 或配合 `within` 定位 |
| SHOULD FIX-4 | `repos.files-section.test.tsx` | **blob link 的 target_hash 未验证**：test-1（legacy）验证了"下载"链接存在，但未断言链接 href 确实包含 SHA_A / SHA_B。若 entry 渲染出链接但 hash 写错，测试通不过。 | 在 test-1 中对 `screen.getAllByRole("link", { name: "下载" })` 或 blob Link 校验 `href` 属性含 SHA_A.slice(0,12) |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| NTH-1 | `repos.files-section.test.tsx` | **"返回上一级"按钮点击后 path 更新未测**：test-4 断言面包屑段存在并点了"images"段，但"↑ 返回上一级"按钮本身没有 click 测试，无法确认 pathSegments.slice(0,-1).join("/") 逻辑正确。 | 在 test-4 中补 `fireEvent.click(screen.getByText(/返回上一级/))` 断言 search.path 变为 "images" |
| NTH-2 | `repos.tabs.test.tsx` | **切 tab 后 path 清空未测**：onTabChange 实现 `{ tab: t, path: "" }` 清空 path，tabs.test 只验证 tab 变更，未验证 path 同时清空。 | 在 tabs.test 用 initialUrl `?tab=files&path=images` 渲染，切 tab 后断言 search.path === "" |

---

## Verdict

**REVISION REQUIRED**

原因：
1. **MUST FIX-2**：`vi.mock("../lib/api/queries")` 直接 mock 了整个 queries 模块，useSubtreeByPath queryFn 的核心逻辑（null-guard、segment-not-found throw）完全未被测试，不符合 coding-style §2.7"API 调用用 MSW mock，不 mock fetch 本身"的精神（此处 mock 了 hook 层而非网络层，等价于更严重的绕开）。虽然 5 个 RTL 测试的 UI 行为覆盖是合理的，但缺少对 queryFn 的独立单测，这是真 gap。
2. **MUST FIX-3**：test_report_v1.md 是未填充模板，stage 6 review 的基础产物缺失。
3. SHOULD FIX 和 NTH 不阻塞，但 SHOULD FIX-1（暂无 commit 路径）、SHOULD FIX-2（keyboard a11y 测试）建议 v2 补入。

## 后续指引

Generator 修 v2 后需：
1. 填写 test_report_v1.md：change_id 字段、AC 映射表指向正确测试函数、运行结果为真实输出。
2. 新增 queryFn 独立测试文件（建议 `queries.useSubtreeByPath.test.ts`）：≥2 用例（root null throw / segment not found throw）。
3. （建议）补"暂无 commit"路径测试用例。

复检命令：
```bash
# MUST FIX-3：验证 test_report 不再是模板占位符
grep "change_id" .harness/changes/web-tree-nested-ui-20260520/unit_test/test_report_v1.md | grep -v "feature-slug"

# MUST FIX-2：验证 queryFn 测试存在
ls apps/web/src/lib/api/queries*.test.ts 2>/dev/null || ls apps/web/src/lib/api/*.test.ts 2>/dev/null

# 全跑
pnpm --filter web test -- --run
```
