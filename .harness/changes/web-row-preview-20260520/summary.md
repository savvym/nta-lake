---
change_id: web-row-preview-20260520
title: 通用 silver/gold row 预览 + react-virtual (W4-2)
owner: application-owner-agent
started_at: 2026-05-21T11:00:00Z
phase: merged
status: closed
last_updated: 2026-05-21T11:35:00Z
related_changes:
  - web-pdf-mineru-ui-v2-20260520 (W4-1, useSnapshotRows hook + endpoint 上游)
  - operator-protocol-20260520 (W1-2, SilverRow schema)
  - dataset-export-engine-20260520 (W2-6, silver JSONL 写入方)
  - api-snapshot-rename-20260520 (W1-1, snapshots router prefix)
process_variant: v3-mini-design
---

# Summary

> v3 mini-design 流程（D-13）。Wave 4 第二个 change；apps/web 通用 silver/gold row 预览路由 + @tanstack/react-virtual 行虚拟化（仅前端，apps/api 不动）。

## 一句话目标

新增 `/snapshots/$owner/$name/$hash/rows` folder-form 子路由，消费 W4-1 `useSnapshotRows` hook，引入 `@tanstack/react-virtual@^3` 单页支持 5k+ 行 silver/gold 数据流畅滚动 + 行级展开看完整 JSON（source_ref / stats / lineage_ops），URL search param 驱动分页。

## 范围摘要

- **In scope**：`apps/web/package.json` +`@tanstack/react-virtual@^3`；`routes/snapshots/$owner.$name.$hash.tsx` +`<Outlet />` + `.jsonl`/`.jsonl.gz` 行旁 "Preview rows" Link；`routes/snapshots/$owner.$name.$hash/rows.tsx` 新（folder form，zod search schema，useVirtualizer 600px 容器 estimateSize 48，行展开 useState local，URL search 驱动 offset/limit/blobSha 分页）；`rows.test.tsx` 新（3 vitest+RTL 用例，vi.mock useSnapshotRows + useSnapshot 模式）
- **Out of scope**：不改 apps/api（W4-1 endpoint 已满足）；不做行筛选 / search / sort（follow-up）；不做 source_ref → bronze blob 跳转（W4-3）；不做列选择 / 列宽 / image 列预览（follow-up）；不做导出（W4-4）；不做 playwright e2e（W4-6）；不做 manifest.yaml (D-1)

## 阶段进度

| 阶段 | 模型 | 状态 | verdict | commit | 产物 |
|---|---|---|---|---|---|
| Phase 1 Design | opus (application-owner 自写) | done | n/a (v3 无 Phase 1 reviewer) | d4bd102 | [design.md](design.md) |
| Phase 2 Implementation | sonnet | done | n/a | 70702fc + 41c09b9 | [implementation.md](implementation.md) |
| Phase 3 Verify | opus | done | APPROVED | (本 commit) | [verify_review.md](verify_review.md) |

## 关键决策

| 时间 | 决策 | 理由 | 关联 |
|---|---|---|---|
| 2026-05-21 11:00 | 路由位置 `/snapshots/$owner/$name/$hash/rows` 平级子路由 | 通用预览归 snapshots 命名空间，非 PDF 专用 | design.md § 决策 1 |
| 2026-05-21 11:00 | folder form 子路由 + parent `<Outlet />` | W4-1 实测 flat-dot 嵌套问题；省去 fallback | design.md § 决策 2 |
| 2026-05-21 11:00 | 复用 W4-1 useSnapshotRows hook，不重造 | endpoint + hook 已就位 | design.md § 决策 3 |
| 2026-05-21 11:00 | @tanstack/react-virtual v3 | TanStack 同生态零负担 | design.md § 决策 4 |
| 2026-05-21 11:00 | 虚拟化容器固定高度 600px / estimateSize=48 | MVP；响应式高度留 follow-up | design.md § 决策 5/6 |
| 2026-05-21 11:00 | 行展开 = useState local Set<idx>，不入 URL | transient 操作；避免 URL 爆炸 | design.md § 决策 7 |
| 2026-05-21 11:00 | URL search 驱动 offset/limit/blobSha | 可分享链接；与 W4-1 一致 | design.md § 决策 8 |
| 2026-05-21 11:00 | limit 默认 100（vs W4-1 的 50） | 虚拟化解决渲染压力 | design.md § 决策 9 |
| 2026-05-21 11:00 | 空 snapshot 不渲染虚拟化容器 | 避免 react-virtual 0-row console.warn | design.md § 决策 10 |
| 2026-05-21 11:00 | 错误流复用 W4-1 endpoint 行为 | 422 / 404 / 0-row 走同一 UI | design.md § 决策 11 |

## Deferred 项

| 类型 | 描述 | 跟进位置 |
|---|---|---|
| NICE TO HAVE (verify) | jsdom 下 `window.scrollTo` not-implemented 噪音；建议 vitest.setup.ts 全局 stub | follow-up `web-test-suppress-jsdom-scroll-noise-*` |
| follow-up (design) | 行筛选 / 文本搜索 / 列条件过滤 | `web-rows-filter-*` |
| follow-up (design) | 点 source_ref → 跳到 bronze blob 预览 | `web-rows-lineage-jump-*` |
| follow-up (design) | 列选择 / 列宽 / 列顺序 | `web-rows-column-config-*` |
| follow-up (design) | images 列 thumbnail 展示 | `web-rows-image-preview-*` |
| follow-up (design) | 无限滚动模式（vs 翻页） | `web-rows-infinite-scroll-*` |
| follow-up (design) | 虚拟容器响应式高度 | `web-rows-responsive-height-*` |

## 交付

- Branch：`change/web-row-preview-20260520`
- Merge commit：（merge 后回填）
- 关闭时间：2026-05-21T11:35:00Z
