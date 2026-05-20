---
change_id: <feature-slug>-<yyyymmdd>
phase: design
status: draft           # draft | reviewing | approved | small_revisions | big_rewrite
authored_at: <YYYY-MM-DDTHH:MM:SSZ>
author: application-owner-agent
model_used: opus
# 若是纯文档 / harness 治理 change，可设 exempt（详 .harness/skills/design-review/SKILL.md）
ac_kind_lint: <exempt | enforce>
ac_kind_lint_exempt_reason: <一句话理由，仅 exempt 时填>
---

# Design：<标题>

> 这是 Phase 1 的唯一产物。spec + tasks 合并在这里。Phase 2 sonnet 按本文件落地，Phase 3 reviewer 对照本文件验收。

## 一句话目标

<≤ 30 字，复述用户诉求>

## 背景

<为什么现在做。1-2 段。可以引用相关 wiki、design.md、上下游 change。>

## 范围

In scope：

- <要做的事 1>
- <要做的事 2>

## 非范围

显式列出**不做**的事 + 理由（避免 scope creep）：

- 不做 X：<理由>
- 不做 Y：<理由 + 跟进 change 占位，如 `follow-up-change-name-*`>

## 验收标准

每条必须可演示且可机械化。`kind` 二选一：

- `static`：grep / test -f / dry-import / 文件结构断言
- `behavioral`：真跑代码并断言行为（HTTP roundtrip / pytest 集成 / curl smoke / bash fixture）

**每个非豁免 change 至少 1 条 `behavioral`**。混合型 AC 必须拆。

| ID | kind | 描述 | 验证方式 | 期望 |
|---|---|---|---|---|
| AC-1 | static | <e.g. routers/x.py 含 @router.post(/x)> | `grep -q "@router.post(\"/x\")" apps/api/.../x.py` | 命中 |
| AC-2 | behavioral | <e.g. POST /x 返回 201> | `uv run pytest tests/test_x.py::test_post_x_201` | passed |

> ⚠ Phase 1 reviewer 必须**真去跑** AC 命令验证语法可执行 + 当前未实现时如预期失败。

## 任务清单

粒度 30-90 分钟。每条标 `covers_ac`。

| Task | 描述 | covers_ac | 依赖 |
|---|---|---|---|
| T-1 | <e.g. routers/x.py 加 POST 端点> | AC-1 | — |
| T-2 | <e.g. 写 test_x.py 集成测试> | AC-2 | T-1 |

## 风险

| 风险 | 概率 | 影响 | 缓解 |
|---|---|---|---|
| <例：跨 change 影响 web-write-flows AC-2 grep> | 中 | self_check 回归 | T-3 顺手修上游 AC |

## 决策日志（如适用）

> 如果本 change 是从用户对话沉淀来的，列时间戳 + 决策点。便于 Phase 3 reviewer 理解上下文。

| 时间 | 决策 | 出处 |
|---|---|---|
| <YYYY-MM-DD HH:MM> | <e.g. 选 A 不选 B> | <用户对话 / 调研结论> |

## 交叉引用清单（reviewer 必查）

- 引用但不修改的文件：
- 应当不动的文件 / 目录（防 scope creep）：
- 引用的其他 change：

## 关联 follow-up（如有）

- <change-name-*>：<这条 change 完成后启动 / 依赖>
