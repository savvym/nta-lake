---
change_id: commit-api-mvp-20260517
version: 1
authored_at: 2026-05-17T10:40:00Z
status: waiting_review
---

# Test Report v1

## 验收项 ↔ 测试映射

| spec AC | 语义 | 测试 | 文件 |
|---|---|---|---|
| AC-1 | 7 schemas + extra=forbid + CommitCreate 无 created_at | self_check AC-1 | scripts/_self_check.sh |
| AC-2 | BlobService 不查 session/role | self_check AC-2 | scripts/_self_check.sh |
| AC-3 | CommitService 3 公共 + 5 私有方法 | self_check AC-3 | scripts/_self_check.sh |
| AC-4 | router 5 路由 + prefix=/repos | self_check AC-4 + `test_a`~`test_q`（5 路由路径覆盖） | shell + tests/test_commits.py |
| AC-5 | main + OpenAPI 5 paths | self_check AC-5 + make codegen 同步 | shell |
| AC-6 | 404 不泄露 + 复用 RepoService visibility | self_check AC-6（grep 不重复实现）+ `test_l`（三路由 404）+ `test_m/p/q`（user × visibility） | shell + tests |
| AC-7 | Blob 完整性（服务端真实哈希） | self_check AC-7 + `test_a`（sha256 与本地 hashlib 一致）+ `test_b`（dedup） | shell + tests |
| AC-8 | 事务前 blob 存在性校验 | self_check AC-8（grep 顺序）+ `test_e`（missing → 400 + missing_hashes 字段） | shell + tests |
| AC-9 | canonical hash 确定性 | self_check AC-9 + `test_g1_canonical_hash_is_deterministic`（**单元**：entries / parents 排序不变性 + 改 message 变 hash） | shell + tests |
| AC-10 | 幂等 commit_hash 唯一 | self_check AC-10（DDL 反射）+ `test_g2`（顺序幂等 deduplicated=true） | shell + tests |
| AC-11 | ≥ 16 集成全 PASS | self_check AC-11（≥ 16 计数）+ `test_a`~`test_q` 18 个 | shell + tests |
| AC-12 | ruff + mypy | self_check AC-12 | shell |
| AC-13 | self_check 自递归 | self_check AC-13 | shell |

每条 AC 至少一个测试断言；spec v2 13 AC 无孤立项。

## 测试文件清单

| 文件 | 类型 | 用例数 |
|---|---|---|
| `apps/api/tests/test_commits.py` | 单元 + 集成（依赖 PG + MinIO） | 18（1 单元 g1 + 17 集成 a~q） |
| `scripts/_self_check.sh` commit-api-mvp block | shell | 13 |

**总有效断言：18 + 13 = 31 条**

集成测试覆盖 18 case：
- g1：单元 canonical hash 确定性（不依赖 PG / MinIO）
- a~c：POST blob（admin 200 / dedup / user 403）
- d~g2：POST commit（含 entry / missing 400 / ref upsert / 顺序幂等）
- h~k：GET commit/blob（含/不存在）
- l~m：visibility 矩阵（私 anon 404 / 公 anon 200）
- n：2MB 大文件流式 round-trip（spec 风险 #2 缓解落地）
- o：lineage round-trip（spec 风险 #5 缓解落地）
- p~q：user × internal/private commit visibility

## Mock 范围声明

- **无 mock**：直连 docker-compose Postgres（5433 dataplat-pg-test 容器）+ MinIO（9100 dataplat-minio-test 容器，凭据 dataplat/dataplat-secret）+ 真实 FastAPI ASGI + 真实 BlobStore CAS 算法。
- 与 `.harness/skills/unit-test-write/SKILL.md` §1.7 一致。
- 唯一的 dependency_overrides：`app.dependency_overrides[get_blob_store]` 注入 per-test bucket 隔离（避免 default singleton 污染），fixture teardown 严格 pop + delete_bucket。

## 本地运行结果

```text
=== apps/api 测试（PG 5433 + MinIO 9100）===
51 passed in ~18s
  - 18 新 test_commits.py::test_a/b/c/d/e/f/g1/g2/h/i/j/k/l/m/n/o/p/q
  - 14 既有 test_repos.py（repo-api-mvp 回归全 PASS）
  - 11 既有 test_auth.py（auth-scaffold 回归全 PASS）
  - 2 ORM smoke
  - 1 health
  - 5 cas-storage MinIO 集成（这次环境对齐后全 PASS，pre-existing env-drift 消化）

=== packages/core 测试 ===
33 passed in ~0.2s

=== ruff + mypy ===
ruff: All checks passed!
mypy: Success: no issues found in 49 source files

=== self_check commit-api-mvp ===
PASS=13 FAIL=0 SKIP=0

=== self_check 全仓 ===
PASS=95 FAIL=0 SKIP=0（5 个 block × 各自 AC 总数）

=== make codegen ===
openapi.json 同步：/repos 命名空间 8 paths（3 repo CRUD + 5 commit-api）
```

## 已知 flaky / 跳过

- 无 flaky
- PG / MinIO 不可达时 self_check AC-11 SKIP（双探针前置）
- 默认 5432 端口被另一个 PG 占用 → 必须显式 `DATAPLAT_PG_PORT=5433`
- 默认 9000 端口的 MinIO 凭据与 compose 不同（系统装的不是 dataplat）→ 必须显式 `DATAPLAT_MINIO_PORT=9100 DATAPLAT_MINIO_ACCESS_KEY=dataplat DATAPLAT_MINIO_SECRET_KEY=dataplat-secret` 指向 dataplat-minio-test 容器

## 覆盖率

未配置 coverage 阈值；新增模块断言密度：
- `schemas/{blob,tree,commit}.py` 共 ~110 行：AC-1 + extra=forbid + canonical hash 测试驱动
- `services/blob.py` 40 行：18 集成测试驱动 stream upload/get
- `services/commit.py` ~230 行：AC-9 单元 (g1) 直接断言 canonical 函数 + 集成测试驱动 5 私有 + 3 公共方法主路径与 race 兜底
- `routers/commits.py` ~210 行：5 路由 × admin/visitor/anon 三视角 + 大文件 + lineage 全路径覆盖

## 偏离 SKILL 标准

| 偏离 | 说明 |
|---|---|
| 大部分测试是集成（仅 g1 是纯单元） | 接受：service/router 都很薄，业务逻辑跑在 DB + MinIO lifecycle 上；mock CAS / DB 失真。与 auth-scaffold / repo-api-mvp 一致。 |
| dependency_overrides 用于 BlobStore 隔离 | 接受：避免 default singleton 跨测试污染；teardown 严格 pop + 清 bucket；非 mock 数据访问层。 |

## 下一步

stage 6 单测评审：独立 reviewer 复核测试断言密度 + AC 映射诚实性。
