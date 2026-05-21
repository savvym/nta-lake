---
change_id: web-operator-chain-builder-20260520
title: Recipe v2 chain builder UI (W4-3)
owner: application-owner-agent
started_at: 2026-05-20T22:50:00Z
phase: merged
status: closed
last_updated: 2026-05-21T12:45:00Z
related_changes:
  - web-row-preview-20260520 (W4-2, snapshots routes layout + apps/web baseline 52 tests)
  - web-pdf-mineru-ui-v2-20260520 (W4-1, folder-form route + createMemoryHistory test pattern)
  - recipe-yaml-v2-20260520 (W2-5, recipe v2 yaml schema 上游)
  - operator-suite-mvp-20260520 (W2-1, OPERATOR_NAMES 来源)
  - loader-html-md-20260520 (W3-4, LOADER_NAMES 来源 之一)
process_variant: v3-mini-design
---

# Summary

> v3 mini-design 流程（D-13）。Wave 4 第三个 change；apps/web 纯前端 recipe v2 chain builder UI（apps/api 不动）。

## 一句话目标

新增 `/recipes/builder` 三栏路由（Palette / Chain / YAML Preview），用 `@dnd-kit/sortable` 排序 operator 链 + `js-yaml` 实时序列化 recipe v2 yaml，零 react-flow / 零 apps/api 改动。

## 范围摘要

- **In scope**：`apps/web/package.json` +`@dnd-kit/core@^6` +`@dnd-kit/sortable@^8` +`@dnd-kit/utilities@^3` +`js-yaml@^4` +`@types/js-yaml@^4` devDep；`routes/recipes/builder.tsx` 新（folder form，zod searchSchema，三栏：Palette 左 / Chain 中（dnd-kit sortable）/ YAML Preview 右；操作：选 loader、加 / 删 operator、拖序、复制 / 下载 yaml）；`builder.test.tsx` 新（3 vitest+RTL：yaml 反映 loader+operator / remove operator / 错误 yaml 内联）；`lib/recipe-v2-builder.ts` 新（pure 函数 `buildRecipeYaml` + LOADER_NAMES + OPERATOR_NAMES 常量）；`recipe-v2-builder.test.ts` 新（3 pure 函数：minimal recipe / empty yaml→{} / invalid yaml throw）；`routeTree.gen.ts` 手动注册（无 vite plugin）
- **Out of scope**：不改 apps/api（不接 execute endpoint，W4-4 / W4-5 范畴）；不做 zod schema 真实校验（仅 yaml.load round-trip 检查；follow-up）；不做 per-operator config 表单（仅自由 yaml 文本编辑 input/config）；不做 react-flow / DAG 可视化（design 决策 1 显式拒）；不做 LLM Gateway 真跑；不做 registry 动态拉取（hard-code，design 决策 5）；不做 manifest.yaml (D-1)；不做 dataset-card.yaml (D-1)

## 阶段进度

| 阶段 | 模型 | 状态 | verdict | commit | 产物 |
|---|---|---|---|---|---|
| Phase 1 Design | opus (application-owner 自写) | done | n/a (v3 无 Phase 1 reviewer) | b8e6e21 | [design.md](design.md) |
| Phase 2 Implementation | sonnet | done | n/a | c48031d + c3ef87a | [implementation.md](implementation.md) |
| Phase 3 Verify | opus | done | APPROVED | <verify_commit> | [verify_review.md](verify_review.md) |

## 关键决策

| 时间 | 决策 | 理由 | 关联 |
|---|---|---|---|
| 2026-05-20 22:50 | 拖拽用 @dnd-kit/sortable，不引 react-flow | 单列序列拖序需求；react-flow 是 DAG 画布，重且 design D-1 无 DAG 概念 | design.md § 决策 1 |
| 2026-05-20 22:50 | yaml 序列化用 js-yaml | 业界标准；零自造解析器；与 packages/core recipe v2 一致 | design.md § 决策 7 |
| 2026-05-20 22:50 | LOADER_NAMES / OPERATOR_NAMES hard-code in web | MVP；registry 动态拉取需 apps/api endpoint（W4-4 后） | design.md § 决策 5 |
| 2026-05-20 22:50 | folder form 路由 `routes/recipes/builder.tsx` | W4-1 / W4-2 同模式；预留 future `/recipes/$id/edit` | design.md § 决策 2 |
| 2026-05-20 22:50 | input / config 字段先用 yaml 文本（非表单） | MVP；per-operator 表单 follow-up | design.md § 决策 3 |
| 2026-05-20 22:50 | builder state 用 useState（非 zustand / context） | 单页 + 单组件；持久化非范围 | design.md § 决策 4 |
| 2026-05-20 22:50 | yaml preview readonly + 复制 + 下载 | 不双向编辑（避免 builder state ↔ yaml 同步歧义） | design.md § 决策 6 |
| 2026-05-20 22:50 | URL search 仅可选 loader + recipe_name | 链接分享场景轻量；operators 不入 URL | design.md § 决策 10 |
| 2026-05-21 10:55 | 实施时 LOADER_NAMES / OPERATOR_NAMES 用实际 registry 名（DEV-1） | grep packages/core 实际注册：4 loaders + 9 operators；design.md AC-2 举例的 `pdf_mineru` 是 W1-4 adapter 名（非 loader），`normalize_unicode` 不存在 | implementation.md DEV-1 |

## 当前阻塞

无。

## Deferred 项

| 类型 | 描述 | 跟进位置 |
|---|---|---|
| NICE TO HAVE (verify, 继承 W4-2) | jsdom `window.scrollTo` not-implemented 噪音 | follow-up `web-test-suppress-jsdom-scroll-noise-*` |
| NICE TO HAVE (verify, DEV-1 衍生) | design.md AC-2 字面 example 用了不存在的 `pdf_mineru` + `normalize_unicode`；建议 follow-up 修订 design.md AC 字面举例 + 在 development-process.md / coding-style.md 加 "design 阶段举例 loader/operator 名要 grep 已注册列表" 规则 | follow-up `harness-design-example-real-name-*` |
| follow-up (design) | per-operator 参数化表单（替代自由 yaml 文本） | `web-builder-operator-form-*` |
| follow-up (design) | zod schema 真实校验（vs 仅 yaml.load round-trip） | `web-builder-zod-validation-*` |
| follow-up (design) | recipe submit → apps/api pipeline run（W4-4 同期） | `web-builder-submit-endpoint-*` |
| follow-up (design) | registry 动态拉取（apps/api loaders/operators 列表 endpoint） | `web-builder-dynamic-registry-*` |
| follow-up (design) | recipe save / load / draft persistence | `web-builder-persistence-*` |
| follow-up (design) | DAG 模式（多 loader 输入 / 分支 operator） | `web-builder-dag-mode-*`（北极星 D-1 评估后） |

## 交付

- Branch：`change/web-operator-chain-builder-20260520`
- Merge commit：`<merge_sha>`
- 关闭时间：2026-05-21T12:45:00Z
