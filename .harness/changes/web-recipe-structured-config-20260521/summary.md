---
change_id: web-recipe-structured-config-20260521
title: Recipe Builder 结构化算子配置 + Run 按钮
owner: application-owner-agent
started_at: 2026-05-21T20:40:00Z
phase: merged
status: done
last_updated: 2026-05-21T21:30:00Z
related_changes: [web-ux-nav-repo-form-20260521]
---

# Summary

## 一句话目标

新增 `GET /operators` 端点暴露 operator config_schema；`recipes/builder` 用结构化输入替代 YAML textarea；加"运行 recipe"按钮 POST `/pipelines/runs:from-yaml`。

## 范围摘要

- **In scope**：
  - 后端 `apps/api/dataplat_api/routers/operators.py`（新，GET /operators 列出 11 operators 含 config_schema）
  - 后端 `apps/api/tests/test_operators_endpoint.py`（新，behavioral httpx ASGI）
  - 前端 `apps/web/src/components/operator-config-form.tsx`（新，结构化输入渲染 + YAML fallback）
  - 前端 `apps/web/src/lib/api/queries.ts`（加 useOperatorsQuery + useCreateRunFromYaml hooks）
  - 前端 `apps/web/src/lib/recipe-v2-builder.ts`（删 OPERATOR_NAMES 硬编码；BuilderState.op 加 configObject；buildRecipeYaml 双轨）
  - 前端 `apps/web/src/routes/recipes/builder.tsx`（替换 textarea + Run 按钮 + admin gate + run_id 反馈 + /jobs Link）
  - 前端 `apps/web/src/routes/recipes/builder.test.tsx`（+2 RTL tests）
- **Out of scope**：Loader 结构化（仍 YAML）/ 嵌套 array/object visual editor / operator descriptions / 客户端 schema validate / run detail 页 / OperatorSpec 改造

## 阶段进度

| 阶段 | 模型 | 状态 | verdict | commit | 产物 |
|---|---|---|---|---|---|
| Phase 1 Design | opus (self) | approved | — | 3748095 | [design.md](design.md) |
| Phase 2 Implementation | sonnet | done | — | 79f0503 | [implementation.md](implementation.md) |
| Phase 3 Verify | opus | approved | APPROVED | （待回填） | [verify_review.md](verify_review.md) |

## 关键决策

| 时间 | 决策 | 理由 | 关联 |
|---|---|---|---|
| 2026-05-21 | GET /operators 不加 admin gate | 纯只读元数据；与 /me、/healthz 同级 | design.md §决策 1 |
| 2026-05-21 | configObject + configYaml 双轨 | 结构化更新 obj；fallback 用 yaml；同一卡只用一种 | design.md §决策 3 |
| 2026-05-21 | 删 OPERATOR_NAMES 硬编码 | 与后端注册脱钩风险；W4-8/W4-9 漏更新已暴露 | design.md §决策 5 |
| 2026-05-21 | Run 按钮 admin-only | 后端 require_admin；非 admin 点了 403 体验差 | design.md §决策 7 |
| 2026-05-21 | Run 后跳 /jobs 而非 run detail | run detail 路由 follow-up；/jobs 列表足够 | design.md §决策 8 |

## 当前阻塞

无

## Deferred 项

| 类型 | 描述 | 跟进位置 |
|---|---|---|
| NICE TO HAVE | useCreateRunFromYaml mutation 返回类型 `{run_id, status?}` 过松 | follow-up `web-pipeline-response-type-tighten-*` |
| NICE TO HAVE | builder.test.tsx 旧 "yaml 校验" test 命名漂移 | follow-up `web-recipe-test-rename-*` |
| follow-up | Loader input/config 结构化 | `web-loader-config-form-*` |
| follow-up | array/object 嵌套配置 visual editor | `web-recipe-nested-config-*` |
| follow-up | operator descriptions + 用法示例 | `web-operator-docs-*` |
| follow-up | run detail 路由 `/pipelines/runs/$id` | `web-pipeline-run-detail-*` |
| follow-up | JSON-Schema → zod 实时校验 | `web-recipe-config-client-validate-*` |
| follow-up | OperatorSpec 加 description 字段 | `harness-operator-spec-description-*` |

## 交付

- Branch：`change/web-recipe-structured-config-20260521`（merge 后删）
- Merge commit：（待回填）
- 关闭时间：（待回填）

## 复盘

- **顺利**：v3 mini-design 端到端 ~25 min（design ~5 min + sonnet impl ~13 min + opus verify ~5 min + housekeeping）；5/5 AC PASS；零 MUST/SHOULD FIX 一遍过。
- **意外收获**：sonnet 实现 OperatorConfigForm 时主动覆盖 5 种 JSON-Schema 基础 type 同时保留 fallback 路径，verify 后立即可用，无需第二轮。
- **0-issue APPROVED 连续 26 次**（W1-4..W4-10..web-ux-nav-repo-form..web-recipe-structured-config）。
