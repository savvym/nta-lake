---
change_id: stage9-followup-cleanup-20260518
version: 1
authored_at: 2026-05-18T12:00:00Z
status: waiting_review
---

# Test Report v1

> 本变更的"测试"载体是 `apps/api/tests/test_pipeline_orchestrator.py`（既存测试文件 + 本 change 修了 fixture）+ `scripts/_self_check.sh::run_stage9_followup_cleanup`（本 change 新建 self_check block）。Stage 3 已落地真跑证据。

## 验收项 ↔ 测试映射

| AC ID | kind | 测试形态 | 测试位置 | 测试函数/步骤 |
|---|---|---|---|---|
| AC-1 | static | self_check bash 断言 | `scripts/_self_check.sh::run_stage9_followup_cleanup` | `run_ac AC-1`：awk 状态机锚定 PipelineCacheORM 类 + grep CASCADE；ls 0005_*.py + grep CASCADE；grep 0004 保留 RESTRICT |
| AC-2 | **behavioral** | alembic 三连 + DB SQL 断言 | self_check + 本机 dev | `run_ac AC-2`：alembic current=0005 + `information_schema.referential_constraints.delete_rule = CASCADE` 双层断言（PG 真查） |
| AC-3 | static | self_check bash 断言 | self_check | `run_ac AC-3`：awk 状态机锚定 `_seed_bronze` 函数体 + grep `uuid.uuid4().hex.*content` 或 `unique_content.*=.*uuid` |
| AC-4 | **behavioral** | pytest 集成测试真跑 | `apps/api/tests/test_pipeline_orchestrator.py` | `run_ac AC-4`：dry run pytest -q 全文件，期望 `10 passed`（4 sync + 6 async@pytestmark_int；含 cache_hit 3） |

每条 AC 至少一个测试。**behavioral AC：AC-2（L3 alembic + SQL 真查）+ AC-4（L2 ASGITransport pytest 真跑）**，满足 ≥1 自约束。

## 测试文件清单

| 文件 | 类型 | 用例数 |
|---|---|---|
| `apps/api/tests/test_pipeline_orchestrator.py` | pytest 集成 | 10（4 sync + 6 async@pytestmark_int） |
| `scripts/_self_check.sh::run_stage9_followup_cleanup` | self_check block | 4 AC |

## Mock 范围声明

- **允许 mock**：`DATAPLAT_LLM_PROVIDER=fake`（FakeLLMProvider，避免 anthropic 调用）；`_override_blob_store` fixture monkeypatch MinIO bucket 到 uuid 唯一名（已有，本 change 不动）。
- **禁止 mock**：alembic migration（AC-2 必须真跑 PG schema 切换）；pipeline orchestrator / processor runner（AC-4 真跑 ASGITransport in-process roundtrip）。

## 测试真跑证据

### AC-2 alembic 三连 + DB SQL 断言

```text
$ cd apps/api && export DATAPLAT_DATABASE_URL=postgresql+asyncpg://dataplat:dataplat@localhost:5433/dataplat
$ uv run alembic current
0004
$ uv run alembic upgrade head
INFO  Running upgrade 0004 -> 0005, pipeline_cache.output_commit_hash FK RESTRICT → CASCADE
$ uv run alembic downgrade 0004
INFO  Running downgrade 0005 -> 0004
$ uv run alembic upgrade head
INFO  Running upgrade 0004 -> 0005
$ docker exec dataplat-pg-test psql -U dataplat -d dataplat -tA -c \
    "SELECT delete_rule FROM information_schema.referential_constraints \
     WHERE constraint_name='pipeline_cache_output_commit_hash_fkey';"
CASCADE
```

### AC-4 pytest 全 10 测试 PASS（含 stage 9 后曾 FAIL 的 3 个 cache_hit）

```text
$ DATAPLAT_DATABASE_URL=... DATAPLAT_JWT_SECRET=... DATAPLAT_MINIO_ENDPOINT=... \
  DATAPLAT_MINIO_ACCESS_KEY=dataplat DATAPLAT_MINIO_SECRET_KEY=dataplat-secret \
  DATAPLAT_REDIS_URL=... DATAPLAT_LLM_PROVIDER=fake \
  uv run pytest -q apps/api/tests/test_pipeline_orchestrator.py
..........                                                               [100%]
10 passed in 6.67s
```

### 全仓 self_check（本 change block + global lint）

```text
=== stage9-followup-cleanup-20260518 :: 4 AC ===
PASS  AC-1        model + 0005 migration FK CASCADE；0004 保留 ondelete=RESTRICT
PASS  AC-2        alembic head=0005 + information_schema delete_rule=CASCADE
PASS  AC-3        _seed_bronze 含 uuid 前缀注入（awk 状态机锚定函数体）
PASS  AC-4        test_pipeline_orchestrator.py 10/10 PASS（含 cache_hit 3）

=== global :: ac-kind-lint ===
PASS  ac-kind-lint  AC 分层规约守门（kind 列存在 + AC 行 kind=behavioral 锚定 regex）

=== 汇总 ===
PASS: 252
FAIL: 0
SKIP: 0
```

**项目史上第一次 self_check 全仓 FAIL=0**（之前 238/239 因 pipeline AC-8 cache_hit fixture pollution，本 change 直接修掉）。

## 覆盖维度

| 维度 | 是否覆盖 | 备注 |
|---|---|---|
| FK CASCADE 在 DB 真生效 | ✓ | AC-2 + 跨 repo refs cleanup 双重测试 |
| alembic upgrade / downgrade / re-upgrade 对称 | ✓ | AC-2 三连 |
| _seed_bronze 加 uuid 前缀后 6 个调用点全 PASS | ✓ | AC-4 跑全文件含 3 个 cache_hit 测试 |
| 跨 repo refs cleanup（stage 3 偏离扩展）| ✓ | AC-4 cache_hit 3 测试间接覆盖 |
| markdown-normalize 对 HTML 注释前缀的处理 | ✓ | stage 4 reviewer 实读 processors/markdown_normalize.py 确认不当 markdown 解析 |

## 已知未解决问题

- `test_pipeline_e2e.py` 同名 `_seed_bronze` 未跟修（risk 表已显式 accept，follow-up `test-fixture-isolation-other-files-*`）

## 下一步

- 准备 stage 6 review：spawn `claude-agent:stage9-followup-cleanup-20260518-stage6-reviewer-v1`
- summary.md stage=`unit_test_review` status=`in_progress`
