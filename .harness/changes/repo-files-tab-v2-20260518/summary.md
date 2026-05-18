---
change_id: repo-files-tab-v2-20260518
title: Repo 详情页 Files 独立 Tab + 文件预览页（独立路由 + 5MB + 4 格式）
owner: application-owner-agent
started_at: 2026-05-18T20:30:00Z
stage: closed
status: closed
last_updated: 2026-05-18T23:30:00Z
related_changes:
  - repo-files-tab-20260517
  - pipeline-ui-tab-20260518
  - web-mvp-pages-20260517
  - web-write-flows-20260517
  - commit-api-mvp-20260517
---

# Summary

> 这是本变更的 Single Source of Truth。任何阶段开始 / 通过 / 失败都必须同步更新这里。

## 一句话目标

把 Repo 详情页现有的 Files / Ingest / Pipelines 三个堆叠 section **改造为 Tab 切换**（Files 默认），并让 Files Tab 中的每个文件支持**点击进入独立预览页**（独立路由可分享 URL，按扩展名走 4 套渲染策略，5 MB 守门）。

## 范围摘要

- **In scope**：
  - AC-1：后端新增 `GET /repos/{o}/{n}/blobs/{sha}/meta` 返 `{sha256, size}`
  - AC-2：`useBlobMeta` query hook + `BlobMetaResponse` TS 类型
  - AC-3：RepoDetailPage 重构 Metadata 卡 + Tabs（URL `?tab=` 控制）
  - AC-4：新路由 `/blob/$owner/$name/$hash`（4 渲染策略 + 5MB 守门 + minimal markdown）
  - AC-5：FilesSection entries 表 path 列改 Link
  - AC-6：vitest 5 测试（**behavioral**）
  - AC-7：pytest 3 测试（**behavioral**）
  - AC-8：self_check block + npm run build 干净（**behavioral**）

- **Out of scope**：嵌套目录 / 完整 Markdown 渲染 / 第三方依赖 / 编辑删除 / 历史 blame / 分支切换器 / SSE 推送（详 spec.md §非范围）

## 阶段进度

| 阶段 | 状态 | 最新版本 | verdict | 产物 / 报告 |
|---|---|---|---|---|
| 1 需求分析 | done | v2 | — | [spec.md](request_analysis/spec.md) v2 · [tasks.md](request_analysis/tasks.md) v2（闭 v1 review 5 MUST FIX + 3 SHOULD + 2 NICE） |
| 2 需求评审 | done | v2 | **APPROVED** | v1：[spec_review_v1.md](request_analysis/review/spec_review_v1.md) · [tasks_review_v1.md](request_analysis/review/tasks_review_v1.md)；v2：[spec_review_v2.md](request_analysis/review/spec_review_v2.md) · [tasks_review_v2.md](request_analysis/review/tasks_review_v2.md)（11/11 CLOSED） |
| 3 编码实现 | done | v1 | — | [coding_report_v1.md](coding/coding_report_v1.md) |
| 4 编码评审 | done | v1 | **APPROVED**（0 MUST · 2 SHOULD · 2 NICE；self_check 8/8 实跑） | [code_review_v1.md](coding/review/code_review_v1.md) |
| 5 单测编写 | done | v1 | — | [test_report_v1.md](unit_test/test_report_v1.md)（5 vitest + 3 pytest 全 PASS） |
| 6 单测评审 | done | v1 | **APPROVED**（0 MUST · 2 SHOULD · 2 NICE） | [test_review_v1.md](unit_test/review/test_review_v1.md)（vitest 5/5 + pytest 3/3 实跑确认） |
| 7 代码推送 | done | — | — | main 3 commit：`33d791e` spec v2 → `49b28bd` stage 3 实现 → SHOULD-1 fix（待 cherry-pick） |
| 8 CI 验证 | self-attest | — | — | 项目无 remote 长期未决（沿用既往）|
| 9 部署验证 | done | v1 | **PASS** | [deploy_verify_v1.md](deployment/deploy_verify_v1.md)（self_check 8/8 + reviewer-lint + ac-kind-lint 全 PASS；SHOULD-1 fix 后再次 8/8） |
| 10 用户确认 | done | v1 | **PASS** | zhhdzhang @ 2026-05-18T23:30:00Z 浏览器实测通过：Tab 切换 / 4 种文件预览 / 5MB 守门 |

## 关键决策

| 时间 | 决策 | 理由 / 取舍 |
|---|---|---|
| 2026-05-18 | Tab 状态用 URL `?tab=` 而非 React state | 可分享 URL；前进/后退；与 GitHub/HF 一致 |
| 2026-05-18 | 文件预览独立路由 `/blob/$owner/$name/$hash` | 用户明示要可分享 URL |
| 2026-05-18 | sha256 做 URL path、path 做 query | sha 是 CAS 一等公民；commit 内同 path 可能不同 sha |
| 2026-05-18 | 加后端 `/blobs/{sha}/meta` 端点而非前端流式累计 | 一次轻量调用得 size；避免浪费 5MB 带宽 |
| 2026-05-18 | Markdown 仅 4 类语法 + 内置 renderer | 零新依赖；80% 价值；剩余 follow-up |
| 2026-05-18 | 不动 commit 详情页 entries 表 | 范围隔离；commit 页是历史快照视图 |
| 2026-05-18 | stage 4 SHOULD-1 在本 change 修复（不推 follow-up） | 真 UX bug（非 admin 访问 URL 空白），3 行修，PR 完整度 |

## 当前阻塞

- 无。change 全流程关闭。

## Deferred 项（已 review 通过但未在本 change 内修）

| 类型 | 描述 | 跟进位置 |
|---|---|---|
| SHOULD FIX (stage 4 SHOULD-1) | 非 admin 访问 `?tab=ingest\|pipelines` URL 空白 | **已在本 change 修复**（worktree commit `e66e560`；RepoDetailPage activeTab 加非 admin 回退守门） |
| SHOULD FIX (stage 4 SHOULD-2) | `queries.ts` L325 任务追踪注释违 coding-style §2.6 | follow-up `web-purge-task-marker-comments-*`（前驱 pipeline-ui-tab 已有同问题）|
| NICE (stage 4 NICE-1) | ARIA tabs 不完整（缺 `role="tabpanel"` + 键盘导航）| follow-up `web-tabs-a11y-*` |
| NICE (stage 4 NICE-2) | `renderMinimalMarkdown` 应抽到 `src/lib/markdown.ts` | follow-up `web-markdown-renderer-extract-*` |
| SHOULD FIX (stage 6 SHOULD-1) | bulk mock queries 模块脆性 | follow-up `web-test-import-actual-*` |
| SHOULD FIX (stage 6 SHOULD-2) | `repos.tabs.test.tsx` 无 `beforeEach` mock reset | 同 `web-test-import-actual-*` |
| NICE (stage 6 NICE-1) | `renderMinimalMarkdown` 无直接单测 | follow-up `web-markdown-renderer-direct-test-*` |
| NICE (stage 6 NICE-2) | jsdom `window.scrollTo` stderr noise | follow-up `web-test-jsdom-scrollTo-shim-*` |

## 流程级 follow-up（harness 演进）

| follow-up | 触发现象 | 建议改 |
|---|---|---|
| `harness-route-schema-callsite-audit-*` | validateSearch 收敛触发 5 处既有调用编译错 | code-review SKILL 加"路由 schema 变更必须 grep 所有 to= 调用点" |
| `harness-test-grep-strip-ansi-*` | vitest ANSI escape 干扰 spec grep | unit-test-write SKILL 加"spec AC 测试 grep 默认 NO_COLOR=1 + sed 剥 ANSI" |
| `harness-reviewer-no-summary-edit-*` | reviewer subagent 改 summary.md | reviewer-agent.md §2 加 "summary.md 也是 Owner 产物，reviewer 不改" |

## 交付

- Branch：main（无 remote）
- PR：N/A
- Merge commits：`33d791e` / `49b28bd` / SHOULD-1 fix commit（待 cherry-pick 后回填 sha）
- 部署版本：dev 本机（API 8080 + Web 5174，stage 10 用户实测时启动）
- 用户确认：zhhdzhang @ 2026-05-18T23:30:00Z 浏览器实测通过
- 关闭时间：2026-05-18T23:30:00Z

## 复盘

### 哪些步骤超预期顺利

- **stage 2 sonnet reviewer**：用 `harness-reviewer-model-sonnet-20260518` 落地的 sonnet 默认规约后，2 轮 review v1+v2 合计 ~18 分钟，比预期 opus 路径快 3-5x；review 质量未下降。
- **stage 9 self_check 8/8**：spec_v2 拆 alternation + 去单引号策略真实降低假阴性；AC-3/AC-6 两次 FAIL 都是合理实质问题，修法清晰。
- **stage 4/6 并行 reviewer**：两个 sonnet reviewer 后台并行，~9 分钟拿到 verdict + 真跑确认，节约 owner 等待时间。

### 哪些步骤踩坑

- **TanStack Router `validateSearch` 副作用**：加 validateSearch 后既有 5 处 `Link/navigate` 全部要求传 `search` prop（TS 收敛）。教训：**路由 schema 变更要做调用点 grep audit**。
- **vitest ANSI escape 拦 grep**：spec AC-6 设计正确但 vitest 默认 ANSI 颜色导致 grep MISS。修法 `NO_COLOR=1 + sed`。教训：**spec 测试断言 grep 应统一剥 ANSI**。
- **bg session worktree isolation guard 反复**：多次 EnterWorktree/ExitWorktree 后 guard 状态不稳；reviewer subagent 主动改 main checkout summary.md（违反"reviewer 不改被评审产物"硬约束的 summary 边界）。教训：**reviewer 角色边界应明示 summary.md 也不改**。

3 个流程级 follow-up 已记入上方。当前会话不立即开新 harness change（避免无限套娃），下一轮 harness 维护合并处理。
