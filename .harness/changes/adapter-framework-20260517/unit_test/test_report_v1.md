---
change_id: adapter-framework-20260517
version: 1
authored_at: 2026-05-17T11:55:00Z
status: waiting_review
---

# Test Report v1

## 验收项 ↔ 测试映射

| spec AC | 语义 | 测试 | 文件 |
|---|---|---|---|
| AC-1 | IngestResult.files + IngestFileRef | self_check AC-1（含既有字段保留）+ packages/core 33 测试无回归 | shell + packages/core/tests |
| AC-2 | AdapterRegistry 单例 + 内置注册 | self_check AC-2 + `test_a_registry_register_get_list`（单元，含幂等） | shell + tests/test_ingest.py |
| AC-3 | StandardRunContext 满足 RunContext Protocol | self_check AC-3 | shell |
| AC-4 | AdapterRunner.run async + 3-tuple | self_check AC-4 + 集成测试 c~m 间接覆盖 | shell + tests |
| AC-5 | RawFileUploadAdapter ingest pass-through | self_check AC-5 + `test_b_raw_adapter_ingest_pass_through`（单元；含 path 重复 ValueError） | shell + tests |
| AC-6 | IngestRequest extra=forbid + parents 字段 | self_check AC-6 + 集成测试中所有 payload 实测 | shell + tests |
| AC-7 | router 路由路径正确 | self_check AC-7 + `test_c`~`test_m` 11 集成（路径覆盖） | shell + tests |
| AC-8 | main include + OpenAPI 含 path | self_check AC-8 + make codegen 同步 | shell |
| AC-9 | 复用 RepoService.get_by_owner_name 不重复 visibility | self_check AC-9（test -f + 正向 grep + 反向 grep；不再沉默通过） | shell |
| AC-10 | 404 unknown adapter / 400 validation / 幂等 / parent 接链 | self_check AC-10（grep 实现端关键词）+ `test_f` `test_l` `test_g` `test_m` 端到端覆盖 | shell + tests |
| AC-11 | ≥ 13 测试全 PASS | self_check AC-11（≥ 13 计数）+ `test_a`~`test_m` 13 个 | shell + tests |
| AC-12 | ruff + mypy | self_check AC-12 | shell |
| AC-13 | self_check 自递归 | self_check AC-13 | shell |

每条 AC 至少一个测试断言；spec v2 13 AC 无孤立项。

## 测试文件清单

| 文件 | 类型 | 用例数 |
|---|---|---|
| `apps/api/tests/test_ingest.py` | 单元 + 集成（依赖 PG + MinIO） | 13（2 单元 a/b + 11 集成 c~m） |
| `scripts/_self_check.sh` adapter-framework block | shell | 13 |

**总有效断言：13 + 13 = 26 条**

13 case 覆盖：
- (a) **单元** registry register/get/list（含幂等）
- (b) **单元** RawAdapter ingest（含 path 重复 ValueError）
- (c) admin POST /ingest 200
- (d) missing blob → 400 missing_hashes
- (e) user → 403
- (f) unknown adapter → 404 含 available
- (g) 幂等 → deduplicated=true
- (h) ref upsert
- (i) GET commit round-trip 含 tree
- (j) anon → 401（require_admin gate）
- (k) 多文件 tree 顺序（name 升序）
- (l) adapter 校验失败 → 400
- (m) **parent 自动接链**：C1.parents=[]，C2.parents=[C1.hash]，C1 可达

## Mock 范围声明

- **无 mock**：直连 docker-compose Postgres 5433 + MinIO 9100；adapter / runner / service 真跑；fixture 仅用 `app.dependency_overrides[get_blob_store]` 注入 per-test bucket（**真实** MinioBlobStore，不是 mock）
- `RawFileUploadAdapter.ingest` 单元测试 (b) 传 workspace=None / ctx=None 是合法 Protocol contravariance（adapter 不依赖；其他 adapter 应按 Protocol 严类型）
- 与 `.harness/skills/unit-test-write/SKILL.md` §1.7 一致

## 本地运行结果

```text
=== apps/api 测试（PG 5433 + MinIO 9100 dataplat-secret）===
64 passed in ~24s
  - 13 新 test_ingest.py
  - 18 既有 test_commits.py 回归（commit-api-mvp 无破坏）
  - 14 既有 test_repos.py 回归
  - 11 既有 test_auth.py 回归
  - 5 MinIO + 2 ORM smoke + 1 health

=== packages/core 测试 ===
33 passed in ~0.2s（IngestResult.files 加字段无回归）

=== ruff + mypy ===
ruff: All checks passed!
mypy: Success: no issues found in 57 source files

=== self_check adapter-framework ===
PASS=13 FAIL=0 SKIP=0

=== self_check 全仓 ===
PASS=108 FAIL=0 SKIP=0（8 个 block 全过）

=== make codegen ===
openapi.json 同步：/repos 命名空间 9 paths（含新 /ingest）
```

## 已知 flaky / 跳过

- 无 flaky
- PG / MinIO 不可达时 self_check AC-11 SKIP（双探针）
- 默认 5432 端口被另一个 PG 占用 → 显式 `DATAPLAT_PG_PORT=5433`
- MinIO 9100 容器凭据 `dataplat / dataplat-secret`（与 compose 默认不同；环境侧已知）

## 偏离 SKILL 标准

| 偏离 | 说明 |
|---|---|
| 大部分集成（仅 a/b 单元）| 接受：service/router/runner 都很薄，业务跑在 DB + MinIO lifecycle 上；mock CAS / DB 失真。与 commit-api-mvp 一致 |
| dependency_overrides 用于 BlobStore 隔离 | 接受：避免 default singleton 跨测试污染；teardown 严格 pop + 清 bucket |
| RawFileUpload.ingest 类型放宽 workspace/ctx | NICE TO HAVE：adapter 不依赖；commit_report 已显式声明 |

## 下一步

stage 6 单测评审：独立 reviewer 复核 AC 映射诚实性 + parent 链测试是否真覆盖。
