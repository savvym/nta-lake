---
change_id: harness-reviewer-agent-separation-20260518
target: spec_v2.md
target_version: 2
review_version: 2
reviewer: claude-agent:harness-reviewer-agent-separation-stage2-reviewer-v2
reviewed_at: 2026-05-18T04:16:49Z
verdict: REVISION REQUIRED
---

# Spec Review v2

> v2 reviewer 与 v1 reviewer / generator 均不共享上下文，独立子 agent 复检。

## v1 MUST FIX 复检

| v1 MUST FIX | 状态 | 证据 |
|---|---|---|
| #1 AC-12 算法自相矛盾（spec +13=238 vs tasks +1=226+） | **partial closed** | spec_v2 §改动摘要明确选 "+1"；AC-12 写 `PASS: 226`；tasks_v2 T-11 写 `期望 PASS = baseline + 1 = 225 + 1 = 226`。两文档数字一致 ✓。但 **baseline = 225 未给推导**：spec v2 仅称 "实测于 stage 1 末"，仓库内没有任何记录该实测的产物（无 `request_analysis/baseline.md`、summary 也未记录），无法复检；且实测 `grep -cE "^[[:space:]]*run_ac" scripts/_self_check.sh = 234`（去掉 4 个函数定义行 = 230 调用），其中 ≥1 个 skipif 在当前环境会 SKIP，实际 PASS 不必然等于 225。详见 MUST FIX #1 下。|
| #2 AC-3 grep 漏覆盖 stage 4/6 | **closed** | spec_v2 拆为 AC-3a/3b/3c，分别用 `awk '/^## 阶段 2/,/^## 阶段 3/'`、`'/^## 阶段 4/,/^## 阶段 5/'`、`'/^## 阶段 6/,/^## 阶段 7/'`。我实测 `grep -E "^##" .harness/rules/development-process.md` 确认实际标题为 `## 阶段 N · ...`（不是 `###`、不是 `# `），三个 awk pattern 在当前 development-process.md 都能正确截到目标段（已验证 stage 2 段输出 "Entry Criteria：阶段 1 产物齐全" 起 13 行；stage 4 / 6 段同样成功截取）。注意：**此时段内尚未含 "独立/不允许 self-review/spawn" 字面**，所以三条 AC 现在仍 FAIL — 这是预期态（T-3 stage-3 才加），spec 是描述目标态，不是描述当前态。✓ |
| #3 历史回溯数字 7/12 与实测不符 | **partial closed** | spec_v2 改为实测 "20 application-owner-agent 行 + 12 template 占位符行 = 32 行"。我复检：(a) `grep -rE "^reviewer:[[:space:]]+application-owner-agent" .harness/changes/ \| wc -l = 20` ✓，分布在 5 closed change（adapter-firecrawl / llm-gateway-mvp / llm-qa-gen / processor-framework / sdk-cli-mvp）；(b) template 占位符 non-_template = **12** ✓，但 **分布在 4 个 change，不是 spec v2 §背景写的 "5 个早期 change"**（实测：harness-reviewer-agent-separation-20260518 本变更 3 行 + repo-files-tab 3 行 + web-mvp-pages 3 行 + web-write-flows 3 行 = 12 行 / 4 change）；(c) **关键陷阱**：这 12 行包含 **本变更自己的 3 个未填 review 占位符**（coding/review/code_review_v1 + unit_test/review/test_review_v1 + ... 还有一处 — 等本变更进入 stage 4/6 spawn 后 reviewer 字段会被子 agent 填入 `claude-agent:`，这 3 行会自然消失，**T-6b 不应回溯它们**。详见 MUST FIX #2。|

## v1 SHOULD FIX 复检（简表）

| # | v1 issue | v2 状态 | 备注 |
|---|---|---|---|
| 1 | AC-7 时序：stage 2 末 stage 4/6 文件不存在 | closed | spec_v2 改动摘要写"stage 2 末 ≥2 / stage 4 末 ≥3 / stage 6 末 ≥4 总数 4 文件"；AC-7 行文注 "stage 6 末才能完整断言"。AC-7 命令含 `2>/dev/null` 抑制 stderr。✓ |
| 2 | spec §跨链路 7 "process_tasks 6 条" 与 tasks 3 条 不一致 | **closed but inconsistently** | spec_v2 §跨链路 7 改为"tasks_v2 中将明确 3 条 process_tasks（T-12/T-13/T-14）"，但 tasks_v2 §process_tasks 实际列出 **6 条**（T-7/T-8/T-9 + T-12/T-13/T-14）。spec ↔ tasks 又对不上！详见 SHOULD FIX #1。|
| 3 | AC-13 命令空 | closed | spec_v2 AC-13 改为 `bash scripts/_self_check.sh reviewer-lint 2>&1 \| grep -q "reviewer-lint"`。✓ |
| 4 | AC-11 baseline mypy/ruff 已有 FAIL，"无回归"措辞模糊 | partial closed | spec_v2 AC-11 改为"断言 self_check AC-11 仍 PASS"，但用 `bash scripts/_self_check.sh sdk-cli-mvp 2>&1 \| grep -E "^PASS" \| grep -qE "AC-11"` — sdk-cli-mvp block 的 AC-11 与本变更"全仓 ruff/mypy 不回归"不是同一事；语义偏移。详见 SHOULD FIX #2。|
| 5 | spec stage 1 末缺 dry-parse 证据 | not closed | spec_v2 §跨链路 8 只说 "v2 在 stage 2 末手动 bash -n 验证全 13 条"，但 stage 2 评审产物里（即本 review）也没有 bash -n 结果。我直接在本 review 复检了 4 条关键 AC（AC-3a/3b/3c、AC-6、AC-7、AC-9）的命令可执行性，**AC-12 钉死字符串 `PASS: 226$` 没有任何 dry-run 证据**。详见 SHOULD FIX #3。|

## v2 自身新检查（plan 模式 7 条 + SKILL 9 条 + dogfood）

### plan 模式 spec 7 条

- [x] 1 背景写明了为什么现在做（实证 20 行 + dogfood 实证 5 MUST FIX）
- [x] 2 问题陈述沿用 v1（"不变"）
- [x] 3 范围 / 非范围都有
- [ ] 4 验收标准每条可机械化 — AC-12 钉死字符串，环境敏感；AC-11 sdk-cli-mvp block 与"全仓不回归"语义不等
- [x] 5 风险有缓解措施且与 AC 映射 — 新增 3 行风险都有 mitigation
- [x] 6 没把已有架构当新提案 — meta-change
- [ ] 7 没有遗留待澄清问题 — §"v2 调整：AC 个数" 段说 "v2 是 **15 AC**" 又说 "对齐 13 AC 模板把 AC-3a/3b/3c 视为同一 AC"，但 tasks_v2 §AC 覆盖矩阵把 AC-3a/3b/3c 当 1 行写 "T-3"，整体计数仍模糊。详见 SHOULD FIX #4。

### SKILL 9 条跨链路自审复核

- [x] 1 四链路一致（reviewer-agent.md / spawn 模板 / SKILL 字段规约 / self_check lint）
- [x] 2 事务边界（纯文档 + shell）
- [ ] 3 AC 验证命令一行式 — AC-3a/3b/3c 单行 ✓；但 AC-8 用 `grep -A40 ... \| grep -qE "! *grep" && ... \| grep -qE "self-attest"` 两次执行 `grep -A40 run_reviewer_lint scripts/_self_check.sh`，逻辑等价但效率差；不阻塞
- [ ] 4 风险缓解 ↔ AC — 新风险 "AC-3 awk 在文件无 `## 阶段 N` 时失败" 的 mitigation 写 "T-3 实施前先 cat 文件确认"，但**这是 stage 3 才执行**，stage 2 评审时该 mitigation 实际未跑；我替它跑了（结果 PASS，见 v1 MUST FIX #2 复检）。可接受。
- [x] 5 commit 链：base sdk-cli-mvp-20260518 不变
- [ ] 6 反向 grep 安全性 — AC-9 用 `grep -v _template` 按行字面过滤，**当前数据**与 `--exclude-dir=_template` 等价（12 行），但若未来 review 文件正文中出现 "_template" 字面（如复盘语 "复用 _template 的字段结构"），该过滤会误吃掉合法行。详见 NICE TO HAVE #1。
- [ ] 7 process_tasks 数量 — spec §跨链路 7 说 "3 条"，tasks_v2 §process_tasks 段实际 **6 条**。详见 SHOULD FIX #1。
- [ ] 8 AC 验证命令真跑 dry-parse — spec 自称 stage 2 末跑，但未在 spec 文档留证据
- [ ] 9 summary.md SSoT — spec_v2 §跨链路 9 写 "v2 后将更新 summary §阶段进度 v1 → v2"，**但实际 summary.md 当前阶段进度表仍写"阶段 1 in_progress v1"，未更新为 v2**；frontmatter 也仍是 stage=request_analysis，没有反映 spec/tasks 已到 v2。详见 SHOULD FIX #5。

### dogfood 实证段

spec v2 §背景末段写"dogfood 实证：5 MUST FIX + 11 SHOULD FIX + 7 NICE TO HAVE"——作为元信息有价值但放 §背景偏自夸；建议放 §决策记录或单独 §dogfood 实证段。不阻塞，列入 NICE TO HAVE #2。

## 问题列表

### MUST FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | spec_v2.md AC-12 + §改动摘要 baseline=225 | **baseline=225 数字未给推导**：spec v2 把 v1 的"+13=238 vs +1=226+"修成"+1=226"，统一性 ✓；但 baseline=225 这个数字仍是凭空声明（"实测于 stage 1 末"无产物可查）。实测 `grep -cE "^[[:space:]]*run_ac" scripts/_self_check.sh` 共 230+ 行 run_ac 调用（含 skipif 变种），具体 PASS 数依赖环境是否能跑 PG/MinIO/Redis。AC-12 命令 `grep -qE "^PASS: 226$"` 字符串完全锚定，**只要实际 baseline ≠ 225，AC-12 在 stage 3 末必 FAIL**。我尝试在本评审中跑 self_check 实测，进程 >2min 仍无输出（fork×16+ block 全跑很慢），无法快速验证。 | 二选一：① AC-12 改为**动态对比**——在 T-5 实现前先记录 `baseline=$(bash scripts/_self_check.sh 2>&1 \| awk -F: '/^PASS:/{print $2+0}')` 写入 `request_analysis/baseline.md`（stage 1 末新产物），AC-12 命令变 `[ "$(... PASS 数)" -eq $((baseline+1)) ]`；② 保留钉死字符串但 T-11 描述加 "若实测 baseline ≠ 225，本变更先开 sub-change 调 spec"。**强烈推荐 ①**。同时把 baseline 数字的来源写进 spec §改动摘要（哪个 commit、什么环境跑出 225）。|
| 2 | spec_v2.md §范围"历史回溯：32 行" + §改动摘要 + tasks T-6b | **12 行 template 占位符包含本变更自己的 3 行**：spec v2 §背景"5 个早期 change"实测错——12 行分布在 **4 个 change**（harness-reviewer-agent-separation-20260518 本变更 + repo-files-tab + web-mvp-pages + web-write-flows）。其中本变更自己的 3 行（coding/review/code_review_v1.md + unit_test/review/test_review_v1.md + 另一处）在 stage 4/6 spawn 后会被子 agent 写为 `claude-agent:...`，**T-6b 把本变更自己的 3 行也回溯成 self-attest 是错的**（会冲掉 dogfood 真实记录）。 | (a) §背景改 "12 行分布在 **4** 个 change（含本变更未填 3 行）"；(b) T-6b 描述加排除 "回溯范围排除本 change（id=harness-reviewer-agent-separation-20260518），本变更 stage 4/6 由 spawn 子 agent 填字段"；(c) T-6b 命令实际只改 9 行（12-3）；(d) AC-9 数 `-ge 32` 改 `-ge 29` 或 `-ge 32 - 3`（动态减去本变更未填行），更稳的做法是 AC-9 表达式排除本 change：`grep -rhE "^reviewer:[[:space:]]+self-attest" .harness/changes/ \| grep -v _template \| grep -v "本 change-id 路径" \| grep -cE "\\(.+\\)" -ge 29`。|

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | spec_v2.md §跨链路 7 vs tasks_v2 §process_tasks | spec §跨链路 7 写 "3 条 process_tasks（T-12/T-13/T-14）"，tasks_v2 §process_tasks 段实际列 **6 条**（T-7/T-8/T-9 + T-12/T-13/T-14；这是 v1 tasks_review SHOULD FIX #1 修复的结果）。spec 又对不上 tasks。 | spec §跨链路 7 改 "**6** 条 process_tasks（T-7/T-8/T-9 dogfood + T-12/T-13/T-14 闭环）"。|
| 2 | spec_v2.md AC-11 | AC-11 命令只看 sdk-cli-mvp block 是否 PASS AC-11，与"全仓 ruff/mypy 不回归"语义不等价。若本变更意外动了 Python，其他 block 的 AC-11 可能 FAIL 而 sdk-cli-mvp 仍 PASS。 | AC-11 命令改 `grep -E "^FAIL" output \| grep -c "AC-11" == 0`（全仓 AC-11 行 FAIL 数 = 0），或简化为 "前后跑 self_check，新增 FAIL 行数 = 0"。|
| 3 | spec_v2.md §跨链路 8 + 整个 spec 末尾 | spec 自称 "stage 2 末手动 bash -n 验证全 13 条"，但 stage 2 评审是 reviewer 子 agent 写 review（不是 generator 写更多 spec 内容）；validate 应在 spec 文档 §"AC dry-parse 证据" 段留下，或挪到 T-0/T-1 之前作为产物。 | spec 末尾加 §"AC dry-parse 证据"，把 13 条命令 `bash -n` 输出贴上（或 sha + timestamp）。|
| 4 | spec_v2.md §"v2 调整：AC 个数" | 文本说 "v2 是 15 AC"，又说 "为对齐 13 AC 模板把 AC-3a/3b/3c 视为同一 AC-3" — 自我矛盾；reviewer-lint 在 self_check 内是 **1 个还是多个 run_ac 调用**？spec §澄清说 "1 个 PASS"，但 T-5 实现可能写成 3 个独立 `run_ac` 调用（反向 grep #1 + 反向 grep #2 + 白名单），则 self_check baseline+3 不是 +1，AC-12 必 FAIL。 | (a) 明确选 "13 AC 计数，AC-3 是 3 sub-check"；(b) §澄清段加硬约束 "**T-5 实现 run_reviewer_lint 内部即便有 3 个 grep，对外只 echo 1 行 PASS/FAIL**"，并把这条写进 T-5 描述。|
| 5 | summary.md §阶段进度 + frontmatter | spec_v2 §跨链路 9 承诺 "更新 summary §阶段进度 v1 → v2"，但 summary.md 当前仍写 "1 需求分析 in_progress v1"、frontmatter stage=request_analysis（未升 stage 2）。generator 没履行承诺。 | T-0（或本 stage 2 末）更新 summary：阶段 1 行加 "v2"，阶段 2 行加 review_v1 + review_v2 链接，frontmatter `last_updated` 改 2026-05-18。|

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | spec_v2.md AC-9 | `grep -v _template` 按行字面过滤，未来 review 正文出现 `_template` 字面会误吃。当前数据 PASS。 | 改为 `--exclude-dir=_template` 更严谨（实测两种现在等价但语义更准）。|
| 2 | spec_v2.md §背景末段 | "dogfood 实证：5 MUST FIX + 11 SHOULD FIX + 7 NICE TO HAVE" 元信息有价值，但放 §背景偏自夸；spec 是给未来读者看的，dogfood 数字属于本变更的事后复盘。 | 挪到 summary.md §复盘段，或单独 spec §dogfood 实证。|
| 3 | spec_v2.md AC-6 | AC-6 反向 grep 与 reviewer-lint 反向 grep #1 是同一条；spec 没明示 AC-6 与 reviewer-lint 是 redundant 还是分层（spec-level vs 运行时-level） | spec §AC-6 注 "与 reviewer-lint 反向 grep #1 同；分层冗余可接受"。|
| 4 | spec_v2.md AC-5 | `grep -q "run_reviewer_lint\|reviewer_field_lint" scripts/_self_check.sh` 用 alternation 兼容两个命名 — 但 T-5 实际命名必须固定其一，AC-5 模糊。 | T-5 固定一个 function 名（建议 `run_reviewer_lint`），AC-5 命令同步收紧。|
| 5 | spec_v2.md §"v2 调整：AC 个数" | "13 AC（AC-3 单条）→ 15 AC（AC-3 拆 3）→ 视为 13 AC" 的论证绕；外部读者读不懂。 | 直接说 "spec 含 15 条 AC 行，但 reviewer-lint 在 self_check 算 1 个 AC（baseline+1）"。|

## Verdict

**REVISION REQUIRED**

理由：2 条 MUST FIX 未关闭：

1. **AC-12 baseline=225 未给推导，钉死字符串 `PASS: 226$` 在 stage 3 末高概率 FAIL**——v1 MUST FIX #1 的根因（数字凭空）只修了一半（让 spec 和 tasks 数字对齐），但 baseline 本身未实测落地。
2. **T-6b 会把本变更自己的 3 行 template 占位符也回溯成 self-attest**——会冲掉 dogfood 真实记录；§背景"5 个早期 change"也实测错。

v1 MUST FIX #2（AC-3 拆分）✓ 真修；MUST FIX #3 数字（20 行 + 12 行）✓ 实测匹配；其余 SHOULD FIX 大体收口。

## 后续指引

Generator 修 spec_v3 后请自检：

1. **AC-12 baseline 推导**：在 stage 1 / stage 2 末跑 `DATAPLAT_PG_PORT=5433 DATAPLAT_MINIO_PORT=9100 DATAPLAT_MINIO_ACCESS_KEY=dataplat DATAPLAT_MINIO_SECRET_KEY=dataplat-secret DATAPLAT_REDIS_PORT=6379 bash scripts/_self_check.sh 2>&1 \| awk -F: '/^PASS:/{print $2+0}'` 拿到精确 baseline，写入 spec §改动摘要 + `request_analysis/baseline.md` 作为新产物。AC-12 改用 `[ "$(... PASS 数)" -eq $((baseline+1)) ]` 动态比较（不钉死 226）。
2. **T-6b 排除本 change**：把 §背景"5 个早期 change"改 "4 个 change（含本变更自身未填 3 行）"；T-6b 命令加 `grep -v harness-reviewer-agent-separation-20260518`；AC-9 阈值改 `-ge 29` 或表达式排除本 change。
3. **process_tasks 数量**：spec §跨链路 7 改 "6 条" 与 tasks §process_tasks 一致。
4. **summary.md SSoT**：阶段 1 升 v2 + 阶段 2 加 v1/v2 review 链接 + frontmatter last_updated。
5. **AC-11 全仓 / AC-13 自递归命令** 收紧（见 SHOULD FIX #2、NICE TO HAVE #4）。
6. **T-5 输出 1 行 PASS** 硬约束写入任务描述（见 SHOULD FIX #4）。
7. 重提 spec_v3 + tasks_v3 后开 `spec_review_v3.md` / `tasks_review_v3.md`（保留 v1/v2 历史）。
