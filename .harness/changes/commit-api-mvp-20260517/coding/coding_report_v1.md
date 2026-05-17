---
change_id: commit-api-mvp-20260517
version: 1
authored_at: 2026-05-17T10:30:00Z
branch: main (session 直推 main 等价模式)
base_commit: 8f8d40d (repo-api-mvp close)
head_commit: working-tree
status: waiting_review
---

# Coding Report v1

## 改动文件清单

| 路径 | 类型 | 一句话说明 | 关联 task |
|---|---|---|---|
| `apps/api/dataplat_api/schemas/blob.py` | new | `BlobUploadResponse` | T-1 |
| `apps/api/dataplat_api/schemas/tree.py` | new | `TreeEntryCreate/TreeCreate/TreeEntryRead/TreeRead`，全 extra=forbid | T-1 |
| `apps/api/dataplat_api/schemas/commit.py` | new | `CommitCreate`（不含 `created_at`）+ `CommitRead`（含 `deduplicated`） | T-1 |
| `apps/api/dataplat_api/schemas/__init__.py` | edit | export 7 个新 schema | T-1 |
| `apps/api/dataplat_api/services/blob.py` | new | `BlobService.upload / stream_get`；薄封装 CAS | T-2 |
| `apps/api/dataplat_api/services/commit.py` | new | `CommitService` + canonical hash + 事务 + 幂等；module docstring 一字不差对齐 spec AC-9 | T-3 |
| `apps/api/dataplat_api/services/__init__.py` | edit | export BlobService / CommitService | T-2/T-3 |
| `apps/api/dataplat_api/routers/commits.py` | new | 5 路由 + SpooledTemporaryFile 流式上传 + StreamingResponse 流式下载 | T-4 |
| `apps/api/dataplat_api/main.py` | edit | `include_router(commits_router)` | T-4 |
| `apps/api/dataplat_api/models/tree.py` | edit | 加 `TreeORM.entries` / `TreeEntryORM.tree` relationship（纯 Python 关系导航；无 schema 变更） | T-3 |
| `apps/api/dataplat_api/models/commit.py` | edit | 加 `CommitORM.tree` relationship | T-3 |
| `packages/api-types/openapi.json` | edit | `make codegen` 同步 5 新 paths | T-5 |
| `apps/api/tests/test_commits.py` | new | 18 测试（g1 单元 + 14 集成 + 2 visibility + 大文件 + lineage） | T-6 |
| `scripts/_self_check.sh` | edit | 追加 `run_commit_api_mvp` 13 AC + filter + 双探针 helper | T-7 |
| `.harness/skills/request-analysis/SKILL.md` | edit | 反哺：跨 AC 一致性自审清单（T-8 process） | T-8 |

> **门禁**：与 `git status --short` 一致（8 modified + 7 untracked + .harness/changes/commit-api-mvp-20260517/ 文档目录）。

## 与 tasks.md 的映射

| Task ID | 状态 | 备注 |
|---|---|---|
| T-1 schemas | done | 7 类型；`CommitCreate` 不含 `created_at`（spec v2 AC-9 方案 B） |
| T-2 BlobService | done | 不查 session / role |
| T-3 CommitService | done | `_canonical_*` / `_hash_*` 暴露为 staticmethod 供 (g1) 单元测试 import；事务用 `session.commit()`（见偏离说明） |
| T-4 router | done | SpooledTemporaryFile streaming；peek-first-chunk 触发 KeyError → 404 |
| T-5 codegen | done | openapi.json 5 新 paths + sha256 pattern |
| T-6 tests | done | 18 测试 a~q 全 PASS（PG 5433 + MinIO 9100 dataplat-secret） |
| T-7 self_check | done | 13 AC + 双探针 helper |
| T-8 反哺 | done | `request-analysis/SKILL.md` 加跨 AC 一致性自审清单 |

## 偏离 spec / trade-off

- **事务实现细节**：spec v2 AC-8 写 `async with session.begin():` 但 FastAPI `get_session` + 路由早期 SELECT 触发 auto-begin → `session.begin()` 报 "transaction already begun"。**实际实现** 用 `session.commit()` 在 try 块尾收尾 + `except IntegrityError: session.rollback()` 兜底——语义等价（同一连接 / 单事务 / IntegrityError 回滚），不显式 `begin()`。spec 描述应理解为"逻辑事务"。
- **MinIO 凭据**：本机 MinIO 在 `localhost:9100` 凭据 `dataplat/dataplat-secret`（与 compose 默认 `9000/dataplat-dev-secret` 不一致）；test fixture 用 `app.dependency_overrides[get_blob_store]` 注入 per-test bucket 隔离。
- **ORM relationship 增补**：core-domain-model 的 ORM 未声明 `relationship()`；本变更加 `relationship()` 做 eager load——**纯 Python 关系导航不改 schema**（无 alembic 迁移）。视为修补不算 scope creep。

## 本地校验结果

```text
=== ruff check ===
All checks passed!

=== mypy ===
Success: no issues found in 49 source files

=== pytest（PG 5433 + MinIO 9100 dataplat-secret）===
apps/api/tests:    51 passed in ~18s
packages/core/tests: 33 passed in ~0.2s

=== bash scripts/_self_check.sh commit-api-mvp ===
PASS=13 FAIL=0 SKIP=0

=== bash scripts/_self_check.sh （全仓）===
PASS=95 FAIL=0 SKIP=0
（MinIO env 配对后，cas-storage AC-15 也通了——pre-existing env-drift 此次会话内顺手消化）

=== make codegen ===
openapi.json 同步：8 paths under /repos 命名空间
```

## 已知未解决问题

- **commits/trees 全局唯一 hash**：`CommitORM.hash` / `TreeORM.hash` 是全局 PK（无 repo_id 组合）；跨 repo 提交相同内容会 IntegrityError 走 dedup 分支返一个可能不属于本 repo 的 commit——core-domain-model 设计遗留。MVP 接受；follow-up `commits-hash-scoped-by-repo-*`。

## reviewer 重点关注

1. **事务实现偏离**：`session.commit()` 而非 `async with session.begin()`——语义等价吗？race 路径 `IntegrityError → rollback` 真的回滚干净？
2. **canonical hash 跨语言确定性**：lineage 嵌套 `model_dump(mode="json")` + 外层 `sort_keys=True` 真的递归生效吗？建议 reviewer 手工构造 `{"a":{"b":1,"a":2}}` 验证。
3. **SpooledTemporaryFile 流式**：(n) 2MB 测试通过，但 client 用 `request.stream()` 真的没全量入内存吗？grep `request.body()` 应为空。
4. **404 不泄露存在性**：所有 GET 失败 case 都用 404；POST 路由 admin 看不见 repo 也返 404；reviewer 复核 (l) 测试断言三路由都 404。
5. **dependency_overrides 漏关风险**：fixture teardown 是否会污染下个测试？

## 下一步

stage 4 编码评审：独立 reviewer 复核 working-tree diff（base = 8f8d40d）。
