---
change_id: tree-nested-domain-20260520
title: Tree 嵌套支持（soft mode + recursive GET）
owner: application-owner-agent
started_at: 2026-05-19T13:54:24Z
stage: user_confirmation
status: done
last_updated: 2026-05-19T16:35:00Z
related_changes:
  - commit-api-mvp-20260517            # 现状来源（"MVP 仅支持单层"声明）
  - processor-framework-20260517       # 引入 follow-up `tree-nested-*` 的 change
  - processor-pdf-mineru-assets-20260520  # 痛点示例：81 张 image 全在扁平根 tree
---

# Summary

> 这是本变更的 Single Source of Truth。任何阶段开始 / 通过 / 失败都必须同步更新这里。

## 一句话目标

把后端 tree 模型从"单层扁平 + name 含 /"演进为"类 git 嵌套"，调用方零改动（soft mode：服务端自动 nested 化），GET API 默认只本级 + `?recursive=1` 全展开。本 change 仅后端，Web UI 留独立 follow-up。

## 范围摘要

- **In scope**：schemas Literal 放宽 / service `_normalize_to_nested` / create_commit 多 tree upsert / GET 加 recursive + 新 subtree by hash 端点 / ≥ 8 单测 / self_check 14 AC
- **Out of scope**：Web UI（独立 follow-up `web-tree-nested-ui-*`）/ adapter/processor 代码（soft mode 透明兼容）/ 历史 commit 数据迁移（旧扁平永远以扁平存储）/ 空目录 .gitkeep / GET 分页 / tree 算法本身（_canonical / sha256 不变）

## 阶段进度

| 阶段 | 状态 | 最新版本 | verdict | 阶段 commit | 产物 / 报告 |
|---|---|---|---|---|---|
| 1 需求分析 | done | spec v3 / tasks v2 | — | 986e0a0 | [spec.md](request_analysis/spec.md) · [tasks.md](request_analysis/tasks.md) |
| 2 需求评审 | done | v3 | APPROVED (spec v3 + tasks v2) | 986e0a0 | v1: [spec_review_v1.md](request_analysis/review/spec_review_v1.md) · [tasks_review_v1.md](request_analysis/review/tasks_review_v1.md) <br>v2: [spec_review_v2.md](request_analysis/review/spec_review_v2.md) · [tasks_review_v2.md](request_analysis/review/tasks_review_v2.md) <br>v3: [spec_review_v3.md](request_analysis/review/spec_review_v3.md) |
| 3 编码实现 | done | v2 | — | dc10a7d → d3b3099 | [coding_report_v1.md](coding/coding_report_v1.md) |
| 4 编码评审 | done | v3 | APPROVED (v1 报 2 MUST / v2 抓 prefix dedup bug / v3 全 RESOLVED) | d3b3099 | v1: [code_review_v1.md](coding/review/code_review_v1.md) <br>v2: [code_review_v2.md](coding/review/code_review_v2.md) <br>v3: [code_review_v3.md](coding/review/code_review_v3.md) |
| 5 单测编写 | done | v1 | 9/9 PASS | bd83de2 → f5a1e0c | [test_report_v1.md](unit_test/test_report_v1.md) |
| 6 单测评审 | done | v1 | APPROVED (0 MUST / 2 SHOULD 已处理) | f5a1e0c | [test_review_v1.md](unit_test/review/test_review_v1.md) |
| 7 代码推送 | done | — | — | 888c2ac | origin/change/tree-nested-domain-20260520（已合并并删除） |
| 8 CI 验证 | done | v1 | PASS (14/14 + 9 preflight = 23/23) | 888c2ac | [ci_result_v1.md](ci_result/ci_result_v1.md) |
| 9 部署验证 | done | v1 | SKIPPED (noop) | 888c2ac | [deploy_verify_v1.md](deployment/deploy_verify_v1.md) |
| 10 用户确认 | done | — | PASS（用户 2026-05-19 演示会话确认 merge） | b0ac18f | 用户：2026-05-19 |

## 关键决策

| 时间 | 决策 | 理由 / 取舍 | 关联文件 |
|---|---|---|---|
| 2026-05-19 | Soft mode 迁移：服务端自动把 name="a/b/c" 拆为嵌套 tree | 用户选定；调用方 0 改动；旧 commit 只读不动 | spec.md §背景 |
| 2026-05-19 | GET 默认只本级 + ?recursive=1 全展开 | 用户选定；类 git ls-tree 语义；可下钻 | spec.md §AC-7 |
| 2026-05-19 | 仅后端，Web UI 单开 follow-up | 用户选定；前后端拆解便于独立评审与回滚 | spec.md §范围 |
| 2026-05-19 | stage 2/4/6 走完整 reviewer spawn，不 self-attest | 本 change 改动基础设施 (Tree 是所有 commit 必经)，blast radius 大；不接受偏离 | tasks.md process_tasks |
| 2026-05-19 | 子目录 entry mode = 0o040000 (16384)；reader 不依赖此区分 type | 沿 POSIX / git 习惯；判断 type 用 entry_type 字段更稳 | spec.md §风险 |

## 当前阻塞

- 无（change 已关闭，合并到 main b0ac18f）

## Deferred 项

| 类型 | 描述 | 跟进位置 |
|---|---|---|
| 非范围 | Web UI 树形展开 | follow-up `web-tree-nested-ui-*` |
| 非范围 | tree 内分页 | follow-up `tree-nested-pagination-*` |
| 非范围 | 历史扁平数据迁移到嵌套结构（offline rebuild） | follow-up `tree-nested-history-rebuild-*`（如有需要） |

## 交付

> 关闭本变更时填写。

- Branch：`change/tree-nested-domain-20260520`（已合并到 main，远端/本地分支均已删除）
- PR：跳过 PR（PAT 缺 pull-requests scope）→ 直接 no-ff merge 到 main
- Merge commit：`b0ac18f`
- 部署版本：n/a（stage 9 SKIPPED noop；无 schema / 部署面变化）
- 用户确认：2026-05-19 演示会话内确认
- 关闭时间：2026-05-19T16:35:00Z
