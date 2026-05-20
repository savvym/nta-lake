---
change_id: harness-3-phase-pivot-20260520
title: harness 框架从 v1 十阶段简化为 v2 三阶段
owner: application-owner-agent
started_at: 2026-05-20T17:00:00Z
phase: done
status: closed
last_updated: 2026-05-20T17:30:00Z
related_changes:
  - platform-north-star-pivot-20260520    # 同期完成的另一个 pivot
process_override: |
  本 change **绕过常规 10 阶段流程**直接落地。
  用户授权时间：2026-05-20T17:00（会话内显式说"你来直接对 harness 框架进行改动，
  不要走繁琐的 changes 变更"）。
  绕过理由：本 change 改的就是流程本身；如果走旧流程会有 self-referential 死锁
  （旧流程的 reviewer / skill / template 都要被它替换掉，没法用旧产物评审改它自己）。
  这是 CLAUDE.md 硬约束 #6 允许的特殊情形："harness 框架本身的改动可以由用户授权
  直接落地，但要留 meta 记录"。
---

# Summary

## 一句话目标

把 harness 流程从 v1 的 10 阶段简化为 v2 的 3 阶段，硬绑定模型分配（opus / sonnet / opus）。

## 范围摘要

- **In scope**：development-process.md 重写 / _template/ 重构 / application-owner.md 重写流程章节 / harness_new_change.sh 适配新 template / CLAUDE.md 流程指针 + 硬约束 / 老 skills 加 DEPRECATED banner / skills/README.md 重写 / 本 meta 记录
- **Out of scope**：23 个 v1 时期 change 回写（保留原结构作历史）/ 业务代码 / 测试代码 / design.md（北极星 pivot 是上一个 change）

## 改动文件清单

| 路径 | 类型 | 说明 |
|---|---|---|
| `.harness/rules/development-process.md` | rewrite | v1 → v2 三阶段定义 + 模型分配硬约束 + 反 over-engineering 约束 |
| `.harness/rules/development-process-v1-deprecated.md` | new (backup) | v1 原文备份，新文件指向它作历史参考 |
| `.harness/changes/_template/` | restructure | 删除 request_analysis/ coding/ unit_test/ ci_result/ deployment/ 子目录；新增 design.md / design_review.md / implementation.md / verify_review.md 4 个顶层文件；summary.md 改成 3-phase 阶段表 |
| `.harness/agents/application-owner.md` | rewrite | § 3.2 Skills / § 4 工作流 / § 6 硬约束 / § 7 启动模板 / § 7.5 spawn 模板 全部重写为 v2 |
| `scripts/harness_new_change.sh` | rewrite | 适配新 template；新 next-steps 提示三阶段 |
| `.harness/skills/code-review/SKILL.md` | edit | 加 DEPRECATED banner |
| `.harness/skills/unit-test-write/SKILL.md` | edit | 加 DEPRECATED banner |
| `.harness/skills/unit-test-ci/SKILL.md` | edit | 加 DEPRECATED banner |
| `.harness/skills/ci-generate/SKILL.md` | edit | 加 DEPRECATED banner |
| `.harness/skills/deploy-verify/SKILL.md` | edit | 加 DEPRECATED banner |
| `.harness/skills/project-analysis/SKILL.md` | edit | 加 DEPRECATED banner |
| `.harness/skills/README.md` | rewrite | 现役 3 个 skill + Deprecated 清单 + v2 关系图 |
| `CLAUDE.md` | edit | "你的第一件事" 改三阶段 / 关键文件导航换链接 / 硬约束 1-8 全部重写 |
| `.harness/changes/harness-3-phase-pivot-20260520/summary.md` | new | 本文件，meta 记录 |

## v1 vs v2 对照（决策要点）

| 维度 | v1 (10 阶段) | v2 (3 阶段) |
|---|---|---|
| 阶段数 | 10 | 3 |
| 每 change 文件数 | 12-20+ | 5 |
| 每 change reviewer spawn 次数 | 3-6 | 2（Phase 1 + Phase 3） |
| 模型分配 | 不固定 | 硬绑定：opus / sonnet / opus |
| Generator vs Reviewer | 严格分离（多次 spawn）| 仍分离但合并 spawn 次数 |
| 单元测试评审 | 独立 stage 6 reviewer | 并入 Phase 3 Verify Reviewer（对照 design 验 AC）|
| CI / 部署评审 | 独立 stage 8 / 9 | 并入 Phase 2 sonnet 自验 + Phase 3 reviewer 复核 |
| 反复 spawn reviewer 复审 | 经常发生（v1/v2/v3 链）| **显式禁止**（SMALL REVISIONS 修一轮直接进；MINOR FIX 修一轮直接 merge）|

## 关键决策

| 时间 | 决策 | 理由 |
|---|---|---|
| 2026-05-20 16:30 | 用户提"每个 change 还是太长了，是不是有些 review 没必要" | 23 个 change 跑下来文档开销大、reviewer cycle 频繁 |
| 2026-05-20 16:40 | 用户提出三阶段方案：Phase 1 opus design + opus reviewer，Phase 2 sonnet 端到端，Phase 3 opus reviewer 对 PR | 简化但保留双 reviewer 把关 |
| 2026-05-20 17:00 | 用户授权"直接对 harness 框架进行改动，不要走繁琐的 changes 变更" | self-referential 死锁场景，框架自身改动允许特殊处理 |

## 哪些 v2 的影响后续会显现

- 新 change 文件数 5 个 vs v1 的 12-20+：单 change 文档维护工作量 ↓ 60-70%
- reviewer spawn 从 3-6 次降到 2 次：单 change wall-time ↓ ~30-40%
- 模型分配硬绑定：避免 opus 浪费在执行密度高的编码、sonnet 在架构判断不够深的设计评审
- 反复 spawn reviewer 禁止：避免 v1/v2/v3 链拉长（platform-north-star-pivot 之前跑了 spec_review_v1 + spec_review_v2，v2 下只允许一轮）

## 风险 + 缓解

| 风险 | 缓解 |
|---|---|
| v1 时期 23 个 change 引用了被 deprecated 的 skill | 保留 deprecated skill 文件 + banner 不删，老引用不 404 |
| 新会话不清楚要走 v2 不是 v1 | CLAUDE.md "你的第一件事" 改成 v2；application-owner.md 顶部明确 v2；development-process.md 顶部解释 v1→v2 演化 |
| sonnet 在 Phase 2 一次调用做不完所有事（编码+测试+e2e+commit） | implementation.md 模板含完整产出清单，sonnet 按清单逐项；做不完时回报 application-owner 接续 |
| Phase 3 reviewer 漏审隐式偏离 | development-process.md § Phase 3 显式列"隐式偏离 = MUST FIX"；verify_review.md 模板含审计章节 |

## 交付

- Branch：`change/harness-3-phase-pivot-20260520`（本会话已切到）
- Merge commit：TBD（push 后回填）
- 关闭时间：2026-05-20T17:30Z

## 验证：v2 流程能跑通

下一个 change 用 v2 流程跑一遍即可验证。候选：
- **`api-snapshot-rename-*`**：业务功能 change，验 Phase 1+2+3 三轮 spawn
- **`web-pdf-mineru-ui-*`**：UI change，验 sonnet 在 Phase 2 端到端做完前端

## 复盘

- 顺利：用户直接授权绕过流程让这次 pivot 极快落地（< 30 分钟 vs 走完整流程估计 3-5 小时）
- 踩坑：harness_new_change.sh 老版本 hardcode 引用 `request_analysis/spec.md` 等旧路径，必须同步更新；忘了改的话下次新 change 会卡住
- 防复发：本 summary.md 文件清单逐项列出，未来类似框架自改要按此清单核对
