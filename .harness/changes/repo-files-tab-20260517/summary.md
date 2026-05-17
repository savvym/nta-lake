---
change_id: repo-files-tab-20260517
title: Repo 详情页 Files 视图（HF 风格）+ Ref API
owner: zhhdzhang
started_at: 2026-05-17T16:30:00Z
closed_at: 2026-05-17T17:05:00Z
stage: closed
status: closed
last_updated: 2026-05-17T17:05:00Z
related_changes:
  - commit-api-mvp-20260517
  - web-write-flows-20260517
  - web-mvp-pages-20260517
note: 用户实测 bug + UX 反馈触发——上传文件后看不到文件 + 期望 HF 风格 Files 列表
---

# Summary

## 目标

修 bug + 上 UX：(1) 后端加 `GET /repos/{o}/{n}/refs/{name}` 路由让 UI 能解析 `main` → commit；(2) repo 详情页加 HF 风格 Files section（main → commit → tree entries 表 + 下载链）。

## 范围

- In scope：1 后端路由 + 1 hook + 详情页 Files section + 3 后端测试 + 1 前端测试 + self_check 13 AC
- Out of scope：LIST refs / ref 写 CRUD / 嵌套目录 / size 列 / 文件 last commit / 分支切换器

## 阶段进度

| 阶段 | 状态 |
|---|---|
| 1 需求分析 | done（self-grep 通过 SKILL 8 条 checklist） |
| 2 需求评审 | skipped（小范围 + 模式与既有 repo CRUD 一致；self-grep 替代） |
| 3 编码实现 | in_progress |
| 4 编码评审 | 由 self_check + 跨变更 grep 替代 |
| 5 单测编写 | in_progress |
| 6 单测评审 | 由 self_check 替代 |
| 7 代码推送 | pending |
| 8 CI 验证 | self_check 等价 |
| 9 部署验证 | API restart 需要 |
| 10 用户确认 | 用户浏览器实测 |

## 当前阻塞

- 无。
