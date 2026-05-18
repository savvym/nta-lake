---
change_id: repo-files-tab-v2-20260518
target: spec.md
target_version: 1
review_version: 1
reviewer: claude-agent:repo-files-tab-v2-20260518-stage2-reviewer-v1
reviewed_at: 2026-05-18T22:00:00Z
verdict: REVISION REQUIRED
must_fix_count: 5
should_fix_count: 3
nice_to_have_count: 2
---

# Spec Review v1

> 评审者声明：本 reviewer 是独立 sub-agent（claude-sonnet-4-6），未参与本 change spec/tasks 撰写。完整读了 reviewer-agent.md / expert-reviewer SKILL / request-analysis SKILL / development-process.md / summary.md / spec.md / tasks.md，并实读了 minio_store.py L168-178（get_size 实现）/ apps/web/src/routes/repos/$owner.$name.tsx（既有 PipelinesSection / validateSearch 用法）/ scripts/_self_check.sh pipeline-ui-tab block（L1310-1332）/ apps/web/src/routes/commits.$owner.$name.$hash.tsx（路由命名约定）/ apps/web/src/routes/repos.test.tsx（vitest 测试模式）/ apps/web/src/lib/api/queries.ts（usePipelineRun enabled 标志）/ pipeline-ui-tab-20260518 spec_review_v1.md（对照模板）。所有 grep/bash 命令均在本机实跑验证。

---

## stage 2 AC kind 必查 3 项

| # | 检查项 | 结果 | 证据 |
|---|---|---|---|
| 1 | AC 表存在 `kind` 列 | PASS | spec.md L83 表头 `| ID | kind | 描述 | 验证方式 | 期望 |`；`awk '/^## 验收标准/{p=1;next} p && /^## /{exit} p' spec.md | grep -qE '^\|[^|]*\|[[:space:]]*kind[[:space:]]*\|'` 命中；自跑 `bash scripts/_self_check.sh ac-kind-lint` 输出 `PASS ac-kind-lint`（FAIL=0） |
| 2 | 至少 1 行 AC kind 单元格真值 `behavioral`（锚定 AC 行 regex） | PASS | AC-6 `**behavioral**` / AC-7 `**behavioral**` / AC-8 `**behavioral**` 共 3 行；锚定 regex `^\|[[:space:]]*AC-[0-9]+[a-z]?[[:space:]]*\|[[:space:]]*(\*\*)?behavioral(\*\*)?[[:space:]]*\|` 命中；self_check ac-kind-lint PASS |
| 3 | frontmatter 是否声明 `ac_kind_lint: exempt` | N/A | spec.md frontmatter L1-6 无 `ac_kind_lint: exempt`，无需 git diff 校验 |

三项全 PASS，AC 分层规约硬约束**未违反**。

---

## 检查清单结论（expert-reviewer SKILL §1 plan 模式）

### spec.md

- [x] 背景写明了为什么现在做（pipeline-ui-tab 后垂直四段叠加过长 + 只能下载不能预览）
- [x] 问题陈述对外部读者可理解（3 条具体 UX 缺陷：滚动 / 无预览 / 刷新丢状态）
- [x] 范围 / 非范围都有（AC 1-8 in-scope + 7 项明确 out-of-scope）
- [~] 每条验收标准可演示且可机械化 —— **AC-4 / AC-6 / AC-7 / AC-8 验证命令有实质 bug**（详 MUST FIX-1 / MUST FIX-2 / MUST FIX-3）
- [x] 风险有缓解或显式 accept（6 条风险，含 BlobStore.get_size 异常路径显式 deferred 给 reviewer）
- [x] 没有把已有架构当新提案（引用 existing commits.py L119-148 download / minio_store.py L168-180 get_size）
- [x] 待澄清问题已清零（6 条已决，1 条显式 deferred 给 reviewer）

### tasks.md

- [x] 每个任务粒度合理（1-3 小时；T-1~T-10 实现任务 + process_tasks 7 条）
- [x] depends_on 形成 DAG 无环（手动 trace：T-1→T-2→T-3→T-9；T-4→T-7→T-8c→T-9；T-4→T-8a→T-9；T-5→T-6；T-5→T-8b→T-9；T-2/T-5/T-6/T-7→T-10；无环，终点 T-9+T-10）
- [x] 评审 / 单测 / CI / 部署 process_tasks 都存在（P-spec-review / P-code-review / P-test-review / P-push / P-ci / P-deploy / P-user-confirm，stage-N 格式全部正确）
- [x] 无"实现整个系统"类目标性任务

---

## 跨 AC 一致性自审 9 条（reviewer 复核）

| # | checklist 条目 | 结果 | 备注 |
|---|---|---|---|
| 1 | schema 字段 ↔ hash ↔ idempotency ↔ fixture 四链路一致 | N/A | 无 hash/idempotency 链路（BlobMetaResponse 仅 sha256+size，读操作） |
| 2 | 事务边界 AC / 风险 / tasks 三处一字不差 | N/A | 无事务边界（只读 + 前端 state） |
| 3 | AC 验证命令一行式可执行 | FAIL | AC-4 / AC-6 / AC-7 / AC-8 验证命令含 ERE `\|` bug（见 MUST FIX-1/2/3） |
| 4 | 风险缓解 ↔ AC 测试列表 | OK | BlobStore 风险 deferred 给 reviewer（已查，符合预期）；其余 6 条风险与 AC 对应 |
| 5 | commit 历史链连续性 | N/A | 无写 commit 路径 |
| 6 | 反向 grep 配 `test -f` 前置 + 不吞 stderr | FAIL | AC-8 `! grep -qE 'error TS\|Found N errors'` 中的 `\|` 是 ERE 字面竖线（见 MUST FIX-3）；无 `2>/dev/null` 吞 stderr（OK） |
| 7 | process_tasks 6 条必填 + estimated_stage 命名 | PASS | 7 条 process_tasks 全部用 `stage-N` 形态（`grep -cE "estimated_stage: stage-(2|4|6|7|8|9|10)" tasks.md` = 7，含 stage-8 self-attest） |
| 8 | AC 验证命令 dry-parse | FAIL | AC-4/AC-7/AC-8 grep ERE `\|` 语法合法但 semantic 假阴性；AC-6 `$()` 内 `\|` 非 shell pipe（见 MUST FIX） |
| 9 | summary.md frontmatter 无模板占位符 | PASS | `grep -cE "<feature-slug>|<YYYY-MM-DDTHH:MM:SSZ>|<复述|<bullet list>" summary.md` = 0；frontmatter 全填实值 |

---

## 必查 1：AC 验证命令 grep ERE alternation 陷阱（全部实跑验证）

### AC-3 `grep -q 'Route.useSearch\|useSearch'`

**结论：不是 bug**。此命令用基本 grep（无 `-E`），在 BRE 中 `\|` **是 alternation**（不是字面竖线）。实跑：
```
printf "const s = Route.useSearch();\n" | grep -q 'Route.useSearch\|useSearch' && echo HIT  # → HIT
printf "const s = useSearch();\n" | grep -q 'Route.useSearch\|useSearch' && echo HIT  # → HIT
```
两者均 HIT，语义正确。

### AC-4 `grep -qE '5 ?\* ?1024 ?\* ?1024\|5242880\|MAX_PREVIEW_SIZE'` 和 `grep -qE '\.png\|\.jpg\|\.jpeg'`

**结论：MUST FIX**。`-E`（ERE）模式中 `\|` 是**字面竖线**，不是 alternation。实跑：
```
printf "5 * 1024 * 1024\n" | grep -qE '5 ?\* ?1024 ?\* ?1024\|5242880\|MAX_PREVIEW_SIZE' && echo HIT || echo MISS
→ MISS （假阴性！代码正确实现也无法 PASS）
printf "5 * 1024 * 1024\n" | grep -qE '5 ?\* ?1024 ?\* ?1024|5242880|MAX_PREVIEW_SIZE' && echo HIT || echo MISS
→ HIT （正确）
```
同理，`\.png\|\.jpg\|\.jpeg` 在 `-E` 下是字面竖线，只能匹配包含 `\.png|\.jpg|\.jpeg` 这些字符的行（永不命中正常 TS 源码）。

### AC-6 `$()` 内 `\|` 非 shell pipe（MUST FIX）

AC-6 验证命令有一处：`[ "$(grep -oE 'Tests +([0-9]+) passed' /tmp/... \| awk '{print \$2}')" -ge 5 ]`

`\|` 在 `$()` subshell 内不被解释为 shell pipe，而是传给 grep 的 **字面参数**（grep 把 `|` `awk` 等当作文件参数，报 "No such file or directory"），导致：
- grep 的输出是完整匹配字符串（如 `Tests  5 passed`），不是纯数字
- `[ "Tests  5 passed" -ge 5 ]` 会报 non-numeric error 并退码非零
- AC-6 即便测试真 PASS ≥5，此比较也会 FAIL

实跑验证：
```
bash -c 'printf "Tests  5 passed (5)\n" > /tmp/t.log; echo "$(grep -oE '"'"'Tests +([0-9]+) passed'"'"' /tmp/t.log \| awk '"'"'{print $2}'"'"')"'
→ 输出 "Tests  5 passed" (带 "| awk..." 作为 grep 参数)，而非 "5"
```

### AC-7 `grep -qE '[3-9] passed\|[1-9][0-9]+ passed'`

**结论：MUST FIX**。`-E` 下 `\|` 是字面竖线。实跑：
```
printf "3 passed\n" | grep -qE '[3-9] passed\|[1-9][0-9]+ passed' && echo HIT || echo MISS
→ MISS （实际 pytest 输出 "3 passed" 无法匹配！）
printf "3 passed\n" | grep -qE '[3-9] passed|[1-9][0-9]+ passed' && echo HIT || echo MISS
→ HIT
```

### AC-8 `! grep -qE 'error TS\|Found [0-9]+ errors'`

**结论：MUST FIX**。`-E` 下 `\|` 是字面竖线，所以此正则只匹配含字面竖线的行（永远不命中 tsc error 输出），`!` 反转后永远 PASS——即便 build 有 TS 错误也无法拦截。实跑：
```
printf "error TS2345: Type\n" | grep -qE 'error TS\|Found [0-9]+ errors' && echo HIT || echo MISS
→ MISS （bug：应该命中但没有命中）
printf "error TS2345: Type\n" | grep -qE 'error TS|Found [0-9]+ errors' && echo HIT || echo MISS
→ HIT （正确）
```

---

## 必查 2：AC-3/AC-4/AC-5 单引号 `\$` 路径陷阱（全部实跑验证）

spec AC-3 / AC-4 / AC-5 的 test -f 和 awk 命令使用**单引号**包裹含 `\$` 的文件路径：
```
test -f 'apps/web/src/routes/repos/\$owner.\$name.tsx'
```
在单引号字符串中，`\$` 是**字面反斜杠+美元符**，即 path = `repos/\$owner.\$name.tsx`（含实际反斜杠），而实际文件名是 `repos/$owner.$name.tsx`（含美元符，无反斜杠）。

实跑验证（文件存在）：
```bash
test -f 'apps/web/src/routes/repos/\$owner.\$name.tsx' && echo FOUND || echo NOT_FOUND
→ NOT_FOUND （单引号 \$ = 路径错误）

test -f apps/web/src/routes/repos/\$owner.\$name.tsx && echo FOUND || echo NOT_FOUND
→ FOUND （无引号 \$ = shell 转义 $ = 正确路径）
```

对照：`pipeline-ui-tab-20260518/spec.md` AC-2 使用**无引号**形式：
```
test -f apps/web/src/routes/repos/\$owner.\$name.tsx && grep -q ...
```
`scripts/_self_check.sh` pipeline-ui-tab block（L1325）使用 `bash -c` 内**双引号**形式：
```
bash -c 'test -f "apps/web/src/routes/repos/\$owner.\$name.tsx" && ...'
```
两者均正确，但本 spec 的单引号形式**错误**。

受影响的 AC 命令：
- **AC-3**：`test -f 'apps/web/src/routes/repos/\$owner.\$name.tsx'` → 永远 NOT_FOUND
- **AC-4**：`test -f 'apps/web/src/routes/blob.\$owner.\$name.\$hash.tsx'` → 永远 NOT_FOUND
- **AC-5**：`awk ... 'apps/web/src/routes/repos/\$owner.\$name.tsx' \| grep ...` → awk 找不到文件

注：AC-4 中的 `grep -q 'createFileRoute("/blob/\$owner/\$name/\$hash")'` **不是 bug**——在 BRE 中 `\$` 匹配字面美元符，可正确匹配源码中的 `createFileRoute("/blob/$owner/$name/$hash")`。

---

## 必查 3：BlobStore.get_size 异常路径实读（spec deferred item 关闭）

实读 `apps/api/dataplat_api/storage/minio_store.py` L168-178：

```python
async def get_size(self, sha256: str) -> int | None:
    key = storage_key_for(sha256)
    try:
        resp = await asyncio.to_thread(
            self._client.head_object, Bucket=self._bucket, Key=key
        )
    except ClientError as exc:
        if _client_error_code(exc) in _NOT_FOUND_CODES:
            return None
        raise
    return int(resp["ContentLength"])
```

其中 `_NOT_FOUND_CODES = {"404", "NoSuchKey", "NotFound"}`（L31）。

**结论：关闭此 deferred item，行为符合 spec 假设。**

- blob 不存在时：`head_object` 抛 `ClientError`，error code 属于 `_NOT_FOUND_CODES`，返回 `None`。
- S3 transient error（非 404）：`ClientError` 不在 `_NOT_FOUND_CODES`，重新 `raise`，FastAPI 框架返回 500。
- spec 风险表："None → 404，否则 200" 逻辑正确；router 中 `if size is None: raise HTTPException(404)` 假设成立。
- **无需在 router 显式 `try/except`**：非 404 的 ClientError 已由 minio_store 向上传播，FastAPI 默认处理为 500（符合行为预期）。

---

## 必查 4：TanStack Router search param 用法实读

实读 `apps/web/src/routes/repos/$owner.$name.tsx`：

- L27-29：`export const Route = createFileRoute("/repos/$owner/$name")({ component: RepoDetailPage })` —— **无 `validateSearch` 声明**
- L34：`const { owner, name } = Route.useParams()` —— **无 `Route.useSearch()` 用法**

全仓搜索：`grep -rn "validateSearch\|Route\.useSearch\|useSearch()" apps/web/src/ 2>/dev/null` —— **零命中**（exit 1）

**结论：仓库当前无 validateSearch 先例**。spec 风险表已显式评估此风险，缓解方案为"用极简 validateSearch 或 Route.useSearch() 默认行为 + 运行时校验"。spec T-5 description 给出了 `validateSearch: (s) => ({ tab: ... })` 的具体实现形态，与 TanStack Router v5 API 兼容。**无严重问题，但 coding 阶段需验证 tsc 不报错**。

---

## 必查 5：Tab 切换保 state 设计验证

实读 `apps/web/src/routes/repos/$owner.$name.tsx` L597-664：

```typescript
export function PipelinesSection({ ... }) {
  const [yamlText, setYamlText] = useState("");
  const [activeRunId, setActiveRunId] = useState<string | null>(null);
  ...
  const runQuery = usePipelineRun(activeRunId);
```

实读 `apps/web/src/lib/api/queries.ts` L308-316：

```typescript
export function usePipelineRun(runId: string | null) {
  return useQuery({
    ...
    enabled: !!runId,
  });
}
```

**结论：隐藏机制安全**。
- `usePipelineRun(null)`：`enabled = !!null = false`，初始不 fire，safe。
- `useCreatePipelineRun`：mutation hook，不自动 fire，safe。
- `hidden` className 方案：PipelinesSection 始终 mount，state 保留，无 unconditional 副作用。
- 无 unconditional `useEffect` 副作用（实读 L597-664 全函数体确认）。

---

## 必查 6：Behavioral AC 证据合规性

| AC | 形态 | 判定 |
|---|---|---|
| AC-6 | `npx vitest run ...` 真跑 5 个测试 → 断言 Tests N passed | L3（bash fixture 真跑断言）—— behavioral 合规 |
| AC-7 | `uv run pytest -k blob_meta` 真跑 3 个 pytest 测试 → 断言 ≥3 passed | L3—— behavioral 合规 |
| AC-8 | `npm run build`（vite build && tsc --noEmit）真编译 → 断言 built in + 无 error TS | L3—— behavioral 合规 |

三个 behavioral AC 判定全部合规。注：AC-8 `npm run build` 包含 tsc --noEmit（与 pipeline-ui-tab 评审 MUST FIX-3 已修 → tsc 覆盖到位），此处无问题。

---

## 必查 7：Markdown 极简渲染器 edge case

spec AC-4 描述 `renderMinimalMarkdown` 的 4 类语法优先级：
- (a) `^#{1-6} ` → heading
- (b) `^- ` / `^* ` 连续行 → ul/li
- (c) ` ``` ... ``` ` fenced → pre/code
- (d) 其余非空行 → p

tasks.md T-7 说明"fenced code 用栈状态机"，但 spec AC-4 的**语法优先级列表未明示 "fenced block 内 heading 识别被压制"**。即：当 fenced block 内出现 `# heading` 行时，应当优先处理为 fenced block 内容还是作为 heading？这是歧义点，coding 实现者可能在有效 fenced block 内误识别 heading。

---

## 问题列表

### MUST FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| MUST FIX-1 | spec.md AC-4 验证方式（L87）：`grep -qE '5 ?\* ?1024 ?\* ?1024\|5242880\|MAX_PREVIEW_SIZE'` 和 `grep -qE '\.png\|\.jpg\|\.jpeg'` | ERE 模式 `\|` 是字面竖线，不是 alternation。实跑两条命令均 MISS（代码正确实现也假 FAIL）。另：AC-8 `! grep -qE 'error TS\|Found [0-9]+ errors'` 同理：`\|` 是字面竖线，tsc error 输出中没有字面竖线，`!` 反转后永远 PASS → 无法拦截真正的 TS 错误。三处 `\|` 均为**同型 bug**（参考 pipeline-ui-tab spec_review_v1 MUST FIX-1 实证） | 去掉 `\` 改为裸 `|`，或拆分为多条独立 grep 命令（拆开最稳，参考 pipeline-ui-tab _self_check.sh L1325 风格）。修后自验：把命令在本机真跑一遍 |
| MUST FIX-2 | spec.md AC-6 验证方式（L89）：`[ "$(grep -oE 'Tests +([0-9]+) passed' /tmp/... \| awk '{print \$2}')" -ge 5 ]` | `\|` 在 `$()` subshell 内不是 shell pipe，而是传给 grep 的字面参数（grep 把 `|` `awk` 当文件处理）。实跑确认：输出为 `Tests  5 passed`（不是纯数字），`-ge 5` 比较报 non-numeric 错误，AC 即便测试真跑 PASS 也无法通过 | 将 `\|` 改为真正的 pipe：`$(grep -oE 'Tests +([0-9]+) passed' /tmp/... | awk '{print $2}')`，或改用 `grep -c 'passed'` 统计行数后比较；在 self_check.sh 的 bash -c 单引号外层正确转义 |
| MUST FIX-3 | spec.md AC-3/AC-4/AC-5 验证方式（L86/87/88）：file path 使用单引号 `'\$owner'` | 单引号内 `\$` 是字面 `\$`（反斜杠+美元），test -f 找不到实际文件 `$owner.$name.tsx`（含美元符）。实跑：`test -f 'apps/web/src/routes/repos/\$owner.\$name.tsx' && echo FOUND || echo NOT_FOUND` → NOT_FOUND；去掉引号的无引号形式或 bash -c 内双引号形式均正确。受影响：AC-3 `test -f '...\$owner...'`，AC-4 `test -f '...blob.\$owner...'`，AC-5 `awk ... '...\$owner...'` | 按 pipeline-ui-tab spec/self_check.sh 模式修改：去掉文件路径的单引号（用无引号形式 `test -f apps/web/src/routes/repos/\$owner.\$name.tsx`），或在 T-10 self_check.sh 实现中用双引号 `"apps/web/src/routes/repos/\$owner.\$name.tsx"`。注意：AC-4 中的 `grep -q 'createFileRoute("/blob/\$owner/...")'` 不需要修（BRE `\$` 匹配字面 `$`，正确） |
| MUST FIX-4 | spec.md AC-7 验证方式（L90）：`grep -qE '[3-9] passed\|[1-9][0-9]+ passed'` | ERE `\|` 是字面竖线。实跑：`printf "3 passed\n" | grep -qE '[3-9] passed\|[1-9][0-9]+ passed'` → MISS。pytest 真跑输出 "3 passed" 无法命中，AC-7 即便 pytest 通过也永远 FAIL | 去掉 `\`：`grep -qE '[3-9] passed|[1-9][0-9]+ passed'`。参考 self_check.sh L1352（pipeline-orchestrator block）用无转义 `|`：`grep -qE "10 passed"` |
| MUST FIX-5 | spec.md AC-6 验证方式（L89）：`grep -qE 'Tests +[0-9]+ passed'` 之后还有 `\$2` 问题 | `awk '{print \$2}'` 在 bash -c 单引号上下文中：`\$2` → `$2`，即 bash -c 的位置参数 $2（空字符串）；awk `{print }` 打印整行；此问题与 MUST FIX-2 联动（修完 `\|` 后还需检查 `\$2` 在 awk 里的正确性）| 修完 MUST FIX-2 的同时，确认 awk 命令用 `'{print $2}'`（在 bash -c 单引号字符串内，`$2` 不展开，awk 看到的是字段选择符）。若要在 spec 明文展示，写 `'{print $2}'` 即可（无 backslash） |

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| SHOULD FIX-1 | summary.md frontmatter（L7）：`status: in_progress` | request-analysis SKILL §产出要求"spec/tasks 写完 → summary.md 更新 status=waiting_review"；当前状态仍为 `in_progress`，reviewer 被 spawn 时应已是 `waiting_review`（虽然 reviewer 已能正常工作，但 SSoT 漂移）| generator 提交 spec v2 时同步更新 `summary.md` frontmatter `status: waiting_review` + `last_updated` |
| SHOULD FIX-2 | spec.md AC-4 §Markdown 渲染描述（L45）：缺明示 fenced block 内 heading 识别压制 | AC-4 描述 (a)-(d) 四类语法作为并列列表，但未说明优先级（fenced block 内 `# heading` 行如何处理？）；tasks.md T-7 说"fenced code 用栈状态机"但也未明示 heading 在 fenced block 内被压制。coding 阶段实现者可能作出两种不同决定，导致测试 fixture 不一致 | 在 AC-4 描述中加一句："fenced block 状态机优先级高于 (a)(b)(d)——fenced block 内的行不触发 heading / list / paragraph 识别" |
| SHOULD FIX-3 | spec.md §待澄清问题（L140）：deferred item 表述后无明确"本 reviewer 查后结论" | Owner 显式 deferred"BlobStore.get_size 异常路径"给 reviewer，本次已查（结论：符合假设，关闭），但 spec 本身未更新（reviewer 不改 spec，通过 review 文件关闭） | Owner 收到 review 结论后，在 spec_v2 中把这条 `[ ]` 改为 `[x] reviewer 已查：get_size 返回 None 时路由返回 404 假设成立，无需补强 AC`，以便后续阶段阅读者不疑惑 |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| NICE-1 | spec.md AC-6 (b) Tab URL state 测试描述（L53）：两种路径"createMemoryHistory" vs "降级 mock Route.useSearch" | spec 在 tasks.md T-8b 已给降级方案，但 AC-6 期望行中写"或 Route.useSearch().tab === 'pipelines'"，有歧义；实读 repos.test.tsx L2/47-53 确认仓库已有 createMemoryHistory 先例，首选方案可用 | spec.md AC-6 (b) 期望列去掉"或 Route.useSearch().tab === 'pipelines'"备选措辞，明确"优先用 createMemoryHistory 渲染 + 断言 URL contains tab=pipelines" |
| NICE-2 | spec.md §引用：缺 `apps/web/src/lib/api/pipeline.test.tsx` | T-8a blob-meta.test.tsx 要复用 vi.spyOn(globalThis, "fetch") 模式（pipeline.test.tsx L68），但 §引用未列出；实读 pipeline.test.tsx L68 确认此模式存在 | §引用加 `apps/web/src/lib/api/pipeline.test.tsx`（spyOn fetch 模式参考） |

---

## Verdict

**REVISION REQUIRED**

理由：5 条 MUST FIX 未关闭：

1. **MUST FIX-1**（AC-4/AC-8 ERE `\|` bug）：`grep -qE` 中 `\|` 是字面竖线，5MB 常量 / 图片扩展名 / error TS 三处 grep 均无法命中预期字符串，造成假阴性 / 假阳性。
2. **MUST FIX-2**（AC-6 `$()` 内 `\|` 非 pipe）：subshell 内 `\|` 不是 shell pipe，count 比较 `-ge 5` 永远 FAIL（non-numeric error），测试真跑通过也无法 PASS。
3. **MUST FIX-3**（AC-3/AC-4/AC-5 单引号 `\$` 路径 bug）：单引号内 `\$owner` 是字面 `\$`，test -f / awk 永远找不到实际文件。
4. **MUST FIX-4**（AC-7 ERE `\|` bug）：pytest passed count grep 假 FAIL，`[3-9] passed` 无法命中输出。
5. **MUST FIX-5**（AC-6 `\$2` 联动修复）：MUST FIX-2 修完后须确认 awk `{print $2}` 无 backslash。

stage 2 AC kind 必查 3 项**全 PASS**（kind 列存在 + 3 条 behavioral AC + 无 exempt）。BlobStore.get_size deferred item 已查**关闭**（行为符合 spec 假设）。validateSearch 零先例**已知**（风险表已覆盖）。DAG 无环，process_tasks stage-N 格式正确。

---

## Deferred Item 裁决

**`待澄清问题` 末尾 `BlobStore.get_size 异常路径`：已关闭。**

- `get_size` 返回 `int | None`：blob 不存在 → `ClientError` with `_NOT_FOUND_CODES` → `return None`；S3 transient error → `raise`（FastAPI 500）。
- spec 的 `if size is None: raise HTTPException(status_code=404)` 假设**完全成立**。
- **无需补强 AC**，也无需在 router 加 try/except（非 404 的 S3 error 已由 minio_store 向上传播至 FastAPI 标准 500 路径）。

---

## 后续指引（generator 修 spec_v2 前自查）

修完 spec_v2.md 后逐条自验：

```bash
cd /data/home/zhhdzhang/nta/nta-lake

SPEC=.harness/changes/repo-files-tab-v2-20260518/request_analysis/spec.md

# MUST FIX-1/4: ERE \| 清零（spec 命令里不应再有 grep -E 上下文中的 \|）
grep -nE 'grep[[:space:]]+(-[a-zA-Z]*E[a-zA-Z]*[[:space:]]+|[^ ]*-E)[^|]*\\\\[|]' "$SPEC" | head  # 期望 0 行

# MUST FIX-1/4 直观版：把 AC-4/AC-7/AC-8 grep -qE 命令复制到 shell 真跑
# 例：printf "5 * 1024 * 1024\n" | grep -qE '<修改后 pattern>' && echo HIT || echo MISS

# MUST FIX-2: AC-6 $() 内 pipe 修复验证
grep -n 'awk' "$SPEC"  # 确认无 \| awk 形式

# MUST FIX-3: 单引号 \$ 路径已改为无引号或双引号
grep -n "test -f '\|awk '.*\\\$" "$SPEC"  # 期望 0 行

# MUST FIX-5: awk \$2 确认无 backslash
grep -n "awk.*\\\$2" "$SPEC"  # 期望 0 行（或确认语境正确）

# AC kind 必查（v1 已 PASS，v2 不能回退）
awk '/^## 验收标准/{p=1;next} p && /^## /{exit} p' "$SPEC" | grep -qE '^\|[^|]*\|[[:space:]]*kind[[:space:]]*\|' && echo "kind col OK"
awk '/^## 验收标准/{p=1;next} p && /^## /{exit} p' "$SPEC" | grep -qE '^\|[[:space:]]*AC-[0-9]+[a-z]?[[:space:]]*\|[[:space:]]*(\*\*)?behavioral(\*\*)?[[:space:]]*\|' && echo "behavioral row OK"

# summary.md status（SHOULD FIX-1）
grep "status:" .harness/changes/repo-files-tab-v2-20260518/summary.md | head -1  # 期望 "status: waiting_review"
```

修完 spec_v2 后，把本 review 文件路径写入 summary.md 阶段 2 行，verdict 列标记 `REVISION REQUIRED`，状态改 `spec_review_v2` 待评，开 spec_review_v2.md 申请二次评审（只需复检 MUST FIX 各项，无需全量重评）。

---

## 本次用模型

**sonnet**（claude-sonnet-4-6）。符合 reviewer-agent.md §8 默认规约。本次评审主要工作为：grep 表达式 semantic 验证（实跑 + 反例构造）+ 路径引号语义分析 + 跨文件实读，sonnet 完全胜任，无需升级 opus。
