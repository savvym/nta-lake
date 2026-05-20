---
change_id: web-blob-md-image-resolver-20260520
target: request_analysis/spec.md
target_version: 1
review_version: 1
reviewer: claude-agent:web-blob-md-image-resolver-20260520-stage2-reviewer-v1
reviewed_at: 2026-05-20T14:00:00Z
verdict: REVISION REQUIRED
---

# Spec Review v1

## 检查清单结论

| 项 | 结论 | 备注 |
|---|---|---|
| 背景写明了为什么现在做 | PASS | MinerU paper.md 场景清晰 |
| 问题陈述与目标可被外部读者理解 | PASS | 路径解析方案 A/B 分析清楚 |
| 范围 / 非范围都有 | PASS | 各 6 条，明确 |
| 验收标准每条都可演示且可机械化 | PARTIAL FAIL | AC-2 / AC-5 grep 有逻辑漏洞（见 MUST FIX-1/2） |
| 风险有缓解措施或显式 accept | PASS | 但有 1 条漏登（见 SHOULD FIX-3） |
| 没有把已有架构当新提案重复 | PASS | |
| AC 表存在 kind 列 | PASS | |
| 至少 1 行 AC kind=behavioral | PASS | AC-6 / AC-8 |

## 问题列表

### MUST FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| MUST FIX-1 | spec.md AC-2 验证命令 | `grep -qE "commit" apps/web/src/routes/blob.$owner.$name.$hash.tsx` 过宽：经验证，baseline blob.$owner.$name.$hash.tsx 里**不含** "commit" 字样（reviewer 已 grep 确认），但执行此 AC 时若因实现引入 "commit" 以外的字面（如注释 commits / back-to-commits 导航）也会通过，同时该 AC 粒度与 AC-5 重叠。更深问题：一旦把 commit 写进代码，该 grep 永远 PASS，但**不验证 validateSearch 字段是否真加了**；需用更精确的 grep（如锚定 `commit\?:` 或 `commit.*string` zod schema 行）保证验的是 validateSearch 而不是任意 "commit" 字符 | 将 AC-2 grep 改为 `grep -qE "commit\??\s*:" apps/web/src/routes/blob.\$owner.\$name.\$hash.tsx`（锚定字段声明语法），或加双重条件：`grep -qE "validateSearch" ... && grep -qE 'commit.*string\|commit.*z\.string' ...` |
| MUST FIX-2 | spec.md AC-5 验证命令 | `grep -qE "useSubtreeByPath|target_hash" apps/web/src/routes/blob.$owner.$name.$hash.tsx` 会在 queries.ts 等已有文件命中，但 scope 已正确锁定到 blob 路由文件，**不会误命中 queries.ts**（reviewer 核验路径正确）。真正问题：`target_hash` 已在 queries.ts 中作为接口字段 `TreeEntryRead.target_hash`（第 41 行）存在，**而不是只在 blob.$owner.$name.$hash.tsx 里**，但 grep 已 scope 到 blob 文件，所以这一条其实是安全的——问题是 `useSubtreeByPath` 在 queries.ts（line 185）已存在，若 CustomImage 在其他被 import 的文件里实现（非 blob.$hash.tsx 本体），grep 仍 PASS。核心缺陷：AC-5 对"组件实现在哪个文件"没有约束，实现可以拆到 `components/CustomImage.tsx` → blob 文件只 import → grep 仍 FAIL；或相反实现在 blob 文件 → PASS 但不验证逻辑正确性。建议补充：检测 `/blobs/` 路径重写逻辑而非只检测 hook 名 | 将 AC-5 grep 改为三合一：`grep -qE "useSubtreeByPath" apps/web/src/routes/blob.\$owner.\$name.\$hash.tsx && grep -qE "target_hash" apps/web/src/routes/blob.\$owner.\$name.\$hash.tsx && grep -qE '"/api/repos/.*blobs/"\|blobs/\$\{' apps/web/src/routes/blob.\$owner.\$name.\$hash.tsx`（验证 blob URL 重写逻辑确实在该文件）；或允许 grep 同时 scope `components/CustomImage.tsx` |
| MUST FIX-3 | spec.md AC-6 验证命令 / § "验收标准" | AC-6 期望 `numTotalTests ≥ 3`，但 baseline blob.test.tsx 已有 **3 个测试用例**（txt preview / binary fallback / size > 5MB；reviewer 已核验），新增 0 个也能满足 `≥ 3` → AC-6 对"新测试是否加了"没有真正保护。需改为：要求用例名中包含特定 3 个新场景名（或改 `numTotalTests ≥ 6`，即 baseline 3 + 新增 3） | 将 AC-6 期望改为 `numTotalTests ≥ 6`（baseline 3 + 新增 ≥ 3），或在 python3 断言里同时 grep 测试输出中出现三个指定用例名（如 `md_image_resolves_to_blob_url` / `md_absolute_url_passes_through` / `md_image_without_commit_passes_through`） |
| MUST FIX-4 | spec.md § "范围" / AC-5 描述 | `resolveRelative` 算法对 leading `/` 行为 spec 未明确：T-4 description 写"拒 leading /"，但 markdown 里的 `![](/images/a.jpg)` 是仓内绝对路径引用场景（与 `https://` 不同，不是外部 URL），应该是 accept 还是 fallback 原 src？如果 MinerU 在某些情况生成绝对路径引用，当前 spec 的"拒"意味着 fallback，可能导致图片不显示。spec 应明确: (a) leading `/` 视为绝对 URL 不做仓内解析（fallback 原 src）; (b) 还是视为仓根路径尝试解析 | 在风险表或非范围里明确"leading / 路径视为 fallback（不做仓内路径解析）"，并在 AC-5 描述里注明 |

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| SHOULD FIX-1 | spec.md § "验收标准" AC-6 命令 | `grep -E '^{' /tmp/blob.raw > /tmp/blob.json` 假设 JSON 报告行以 `{` 开头，但 vitest `--reporter json` 在某些版本会在 JSON 前有额外行（如 "RUN..." 前缀行），导致 parse 失败；且多个 `{` 行时只取第一个。建议改为 `jq -s '.[0]'` 或用 `--reporter=json` + `2>/dev/null` + `python3 -c "import json,sys; ..."` 直接读 stdout | 改为 `cd apps/web && pnpm test -- --run --reporter=json src/routes/blob.test.tsx 2>/dev/null | python3 -c "import json,sys; d=json.load(sys.stdin); assert d['numFailedTests']==0 and d['numTotalTests']>=6"` |
| SHOULD FIX-2 | spec.md § "风险" | `commit search param ?commit=<64-hex>` 写入 URL 时，T-2 描述用 zod schema 验证，但 AC-2 / spec 都没指定 commit 字段是否需 hex 正则约束。若用户手动构造 `?commit=../../../etc/passwd` 之类的 path traversal，useSubtreeByPath 的 `enabled: !!commitHash && /^[0-9a-f]{64}$/.test(commitHash)`（queries.ts line 226）会把关——但 spec 没有明示这一安全依赖。应在风险表里显式注明"commit param 安全由 useSubtreeByPath.enabled 的 hex 正则把关；validateSearch 不需额外约束" | 在风险表加一行："commit URL param 注入 → 低概率，由 useSubtreeByPath enabled regex /^[0-9a-f]{64}$/ 在 hook 层把关；accept" |
| SHOULD FIX-3 | spec.md § "风险" | 81 张图片并发 useSubtreeByPath 场景（pdf-mineru-assets 实测同目录 N 张图）：每个 CustomImage 挂载时独立触发 useQuery，queryKey 为 `["subtree-by-path", owner, name, commitHash, dirPath]`，同目录图片的 queryKey **完全相同** → React Query 会 dedup（只发一次 fetch），不构成 N 次并发。但 spec 没有明示此"dedup 依赖"——若 mdPath 计算后 dirPath 各有差异（嵌套目录）则无 dedup，N 个不同 subtree 查询会并发。该情况在 nested pdf（papers/2026/a.md 内引用 papers/2026/images/*.jpg）下实际存在。建议在风险表注明"同目录 N 图场景由 React Query dedup 处理；nested 目录 N 图场景接受并发" | 在风险表追加此条，标注 accept |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| NICE-1 | spec.md AC-5 描述 | CustomImage loading 时显示占位文字的内容（"加载中…" / "图片加载中" / 空？）spec 没规定，导致 a11y / UX 行为不确定。非阻塞，但可在描述里加一行约定 | 加"loading 状态显示 `<span>图片加载中…</span>`，not found 显示 `<span>[图片不可用]</span>`" |
| NICE-2 | spec.md § "受影响模块" | 若 CustomImage 实现在独立组件文件（`components/CustomImage.tsx`），spec 未列出该文件。预防 coding agent 拆文件后 AC-5 grep scope 失效 | 在"受影响模块"里注明"若拆出 components/CustomImage.tsx 需同步更新 AC-5 grep scope" |
| NICE-3 | spec.md § "引用" | useSubtreeByPath API `baseUrl + "/tree/" + commitHash`（注意：queries.ts line 195 是 `/tree/` 而不是 `/trees/`）——AC-5 不验证这个端点，只验证 hook 被调用。若端点名拼错，测试可能 mock 掉，只有 behavioral AC-8 才能发现。建议在风险表注明此端点依赖 | 可在风险表加"useSubtreeByPath API 端点 `/tree/{commit}` vs `/trees/{hash}` 混用问题由 AC-8 behavioral 兜底" |

## Verdict

**REVISION REQUIRED**

4 条 MUST FIX 全部阻塞：
- MUST FIX-1: AC-2 grep 对 validateSearch 字段验证不精确
- MUST FIX-2: AC-5 grep 对 blob URL 重写逻辑验证不充分（虽 scope 正确，但缺"/blobs/"路径重写断言）
- MUST FIX-3: AC-6 baseline 已有 3 个用例，`numTotalTests ≥ 3` 零保护新用例
- MUST FIX-4: resolveRelative leading "/" 行为规格缺失，可能导致 MinerU 绝对路径引用场景静默 fallback

## 复检指引

Generator 修完 spec v2 后，自查以下：

1. **AC-2**：`grep -qE "validateSearch" apps/web/src/routes/blob.\$owner.\$name.\$hash.tsx && grep -qP "commit[?]?\s*:" apps/web/src/routes/blob.\$owner.\$name.\$hash.tsx` → 两者均退出 0
2. **AC-5**：`grep -qE "useSubtreeByPath" apps/web/src/routes/blob.\$owner.\$name.\$hash.tsx && grep -qE "/blobs/" apps/web/src/routes/blob.\$owner.\$name.\$hash.tsx` → 两者均退出 0（或同等 scope 的 CustomImage 文件）
3. **AC-6**：确认 `numTotalTests ≥ 6`（或 ≥ baseline + 3，以具体数字写入 AC）
4. **leading / 行为**：在 AC-5 描述或风险表里找到明确的"leading / → fallback"声明
5. **kind 列 + behavioral**：`awk '/^## 验收标准/{p=1;next} p && /^## /{exit} p' spec.md | grep -qE 'behavioral'` → 退出 0（本次 PASS，复检确认未被改掉）
