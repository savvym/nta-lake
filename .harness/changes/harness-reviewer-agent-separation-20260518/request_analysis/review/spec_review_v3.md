---
change_id: harness-reviewer-agent-separation-20260518
target: spec_v3.md
target_version: 3
review_version: 3
reviewer: claude-agent:harness-reviewer-agent-separation-stage2-reviewer-v3
reviewed_at: 2026-05-18T13:55:00Z
verdict: APPROVED
---

# Spec Review v3

> v3 reviewer 与 v1/v2 reviewer / generator 均不共享上下文，独立子 agent 复检 v2 MUST FIX 真修情况 + v3 自身新检查。

## v2 MUST FIX 复检（2 条）

### MUST FIX #1：baseline=225 未给推导 — **CLOSED**

证据：
- 新建产物 `request_analysis/baseline.md` 存在 ✓（前 frontmatter `purpose: 为 spec_v3.md AC-12 提供 baseline 实测产物（response to spec_review_v2 MUST FIX #1）`）。
- 实测 `grep -oE "baseline 锁定值：\*\*[0-9]+" baseline.md` → 输出 `baseline 锁定值：**225` ✓ 与 spec_v3 AC-12 钉死的 `PASS: 226$` 数学一致（225 + 1 = 226）。
- baseline.md 含 §命令（完整 bash 含环境变量 `DATAPLAT_PG_PORT=5433` 等 5 个）+ §实测输出（`PASS: 225 / FAIL: 0 / SKIP: 0`）+ §环境（容器名/端口/16 个 change block 清单）+ §风险（baseline 漂移 + mitigation）+ 时间戳 `2026-05-18T13:10:00Z` ✓。
- spec_v3 AC-12 行文同时给出动态比较的可选写法（用 `grep -oE` 从 baseline.md 提取再 +1），与本 reviewer v2 MUST FIX #1 "建议 ①" 实质一致；spec 最终选硬钉 226 + baseline.md 提供推导证据，证据链完整。

**结论：CLOSED。**

### MUST FIX #2：T-6b 会冲掉本变更 3 行 dogfood 占位符 — **CLOSED**

证据：
- 实测 `grep -rE "^reviewer:[[:space:]]+<" .harness/changes/ | grep -v _template | grep harness-reviewer-agent-separation-20260518` → 输出 **2 行**（不是 v2 reviewer 报的 3 行）：
  - `coding/review/code_review_v1.md`
  - `unit_test/review/test_review_v1.md`
- spec_v3 line 35 §背景明确写 "本变更未填 **3 行** ... 实测 **2 行**" — generator 独立 grep 后纠正 v2 reviewer 的 3 为实测 2 ✓（自我纠错是好事）；line 53 §范围 + line 105 §风险一致用 "12 - 2 本变更未填 = 30 行"。
- AC-9 命令含 `--exclude-dir=harness-reviewer-agent-separation-20260518` ✓ 实测排除本变更后剩 2 行（_template 0 + 当前 2）；T-6b 在 tasks_v3 描述同样 `--exclude-dir`。
- AC-9 阈值 `-ge 29`：
  - 现状自检：`grep -rhE "^reviewer:[[:space:]]+self-attest" .harness/changes/ --exclude-dir=_template --exclude-dir=harness-reviewer-agent-separation-20260518 | grep -cE "\(.+\)"` = **4**（core-domain-model 2 + cas-storage 2，均为既存 self-attest 偏离记录）。
  - T-6a 后增 20 行 application-owner-agent → self-attest（带括号文案）。
  - T-6b 后增 10 行 template 占位符 → self-attest（带括号文案；12 - 本变更 2 = 10）。
  - stage 3 末预期：4 + 20 + 10 = **34** ≥ 29 ✓ 余量 5（不是 spec 说的 1）。AC-9 通过没问题。
- spec_v3 §改动摘要 cell 仍写 "20 + 12 - 3 本变更未填" 用了 3 不是 2 — 与 §背景/§范围/§风险用 2 不一致，但 AC-9 实际阈值 `-ge 29` 没问题（注 SHOULD FIX #1）。

**结论：CLOSED（核心修复到位；§改动摘要数字陈述与 §范围 inconsistency 列 SHOULD FIX 不阻塞）。**

## v2 SHOULD FIX / NICE TO HAVE 接受核查

| v2 issue | generator v3 处理 | 我的判断 |
|---|---|---|
| SHOULD FIX #1 spec §跨链路 7 "3 条" vs tasks 6 条 | **顺手改 6 条** | ✓ 实测 spec_v3 line 115 §跨链路 7 写 "6 条" + tasks_v3 §process_tasks 实际 6 条（T-7/T-8/T-9 + T-12/T-13/T-14），一致 |
| SHOULD FIX #2 AC-11 全仓 | **顺手改全仓** | ✓ 实测 spec_v3 AC-11 命令 `bash scripts/_self_check.sh ... | grep -c "^FAIL.*AC-11" | grep -q "^0$"`；语义"全仓 AC-11 FAIL 行数 = 0"对，比 v2 sdk-cli-mvp block 严谨 |
| SHOULD FIX #3 spec 末缺 AC dry-parse 证据 | **接受不修**（理由：stage 2 三轮评审已替代） | ⚠️ 接受理由勉强：reviewer 在 spec 内核对 AC 命令是 stage 2 SOP；spec 内不留 dry-parse 证据，未来 reviewer 仍要重跑。**不阻塞**（列 NICE TO HAVE #1），毕竟本 v3 reviewer 替它跑了 AC-3a/3b/3c、AC-6、AC-7、AC-9、AC-12 grep |
| SHOULD FIX #4 "AC 个数" 自相矛盾 | **§澄清明确** | ✓ spec_v3 §澄清 line 92-96 写"13 AC 行（AC-3 sub-check 3 行）= 15 行 / self_check 计数 +1" + T-5 实现硬约束 "function 内部即便 3 个 grep 对外只 run_ac 一次"；表述清晰 |
| SHOULD FIX #5 summary.md SSoT | **T-0 加 stage 2 末更新** | ✓ tasks_v3 T-0 描述明确 "stage 2 末更新 summary v1→v2→v3 + frontmatter last_updated"；本 v3 reviewer 在 review 结束时 generator 应执行 T-0（**注意：当前 summary.md 是否真已更新尚需 stage 2 末独立验证；建议 generator stage 2 末跑一次 `head .harness/changes/harness-reviewer-agent-separation-20260518/summary.md | grep last_updated` 复核**） |
| NICE TO HAVE 1-5 表达/grep -v/redundancy | **接受不修** | ✓ 都不阻塞 |

## v3 自身新检查

### plan 模式 spec 7 条

- [x] 1 背景写明 v3 变化（baseline.md + 数字 2 修正 + dogfood 7 MUST FIX 累积）
- [x] 2 问题陈述沿用 v1/v2（"不变"）
- [x] 3 范围/非范围有（v3 范围新增 baseline.md 实测产物）
- [x] 4 验收标准每条可机械化 — 13 AC 全为单行 bash 表达式
- [x] 5 风险有缓解措施 — 2 条 v3 新风险（baseline 漂移 + T-6b 数 < 30）都有 mitigation 直指 AC
- [x] 6 没把已有架构当新提案 — meta-change
- [ ] 7 §改动摘要 cell 数字 "3" 与 §范围 cell 数字 "2" 不一致 — SHOULD FIX #1，**不阻塞**

### SKILL 9 条跨链路自审

- [x] 1 四链路一致：reviewer-agent / spawn 模板 / SKILL 字段规约 / self_check lint
- [x] 2 事务边界：纯文档 + shell
- [x] 3 AC 验证命令一行式：13 条全单行
- [x] 4 风险缓解 ↔ AC 映射：baseline 漂移 → AC-12；T-6b < 30 → AC-9
- [x] 5 commit 链不变
- [x] 6 反向 grep 安全性：AC-6 + AC-8 反向 + reviewer-lint 三重
- [x] 7 process_tasks：spec §跨链路 7 写 "6 条" 与 tasks §process_tasks 6 条一致
- [x] 8 AC 验证命令真跑：baseline.md 是 dry-run 实测产物；v3 reviewer 复跑 AC-3a/3b/3c + AC-6 + AC-7 + AC-9 + AC-12（部分）等 grep 通过
- [x] 9 summary.md SSoT：T-0 承诺 stage 2 末更新；generator 必须真执行

### baseline.md 自身完整性

- [x] §命令完整可复跑 + 5 个环境变量全列
- [x] §实测输出 PASS/FAIL/SKIP 三行
- [x] §环境写出 16 个 block 名单
- [x] §风险（漂移）+ mitigation（串行 + commit 前 git status）
- [ ] 缺少：self_check 文件 sha 或 commit SHA 锚定（如果跑 baseline 时 self_check 已被本变更外其他改动改了，baseline 失效；当前没人改但建议留个 commit SHA） — NICE TO HAVE #1
- [ ] 缺少：跑 baseline 时的 `git rev-parse HEAD` — NICE TO HAVE #1

### T-5 implementation 硬约束的"实现裂缝"

spec_v3 §澄清承诺 "function 内部即便 3 个 grep，对外只 run_ac 一次"；tasks_v3 T-5 描述同样承诺。但 T-5 没贴具体 bash pseudo-code；stage 3 实施时如果 generator 写出多 run_ac 调用，self_check baseline 不是 +1 而是 +N，AC-12 必 FAIL。这是 **spec 层承诺**但 **tasks 层未给守护**。

**判断**：spec_v3 已经写了硬约束（line 96 "T-5 实现硬约束"）；tasks_v3 T-5 line 50-52 也复述了。**约束声明充分；stage 4 code review 会再卡一次**。不需要 spec 加 pseudo-code（避免 spec 过度规约实现细节）。**不阻塞**，列 NICE TO HAVE #2（tasks T-5 可贴 stub）。

## 问题列表

### MUST FIX

无。

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | spec_v3 line 16 §改动摘要 cell | §改动摘要 #2 cell 写 "20 + 12 - **3** 本变更未填"，与 line 35 §背景 "实测 **2 行**"、line 53 §范围 "12 - **2** 本变更未填 = 30"、line 105 §风险 "20 + **10**（12-2）= 30" 不一致。读者会困惑到底是 2 还是 3。AC-9 阈值 -ge 29 不受影响，但表述混乱。 | §改动摘要 #2 cell 把 "3" 改 "2"，与其余三处对齐。|

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | baseline.md | 跑 baseline 时未记录 commit SHA / self_check 文件 sha。未来若 self_check 被其他 change 修改，baseline 失效但难以审计。 | baseline.md §环境段加 "commit: $(git rev-parse HEAD) / self_check sha: $(sha256sum scripts/_self_check.sh)"。|
| 2 | tasks_v3 T-5 | "对外只 run_ac 一次" 硬约束已声明，但无 pseudo-code 示例；stage 3 实施时风险中等。 | T-5 描述贴 stub：`run_reviewer_lint() { local ok=true; grep -rE "..." || ok=false; ...; if $ok; then run_ac "reviewer-lint" "PASS" "all reviewers compliant"; else run_ac "reviewer-lint" "FAIL" "..."; fi }`。|
| 3 | spec_v3 §澄清 | "13 AC 行（AC-3 sub-check 3 行）= 15 行" 仍稍绕，但比 v2 清晰多了。 | 后续 spec_v4 若有可考虑直接 "本 spec 含 15 条 AC 检查；self_check 计数 +1"（避免 13/15 双数字）。|
| 4 | spec_v3 §背景 line 35 | "v2 reviewer 报 3 行，实测 2 行，差 1 行可能是它把 stage 4 reviewer 已存在算成未填" 是 metadata；放 §背景偏自评。 | 挪 summary.md §复盘段或本 review 报告即可，spec §背景写"本变更未填 2 行"足够。|

## Verdict

**APPROVED**

理由：
- v2 MUST FIX #1（baseline 推导）：closed — baseline.md 实测产物落地，225 锁定，AC-12 数学链完整。
- v2 MUST FIX #2（T-6b 排除本变更）：closed — T-6b 命令含 `--exclude-dir`，AC-9 阈值 -ge 29 数学验证通过（实际 stage 3 末 4+20+10=34 ≥ 29 余量 5）；§背景实测从 3 自我纠正为 2 行。
- v2 SHOULD FIX：6 条全接受 / 修复，理由合理（仅 #3 spec 末 dry-parse 证据接受不修勉强，但 stage 2 reviewer 三轮已替代复检 → 不阻塞）。
- v3 自身：13 AC 全机械化；DAG 依赖一致；process_tasks spec ↔ tasks 一致（6 条）；AC-7 dogfood 时序合理；T-0 承诺 summary 更新。
- 1 条 SHOULD FIX（§改动摘要 cell 数字 2/3 不一致）+ 4 条 NICE TO HAVE，全部不阻塞。

可进 stage 3 编码实现。

## 复检指引（spec_v4 若有）

若 generator 顺手清掉 SHOULD FIX #1（§改动摘要 cell "3" → "2"），无需再开 spec_v4；直接在 stage 3 实施前更新 spec_v3 in-place（或在 summary.md §复盘记一笔），同时确认：

1. `grep -nE "本变更未填" .harness/changes/harness-reviewer-agent-separation-20260518/request_analysis/spec_v3.md` 全部数字一致（应全部是 "2"）。
2. T-0 真已执行：`grep "last_updated" .harness/changes/harness-reviewer-agent-separation-20260518/summary.md` 显示 2026-05-18 + 阶段进度表含 v1/v2/v3 / review_v1+v2+v3 链接。
3. 进 stage 3 前重跑一次 baseline 命令，确认 PASS 仍 = 225（防漂移）；若 ≠ 225，更新 baseline.md + spec_v3 AC-12 数字。
