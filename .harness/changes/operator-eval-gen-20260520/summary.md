---
change_id: operator-eval-gen-20260520
title: operator eval gen (W4-8)
owner: application-owner-agent
started_at: 2026-05-21T04:05:05Z
phase: verify
status: merged
last_updated: 2026-05-21T15:50:00Z
related_changes:
  - cost-budget-system-20260520
  - observability-mvp-20260520
  - operator-suite-mvp-20260520
  - recipe-yaml-v2-20260520
---

# Summary

> 三阶段简化流程下，本文件是 SoT。每阶段开始 / 通过 / 失败都同步这里。

## 一句话目标

新增 EvalGenOperator：对每条 silver row 调 LLM 生成 1 个多选题（question + 4 options + answer）追加到 `row.stats.eval_items`；首个真调 LLM 的 Operator + `run_recipe_v2` 桥接 sync/async operator 双形态。

## 范围摘要

- **In scope**：
  - `operators/eval_gen.py`（new ~265 行）：`async def run`、short_skip / parse_failure 降级 / markdown fence 剥离 / lineage_op 追加
  - `protocols/operator.py` +4 行注释：声明 `run` 可返 list 或 Coroutine
  - `recipe.py` +6 行：`import asyncio` + iscoroutine 分支 await
  - `operators/__init__.py` +5/-1：export + 注册 `eval_gen`（共 10 个内置算子）
  - 5 unit tests + 1 integration test（run_recipe_v2 async metrics）
  - `test_image_to_text_suite.py` len==9 → >=9（反脆弱副作用，DEV-1）
- **Out of scope**（follow-up）：n_per_row > 1 / retry / prompt 文件加载 / worker 注入真 LLMGateway / web eval preview UI / DPO pair gen（W4-9）

## 阶段进度

| 阶段 | 模型 | 状态 | verdict | commit | 产物 |
|---|---|---|---|---|---|
| Phase 1 Design | opus（v3 mini-design 自写） | approved | — | `a512853` | [design.md](design.md) |
| Phase 2 Implementation | sonnet | done | — | `cd7fc47` + `4f3b59c` + `a481d21` | [implementation.md](implementation.md) |
| Phase 3 Verify | opus | approved | **APPROVED** | `4fe75d8` (branch) | [verify_review.md](verify_review.md) |

## 关键决策

| 时间 | 决策 | 理由 | 关联 |
|---|---|---|---|
| 2026-05-21 | Operator Protocol union sync/async | 1 行注释 + 5 行 dispatch；现有 8 个 sync operator 零改动 | design §决策 1 |
| 2026-05-21 | eval_gen 走 ctx.llm 而非 import LLMGateway | packages/core 不依赖 apps/api | design §决策 2 |
| 2026-05-21 | 默认 model_id=fake-model | CI 友好；DEFAULT_RATES rate=0 | design §决策 9 |
| 2026-05-21 | parse failure 不抛 + 降级写 error item | integration 链路 graceful | design §决策 5 |
| 2026-05-21 | test_image_to_text_suite len==9 → >=9（DEV-1） | memory 反脆弱约束 | implementation §DEV-1 |

## 当前阻塞

无。

## Deferred 项

| 类型 | 描述 | 跟进位置 |
|---|---|---|
| follow-up | n_per_row > 1 真生成多题 | `operator-eval-gen-multi-*` |
| follow-up | parse fail retry | `operator-eval-gen-retry-*` |
| follow-up | prompt 模板从 YAML/file 加载 | `operator-eval-gen-prompt-file-*` |
| follow-up | worker 注入真 LLMGateway | `pipeline-runner-llm-injection-*` |
| follow-up | web UI 看生成题目 | `web-eval-preview-*` |
| follow-up | DPO pair gen | `operator-dpo-pair-gen-20260520`（W4-9） |
| follow-up | eval_items 导出 GLUE/MMLU 样式 | `operator-eval-jsonl-export-*` |

## 交付

- Branch：`change/operator-eval-gen-20260520`
- Merge commit：`c9d941b469c24179881d547570f8965c3886f0ee`
- 测试通过数：
  - packages/core：**108 passed in 1.34s**（W4-7 基线 102 + 6 new = 5 eval_gen + 1 recipe_v2 async）
  - apps/api：**51 passed, 131 skipped in 1.85s**（零回归）
  - apps/web：未跑（无 web diff）
- **0-issue streak：22 连胜**（W1-4 / W2-1..W2-6 / W3-1..W3-7 / W4-1..W4-8）
- 关闭时间：2026-05-21T15:50:00Z

## 复盘

### 哪些顺利

- v3 mini-design → sonnet 端到端 → opus verify 一气呵成；零 reviewer cycle
- async Operator 桥接极小 surface（recipe.py +6 行），现有 8 个 sync operator 零回归
- FakeLLMClient 的 call_count 计数使 short_skip 测试可直接断言"LLM 未被调用"
- DEV-1 反脆弱副作用就地修，符合 memory `[[feedback_brittle_count_assertions]]`

### 哪些踩坑

- sonnet 初提交含 unused imports `asyncio`/`pytest`，需 `a481d21` lint 修补
  - **根因**：sonnet 端到端模式 IDE/lint 反馈链路缺失
  - **防复发**：sonnet 自查后 follow-up commit 修补，流程闭环 OK；现有 `coding-style.md` 已覆盖，不新增规则
