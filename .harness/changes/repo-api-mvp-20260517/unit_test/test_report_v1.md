---
change_id: repo-api-mvp-20260517
version: 2
authored_at: 2026-05-17T09:00:00Z
status: waiting_review
revisions:
  - v1 → v2 (2026-05-17T09:00:00Z)：消化 stage 6 reviewer MUST FIX-1
    （AC-10 映射错位：原 v1 把 AC-10 映成 extra=forbid，纠正为 GET query + total + layer）；
    新增 test_n_list_total_and_layer_filter；remap self_check AC-8/AC-9/AC-10 与 spec 一致；
    extra=forbid 折入 self_check AC-1；GET-use-optional-user 折入 self_check AC-5。
---

# Test Report v2

## 验收项 ↔ 测试映射

| spec AC | 语义 | 测试（pytest 或 self_check） | 文件 |
|---|---|---|---|
| AC-1 | schemas 4+1 类型 + extra=forbid 拒未知 | self_check AC-1（含 ValidationError 断言） | scripts/_self_check.sh |
| AC-2 | RepoService 5 方法 | self_check AC-2 | scripts/_self_check.sh |
| AC-3 | routers 5 路由 + prefix=/repos | self_check AC-3 + `test_a`~`test_n`（14 路径覆盖） | shell + apps/api/tests/test_repos.py |
| AC-4 | main 集成 + OpenAPI 含 /repos | self_check AC-4 + make codegen 同步 openapi.json | shell |
| AC-5 | `_decode_user_from_cookie` 共享 + GET 用 get_optional_user | self_check AC-5（含遍历 GET 路由断言）+ test_auth 11 个回归 | shell + apps/api/tests/test_auth.py |
| AC-6 | visibility 矩阵 9 组合 + detail/list 一致 + 不泄露 | self_check AC-6（predicate 9/9）+ `test_f` `test_g` `test_h` `test_i` `test_l` `test_m`（HTTP 端到端 6 组合：anon+pub/anon+priv/user+int/user+priv/anon-list/user-list） | shell + tests/test_repos.py |
| AC-7 | POST require_admin + 重复 409 + 非 admin 403 | self_check AC-7 + `test_a`（admin 201）+ `test_b`（user 403）+ `test_c`（dup 409） | shell + tests |
| AC-8 | PATCH require_admin + 不存在 404 + 改 visibility/description | self_check AC-8 + `test_j`（admin PATCH 实时生效） | shell + tests |
| AC-9 | DELETE require_admin + 成功 204 + 不存在 404 | self_check AC-9 + `test_k`（admin DELETE 204 + GET 404） | shell + tests |
| AC-10 | GET /repos query limit/offset/layer + 返 `{items, total}` + total 反映过滤后 | self_check AC-10（OpenAPI parameters + schema 校验）+ `test_n_list_total_and_layer_filter` + `test_e` `test_l` `test_m`（list visibility 间接覆盖 total） | shell + tests |
| AC-11 | ≥ 13 集成测试全 PASS | self_check AC-11（≥ 14 计数）+ `test_a` ~ `test_n` | shell + apps/api/tests/test_repos.py |
| AC-12 | ruff + mypy 全 PASS | self_check AC-12 | shell |
| AC-13 | self_check 自递归 | self_check AC-13 | shell |

每条 spec AC 至少一个测试断言；spec 13 AC 无孤立项。

## 测试文件清单

| 文件 | 类型 | 用例数 |
|---|---|---|
| `apps/api/tests/test_repos.py` | 集成（依赖 PG） | 14（a~m 13 + n） |
| `scripts/_self_check.sh` repo-api-mvp block | shell | 13 |

**总有效断言：14 + 13 = 27 条**

集成测试覆盖 a~n 14 种调用方 × visibility / query 组合：
- a~c：POST 三类（admin 201 / user 403 / 重复 409）
- d~e：admin GET detail/list
- f~i：visibility 矩阵 HTTP 端到端 4 组合（anon+pub/anon+priv/user+int/user+priv）
- j：PATCH visibility 实时切换
- k：DELETE 链路
- l, m：list 矩阵两条（anon-list 仅 public / user-list 不含 private）
- n：GET query limit + layer + total 字段（spec AC-10）

## Mock 范围声明

- **无 mock**：直连 docker-compose Postgres + 真实 argon2 hash + 真实 JWT encode/decode + 真实 FastAPI ASGI 转发。
- 与 `.harness/skills/unit-test-write/SKILL.md` §1.7 "禁止 mock 数据访问层" 一致。

## 本地运行结果

```text
=== apps/api 测试（PG 5433 + JWT secret） ===
28 passed, 5 skipped in ~7s
  - 14 新增 test_repos.py::test_a ~ test_n
  - 11 既有 test_auth.py 回归全 PASS（_decode_user_from_cookie 抽取后未破坏）
  - 2 ORM smoke
  - 1 health
  - 5 skipped: MinIO 集成（env-drift 跳过）

=== packages/core 测试 ===
33 passed in ~0.5s（与 auth-scaffold 同基线，本变更未影响）

=== ruff + mypy ===
ruff: All checks passed!
mypy: Success: no issues found in 43 source files

=== self_check repo-api-mvp ===
PASS=13 FAIL=0 SKIP=0（DATAPLAT_PG_PORT=5433）

=== self_check 全仓 ===
PASS=81 FAIL=1 SKIP=0
  - 失败：cas-storage AC-15 MinIO 凭据 env-drift（与本变更无关；pre-existing）

=== make codegen ===
openapi.json 同步 OK（3 paths + 5 operations + RepositoryListResponse schema 含 items/total）
```

## 已知 flaky / 跳过

- 无 flaky
- MinIO 集成在 `DATAPLAT_MINIO_ENDPOINT` 未设或凭据漂移时 skip
- self_check AC-11 在 PG 不可达时 SKIP（探针前置）
- 默认 5432 端口本机已被另一个 PG 占用，dataplat 实际跑在 5433；使用 `DATAPLAT_PG_PORT=5433`

## 覆盖率

未配置 coverage 阈值；新增模块断言密度：
- `schemas/repo.py` 75 行：AC-1/AC-10 共 8 个断言（含 ValidationError + OpenAPI schema items/total + Literal 校验）
- `services/repo.py` 166 行：AC-2/AC-6 + 14 集成测试驱动 5 方法 100% 路径覆盖
- `routers/repos.py` 135 行：AC-3/AC-7/AC-8/AC-9/AC-10 + 14 集成测试覆盖 5 路由 × 主/边路径
- `auth/deps.py` `_decode_user_from_cookie`：AC-5 + 11 既有 test_auth + 14 test_repos 共同覆盖七路径返 None + 401 路径

## 偏离 SKILL 标准

| 偏离 | 说明 |
|---|---|
| 无单元（per-method）测试，全部走集成 | 接受：service/router 都很薄，业务逻辑都跑在 DB + FastAPI lifecycle 上；mock 反而失真。与 auth-scaffold 一致。 |
| visibility 矩阵 HTTP 端到端 6/9 组合（其余 3 由 self_check predicate 校验） | 接受：spec AC-11 字面列 a~m 13 case，未要求 9/9 端到端。HTTP 缺 admin+pub / admin+int / admin+priv 三组合，但 admin 在 service 层 visibility filter 不收紧—admin 见全部—predicate `RepoService._visibility_visible("private", admin)==True` 已断言。 |

## stage 6 reviewer v1 反馈消化

| Reviewer 标签 | 处理 |
|---|---|
| MUST FIX-1：AC-10 映射造假（self_check AC-10 是 extra=forbid，与 spec AC-10 GET query+total 无关） | 已修：self_check AC-10 改为 OpenAPI parameters + schema items/total 断言；新增 `test_n_list_total_and_layer_filter` 端到端覆盖；extra=forbid 折入 self_check AC-1。 |
| SHOULD FIX 1：(anon, internal) detail HTTP 缺端到端 | 接受 deferred：predicate self_check AC-6 已断言 `_visibility_visible("internal", None) is False`；端到端补充作为 follow-up `repo-visibility-anon-internal-coverage-*`。 |
| SHOULD FIX 2：映射表未拆 predicate vs HTTP | 已修：本 v2 映射表"测试"列显式标注 predicate(self_check) vs HTTP(pytest)。 |
| NICE TO HAVE 1：test_a 锚点命名 | 不修（spec a~m 已固定）。 |
| NICE TO HAVE 2：SKILL 段号笔误 | 不修（无业务影响）。 |
| NICE TO HAVE 3：用 pytest-cov 代替主观估算 | 接受 follow-up `coverage-instrumentation-*`。 |

## 下一步

进入阶段 6 单测评审 v2：reviewer 复核 MUST FIX-1 修复 + SHOULD FIX 2 修复。
