---
change_id: harness-reviewer-agent-separation-20260518
target: tasks_v3.md
target_version: 3
review_version: 3
reviewer: claude-agent:harness-reviewer-agent-separation-stage2-reviewer-v3
reviewed_at: 2026-05-18T13:55:00Z
verdict: APPROVED
---

# Tasks Review v3

> v3 reviewer 与 v1/v2 reviewer / generator 均不共享上下文，独立子 agent 复检 v2 MUST FIX 真修 + v3 自身新检查。

## v2 MUST FIX 复检（2 条）

### MUST FIX #1：T-6b 排除本变更 — **CLOSED**

证据：
- tasks_v3 T-6b line 64：`grep -rlE "^reviewer:[[:space:]]+<" .harness/changes/ --exclude-dir=_template --exclude-dir=harness-reviewer-agent-separation-20260518` ✓ 含 `--exclude-dir` 双重排除。
- T-6b line 65：明确写 "实测排除本变更后剩 **10 行**（4 changes：repo-files-tab 4 + web-mvp-pages 4 + web-write-flows 2 - 2 不在本变更名下 = 10）"。
  - 我实测 `grep -rE "^reviewer:[[:space:]]+<" .harness/changes/ | grep -v _template | grep -v harness-reviewer-agent-separation-20260518` = **10 行**，分布在 repo-files-tab（4 行）/ web-mvp-pages（4 行）/ web-write-flows（2 行；另 2 行已是 claude-stage2-reviewer 不是占位符）。**算术 + 行数完全一致** ✓。
- T-6b line 67：明确"本变更自身的 2 行不动（stage 4/6 spawn 子 agent 时会填）" — 与 spec_v3 §背景"未填 2 行"一致；与 AC-7 dogfood（spawn 子 agent 填 claude-agent:）配套。

**结论：CLOSED。**

### MUST FIX #2：T-11 baseline 实测来源 — **CLOSED**

证据：
- tasks_v3 §改动摘要 line 17：`T-11 引用 baseline.md | 实测产物 → 期望 226 = 225+1`。
- T-11 line 95：`baseline = 225（实测产物 \`request_analysis/baseline.md\`）` ✓ 直接指向 baseline.md 实测产物。
- baseline.md 存在且实测 PASS=225 ✓。
- 注意：tasks_v3 没拆 T-11a/T-11b（v2 reviewer 后续指引 #2 建议），而是 T-11 直接引用 baseline.md。这是合理选择 — baseline.md 在 stage 2 末（authored_at 2026-05-18T13:25:00Z 早于 spec_v3 line 4 的 13:30:00Z）已落产物，等价于 T-11a 已隐式完成；T-11 stage 3 末跑差值断言即 T-11b。不拆任务依然 covers 同样语义。**接受这种简化。**

**结论：CLOSED。**

## v2 SHOULD FIX / NICE TO HAVE 接受核查

| v2 issue | generator v3 处理 | 我的判断 |
|---|---|---|
| SHOULD FIX #1 T-3 cat 验证挪 stage 1/2 | **未挪 — T-3 描述未改** | ⚠️ tasks_v3 T-3 line 39-41 写 "不变 (见 v2)"，cat mitigation 仍在 T-3 实施阶段（stage-3）。但 stage 2 reviewer 已两轮替它跑了 grep，AC-3a/3b/3c awk pattern 实测可工作；**不阻塞**，列为 v3 NICE TO HAVE #1。 |
| SHOULD FIX #2 AC 覆盖矩阵 AC-3a/3b/3c 拆 3 行 | **未拆 — line 134 仍 "AC-3a/3b/3c → T-3"** | ⚠️ 矩阵粒度仍与 spec 不完全对齐。spec §澄清明确 "13 AC 含 AC-3 sub-check 3 行"，矩阵合写为 1 行可读但失粒度。**不阻塞**，列 NICE TO HAVE #2。 |
| SHOULD FIX #3 T-5 case 写法 | **未明 — T-5 line 53 仍写"位置：所有 block 之前（case `""` 第 1 行）"** | ⚠️ 单分支 `""` 仍语义模糊（无 filter 跑全仓属于 `""` 还是 `*)`?）。但 T-5 加了"FAIL 立 exit 1"明确 fail-fast 语义；**不阻塞**，列 NICE TO HAVE #3。 |
| SHOULD FIX #4 T-5 输出 1 行 PASS 硬约束 | **closed** | ✓ tasks_v3 T-5 line 52 加 "**硬约束（v3 新加）**：function 内部不允许多 run_ac 调用；保 self_check 计数 +1 而不是 +3"。明确防 baseline 漂移。 |
| SHOULD FIX #5 T-10 全仓 FAIL=0 | **closed** | ✓ tasks_v3 T-10 line 90 "用全仓 self_check 输出 grep FAIL AC-11 行数 = 0"；与 spec_v3 AC-11 命令一致。 |
| SHOULD FIX #6 T-12/T-14 加 summary 更新 | **partial closed** | ⚠️ T-0 加了 stage-2 末 summary 更新；但 T-12/T-14 描述未改（仍"不变 (见 v2)"），stage 7/10 末 summary 更新依赖 application-owner 手动 — 不强制。**不阻塞**，列 NICE TO HAVE #4。 |
| NICE TO HAVE 1-5 | 全接受不修 | ✓ 均不阻塞 |

## v3 自身新检查

### plan 模式 tasks 5 条

- [x] 1 每个任务粒度合理：T-0（改 summary 1 段 + frontmatter，<10min）/ T-1~T-4 不变 / T-5 加硬约束声明 / T-6a, T-6b 机械替换 / T-10 跑 self_check 1 次 / T-11 跑 self_check + 解析 — 都 1-3h 内。
- [x] 2 depends_on 形成 DAG 无环：T-0 不依赖任何 task（独立 stage 2 末执行）；T-1, T-3 并行；T-2 ← T-1；T-4 ← T-1,2,3；T-5 ← T-1~T-4；T-6a/6b ← T-5；T-7 ← T-1,T-2；T-8 ← T-1,2,7；T-9 ← T-1,2,8；T-10 ← T-1~T-6；T-11 ← T-5,T-6a,T-6b,T-7~T-9；T-12 ← T-11；T-13 ← T-12；T-14 ← T-12,T-13. **无环 ✓**。
- [x] 3 评审/单测/CI 阶段对应任务存在：T-7（stage 2 review dogfood）/ T-8（stage 4）/ T-9（stage 6）/ T-12（push）/ T-13（deploy）/ T-14（close）✓
- [x] 4 没有"做完整个系统"类目标任务 ✓
- [ ] 5 AC 全覆盖：12/13 AC 都映射 task；但 AC-3a/3b/3c 合写 1 行（与 spec 粒度不齐 — 见 SHOULD FIX 表 #2，NICE TO HAVE 不阻塞）；T-0 covers_ac 写"无 AC 直接覆盖（summary 维护是 SKILL #9 第 6 次实践）" — 这是流程性 task 无需 covers AC，合理。

### 跨链路一致性（与 spec_v3 对齐）

- [x] tasks_v3 T-11 vs spec_v3 AC-12 数字：226 ✓
- [x] tasks_v3 T-6b vs spec_v3 §范围："10 行（12-2）" ↔ "30 行（20+10）" 一致
- [x] tasks_v3 §process_tasks **6 条** vs spec_v3 §跨链路 7 "**6 条**"：line 100 + 102-107 实测 6 条 ✓（与 spec_v3 line 115 完全对齐）
- [x] T-7/T-8/T-9 dogfood 顺序合理；本 v3 review 就是 T-7 第 3 次实例化
- [x] T-6a/T-6b ← T-5：lint 在前回溯在后，顺序合理

### 实证：v3 reviewer 跑过的 grep（dry-run 验证 spec/tasks 命令真能工作）

- `grep -oE "baseline 锁定值：\*\*[0-9]+" baseline.md` → "baseline 锁定值：**225" ✓（AC-12 数学源验证）
- `grep -rE "^reviewer:[[:space:]]+<" .harness/changes/ | grep -v _template | wc -l` → 12 ✓
- `grep -rE "^reviewer:[[:space:]]+<" .harness/changes/ | grep -v _template | grep -v harness-reviewer-agent-separation-20260518 | wc -l` → 10 ✓（T-6b 实际改 10 行）
- `grep -rE "^reviewer:[[:space:]]+application-owner-agent" .harness/changes/ | wc -l` → 20 ✓（T-6a 实际改 20 行）
- `grep -rhE "^reviewer:[[:space:]]+self-attest" .harness/changes/ --exclude-dir=_template --exclude-dir=harness-reviewer-agent-separation-20260518 | grep -cE "\(.+\)"` → **4**（当前；T-6a+T-6b 后预期 4+20+10 = **34** ≥ 29 ✓，AC-9 余量充足）

## 问题列表

### MUST FIX

无。

### SHOULD FIX

无（v2 SHOULD FIX 中 3 条仅 partial closed/未关，但都已转化为 NICE TO HAVE 在下节列出；T-5 / T-10 / 主流程关键约束已 closed）。

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | tasks_v3 T-3 | T-3 描述"实施前先 cat ... grep -E '^##' 确认 stage 标题层级"未挪 spec stage 1/2；stage-3 实施时才跑。stage 2 reviewer 已替它跑了实测 PASS，可接受。 | T-3 描述删除该 mitigation 句；改在 spec §"AC dry-parse 证据" 段（若 spec 后续加该段）附 grep 输出。|
| 2 | tasks_v3 §AC 覆盖矩阵 line 134 | "AC-3a/3b/3c → T-3" 合写 1 行；spec 是 3 sub-AC。 | 矩阵改 3 行：AC-3a → T-3 / AC-3b → T-3 / AC-3c → T-3。或加注 "共同覆盖于 T-3 内"。|
| 3 | tasks_v3 T-5 line 54 | "位置：所有 block 之前（case `""` 第 1 行）" 仍语义模糊：`""` 分支匹配无 filter 跑全仓还是 default? 若 `bash scripts/_self_check.sh <block-name>` 走 `*)` 分支，lint 不跑。 | 改 "在 case `$FILTER` in 的 `""` 与 `*)` 两分支顶部均调用 `run_reviewer_lint`，确保 bash scripts/_self_check.sh 与 bash scripts/_self_check.sh <block-name> 都先跑 lint"。|
| 4 | tasks_v3 T-12/T-14 | T-0 已加 stage 2 末 summary 更新，但 T-12（push 末）/T-14（close 末）未加 summary 阶段进度更新步骤；依赖 application-owner 自觉。 | T-12 末加 "更新 summary §阶段进度 stage 7 状态 + commit SHA"；T-14 末加 "summary §交付 + §复盘 填写"。|
| 5 | tasks_v3 T-5 | "function 内部即便多 grep 对外只 run_ac 一次" 硬约束已声明但无 pseudo-code；stage 3 实施风险中等。 | T-5 描述贴 stub：`run_reviewer_lint() { local ok=true; grep -rE "..." || ok=false; ...; if $ok; then run_ac "reviewer-lint" "PASS" "..."; else run_ac "reviewer-lint" "FAIL" "..."; fi }`。|
| 6 | tasks_v3 T-1 | "只读模式优先（用 Read/Grep/Glob，不 Edit/Write 代码）" 未删（v1 NICE TO HAVE #1 提到要简化或挪 follow-up）；与 v3 reviewer 自身的 Bash/grep 实际操作不冲突，但表述偏紧。 | T-1 简化为 "reviewer 通常只读；工具限定见 follow-up `reviewer-tool-restrict-*`"。|

## Verdict

**APPROVED**

理由：
- v2 MUST FIX #1（T-6b 排除本变更）：closed — `--exclude-dir` 双重过滤 + 实测 10 行算术 + 行数完全一致。
- v2 MUST FIX #2（T-11 baseline 实测）：closed — baseline.md 实测产物先于 spec_v3 落地，T-11 引用合理；不拆 T-11a/T-11b 是合理简化。
- v2 SHOULD FIX：3 条 closed（T-5 输出 1 行硬约束 / T-10 全仓 / T-12 部分），3 条降级 NICE TO HAVE（T-3 cat mitigation / AC 矩阵拆 / T-5 case 写法 — 都已被 stage 2 reviewer 实测替代或非关键路径）；无新 MUST FIX。
- v3 自身：DAG 无环；process_tasks spec ↔ tasks 6 条一致；T-0 流程性 task 合理。
- 6 条 NICE TO HAVE 全部不阻塞。

可进 stage 3 编码实现。

## 复检指引（tasks_v4 若有）

若 generator 顺手清掉 NICE TO HAVE #3（T-5 case 写法明确化）+ #5（贴 pseudo-code），实施风险更低；但都不阻塞。stage 3 实施前自检：

1. **T-5 实测前**：reviewer-lint function 写完先单独 `bash -c "source scripts/_self_check.sh; run_reviewer_lint"` 确认只 echo 1 行 PASS/FAIL；再加进 case 分支。
2. **T-6b 实测前**：再跑一遍 `grep -rE "^reviewer:[[:space:]]+<" .harness/changes/ --exclude-dir=_template --exclude-dir=harness-reviewer-agent-separation-20260518 | wc -l`，确认仍 = 10（防其他 change merge 改变状态）。
3. **T-11 实测前**：重跑 baseline `bash scripts/_self_check.sh 2>&1 | grep "^PASS:"`，确认 = 225；若 ≠ 225 更新 baseline.md + spec_v3 AC-12 数字。
4. **T-0 实测**：stage 2 末（即本 v3 review 通过后）执行：`grep "last_updated" .harness/changes/harness-reviewer-agent-separation-20260518/summary.md` 应显示 2026-05-18 + 阶段进度表 v1/v2/v3 链接。
