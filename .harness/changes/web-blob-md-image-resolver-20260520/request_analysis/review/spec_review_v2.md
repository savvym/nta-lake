---
change_id: web-blob-md-image-resolver-20260520
target: request_analysis/spec.md
target_version: 2
review_version: 2
reviewer: claude-agent:web-blob-md-image-resolver-20260520-stage2-reviewer-v2
reviewed_at: 2026-05-20T15:00:00Z
verdict: APPROVED
---

# Spec Review v2

## v1 MUST FIX 复检

| # | v1 issue | 状态 | 证据 |
|---|---|---|---|
| MUST FIX-1 | AC-2 grep 过宽，不锚定 validateSearch 字段声明 | RESOLVED | v2 AC-2 改为 `grep -qE 'commit\?:\s*z\.string\(\)\|commit\?:\s*string' apps/web/src/routes/blob.\$owner.\$name.\$hash.tsx`，锚定 zod 字段语法，不再泛匹配任意 "commit" 字符串 |
| MUST FIX-2 | AC-5 缺 URL 重写断言（`/blobs/` 路径模板未验证） | RESOLVED | v2 AC-5 改为双锚：`grep -q "useSubtreeByPath" ... && grep -qE "/api/repos/.*blobs/" ...`，明确验证 blob URL 重写逻辑写在 blob 路由文件中 |
| MUST FIX-3 | AC-6 baseline 已 3，`numTotalTests ≥ 3` 对新用例零保护 | RESOLVED | v2 AC-6 改为 `numTotalTests ≥ 6`（baseline 3 + 新增 ≥ 3），python3 断言已更新；spec § "AC-6 完整命令" 注释也已同步 |
| MUST FIX-4 | resolveRelative leading "/" 行为语义模糊（拒绝 vs fallback vs 仓根解析） | RESOLVED | v2 AC-5 描述明确：`/` 开头视为"仓根绝对路径"，去掉 leading `/` 后用 useSubtreeByPath 解析，不 fallback；三种路径模式（绝对 URL / 仓根绝对 / 相对）均有明确处理 |

## 检查清单结论

| 项 | 结论 | 备注 |
|---|---|---|
| 背景写明了为什么现在做 | PASS | MinerU paper.md 场景说明清楚；选型 A/B 分析保留 |
| 问题陈述与目标可被外部读者理解 | PASS | URL 传参方案选 A 有理由；commit 缺失降级语义明确 |
| 范围 / 非范围都有 | PASS | 各 6 条，与 AC 对齐 |
| 验收标准每条都可演示且可机械化 | PASS（minor 剩余，见 SHOULD FIX） | AC-2/AC-5/AC-6 grep 已修精；AC-6 bash 命令仍有脆弱点 |
| 风险有缓解措施或显式 accept | PASS | 7 条风险全有缓解或 accept 说明 |
| 没有把已有架构当新提案重复 | PASS | |
| AC 表存在 kind 列 | PASS | kind 列存在 |
| 至少 1 行 AC kind=behavioral | PASS | AC-6 kind=behavioral、AC-8 kind=behavioral，共 2 条 |

## 问题列表

### MUST FIX

无。

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| SHOULD FIX-1 | spec.md § "AC-6 完整命令" | `grep -E '^{' /tmp/blob.raw > /tmp/blob.json` 仍保留 v1 标注的脆弱点：vitest `--reporter json` 在部分版本于 JSON 前输出 `RUN ...` 前缀行；多行 `{` 时 grep 仅取首行；若 JSON 被截断则 python3 parse 静默报错。v1 SHOULD FIX-1 未被修复 | 改为 `cd apps/web && pnpm test -- --run --reporter=json src/routes/blob.test.tsx 2>/dev/null \| python3 -c "import json,sys; d=json.load(sys.stdin); assert d['numFailedTests']==0 and d['numTotalTests']>=6"`（直接读 stdout 不经中间文件） |
| SHOULD FIX-2 | spec.md § "AC-6 完整命令" 注释 | 注释写 "v2 reviewer 复核确认" baseline = 3，但该确认须在 reviewer 读完产物后做出，不应预写在 spec 正文里（时序倒置：spec 作者无法代 reviewer 做确认）。当前表述可能误导后续读者以为 baseline 已被独立复核 | 将注释改为 "spec 作者实测 baseline = 3（txt preview / binary fallback / size > 5MB）；v2 reviewer 可自行复核"，去掉 "v2 reviewer 复核确认" 措辞 |
| SHOULD FIX-3 | spec.md § "风险" | v1 标注的"81 张图片并发 useSubtreeByPath / React Query dedup 依赖"（v1 SHOULD FIX-3）与"commit URL param 注入安全依赖"（v1 SHOULD FIX-2）两条 spec 未追加到风险表；generator 选择 deferred 但 spec 无记录 | 在风险表追加两行：(a) 同目录 N 图并发由 React Query dedup 处理，接受；(b) commit URL param 注入由 useSubtreeByPath enabled regex `/^[0-9a-f]{64}$/` 把关，accept |
| SHOULD FIX-4 | spec.md § "验收标准" AC-6 | `entry 找不到 / tree miss` 降级行为（AC-5 描述中明确的两个 fallback 分支）没有对应的命名测试用例。T-5 要求的三用例（image rewrite / 绝对 URL / commit 缺）覆盖 commit 缺分支，但 `useSubtreeByPath` 返回 isError 或 entries 中找不到 basename 的 fallback 无专属测试 | 在 AC-6 描述里将"entry 找不到 fallback"列为第 4 个必须新用例（可与 T-5 optional d 合并改为 required），或在风险表注明"tree-miss / entry-not-found fallback 仅由 AC-8 端到端兜底" |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| NICE-1 | spec.md AC-5 描述 | loading 状态占位文本（`(loading {src})`）与错误状态提示在 spec 里有提及，但 a11y 属性（aria-label / role）未规定 | 可加一句：loading span 加 `role="status"`；not found 加 `title="图片解析失败"` |
| NICE-2 | spec.md § "受影响模块" | 若 coding agent 将 CustomImage 拆到 `components/CustomImage.tsx`，AC-5 grep scope 仅锁 blob.\$owner.\$name.\$hash.tsx 会 FAIL。v1 NICE-2 未修 | 在"受影响模块"加注：若拆出 CustomImage 独立文件，需同步更新 AC-5 grep scope，或统一约定 CustomImage 内联在 blob 路由文件 |

## Verdict

**APPROVED**

4 条 v1 MUST FIX 全部核实关闭：
- MUST-1 (AC-2 grep) → 锚定 zod 字段声明 regex，已精准
- MUST-2 (AC-5 /blobs/ 断言) → 双锚验证 hook + URL 重写，已充分
- MUST-3 (AC-6 ≥ 6) → 数字已更新，断言已同步
- MUST-4 (leading / 语义) → 三路径模式明确钉死

v2 无新 MUST FIX。剩余 4 条 SHOULD FIX（其中 2 条来自 v1 SHOULD FIX 未追加）和 2 条 NICE TO HAVE 不阻塞进入 stage 3（coding）。SHOULD FIX-1/2/3/4 建议 generator 在 coding 阶段开始前一并处理，否则在 coding_report 里注明 deferred。

## 后续指引

APPROVED → generator 可进入 stage 3 coding，按 tasks v2 DAG 执行 T-1 → T-2 → T-3 → T-4a → T-4b → T-4c → T-5 → T-6 → T-7。
