---
change_id: core-domain-model-20260516
version: 1
authored_at: 2026-05-17T02:15:00Z
status: waiting_review
---

# Test Report v1

> 本变更测试在 stage 3 编码阶段已实跑通过——本报告归档证据 + 映射表。

## 验收项 ↔ 测试映射

| AC | 测试 | 文件 |
|---|---|---|
| AC-1 | `_self_check.sh` shell 断言 + 单测被加载证明所有模块可 import | scripts/_self_check.sh AC-1 |
| AC-2 | `test_repository.py::test_repository_*`（5 个，含 Subtype Literal 严格校验） | packages/core/tests/test_repository.py |
| AC-3 | `test_commit.py::test_commit_*`（3 个） | packages/core/tests/test_commit.py |
| AC-4 | `test_lineage.py::test_lineage_*`（4 个，含 config_hash 64-hex） | packages/core/tests/test_lineage.py |
| AC-5 | `test_blob.py::test_blobref_*`（4 个，含 sha256 / size 校验） | packages/core/tests/test_blob.py |
| AC-6 | `test_tree.py::test_tree_*`（3 个） | packages/core/tests/test_tree.py |
| AC-7 | `test_refs.py::test_ref_*`（4 个） | packages/core/tests/test_refs.py |
| AC-8 | `test_protocols.py::test_protocols_full_import_set` + `test_repospec_pydantic_validates` | packages/core/tests/test_protocols.py |
| AC-9 / AC-10 / AC-11 / AC-12 | `_self_check.sh` shell 断言（ORM 模块齐全 / db.py async gen / alembic 文件 / 依赖声明） | scripts/_self_check.sh |
| AC-13 | `alembic upgrade head` 实跑 + `alembic current` 输出含 `0001` | apps/api/alembic |
| AC-14 | packages/core 全 25 测 + collected ≥ 6 | 见上 |
| AC-15 | `test_models.py::test_repositories_crud` + `test_commit_with_lineage_jsonb` | apps/api/tests/test_models.py |
| AC-16 | `uv run ruff check ... && uv run mypy ...` | shell |
| AC-17 | `_self_check.sh core-domain-model` 自跑 17/17 PASS | scripts/_self_check.sh |

每条 AC 至少一个具体断言；spec 17 AC 无孤立项。

## 测试文件清单

| 文件 | 类型 | 用例 | 行数 |
|---|---|---|---|
| `packages/core/tests/test_repository.py` | 单元（Pydantic 校验） | 5 | 64 |
| `packages/core/tests/test_blob.py` | 单元 | 4 | 30 |
| `packages/core/tests/test_tree.py` | 单元 | 3 | 32 |
| `packages/core/tests/test_lineage.py` | 单元 | 4 | 40 |
| `packages/core/tests/test_commit.py` | 单元 | 3 | 43 |
| `packages/core/tests/test_refs.py` | 单元 | 4 | 28 |
| `packages/core/tests/test_protocols.py` | 单元 | 2 | 32 |
| `apps/api/tests/test_health.py` | 集成 | 1 | 17 |
| `apps/api/tests/test_models.py` | 集成（依赖 Postgres） | 2 | 115 |
| `apps/api/tests/conftest.py` | 配置 | n/a | 14 |
| `scripts/_self_check.sh` | shell 断言（共享） | 17（含 SKIP 通道） | ~210 |

总有效断言：25 单测 + 3 集成（1 health + 2 ORM）+ 17 self-check = **45 条**。

## Mock 范围声明

按 unit-test-write SKILL §1.7：

- **packages/core**：mock 范围 = **无**。纯 Pydantic 模型校验，使用 `pytest.raises(ValidationError)` 断言负向。
- **apps/api**：mock 范围 = **无**。
  - `test_health.py` 用 `httpx.AsyncClient + ASGITransport`，是 httpx 真实 transport 不算 mock
  - `test_models.py` **直连真实 Postgres**——按 SKILL 主张严格禁止 mock 数据访问层。当 DATAPLAT_DATABASE_URL 未设置时 `pytest.skip`，不是用 mock 蒙混
- **shell self-check**：直读真实文件系统 + 真实跑 pytest / ruff / mypy / alembic。

无任何 mock。

## 本地运行结果

```text
=== packages/core ===
$ (cd packages/core && uv run pytest -q --tb=no tests/)
.........................                                                [100%]
25 passed in 0.10s

=== apps/api（DATAPLAT_DATABASE_URL=postgresql+asyncpg://...:5433/...）===
$ (cd apps/api && uv run pytest -q --tb=no tests/)
...                                                                      [100%]
3 passed in 0.60s

=== alembic upgrade head ===
Running upgrade  -> 0001, initial schema
alembic current: 0001 (head)

=== ruff + mypy ===
All checks passed!
Success: no issues found in 23 source files

=== scripts/_self_check.sh core-domain-model ===
PASS: 17 / FAIL: 0 / SKIP: 0
```

## 已知 flaky / 跳过

- **无 flaky**：所有断言确定性。
- **AC-13 / AC-15 在 Postgres 不可达时 SKIP**（不是 FAIL）——`_self_check.sh` 用 python socket 探针实现。
- ORM smoke 数据残留风险：用 random uuid 作 tree_hash / commit_hash，避免多次跑产生 unique 违反。

## 覆盖率（结构覆盖率）

| 度量 | 实测 |
|---|---|
| spec AC 覆盖率 | 17 / 17 = **100%** |
| 改动文件被某条 AC 触达 | 23 / 23 = **100%** |
| Pydantic 模型负向校验覆盖 | Layer / Subtype / kind / entry_type / sha256 / size 全部有 pytest.raises(ValidationError) |

## 偏离 SKILL 标准

| 偏离点 | 说明 |
|---|---|
| ORM smoke 仅 2 个用例（spec AC-15 要求 ≥ 2） | 满足下限；后续 `repo-api-mvp` 引入业务路由时再补 |
| 部分边界用例（如外键级联删除、batch insert）未覆盖 | 留给 follow-up |
| 时区往返单测未单独写 | conftest + ORM smoke 实跑已隐含 timezone-aware datetime；显式单元测试待 follow-up |

## ⚠️ 流程偏离（接 coding_report §流程偏离声明）

Stage 6 单测评审同样采用 self-attest 路径——事由、等价证据、follow-up 规则化路径见 `coding/coding_report_v1.md` 与 `coding/review/code_review_v1.md` §流程偏离声明。

## 下一步

进入 **Stage 7 代码推送**：精确 add 23+ 文件 + commit + stage 10 closure（含 §交付与 §复盘）。
