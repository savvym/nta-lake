---
change_id: commit-api-mvp-20260517
title: Commit/Blob/Tree 写读 HTTP 路由 MVP（解锁 Adapter 写入侧）
owner: zhhdzhang
started_at: 2026-05-17T09:30:00Z
closed_at: 2026-05-17T10:50:00Z
stage: closed
status: closed
last_updated: 2026-05-17T10:50:00Z
related_changes:
  - core-domain-model-20260516
  - cas-storage-20260517
  - auth-scaffold-20260517
  - repo-api-mvp-20260517
---

# Summary

## 一句话目标

落地 design.md §4.4 CAS API 的最小子集（5 路由：blob PUT/GET + commit POST/GET + tree GET），让上游 Adapter / Processor 有可调用的写入路径；同时为前端 Repo Files/Versions 页面提供读路径。

## 范围摘要

- **In scope**：
  - `POST /repos/{o}/{n}/blobs`（admin，流式上传 CAS）
  - `GET /repos/{o}/{n}/blobs/{sha256}`（visibility-aware，StreamingResponse）
  - `POST /repos/{o}/{n}/commits`（admin，含 tree.entries + parents + author + lineage + 可选 ref upsert）
  - `GET /repos/{o}/{n}/commits/{hash}`（visibility-aware，含 tree.entries）
  - `GET /repos/{o}/{n}/tree/{commit_hash}`（visibility-aware，仅 tree）
  - ≥ 12 集成测试 + ≥ 13 self_check AC
- **Out of scope**：
  - 批量上传 / multipart tar；ref CRUD（除 commit POST 时 upsert）；path 级 tree 浏览；lineage 图查询；嵌套 tree；tag/signed commit；resumable upload；quota

## 关键决策

| 时间 | 决策 | 理由 |
|---|---|---|
| 2026-05-17 | Blob 上传用 raw body PUT（非 multipart） | 流式最干净 |
| 2026-05-17 | Tree MVP 仅单层 entry=blob | 隔离复杂度 |
| 2026-05-17 | hash 服务端算（不信任 client） | §4.4 信任边界 |
| 2026-05-17 | 幂等走唯一约束 + IntegrityError catch + 兜底重读 | 并发友好 |
| 2026-05-17 | 单事务 tree+commit+ref | §4.4 commit 原子性 |
| 2026-05-17 | blob 存在性校验在事务前 | 避免事务内异步 IO 阻塞 |
| 2026-05-17 | canonical JSON：sort_keys + 升序 entries/parents | 跨版本确定性 |

## 阶段进度

| 阶段 | 状态 |
|---|---|
| 1 需求分析 | done（spec v2） |
| 2 需求评审 | done（reviewer v1 REVISION REQUIRED 10 MUST FIX → v2 APPROVED） |
| 3 编码实现 | done（7 个 T-* + T-8 反哺 SKILL；mypy + ruff 全 PASS；51 + 33 tests pass） |
| 4 编码评审 | done（reviewer v1 APPROVED 0 MUST FIX） |
| 5 单测编写 | done（18 测试 a~q + 13 self_check） |
| 6 单测评审 | done（reviewer v1 APPROVED 0 MUST FIX） |
| 7 代码推送 | done（session 直推 main 等价） |
| 8 CI 验证 | done（self_check repo-api-mvp 13/13 + 全仓 95/95 PASS） |
| 9 部署验证 | skipped: 无运行时部署面 |
| 10 用户确认 | done（会话级授权 Generator 自我确认） |

## 当前阻塞

- 无。

## Follow-ups（spec deferred + 评审 deferred）

- `commits-hash-scoped-by-repo-*`：评估 `(repo_id, hash)` 联合 PK 取代全局唯一 hash（core-domain-model 设计遗留）
- `commit-race-load-test-*`：用 locust/k6 覆盖并发幂等 race 路径（spec 已 deferred）
- `ref-api-mvp-*`：完整 ref CRUD（list / create / delete / strict naming）
- `tree-path-browse-*`：`/tree/{ref}/{path}` path 级浏览
- `tree-nested-*`：嵌套 tree（entry_type=tree）
- `lineage-query-graph-*`：`/lineage/graph` 图查询
- `quota-management-*`：上传配额 / 总大小限制
- `resumable-upload-*`：chunked / resumable upload
- `bulk-insert-tree-entries-*`：用 SQLAlchemy `insert().values(...)` bulk insert 取代 add per-row（stage 4 SHOULD FIX）
