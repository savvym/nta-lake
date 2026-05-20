---
change_id: web-blob-md-image-resolver-20260520
target: test_report_v1.md
target_version: 1
review_version: 1
reviewer: claude-agent:web-blob-md-image-resolver-20260520-stage4and6-reviewer-v1
reviewed_at: 2026-05-20T00:00:00Z
verdict: REVISION REQUIRED
---

# Test Review v1

## 检查清单结论（artifact 模式）

| 项 | 结论 |
|---|---|
| 每条 spec AC 映射到至少一条具体测试用例 | PASS（AC-6 behavioral ≥6 用例；AC-7/AC-8 self_check 覆盖）|
| 无空跑断言 | PASS |
| mock 范围合理（useSubtreeByPath 属 data access layer，在 UI 层 mock 合规） | PASS |
| 测试名反映场景 | PASS |
| 9 用例 ≥ spec AC-6 要求的 ≥6 | PASS（3 baseline + 3 markdown + 3 helper = 9） |
| mockSubtreeByPath 默认 null + isError:false，isLoading:false | PASS（beforeEach reset 已设） |
| img 查找用 `document.querySelector("img")` 而非 `getByRole("img")` | PASS（alt="" 时 implicit role 非 img；设计正确）|
| helper 单测用 `await import(...)` | PASS（ESM 动态导入；vitest 支持 ESM，无兼容问题）|
| **CustomImage isLoading 分支缺测** | **SHOULD FIX** |
| **`./` 前缀路径缺测** | NICE TO HAVE |
| **leading `/` path + nested mdPath 联合缺测** | NICE TO HAVE |
| **entry 找不到降级分支缺测** | SHOULD FIX |

## 问题列表

### MUST FIX

无

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| SHOULD-1 | `blob.test.tsx`（整体） | `CustomImage` 的 `isLoading` 分支（`subtreeQuery.isLoading = true`）没有测试用例。spec 风险表提到"useSubtreeByPath 异步：CustomImage 渲染时 tree 未到 → 显占位"，代码实现有 `(loading image: {src})` 占位；但测试 beforeEach 默认 `isLoading: false`，没有 loading=true 覆盖路径。该分支在用户感知上（MinerU 大 paper.md 首次加载闪烁）有实际影响。 | 新增一条测试：`mockSubtreeByPath.mockReturnValue({ data: null, isLoading: true, isError: false, error: null })`，渲染含图片 md + commit，切换 Rendered，断言 `screen.getByText(/loading image:/)` 存在，且 `document.querySelector("img")` 为 null（或 src 不含 blobs）。 |
| SHOULD-2 | `blob.test.tsx`（整体） | `isError` / entry 找不到（找不到 `a.jpg` entry）降级路径无专项测试用例。spec 中"commit 缺"走一种降级，但"tree 存在但 entry 不在 entries 里"是另一种可独立验证的分支（code review SHOULD-1 也指出该分支的渲染行为有待改进）。 | 新增：`mockSubtreeByPath` 返回有 `data.entries` 但 entries 里无目标文件名的 response，断言 `(找不到 ...)` 文字提示出现。 |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| NTH-1 | `blob.test.tsx` helper 单测 | `resolveImagePath("paper.md", "./images/a.jpg")` 未测（`./` 前缀路径）。代码实现正确（`resolveRelative` 跳 `.` 段），但未有显式用例保护。 | 在 helper 单测加一条 `expect(resolveImagePath("a/b.md", "./c.jpg")).toBe("a/c.jpg")`。 |
| NTH-2 | `blob.test.tsx` helper 单测 | leading `/` 且 mdPath 为嵌套路径组合（如 `resolveImagePath("papers/2026/a.md", "/top.jpg")`）未测：期望 `"top.jpg"`（仓根绝对）。当前只测 `leading / → 仓根绝对路径` 用 `paper.md`（根 md），嵌套路径下同样 pass，但无用例验证。 | 加一条 `expect(resolveImagePath("papers/2026/a.md", "/top.jpg")).toBe("top.jpg")`。 |
| NTH-3 | `blob.test.tsx` 行为测试 | md image `../` 上跳相对路径在真实渲染里（有 commit）缺集成测试用例（helper 单测只验 resolveImagePath 返回值，未验端到端 useSubtreeByPath 被调用时 dir 参数是否正确）。 | 可在后续 stage 6 补；优先级低。 |

## Verdict

**REVISION REQUIRED**

SHOULD-1（isLoading 分支缺测）与 SHOULD-2（entry 找不到降级缺测）是规约层 SHOULD FIX：spec §风险 "useSubtreeByPath 异步 → 显占位" 明确要求实现了 isLoading 路径，测试未覆盖，review 按 SHOULD FIX 标记。若 generator 在 summary.md 声明 deferred 并给出跟进理由，可在 generator 显式 deferred 记录后视为条件通过；否则建议补测后再进 stage 7/8。

MUST FIX 数：0。

> 注意：code review v1 有 MUST FIX-1（旧 self_check AC-4 兼容性），需 generator 修复 `scripts/_self_check.sh` 后连带重跑 vitest，确认 test report 声称的 39 passed 仍 PASS。

## 复检指引

Generator 修完后自查命令：

```bash
# 1. 确认新增 isLoading 用例存在
grep -n "isLoading.*true\|loading image" apps/web/src/routes/blob.test.tsx

# 2. 确认新增 entry 找不到用例存在
grep -n "找不到\|entry.*[]\|entries.*\[\]" apps/web/src/routes/blob.test.tsx

# 3. 跑 blob.test.tsx，确认 numTotalTests ≥ 8（两条 SHOULD 补上后 9+2=11，或维持 9 但 deferred 声明）
cd apps/web && pnpm test -- --run --reporter json src/routes/blob.test.tsx > /tmp/blob2.raw 2>&1
grep -E '^{' /tmp/blob2.raw > /tmp/blob2.json
python3 -c "import json; d=json.load(open('/tmp/blob2.json')); print('total:', d['numTotalTests'], 'fail:', d['numFailedTests'])"

# 4. 全量 vitest
cd apps/web && pnpm test -- --run 2>&1 | tail -5
```

SHOULD-1/2 关闭判据（可选 deferred）：blob.test.tsx 新增 ≥2 条覆盖 isLoading / entry-miss 分支的用例，全 PASS；或 summary.md 显式记录 "SHOULD-1/2 deferred → followup test-coverage-20260521"。
