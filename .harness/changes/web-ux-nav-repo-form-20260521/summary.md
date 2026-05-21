---
change_id: web-ux-nav-repo-form-20260521
title: Web UX：顶部 nav + repos/new schema_id+row_format 字段
owner: application-owner-agent
started_at: 2026-05-21T19:30:00Z
phase: merged
status: done
last_updated: 2026-05-21T20:30:00Z
related_changes: [web-recipe-structured-config-20260521]
---

# Summary

## 一句话目标

`__root.tsx` 顶部 nav 加 Repos / New Repo / Recipes Builder 入口；`repos.new.tsx` 在 layer=silver|gold 时显示 schema_id+row_format 下拉，提交时传给已就绪的后端校验。

## 范围摘要

- **In scope**：
  - `apps/web/src/routes/__root.tsx`（3 个 Link 入口；admin gate）
  - `apps/web/src/routes/repos.new.tsx`（SCHEMA_IDS_BY_LAYER 常量 + 条件渲染 schema 字段 + layer-switch 自动重置）
  - `apps/web/src/lib/api/queries.ts`（CreateRepoRequest 扩字段）
  - `apps/web/src/routes/repos.new.test.tsx`（+2 RTL tests）
- **Out of scope**：后端不改 / 不新增 GET /schemas / 不动 Recipes Builder（留 Change B）/ 不加 mobile nav / 不动 W1..W4-10 已 merge 产物

## 阶段进度

| 阶段 | 模型 | 状态 | verdict | commit | 产物 |
|---|---|---|---|---|---|
| Phase 1 Design | opus (self) | approved | — | 1eb828c | [design.md](design.md) |
| Phase 2 Implementation | sonnet | done | — | fea806a | [implementation.md](implementation.md) |
| Phase 3 Verify | opus | approved | APPROVED | 7acae2b | [verify_review.md](verify_review.md) |

## 关键决策

| 时间 | 决策 | 理由 | 关联 |
|---|---|---|---|
| 2026-05-21 | 硬编码 schema 列表常量 | 当前注册 schema 仅 2 个；新增 API 增量过大 | design.md §决策 1 |
| 2026-05-21 | layer 切换自动重置 schema 字段 | 避免 bronze 误传 schema_id 被后端 422 | design.md §决策 2 + 3 |
| 2026-05-21 | New Repo 仅 admin 可见 | 后端 POST /repos 已 admin only；前端 gate 避免点入即报错 | design.md §决策 6 |

## 当前阻塞

无

## Deferred 项

| 类型 | 描述 | 跟进位置 |
|---|---|---|
| follow-up | schema 数 ≥ 5 时新增 GET /schemas + 动态加载 | `web-schemas-api-*` |
| follow-up | schema 选项 hover 说明 / 文档链接 | `web-schema-id-tooltip-*` |
| follow-up | repo 详情页跳 pdf-mineru / snapshots / recipes builder 的上下文按钮 | `web-repo-detail-contextual-links-*` |
| follow-up | 窄屏 hamburger menu | `web-nav-mobile-*` |

## 交付

- Branch：`change/web-ux-nav-repo-form-20260521`（已删，merged）
- Merge commit：`85f2e4b`
- 关闭时间：2026-05-21T20:35:00Z

## 复盘

- **顺利**：v3 mini-design 端到端 ~10 min（design 写 ~3 min + sonnet impl ~4 min + opus verify ~3 min）；4/4 AC PASS；0 issue 一遍过。
- **意外收获**：sonnet 把现有 repos.new.test.tsx mockMutateAsync 提到模块作用域，让新增 2 tests 复用，体现端到端模式自然演化。
- **0-issue APPROVED 连续 25 次**（W1-4..W4-10..web-ux-nav-repo-form）。
