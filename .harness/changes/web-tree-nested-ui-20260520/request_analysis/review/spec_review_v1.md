---
change_id: web-tree-nested-ui-20260520
target: spec.md
target_version: 1
review_version: 1
reviewer: claude-agent:web-tree-nested-ui-20260520-stage2-reviewer-v1
reviewed_at: 2026-05-19T17:30:00Z
verdict: REVISION REQUIRED
---

# Spec Review v1

## v0 MUST FIX 复检

无上一轮，跳过。

---

## 检查清单结论（plan 模式）

| 项 | 状态 | 说明 |
|---|---|---|
| 背景写明了为什么现在做 | PASS | tree-nested-domain merge 后立即冒出 UI 退化，背景清晰 |
| 问题陈述与目标可被外部读者理解 | PASS | 问题陈述具体，包含代码路径与预期失败场景 |
| 范围 / 非范围都有 | PASS | In scope / Out of scope 均明确 |
| 验收标准每条都可演示且可机械化 | PARTIAL - 见 MUST FIX-1 / MUST FIX-2 | AC-9 不可机械化；AC-6 完整命令存在可靠性缺陷 |
| 风险有缓解措施或显式 accept | PASS | 7 条风险，每条均有缓解或 accept 声明 |
| 没有把已有架构当新提案重复 | PASS | 未重复 design.md 内容 |
| AC 表存在 kind 列 | PASS | 表头含 kind 列 |
| 至少 1 行 AC 的 kind 为 behavioral（锚定 regex） | PASS | AC-6/7/9/11 均标 behavioral；spec 自述 "4 behavioral" |

---

## 问题列表

### MUST FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| MUST FIX-1 | spec.md §验收标准 AC-9 | AC-9 kind=behavioral，验证命令为 `n/a（stage 10 填）`，不满足"每条 AC 可机械化或可演示验证"的 stage 1 Quality Gate 约束。标 behavioral 的 AC 在 stage 2 时必须有可执行或可演示的验证路径；"stage 10 填" 等于把 behavioral 价值推迟到最后，与 AC 分层规约初衷相悖。 | 选择其一：(a) 将 AC-9 改为 kind=process（`stage 10 用户实测确认`），从机械化 AC 表中移除，改在 summary.md 的 deferred 区声明；(b) 或补充 smoke 测试命令（如 `curl /api/repos/{owner}/{name}/tree/{hash}` 链路或 vitest behavioral 覆盖），让其可在 stage 8/9 自动验证。 |
| MUST FIX-2 | spec.md §AC-6 完整命令 | `grep -cE 'test_[a-z_]+\|test\(' /tmp/web-tree-nested-vitest.log` 依赖 log 文件中匹配 test 函数名或 `test(` 字面量。vitest `--reporter verbose` 输出用例描述字符串（如 `✓ root shows mixed entries`），**不含** `test_` 前缀，该 grep 在用例描述以 `it(` / `describe+it` 风格书写时将计数为 0，导致 `[ "$(grep ...)" -ge 4 ]` 假 FAIL。此命令作为 behavioral AC 的自动验证入口，可靠性不足。 | 改用 `pnpm --filter web test -- --run --reporter verbose ... \| grep -cE '✓\|✗\|PASS\|FAIL'` 计数；或直接用 vitest `--reporter json` 输出后 `jq '[.testResults[].assertionResults[]] \| length'` 精确统计 pass 数。 |
| MUST FIX-3 | spec.md §AC-3 验证命令 | `grep -qE "path[?:]\\s*z\\.\|path\\?:.*string"` 过于宽松：任何含 `path?:` 的注释、变量或旧代码都会命中。TanStack Router `validateSearch` 返回类型通常形如 `path?: string` 或 `path: z.string().optional()`；但如果实现用了 zod schema 对象（常见 pattern 是 `const searchSchema = z.object({ tab: ..., path: ... })`），该 grep 能匹配到但不能确认字段在 schema 内。更重要的是：未验证默认值是否为空字符串（`""` 而非 `undefined`）；导致 `path=undefined` 与 `path=""` 区分问题（见下 SHOULD FIX-2）。 | 加一条补充 grep 校验默认值，如 `grep -qE 'path.*optional.*default\|default.*"".*path' apps/web/src/routes/repos/\$owner.\$name.tsx` 或在 AC-4 测试中通过行为验证默认值 = `""`。 |
| MUST FIX-4 | spec.md §AC-12 | AC-12 描述为 "AC-12 自递归"，验证命令与 AC-10 完全相同（均为 `grep -q "run_web_tree_nested_ui" scripts/_self_check.sh`），这是一个重复 / 无意义的 AC。AC-12 没有独立验证内容，只是 AC-10 的副本；若这是"自递归"的有意设计，需要说明其含义；否则这是 spec 草稿遗留物，会让 self_check 注册 12 个 block 但其中一个没有实质内容。 | 明确 AC-12 的真实验收意义，或合并到 AC-10，或删除 AC-12 并将 AC 数量改为 11。若保留，必须写出与 AC-10 不同的验证命令和期望。 |

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| SHOULD FIX-1 | spec.md §AC-4 + §风险 | 面包屑 path 拼接规则 `path ? \`${path}/${name}\` : name` 对特殊情况未定义：path 以 `/` 结尾、name 含 `/`（legacy 兼容路径）、path 为 `""` 时 `"" || name` 的 JS 行为（空字符串 falsy）。spec 风险区虽提到 `..` / Unicode，但未覆盖 `/` 结尾和 double-slash `//` 场景。 | 在 spec 中明确 path 不含前导/末尾斜杠的不变量（invariant），并在 AC-2 的 throw 条件里写明 segment 必须是 non-empty non-slash string。 |
| SHOULD FIX-2 | spec.md §AC-3 + §问题陈述 | `path=""` 与 `path=undefined`（URL 无 `?path`）在 TanStack Router 中的行为未定义。spec 写 `默认空字符串`，但 TanStack Router v1（使用 zod schema）中 `z.string().optional()` 默认为 `undefined`，只有 `.default("")` 才能保证 `""`。如实现用 `undefined`，AC-4 的 `path != ""` 判断会失效（`undefined != ""` 为 true → 面包屑误显）。 | 在 spec 中明确写 `path: z.string().default("")` 并验证 URL 不带 `?path` 时路由注入 `path=""`，不得注入 `undefined`。 |
| SHOULD FIX-3 | spec.md §AC-4 folder 行可访问性 | "整行 click 触发 navigate" 未声明 DOM 元素类型。`div onClick` 在 keyboard 导航、屏幕阅读器场景下不可访问（non-interactive element）；AC 没有 accessibility 约束，导致 coding agent 可能用 div。 | 在 AC-4 中加约束："folder 行使用 `<button>` 元素（不是 `div onClick`）确保 keyboard focus + 屏幕阅读器可访问"。 |
| SHOULD FIX-4 | spec.md §AC-4 tab 切换与 path 保留 | T-2 描述 "tab 切换时保留 path（或重置到 ""），看交互期望"，spec 中未明确。spec §AC-4 提到 `...search` 展开，但是否 tab 切换时 path 被保留属于产品决策；不明确会让 coding agent 两种实现方式随机选一。 | 在 spec 中明确：tab 切换（ingest / pipelines → files）时 path **重置为 ""**（否则用户从其他 tab 回 files 看到上次深层路径，体验差）；或明确保留（如 UX 意图如此）。 |
| SHOULD FIX-5 | spec.md §AC-6 + §AC-9 | AC-9 虽标 behavioral，但验证列内容为 `n/a（stage 10 填）`。spec 自审第 4 条写 "4 behavioral"，但 AC-9 实质上是 deferred process task，不是可执行 behavioral test。spec 自审数字有误导性（应为 3 个可执行 behavioral AC：AC-6/7/11）。 | 修正自审第 4 条描述，与 MUST FIX-1 一并处理。 |
| SHOULD FIX-6 | spec.md §风险 useCommit 重复请求 | 风险行写 `可接受；后续可优化让 useSubtreeByPath 在 path=="" 时复用 useCommit cache（NICE TO HAVE）`，但 spec 正文的 AC 列表未为此开 AC / deferred 条目。此 NICE TO HAVE 只存在于风险表注释中，无法被追踪。 | 在 spec deferred 区或 tasks.md 备注中开一条 NICE TO HAVE 条目，确保不丢失。 |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| NTH-1 | spec.md §AC-2 queryKey | queryKey 形如 `["subtree-by-path", owner, name, commit_hash, path]`，其中 path 为字符串 `"a/b"`。React Query 对字符串 key 不做深度比较，`"a/b"` 和 `["a","b"]` 是不同 key（后者在这里不会出现），所以字符串 key 稳定。但 path 参数若在某处被 `encodeURIComponent` 转换，`"a/b"` 与 `"a%2Fb"` 会是不同 key。spec 未声明 queryKey 中的 path 使用 raw（decode）还是 encoded form。建议明确 queryKey 中 path 使用 raw（`/` 不 encode）与 URLSearchParams 保持一致。 |
| NTH-2 | spec.md §AC-2 React Query 并发取消 | 用户快速点多个 folder 触发多次 `useSubtreeByPath` 调用，React Query 默认行为是：对同 queryKey 的并发请求去重（复用 in-flight），不同 queryKey 不取消。快速切换 path 时旧 query 不被取消，可能出现 stale 结果先到达再被新结果覆盖的闪烁。spec 未声明是否接受此行为（acceptable risk），建议在风险表加一行或在 AC 中明确 `staleTime`。 |
| NTH-3 | spec.md §AC-4 | `search.path` 用于 blob view 页面显示完整路径（spec §AC-4 最后一条），但 blob 路由的 `validateSearch` 不一定接受 `path` 参数，需要确认 `/blob/$owner/$name/$hash` 路由的 search schema 兼容。spec 未交叉引用。 |
| NTH-4 | spec.md §背景 | `GET /tree/{commit_hash}` 端点名字在 spec 中写法不一致：§背景写 `/tree/{commit_hash}`，§范围 AC-2 写 `/tree/{commit_hash}`（root），但 useSubtree 调的是 `/trees/{tree_hash}`（复数）。两个端点名字混用（singular /tree vs plural /trees）在 spec 中有歧义，建议统一注明 "root 用 `/tree/{commit_hash}`，子树用 `/trees/{tree_hash}`"。 |

---

## Verdict

**REVISION REQUIRED**

存在 4 条 MUST FIX：
- MUST FIX-1：AC-9 behavioral 但验证为 n/a，违反 AC 可机械化约束
- MUST FIX-2：AC-6 自动验证命令在 vitest verbose 输出中计数逻辑有缺陷，可靠性不足
- MUST FIX-3：AC-3 验证 grep 未覆盖默认值验证，范围过宽
- MUST FIX-4：AC-12 与 AC-10 完全重复，是 spec 遗留草稿，无独立验收意义

SHOULD FIX 6 条，核心是 `path=""` vs `undefined` 的路由语义未定义（SHOULD FIX-2），tab 切换时 path 保留/重置未明确（SHOULD FIX-4），以及 folder 行 accessibility 约束缺失（SHOULD FIX-3）。

---

## 后续指引

Generator 修完 v2 spec 后，自查以下命令：

```bash
# 1. AC 表含 kind 列 + 有 behavioral 行
awk '/^## 验收标准/{p=1;next} p && /^## /{exit} p' .harness/changes/web-tree-nested-ui-20260520/request_analysis/spec.md \
  | grep -E '^\|[^|]*\|[[:space:]]*kind[[:space:]]*\|'   # kind 列存在

awk '/^## 验收标准/{p=1;next} p && /^## /{exit} p' .harness/changes/web-tree-nested-ui-20260520/request_analysis/spec.md \
  | grep -E '^\|[[:space:]]*AC-[0-9]+[a-z]?[[:space:]]*\|[[:space:]]*(\*\*)?behavioral(\*\*)?[[:space:]]*\|'  # 至少 1 行 behavioral

# 2. AC-6 验证命令在本地能跑通（暂不强求 ≥4，但命令不报 syntax error）
bash -n <(grep -A5 "AC-6 完整命令" .harness/changes/web-tree-nested-ui-20260520/request_analysis/spec.md | tail -5)

# 3. AC-12 有独立内容（不等于 AC-10 命令）
# 手动 diff spec.md 中 AC-10 与 AC-12 的"验证"列

# 4. path 默认值在 validateSearch 中有 .default("") 或 catch-all
grep -E 'path.*default\(\s*""\s*\)' apps/web/src/routes/repos/\$owner.\$name.tsx || \
  echo "WARNING: 默认值未确认，需在 spec 中明示或在 AC 测试中覆盖"
```

v2 修完后重新 spawn reviewer v2 复检 MUST FIX 闭合状态。
