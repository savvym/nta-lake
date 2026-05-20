---
change_id: adapter-raw-upload-20260520
phase: design_review
reviewer: claude-agent:opus-phase1-reviewer
model_used: opus
authored_at: <YYYY-MM-DDTHH:MM:SSZ>
verdict: <APPROVED | SMALL REVISIONS | BIG REWRITE>
---

# Design Review

> Phase 1 reviewer 产物。reviewer 应**真去跑** design.md 里所有 static AC 命令验证语法 + 当前未实现时如预期失败。

## 机械化检查

| 项 | PASS / FAIL / SKIP | 证据 |
|---|---|---|
| design.md frontmatter 完整 | | |
| 一句话目标 ≤ 30 字 | | |
| 范围与非范围互不冲突 | | |
| ≥ 1 条 behavioral AC（或合规 exempt + 理由）| | |
| 所有 static AC 命令语法可执行（reviewer 真跑） | | |
| 当前实现下 AC 命令如预期 FAIL（防 false PASS） | | |
| 任务 covers_ac 覆盖所有 AC | | |
| 任务依赖无环 | | |
| 风险清单含至少 1 条 + 缓解 | | |

## 问题列表

### MUST FIX

> reviewer 一次性列**所有** MUST FIX，不允许 "v1 修了再说 v2 还有问题" 挤牙膏。

- <无 / 列出>

### SHOULD FIX

> 建议改但不阻塞。Application Owner 一轮修订时**可选**修；不修则在 implementation.md § 偏离 处声明。

- <无 / 列出>

### NICE TO HAVE

> 完全可选，不计在 verdict 判定里。

- <无 / 列出>

## Verdict

<APPROVED | SMALL REVISIONS | BIG REWRITE>

- **APPROVED**：design.md 可直接进 Phase 2 实施
- **SMALL REVISIONS**：有 MUST FIX 但都是局部修订（typo / AC 命令错误 / 漏 1-2 条非范围）；Application Owner 修一轮直接进 Phase 2，**不再 spawn Phase 1 reviewer**
- **BIG REWRITE**：抽象 / 范围 / 风险有根本问题；Application Owner 重写 design.md，**再 spawn 一次 reviewer**

## 后续指引

<给 Application Owner 的具体下一步>
