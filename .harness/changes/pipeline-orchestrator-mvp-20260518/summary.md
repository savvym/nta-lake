---
change_id: pipeline-orchestrator-mvp-20260518
title: Pipeline 编排引擎 MVP：Recipe YAML + DAG 调度 + cache_key + REST API + 端到端 demo
owner: application-owner-agent
started_at: 2026-05-18T06:01:20Z
stage: push
status: pending
last_updated: 2026-05-18T09:30:00Z
related_changes:
  - processor-framework-20260517
  - rq-worker-skeleton-20260517
  - adapter-framework-20260517
  - core-domain-model-20260516
  - commit-api-mvp-20260517
---

# Summary

> 这是本变更的 Single Source of Truth。任何阶段开始 / 通过 / 失败都必须同步更新这里。

## 一句话目标

让 dataplat 能从一份 YAML recipe 编排多个 processor 节点跑出 Bronze→Silver→Gold 端到端数据流水线，并具备 cache_key 命中复用、节点级状态追踪、REST API 触发与查询能力。

## 范围摘要

- **In scope**：
  - Recipe YAML loader + Pydantic schema 校验（对齐 design.md §4.3 DSL：`nodes[].id/processor/inputs/config/output`，inputs 可引用 `repo@version` 或 `@node-id`）
  - DAG 拓扑排序 + 顺序调度（MVP 不做节点级并行，单 run 串行执行节点）
  - `pipeline_runs` / `pipeline_node_runs` 表 + Alembic migration
  - `cache_key = sha256(canonical(inputs_commit_hashes, processor_name, processor_version, config))` 表 + 命中复用上次 output commit
  - 节点执行：解析 inputs → 调 ProcessorRunner（已有）→ 拿到 output commit → 更新 ref（@auto 写默认 ref）→ 把 output_commit 注入下游节点的 RepoView
  - POST /pipelines/runs（管理员，body 含 recipe inline JSON 或 YAML 文本）
  - GET /pipelines/runs/{run_id}（含节点状态列表）
  - GET /pipelines/runs/{run_id}/nodes/{node_id}（含 cache 命中标志、output commit）
  - 1 个端到端 demo recipe（recipes/examples/demo-bronze-to-gold.yaml）：raw_upload 生成 bronze → markdown_normalize 产 silver → llm_qa_gen 产 gold
  - 后端 pytest ≥ 12 条（仅覆盖本 change 新增模块）
- **Out of scope**：
  - 新 processor 实现（pdf-to-text / html-to-md / dedup / chunker / corpus-merge）→ 下一 change core-processors-mvp-*
  - Pipeline run UI tab、Pipelines 列表页 → 下一 change pipeline-ui-tab-*
  - Lineage DAG 可视化 → Phase 2
  - 节点级并行 / map-over-records 并发框架 → Phase 2（design.md §5.3 IterativeProcessor 概念）
  - Pipeline 自身作为 artifact 进 repo 版本化（design.md §4.3 "Pipeline 也作为 artifact"）→ 下一 change
  - 预算与限流（per-pipeline cost cap）→ Phase 2
  - 补全 repo / commit / blob / auth / adapter / processor / llm 既有模块的后端测试 → 单独 change backend-test-baseline-*

## 阶段进度

| 阶段 | 状态 | 最新版本 | verdict | 产物 / 报告 |
|---|---|---|---|---|
| 1 需求分析 | done | v2 | APPROVED | [spec.md](request_analysis/spec.md) · [tasks.md](request_analysis/tasks.md) |
| 2 需求评审 | done | v2 | APPROVED | v1: [spec_review_v1.md](request_analysis/review/spec_review_v1.md) · [tasks_review_v1.md](request_analysis/review/tasks_review_v1.md) ; v2: [spec_review_v2.md](request_analysis/review/spec_review_v2.md) · [tasks_review_v2.md](request_analysis/review/tasks_review_v2.md) |
| 3 编码实现 | done | v2 | — | [coding_report_v1.md](coding/coding_report_v1.md) · [coding_report_v2.md](coding/coding_report_v2.md) |
| 4 编码评审 | done | v2 | APPROVED | v1: [code_review_v1.md](coding/review/code_review_v1.md) (REVISION REQUIRED) ; v2: [code_review_v2.md](coding/review/code_review_v2.md) (APPROVED) |
| 5 单测编写 | done | v1 | — | [test_report_v1.md](unit_test/test_report_v1.md) |
| 6 单测评审 | done | v1 | APPROVED | [test_review_v1.md](unit_test/review/test_review_v1.md) |
| 7 代码推送 | pending | — | — | branch / commit SHA |
| 8 CI 验证 | pending | — | — | [ci_result_v1.md](ci_result/ci_result_v1.md) |
| 9 部署验证 | pending | — | — | [deploy_verify_v1.md](deployment/deploy_verify_v1.md) |
| 10 用户确认 | pending | — | — | 确认人 / 时间 |

## 关键决策

| 时间 | 决策 | 理由 / 取舍 | 关联文件 |
|---|---|---|---|
| 2026-05-18 | 不引入 Dagster/Prefect，自研最小 DAG 调度 | design.md §8 取舍表"处理引擎 (a) k8s Job 自研编排"；MVP 不依赖外部编排器 | design.md §8 |
| 2026-05-18 | 节点串行执行，不做节点级并行 | MVP 简化；design.md §5.3 已说"map 型 processor 平台提供 IterativeProcessor 基类"是 Phase 2+ | design.md §5.3 |
| 2026-05-18 | cache_key 仅含 inputs_commits + processor_name + processor_version + config（不含 env/python 版本） | 缓存命中应跟随业务输入而非环境；env 差异由 lineage 字段记录但不参与 cache_key | design.md §4.3 / §5.3 |
| 2026-05-18 | 新 processor 实现拆到下一 change | 用户确认；request-analysis SKILL §5 单 change 不超 10 任务硬约束 | 本会话 |
| 2026-05-18 | Pipeline UI tab 拆到下一 change | 用户确认；design.md §9 Phase 1 UI 范围明确不含 Pipelines tab | design.md §9 |
| 2026-05-18 | 后端测试仅覆盖本 change 新增模块 | 用户确认；CLAUDE.md 硬约束 5 "不能做无关重构" | CLAUDE.md |

## 当前阻塞

- 无。stage 1-6 全 APPROVED；stage 5/6 已 done（32 测试 / 0 MUST FIX）。
- **下一动作（需用户决策）**：
  - **stage 7 代码推送** = `git commit` + `git push` → 这是涉及共享状态的高风险操作，按 CLAUDE.md 必须用户明确授权。建议先看 `git status` / `git diff` 确认范围再 commit。
  - **stage 8 CI 验证** = 等 GitHub Actions 跑通 → 需要先推送
  - **stage 9 部署验证** = 重启 API + worker + 跑 demo recipe → 需要 dev 环境（PG + MinIO + Redis 正确凭证）
  - **stage 10 用户确认** = 用户验收

## Deferred 项（stage 2 v2 review APPROVED 后未在本阶段修，进 stage 3 前同步处理）

| 类型 | 描述 | 跟进位置 |
|---|---|---|
| SHOULD FIX (v2 #1) | `RefService.update_ref` 实际不存在；`services/ref.py:16` 仅暴露 `get_by_name`，既有 ref upsert 逻辑嵌在 `CommitService.create_commit`（commit.py:192-209）。tasks.md T-5d 命名误导，coder 易撞墙 | stage 3 入口时：要么在 T-5d 同步把 ref upsert 逻辑抽出 `RefService.upsert_ref`，要么改用 `INSERT ... ON CONFLICT DO UPDATE` 在 orchestrator 内联 |
| SHOULD FIX (v2 #2) | AC-12 命令链在 `scripts/_self_check.sh` 复用时建议包裹 `(cd apps/api && ...)` 子 shell 防 cwd 污染 | T-8 实现时 |
| SHOULD FIX (v2 #3) | AC-7 grep 正则 `[.produced_by.]` 在字符类内点 = 任意字符（reviewer 评估：实际不产生伪命中，工程可接受） | stage 6 单测评审复核；如有更严测试代码可改用 `produced_by\.name` 精确正则 |
| SHOULD FIX (v2 #4) | R-7 缓解栏"行级 lock"措辞夸大（commit.py:192-209 实际是 select+update + IntegrityError rollback retry，非行级 lock） | spec_v3 或在 stage 3 close 时同步修 R-7 描述 |
| 后续 follow-up | `lineage-env-field-*`：补 commit.lineage_json["env"] 字段写入（design.md §4.4 含但本 MVP defer） | 单独 change |
| 后续 follow-up | `adapter-lineage-bugfix-*`：修 AdapterRunner.run lineage=None bug（adapter_runner.py:109） | 单独 change |
| 后续 follow-up | `pipeline-ref-locking-*`：演进为乐观锁 / `--if-current-ref` 头解决多 worker 并发 ref race | Phase 2 |
| 后续 follow-up | `pipeline-cancel-api-*`：DELETE /pipelines/runs/{id} 取消 API | 单独 change |
| 后续 follow-up | `pipeline-adapter-node-*`：Recipe 节点扩支持 Adapter；orchestrator 同时调 AdapterRegistry + ProcessorRegistry | 单独 change |
| 后续 follow-up | `pipeline-ui-tab-*`：Pipeline 列表 + run 详情前端 | 单独 change |
| 后续 follow-up | `core-processors-mvp-*`：pdf-to-text / html-to-md / dedup / chunker / corpus-merge 等核心 Processor | 单独 change |
| 后续 follow-up | `backend-test-baseline-*`：补全 repo / commit / blob / auth / adapter / processor / llm 既有模块的 backend test | 单独 change |

## 交付

> 关闭本变更时填写。

- Branch：`application-owner/pipeline-orchestrator-mvp-20260518`
- PR：TBD
- Merge commit：TBD
- 部署版本：TBD
- 用户确认：TBD
- 关闭时间：TBD

## 复盘（可选）

> 关闭时填写。
