---
change_id: repo-files-tab-v2-20260518
target: tasks.md
target_version: 1
review_version: 1
reviewer: claude-agent:repo-files-tab-v2-20260518-stage2-reviewer-v1
reviewed_at: 2026-05-18T22:00:00Z
verdict: REVISION REQUIRED
must_fix_count: 0
should_fix_count: 1
nice_to_have_count: 1
---

# Tasks Review v1

> 评审者声明：同 spec_review_v1.md（独立 sub-agent，sonnet，未参与撰写）。

---

## 检查清单结论（expert-reviewer SKILL §1 plan 模式 tasks）

- [x] 每个任务粒度合理（1-3 小时可完成：T-1 ~30min / T-2 ~1h / T-3 ~1h / T-4 ~30min / T-5 ~2h / T-6 ~30min / T-7 ~3h / T-8a/b/c 各 ~1h / T-9 ~30min 触发 / T-10 ~1h）
- [x] depends_on 形成 DAG 无环
- [x] 评审 / 单测 / CI / 部署阶段任务存在（process_tasks 7 条，estimated_stage 用 stage-N 格式）
- [x] 无"做完整个系统"类目标性任务

---

## DAG 健全性验证（手动 trace）

```
T-1 (depends_on:[])   → T-2 (depends_on:[T-1])   → T-3 (depends_on:[T-2]) ──────────────────┐
T-4 (depends_on:[])   → T-7 (depends_on:[T-4])    → T-8c (depends_on:[T-7]) ─────────────────┤
T-4 (depends_on:[])   → T-8a (depends_on:[T-4])                            ─────────────────┤
T-5 (depends_on:[])   → T-6 (depends_on:[T-5])                                              │
T-5 (depends_on:[])   → T-8b (depends_on:[T-5])                            ─────────────────┤
                                                                                             ├──→ T-9
T-2, T-5, T-6, T-7   ────────────────────────────────────────────────────────────────────── → T-10
```

**无环**。终点为 T-9（真跑 vitest + pytest + build）和 T-10（self_check block）。tasks.md §DAG 健全性图示与以上 trace 一致。

---

## 验收覆盖矩阵验证

| AC | kind | 关联任务 | 非 process_tasks 任务数 | 合规 |
|---|---|---|---|---|
| AC-1 | static | T-1, T-2, T-10 | 3（T-1/T-2/T-10 均为非 process） | PASS（≥2） |
| AC-2 | static | T-4, T-10 | 2 | PASS |
| AC-3 | static | T-5, T-10 | 2 | PASS |
| AC-4 | static | T-7, T-10 | 2 | PASS |
| AC-5 | static | T-6, T-10 | 2 | PASS |
| AC-6 | behavioral | T-8a, T-8b, T-8c, T-9, T-10 | 5 | PASS |
| AC-7 | behavioral | T-3, T-9, T-10 | 3 | PASS |
| AC-8 | behavioral | T-9, T-10 | 2 | PASS |

每条 AC 均有 ≥2 个非 process_tasks 任务覆盖，覆盖矩阵**健全**。

---

## process_tasks 完整性验证

```yaml
process_tasks:
  P-spec-review    estimated_stage: stage-2  ✅
  P-code-review    estimated_stage: stage-4  ✅
  P-test-review    estimated_stage: stage-6  ✅
  P-push           estimated_stage: stage-7  ✅
  P-ci             estimated_stage: stage-8  ✅（self-attest，有 notes 说明）
  P-deploy         estimated_stage: stage-9  ✅（有 notes：必须真跑 deploy_verify）
  P-user-confirm   estimated_stage: stage-10 ✅
```

`grep -cE "estimated_stage: stage-(2|4|6|7|8|9|10)" tasks.md` = 7，满足 SKILL §跨 AC 第 7 条"期望 ≥6"（含 stage-8 self-attest）。

注：本 change tasks.md 包含 7 个 process_tasks（较 pipeline-ui-tab 多 stage-8），命名格式全部正确。

---

## 任务实现可行性评估

| 任务 | 潜在风险 | 评估 |
|---|---|---|
| T-5（RepoDetailPage Tabs 重构） | validateSearch 仓库无先例；TanStack Router search param 类型推断可能报 tsc 错 | spec 已覆盖（风险 #1 + 降级方案）；T-9 npm run build 含 tsc，自动检测 |
| T-7（blob.tsx 4 渲染策略 + renderMinimalMarkdown） | ~60-80 行 JSX + 状态机；spec 说"~50 行"略低估 | 可接受（1-3h 内完成；50 行估计仅 JSX 不含 helper 函数）；无阻塞 |
| T-8b（Tab URL state 测试）| createMemoryHistory 需要真实 routeTree（vite-plugin 生成）；test 环境可能找不到 route | 实读 repos.test.tsx L2/47-53 确认已有 createMemoryHistory 先例；风险已评估 |
| T-10（self_check block）| spec AC 命令有 MUST FIX（见 spec_review_v1）；T-10 必须修正后才能正确实现 | 明确依赖 spec MUST FIX 全关闭 |

---

## 问题列表

### MUST FIX

（无）

tasks.md 自身无 MUST FIX——任务粒度 / DAG / process_tasks / 覆盖矩阵均合规。spec_review_v1.md 的 5 条 MUST FIX 会在 spec_v2 修正后，自动修正 T-10 的实现依据（T-10 描述的 8 个 AC 命令照搬自 spec，spec 修了 tasks 自然跟上）。

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| SHOULD FIX-T-1 | tasks.md T-10 description（L261-276）：AC 命令描述 "AC-3 static：6 grep（tab= / 3 个 tab key / useSearch）" | T-10 描述是对 spec AC 命令的**转述**，不是完整复制。若 spec AC-3 命令修了（单引号改双引号 / 无引号），T-10 description 需同步更新措辞。当前 T-10 description 不含具体 shell 命令（只是摘要），影响较小，但 coding 阶段可能照此转述写出错误 self_check 命令 | T-10 description 加一句"AC 命令以 spec_v2 为准，不要照搬 spec_v1 转述" |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| NICE-T-1 | tasks.md T-8b description（L203-215）：降级方案描述 "如 createMemoryHistory 测试模式仓库未建立，降级..." | 实读 repos.test.tsx L2/47-53 确认 createMemoryHistory 已建立（`createRouter({ routeTree, history: createMemoryHistory(...) })`），降级方案可删除以减少歧义 | 删除"如 createMemoryHistory 测试模式仓库未建立，降级方案：..."段落；T-8b 直接写"用 createMemoryHistory + createRouter 渲染，参考 repos.test.tsx L47-53 模式" |

---

## Verdict

**REVISION REQUIRED**（跟随 spec_review_v1：spec 修 v2 后，tasks 不需单独重提评审，但 T-10 description 应与 spec_v2 同步）

tasks.md 自身质量良好：DAG 无环、粒度合理、覆盖矩阵健全、process_tasks stage-N 格式全部正确（PASS）。REVISION REQUIRED 的判定源于 spec_review_v1 的 5 条 MUST FIX——tasks 中的 T-10 实现依赖 spec 的 AC 命令，spec 修正前 T-10 无法正确实施。

待 spec_v2 MUST FIX 全关闭后，tasks 无需重新评审，直接进入 stage 3 编码（T-10 description 同步修改视为随附改动，不需独立 tasks_review_v2）。

---

## 后续指引（generator 收到 spec_v2 后）

spec_v2 MUST FIX 全关闭后，tasks 随附更新 T-10 description（同步 AC 命令修正），然后：

```bash
cd /data/home/zhhdzhang/nta/nta-lake
TASKS=.harness/changes/repo-files-tab-v2-20260518/request_analysis/tasks.md

# DAG 无环确认（结构不变，仍无环）
grep -cE "depends_on:" "$TASKS"  # 期望 ≥ 10

# process_tasks stage-N 格式
grep -cE "estimated_stage: stage-(2|4|6|7|8|9|10)" "$TASKS"  # 期望 ≥ 6

# 覆盖矩阵每条 AC 有关联任务
grep -cE "covers_ac:" "$TASKS"  # 期望 ≥ 10
```

全部 OK 后直接进 stage 3 coding。
