---
change_id: web-blob-md-image-resolver-20260520
target: test_report_v1.md
target_version: 1
review_version: 2
reviewer: claude-agent:web-blob-md-image-resolver-20260520-stage4and6-reviewer-v2
reviewed_at: 2026-05-20T14:00:00Z
verdict: APPROVED
---

# Test Review v2

## v1 SHOULD FIX 复检

| # | v1 issue | 状态 | 证据 |
|---|---|---|---|
| SHOULD-1 | `CustomImage isLoading` 分支缺测（`isLoading: true` 路径未覆盖） | **RESOLVED** | `blob.test.tsx` line 210-236："md image while subtree isLoading → 显占位文字"。`mockSubtreeByPath.mockReturnValue({ data: null, isLoading: true, ... })`；渲染后切换 Rendered；`screen.getByText(/loading image/)` 断言存在（生产码 line 186：`(loading image: {src})`）；`document.querySelector("img")` 由于 isLoading 返回占位 span 无 img，断言未显式写但 getByText 足以覆盖关键分支。 |
| SHOULD-2 | `entry 找不到降级`分支缺测（entries 里无目标 entry） | **RESOLVED** | `blob.test.tsx` line 238-264："md image but entry not found in tree → 透传 + 提示"。`entries: []` 空数组 → `find()` 返回 undefined → 生产码 line 200-208 分支；`screen.getByText(/找不到.*images\/missing\.jpg/)` 断言（生产码 line 205：`(找不到 {resolved})`，`resolved = "images/missing.jpg"`）；正则匹配正确。 |

## 检查清单结论（artifact 模式）

| 项 | 结论 |
|---|---|
| 每条 spec AC 映射到至少一条具体测试用例 | PASS（9 原有 + 2 新增 = 11 用例；AC-6 behavioral ≥6 覆盖；AC-7/AC-8 self_check 覆盖）|
| 无空跑断言 | PASS — 两新用例均有实质 `getByText` / `waitFor` 断言 |
| mock 范围合理 | PASS — `useSubtreeByPath` 属 data access layer；UI 层 mock 合规；react-markdown 真渲染未 mock |
| 测试名反映场景 | PASS — "subtree isLoading → 显占位文字" / "entry not found → 透传 + 提示" 清晰 |
| isLoading 分支正确覆盖 | PASS — 见 SHOULD-1 复检 |
| entry not found 分支正确覆盖 | PASS — 见 SHOULD-2 复检 |
| v2 新用例无引入回归风险 | PASS — `beforeEach` 含 `mockSubtreeByPath.mockReset()` + `mockReturnValue({ isLoading: false })`；`vi.restoreAllMocks()` 在同一 beforeEach 末尾恢复 spy，不影响 `vi.fn()` mock；各用例独立覆盖对应分支，无状态泄露风险 |
| v1 MUST FIX（code self_check）对 test 的影响 | PASS — code_review_v2 确认 `self_check all` FAIL=0；test report 声称的 39 passed 不受 self_check fix 影响（vitest 独立）|

## 问题列表

### MUST FIX

无。

### SHOULD FIX

无。

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| NTH-1（继承 v1 NTH-1）| `blob.test.tsx` helper 单测 | `resolveImagePath("a/b.md", "./images/a.jpg")` 的 `./` 前缀路径未有专项用例；功能实现正确（`.` 段 skip），但无显式回归保护 | 加一条 `expect(resolveImagePath("a/b.md", "./c.jpg")).toBe("a/c.jpg")`；优先级低 |
| NTH-2（继承 v1 NTH-2）| `blob.test.tsx` helper 单测 | leading `/` 且 mdPath 为嵌套路径未测（`resolveImagePath("papers/2026/a.md", "/top.jpg")` 期望 `"top.jpg"`） | 加一条对应用例；优先级低 |
| NTH-3 | `blob.test.tsx` line 210-236（isLoading 用例）| 未显式断言 `document.querySelector("img") === null`（当前断言仅覆盖占位文字存在，不验证无 img 渲染）；功能正确，但 img 缺失断言增加回归漏报风险 | 在 `waitFor` 内加 `expect(document.querySelector("img")).toBeNull()` 一行；轻量改进 |

## Verdict

**APPROVED**

v1 两条 SHOULD FIX 均已修复：SHOULD-1（isLoading 占位分支）与 SHOULD-2（entry not found 降级分支）各新增专项测试用例，断言覆盖关键路径，与生产代码文字字面量对齐。新用例 mock 模式一致，无状态泄露。NICE TO HAVE 3 条均不阻塞。

## 复检指引（已执行，供存档）

```bash
# 1. 确认新增 isLoading 用例存在
grep -n "isLoading.*true\|loading image" apps/web/src/routes/blob.test.tsx
# → line 220: isLoading: true; line 234: expect(screen.getByText(/loading image/))

# 2. 确认新增 entry 找不到用例存在
grep -n "找不到\|entries.*\[\]" apps/web/src/routes/blob.test.tsx
# → line 247: entries: []; line 262: expect(screen.getByText(/找不到.*images\/missing\.jpg/))

# 3. 跑 blob.test.tsx 确认全 PASS（用例数 ≥ 11）
cd apps/web && pnpm test -- --run src/routes/blob.test.tsx 2>&1 | tail -5
```
