---
change_id: harness-ac-behavioral-tier-20260518
target: tasks.md
target_version: 1
review_version: 1
reviewer: claude-agent:harness-ac-behavioral-tier-20260518-stage2-reviewer-v1
reviewed_at: 2026-05-18T09:30:00Z
verdict: REVISION REQUIRED
---

# Tasks Review v1

## 检查清单结论

### expert-reviewer SKILL §1 tasks 部分 4 条

- [x] 每个任务粒度合理（1-3 小时）：T-1（SKILL 加段 + 18-19 ID 名单）可能略宽，~3-4h；其余 T-2..T-7 在 1-3h 内可完成。
- [x] depends_on 无环：DAG 已校验 `T-1 → {T-2, T-4, T-5}; T-4 → T-6 → T-7; T-3 独立`，无环。
- [x] 评审 / 单测 / CI / 部署 / 用户确认 对应任务都存在（process_tasks 6 条都在）。
- [x] 没有"做完整个系统"类目标任务。
- [x] 每条 AC 至少一个 T-* 关联 + 覆盖矩阵清晰。

### 与 spec.md 的 trace 一致性

- [x] AC-1 → T-1, T-5 ✓
- [x] AC-2 → T-1 ✓
- [x] AC-3 → T-2 ✓
- [x] AC-4 → T-4, T-6, T-7 ✓（但 fixture 真跑机制描述不足，详 MUST FIX-1）
- [x] AC-5 → T-3 ✓
- [x] AC-6 → T-4, T-5, T-6 ✓
- [x] AC-7 → T-1 ✓
- [x] AC-8 → T-6, T-7 ✓

## 问题列表

### MUST FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | tasks.md T-4（L52-L66）+ T-6（L80-L90） | **依赖 spec MUST FIX-1（awk 表达式语义错）+ MUST FIX-6（fixture 真跑机制）连锁**：T-4 description 写"对剩余 change：用 awk 截取 '## 验收标准' 到下一个 '## ' 之间的段"——这正是 spec.md AC-4 的错误 awk 表达式的复述。一旦实现，对所有正常 spec 都会返回 1 行（仅章节标题），lint 大面积误报。T-6 写"AC-4 行为型（构造 /tmp 临时不合规 spec.md fixture + 临时豁免清单 override + cleanup trap）"——但 T-4 现设计无 `AC_KIND_LINT_SCAN_DIR` / `AC_KIND_LINT_EXEMPT_OVERRIDE` 注入点，T-6 fixture 无法真跑（详 spec_review MUST FIX-6）。 | (a) T-4 description 把 awk 改为 `awk '/^## 验收标准/{p=1;next} p && /^## /{exit} p'`；(b) T-4 description 加"提供 `AC_KIND_LINT_SCAN_DIR` 与 `AC_KIND_LINT_EXEMPT_OVERRIDE` 两个 env 注入入口；fail-fast 行为通过 subshell 隔离 fixture 测试"；(c) T-6 description 重写 fixture：在 `run_harness_ac_behavioral_tier()` 内部以 subshell + env override 跑两次 `run_ac_kind_lint`（PASS / FAIL 场景）；retVal 校验；trap cleanup `/tmp/fixture-*`。 |
| 2 | tasks.md T-1（L15-L26） | **T-1 任务覆盖范围过载 + 与 spec MUST FIX-2/3/5 联动**：单一 T-1 同时负责 (i) 加 AC 分层规约段、(ii) 加 18 个 ID 豁免名单（应为 19 + 分类）、(iii) 加判定指引（grep/test -f/dry-import → static；HTTP roundtrip 等 → behavioral）、(iv) 加 `ac_kind_lint: exempt` 自声明机制、(v) "豁免判定标准"小段（spec MUST FIX-5）、(vi) 混合 AC 拆分示例（spec SHOULD FIX-4）、(vii) behavioral 三层判定（spec SHOULD FIX-6）。任务粒度严重偏大（实际 ≥3h），且修 spec MUST FIX 后会进一步膨胀。 | 拆为：T-1a "SKILL 加 AC 分层规约定义 + 判定指引 + behavioral 三层"；T-1b "SKILL 加豁免清单（19 ID 分两类）+ 自声明机制 + 豁免判定标准"；T-1c "SKILL 加混合 AC 拆分示例"。各 ~1h。 |
| 3 | tasks.md T-6（L80-L90） | **T-6 与 spec MUST FIX-7（缺 reviewer 字段约束风险）联动**：T-6 现仅覆盖 AC-4 + AC-6 + AC-8，未覆盖"lint 同时硬检查 kind 列表头存在"的双条件断言（spec MUST FIX-7 要求 AC-4 扩展）。 | T-6 description 加"AC-4 验证扩展：lint 函数除了 grep behavioral，还要 grep AC 表头是否含 `kind` 列（`grep -q '\| kind \|' <spec.md>` 或同等）；二者缺一则 FAIL；fixture 测试也覆盖此条件"。 |
| 4 | tasks.md T-3（L40-L50） | **T-3 与 spec MUST FIX-4（self-attest 字段闭合）联动**：T-3 只写"加硬约束文案 + self-attest 模板示例"，但未要求文案必含 (i) 默认硬约束 verdict=PASS、(ii) 替代路径 self-attest + 必填字段（理由 / 本机证据列表 / 跑过的命令 / 时间）、(iii) 禁止纯 deferred。 | T-3 description 重写为具体 4 个 checkpoint（默认硬约束 / self-attest 替代路径 + 4 个必填字段 / 禁止纯 deferred / SKILL 引用），让 stage 3 编码者无歧义。 |

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | tasks.md L123（P-ci status=deferred）+ L127（P-deploy status=skipped） | 这两条 process_tasks 在 spec AC-5 / development-process.md stage 9 "不允许 deferred" 文案上下文里，自身就是反例。若 spec MUST FIX-4 收紧 self-attest 字段，本 tasks 也必须改 status=`self-attest` + 注理由 | 修 spec MUST FIX-4 时同步：P-ci.status=`self-attest`，notes="项目无 remote，长期未决"；P-deploy.status=`self-attest`，notes="纯 harness 无部署面" |
| 2 | tasks.md T-5（L68-L77） | T-5 仅改 `_template/request_analysis/spec.md` 示例 AC 表加 `kind` 列；但 spec 非范围明确写"**不**改 _template/request_analysis/spec.md 表头自动加 kind 列"——T-5 与 spec 非范围**直接矛盾** | 二选一：(a) spec 非范围删除"不改 _template 表头"，明示要加；(b) 修 T-5 description 只在 _template 加"示例 + 注释"而不动表头列定义。建议 (a)，因为新 change 复制 _template 时自然带 kind 列利于扩散 |
| 3 | tasks.md T-4 / T-6 description 中 estimated_stage | T-4 estimated_stage=coding ✓；T-6 estimated_stage=coding ✓；但 T-6 含"fixture 行为型 + AC-4 真跑断言"——这是 stage 5 单测性质的工作 | T-6 拆分：编码部分（block 函数定义）→ stage coding；行为型 fixture 真跑断言部分 → 移到 T-7 或新加 T-8（estimated_stage=unit_test） |
| 4 | tasks.md L99（T-7 description "DATAPLAT_PG_PORT=5433 ..."） | T-7 同 spec AC-8，会撞 self_check 总数动态变化（spec SHOULD FIX-5）；T-7 期望"本 change block 8/8 PASS、global run_ac_kind_lint PASS"但未声明若新 lint 触发已 closed 18-19 个 change 中任意一个 FAIL 怎么办（理论上都豁免；但 fail-fast 设计下一旦触发就停） | T-7 description 加"若新 lint 对豁免 change 误报，回 T-1 / T-4 修豁免读取逻辑"作为 rollback 路径；同时 T-7 期望值改为"本 change block 8/8 PASS"，不再精确 `PASS: 238`（同 spec SHOULD FIX-5） |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | tasks.md L137-L141（DAG 图） | DAG 图正确，但 T-3 独立可加注释"独立可并行实现，覆盖 rules 文档；与 T-1 SKILL 改动解耦" | 文档说明，不阻塞 |
| 2 | tasks.md L147（验收覆盖矩阵） | 覆盖矩阵中 AC-6 关联 T-4/T-5/T-6 三个任务，关联范围广；可注 AC-6 是"汇总 AC"（self_check 调用 + spec 自含 kind 列 + 本 change 范本） | 注释清晰；NICE |
| 3 | tasks.md 与 spec.md 关键决策栏 | spec 决策栏写"AC kind 二分不引入 mixed"，但 tasks 没有相应"如发现混合型 AC 必须拆分"的任务卡——只能靠 reviewer / SKILL 文档抓 | 可选在 T-2 加一句"reviewer 必查项含'若发现混合型 AC，必给 MUST FIX 拆分建议'" |

## Verdict

**REVISION REQUIRED**

理由：tasks.md 在结构、DAG、覆盖矩阵上整体良好（粒度可控、AC 全覆盖、process_tasks 6 条齐全），主要问题在于它**与 spec 的 MUST FIX 严格联动**——spec 修 v2 后，tasks 必须同步 v2 修 T-1（拆分）、T-3（4 checkpoint）、T-4（awk 修正 + env 入口）、T-6（fixture 真跑 + kind 列表头双检），以及与 spec 非范围矛盾的 T-5（_template 表头）。tasks 不能独立 APPROVE。

修完 tasks_v2 后重提评审。

## 复检指引（generator 修 v2 后自查命令）

```bash
cd /data/home/zhhdzhang/nta/nta-lake

# MUST FIX-1: T-4 描述含修正 awk + env 入口
grep -nE "awk.*p=1.*next|AC_KIND_LINT_SCAN_DIR|AC_KIND_LINT_EXEMPT_OVERRIDE" .harness/changes/harness-ac-behavioral-tier-20260518/request_analysis/tasks.md
# 期望：≥3 行命中

# MUST FIX-2: T-1 拆为 T-1a/T-1b/T-1c
grep -cE "id: T-1[abc]" .harness/changes/harness-ac-behavioral-tier-20260518/request_analysis/tasks.md
# 期望：3

# MUST FIX-3: T-6 含 kind 列表头双检
grep -q "kind 列" .harness/changes/harness-ac-behavioral-tier-20260518/request_analysis/tasks.md && echo PASS
# 期望：PASS

# MUST FIX-4: T-3 含 4 checkpoint
grep -cE "verdict=PASS|self-attest|必填字段|禁止.*deferred" .harness/changes/harness-ac-behavioral-tier-20260518/request_analysis/tasks.md
# 期望：≥4

# SHOULD FIX-1: P-ci / P-deploy 改 self-attest
grep -cE "status:.*self-attest" .harness/changes/harness-ac-behavioral-tier-20260518/request_analysis/tasks.md
# 期望：2（P-ci + P-deploy）

# SHOULD FIX-2: T-5 与 spec 非范围对齐
grep -q "_template" .harness/changes/harness-ac-behavioral-tier-20260518/request_analysis/spec.md
# 修 spec 非范围或修 T-5；两边一致即可

# DAG 无环 + 覆盖矩阵完整
grep -A 5 "## DAG 健全性" .harness/changes/harness-ac-behavioral-tier-20260518/request_analysis/tasks.md
grep -A 12 "## 验收覆盖矩阵" .harness/changes/harness-ac-behavioral-tier-20260518/request_analysis/tasks.md
# 期望：DAG 图无环；覆盖矩阵每条 AC ≥1 任务
```

复检 v2 tasks 重提评审时，请同步开 `tasks_review_v2.md`（不要覆盖本 v1 文件）。
