---
change_id: processor-framework-20260517
target: spec.md
target_version: 1
review_version: 1
reviewer: application-owner-agent
reviewed_at: 2026-05-17T18:10:00Z
verdict: APPROVED
---

# Spec Review v1

## 检查清单结论（expert-reviewer SKILL §1）

- [x] 背景写明了为什么现在做（解锁 Silver/Gold 流水线 + 复用 adapter framework 已建立的 registry/runner 模式）
- [x] 问题陈述对外部读者可理解（packages/core 已定义 Processor Protocol；缺执行端 runner + 至少一个实现 + HTTP 触发 + worker dispatch）
- [x] 范围 / 非范围都有（明确把 Schema Registry / iter_records / parallel map / subprocess / web UI / 真 PDF/HTML 放 Out of scope）
- [x] 每条 AC 都可机械化且可独立执行（13 条 AC 均给出验证命令，AC-2/3/4/5/6/7/9 已实测 dry-parse 通过）
- [x] 风险有缓解：(1) worker import 触发 register 已沿 adapter 模式；(2) CAS dedup 保证幂等；(3) cycle detection 显式 deferred（MVP 接受 source==target）；(4) SKILL 8 条 checklist 已应用
- [x] 没有把已有架构当新提案（packages/core Processor Protocol、adapter framework、jobs queue 都明确引用）
- [x] 待澄清问题已清零或显式 deferred

## 跨链路一致性检查（request-analysis SKILL §1）

- [x] schema (ProcessRequest) ↔ payload (jobs dispatch) ↔ AC-5 (extra=forbid) ↔ fixture (test_d) 四链路一致
- [x] AC 验证命令均一行式可粘贴；Python 复合语句无 `;` 复合
- [x] 反向 grep + test -f：AC-1 在 self_check 注册时补 `test -f` 前置；AC-8 用 service.py 双正向 grep（run_process_job + run_ingest_job 都必须出现，dispatch 存在的必要条件）
- [x] process_tasks 6 条占位齐全（T-9~T-14）
- [x] AC 验证命令真跑 dry-parse：AC-2/3/4/5/6/7/9 实际执行通过

## 问题列表

### MUST FIX

无。

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | spec §AC-1 | AC-1 仅 grep 不能区分"文件不存在"和"类不存在"，违反 reverse-grep checklist 第 6 条 | 在 _self_check.sh AC-1 注册时补 `test -f apps/api/dataplat_api/runner/repo_view.py &&` 前置；已落实 |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | spec §范围 | 可显式说明 ProcessorRunner 在本 change 中不实现 cycle detection | 已在 §风险段标注，无需 spec v2 |

## Verdict

APPROVED（MUST FIX = 0；SHOULD FIX 1 条在 self_check 注册阶段已修，无需 spec v2）。

## 后续指引

进入 stage 3 coding。Coding report 需声明：
1. 13 AC 全部 PASS（含 AC-13 自递归 + 全仓 173/173）
2. ruff + mypy 全 PASS（含 worker/src）
3. SKILL 8 条 checklist 自审通过
