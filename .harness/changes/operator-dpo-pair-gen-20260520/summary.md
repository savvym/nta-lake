---
change_id: operator-dpo-pair-gen-20260520
title: operator DPO pair gen (W4-9)
owner: application-owner-agent
started_at: 2026-05-21T04:20:52Z
phase: verify
status: done
last_updated: 2026-05-21T17:30:00Z
related_changes:
  - operator-eval-gen-20260520
  - cost-budget-system-20260520
  - observability-mvp-20260520
---

# Summary

> 三阶段简化流程下，本文件是 SoT。

## 一句话目标

新增 `DPOPairGenOperator`：对每条 silver row 调 LLM 2 次（chosen / rejected）→ 写 `row.stats.dpo_pairs = [{prompt, chosen, rejected}]`，为 DPO 训练产出偏好对。

## 范围摘要

- **In scope**：
  - `packages/core/src/dataplat_core/operators/dpo_pair_gen.py`（new，247 行）
  - `packages/core/src/dataplat_core/operators/__init__.py`（注册 `dpo_pair_gen` → DPOPairGenOperator，第 11 个内置算子）
  - `packages/core/tests/test_operator_dpo_pair_gen.py`（new，6 tests：registry_lookup / happy_path / short_text_skip / chosen_failure / rejected_failure / empty_response）
- **Out of scope**（follow-up）：asyncio.gather 并行 / 混合 model_id / 真 prompt 抽取 / retry on error / pipeline runner LLM 注入 / web 预览 UI / DPO 专用 exporter

## 阶段进度

| 阶段 | 模型 | 状态 | verdict | commit | 产物 |
|---|---|---|---|---|---|
| Phase 1 Design | opus | approved | APPROVED (mini-design self-attest，v3 D-13 不 spawn reviewer) | `eac3130` | [design.md](design.md) |
| Phase 2 Implementation | claude-sonnet-4-6 | done | — | `332d0a6` + `c220e9e` + `23de4c8` | [implementation.md](implementation.md) |
| Phase 3 Verify | opus | approved | APPROVED | `de6bb45` | [verify_review.md](verify_review.md) |

## 关键决策

| 时间 | 决策 | 理由 | 关联 |
|---|---|---|---|
| 2026-05-21 | 复用 W4-8 EvalGenOperator 实现骨架，独立实现不抽公共基类 | 三相似优于过早抽象（CLAUDE.md） | design.md §决策 1 |
| 2026-05-21 | 2 LLM 调用串行而非并行 asyncio.gather | 错误归因更易；fake-model 测试可预测；并行留 follow-up | design.md §决策 2 |
| 2026-05-21 | prompt 字段简化为 `row.text[:200]`，不真从 LLM 抽取 | MVP；DPO 论文 setup 一致（同 prompt + 两 response） | design.md §决策 3 |
| 2026-05-21 | chosen / rejected 同 model_id，instruction-based 降级 | 简化 cost 归因；混合 model follow-up | design.md §决策 4 |
| 2026-05-21 | empty_response 视为失败 | LLM 返空通常是 prompt 触发拒答 / max_tokens=0 | design.md §决策 9 |
| 2026-05-21 | sonnet DEV-3：chosen 失败后跳过 rejected 调用（fail-fast） | design "任一失败 → 标 pair_failed" 语义一致；省 cost；test 覆盖 call_count==1 | implementation.md §DEV-3 |

## 当前阻塞

无。

## Deferred 项

| 类型 | 描述 | 跟进位置 |
|---|---|---|
| follow-up | asyncio.gather 并行 2 LLM 调用 | `operator-dpo-parallel-*` |
| follow-up | chosen / rejected 用不同 model_id | `operator-dpo-mixed-models-*` |
| follow-up | 真从 LLM 输出抽取 prompt | `operator-dpo-prompt-extract-*` |
| follow-up | LLM error 重试 | `operator-dpo-retry-*` |
| follow-up | reward model 二筛保留质量真有差距的 pair | `operator-dpo-reward-filter-*` |
| follow-up | worker / orchestrator 注入 LLMGateway 到 ctx.llm | `pipeline-runner-llm-injection-*` |
| follow-up | DPO 格式专用 exporter | `gold-exporter-dpo-*` |
| follow-up | UI 看 chosen vs rejected diff | `web-dpo-pair-preview-*` |

## 交付（merge）

- Branch：`change/operator-dpo-pair-gen-20260520`
- Merge commit：`0a96a0e`（`Merge change/operator-dpo-pair-gen-20260520: operator DPO pair gen (W4-9)`）
- PR：n/a（本地 merge，无 push）
- 关闭时间：2026-05-21T17:30:00Z

## AC 真跑总结（Phase 3）

| AC | 命令 | 结果 |
|---|---|---|
| AC-1 | `python -c "OperatorRegistry.get('dpo_pair_gen') is DPOPairGenOperator"` | `OK` |
| AC-2 | `pytest tests/test_operator_dpo_pair_gen.py -x -q` | `6 passed in 0.11s` |
| AC-3 | `pytest tests/test_recipe_v2.py::test_run_recipe_v2_supports_async_operator -x -q` | `1 passed in 0.13s` |
| AC-4 | `pytest -x -q` (packages/core 全量) | `114 passed in 1.31s` |
| 回归 | `pytest -x -q` (apps/api) | `51 passed, 131 skipped` |

## 复盘

- **顺利**：W4-8 LLM-in-operator 骨架直接复用，sonnet 一气呵成 6 tests 全过；fail-fast 优化 DEV-3 测试覆盖明确（call_count==1）；diff 干净（5 文件 / 752 LOC，包含 design+impl 文档）；apps/api / apps/web 零接触。
- **微调**：sonnet 首版含未使用的 `import pytest`，自补 23de4c8 lint 清理（无功能影响）。
- **0-issue APPROVED 连续 23 次**（W1-4 / W2-1..W2-6 / W3-1..W3-7 / W4-1..W4-9）。
