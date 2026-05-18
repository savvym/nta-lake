---
change_id: stage9-followup-cleanup-20260518
version: 1
authored_at: 2026-05-18T11:50:00Z
branch: main（无 remote）
base_commit: ad170d0
head_commit: (uncommitted)
status: waiting_review
---

# Coding Report v1

## 改动文件清单

| 路径 | 类型 | 一句话说明 | 关联 task |
|---|---|---|---|
| `apps/api/dataplat_api/models/pipeline.py` | mod | `PipelineCacheORM.output_commit_hash` FK `ondelete="RESTRICT"` → `ondelete="CASCADE"` | T-1 |
| `apps/api/alembic/versions/0005_pipeline_cache_fk_cascade.py` | new | alembic 0005 用 `op.drop_constraint` + `op.create_foreign_key` 高层 API ALTER 既有 FK | T-2 |
| `apps/api/tests/test_pipeline_orchestrator.py` | mod | (a) `_seed_bronze` 加 `<!-- fixture-uuid <hex> -->\n` HTML 注释前缀；(b) `_delete_repo_cascade` 加跨 repo refs 清理（删本 repo commits 前，先清掉**所有**指向本 repo commits 的 refs） | T-4 + **stage 3 发现**（见偏离） |
| `scripts/_self_check.sh` | mod | 加 `run_stage9_followup_cleanup()` 含 AC-1..AC-4 + main 调用链 + case 分支 | T-6 |

## 与 tasks.md 的映射

| Task ID | 状态 | 备注 |
|---|---|---|
| T-1 | done | model FK CASCADE |
| T-2 | done | 0005 migration（`op.drop_constraint` + `op.create_foreign_key`，与 0004 风格一致） |
| T-3 | done | 本机三连真跑通过：alembic current=0004 / upgrade→0005 / downgrade→0004 / upgrade→0005；`delete_rule = CASCADE` 经 `information_schema.referential_constraints` 验证 |
| T-4 | done | `_seed_bronze` 加 HTML 注释 uuid 前缀 |
| T-5 | done | `test_pipeline_orchestrator.py` 10/10 PASS（含 cache_hit 3）|
| T-6 | done | `run_stage9_followup_cleanup` 4/4 PASS（其中 AC-2 / AC-4 是 behavioral，真跑 alembic + pytest） |

## 偏离 spec / trade-off

### 偏离 1（新增 cleanup 清理逻辑）

**发现**：T-5 第一次跑 pytest 时仍 3 个 cache_hit 测试 FAIL，错误是 `refs_commit_hash_fkey` violation——`_delete_repo_cascade` 删 bronze commits 时被 silver/tgt 的 ref 卡住，因为 `_preseed_cache(cache_key, src_commit)` 把 silver 的 main ref 指向了 bronze repo 的 commit。

**根因**：跨 repo refs 引用（silver ref → bronze commit）+ cleanup 只删本 repo 的 refs。

**修法**：`_delete_repo_cascade` 在 `DELETE FROM refs WHERE repo_id=:r` 之后加：
```sql
DELETE FROM refs WHERE commit_hash IN (SELECT hash FROM commits WHERE repo_id=:r)
```
清掉所有指向本 repo commits 的 refs（无论该 ref 属哪个 repo）。

**偏离判断**：超出 spec T-4 范围（spec T-4 只说 `_seed_bronze` 加 uuid 前缀）。但这是 stage 3 实施 + T-5 真跑暴露的依赖问题——**没有这个 fixture 改动，AC-4 永远 FAIL**。本质上是同型 fixture-isolation 修复，accept 作为 stage 3 偏离扩展。

**风险评估**：cleanup 更严格，但只在测试 fixture 内部，不影响业务路径。

### 偏离 2（pipeline_cache 显式 DELETE 在 _delete_repo_cascade 保留）

虽然 model 已 CASCADE，`_delete_repo_cascade` 中仍保留 `DELETE FROM pipeline_cache WHERE output_commit_hash IN (...)` 显式清理——理由：
- downgrade 路径（0005→0004）后 FK 是 RESTRICT；若 cleanup 跑在 downgrade 后会失败
- 显式清理保持向后兼容；CASCADE 是"自动兜底"，显式 cleanup 是"显式意图"

注释已加，不阻塞。

## 本地校验结果

### Fixture-bug 真跑闭环（AC-2 + AC-4 behavioral 核心证据）

```text
$ cd apps/api && DATAPLAT_DATABASE_URL=... uv run alembic current
0004
$ DATAPLAT_DATABASE_URL=... uv run alembic upgrade head
INFO  [alembic.runtime.migration] Running upgrade 0004 -> 0005, pipeline_cache.output_commit_hash FK RESTRICT → CASCADE
$ DATAPLAT_DATABASE_URL=... uv run alembic downgrade 0004
INFO  Running downgrade 0005 -> 0004
$ DATAPLAT_DATABASE_URL=... uv run alembic upgrade head
INFO  Running upgrade 0004 -> 0005
$ docker exec dataplat-pg-test psql -U dataplat -d dataplat -tA -c "SELECT delete_rule FROM information_schema.referential_constraints WHERE constraint_name='pipeline_cache_output_commit_hash_fkey';"
CASCADE
```

```text
$ DATAPLAT_DATABASE_URL=... DATAPLAT_JWT_SECRET=... DATAPLAT_MINIO_ENDPOINT=... \
  DATAPLAT_MINIO_ACCESS_KEY=dataplat DATAPLAT_MINIO_SECRET_KEY=dataplat-secret \
  DATAPLAT_REDIS_URL=... DATAPLAT_LLM_PROVIDER=fake \
  uv run pytest -q apps/api/tests/test_pipeline_orchestrator.py
..........                                                               [100%]
10 passed in 6.67s
```

### 全仓 self_check

```text
$ DATAPLAT_PG_PORT=5433 DATAPLAT_MINIO_PORT=9100 DATAPLAT_MINIO_ACCESS_KEY=dataplat \
  DATAPLAT_MINIO_SECRET_KEY=dataplat-secret DATAPLAT_REDIS_PORT=6379 \
  bash scripts/_self_check.sh

=== stage9-followup-cleanup-20260518 :: 4 AC ===
PASS  AC-1        model + 0005 migration FK CASCADE；0004 保留 ondelete=RESTRICT
PASS  AC-2        alembic head=0005 + information_schema delete_rule=CASCADE
PASS  AC-3        _seed_bronze 含 uuid 前缀注入（awk 状态机锚定函数体）
PASS  AC-4        test_pipeline_orchestrator.py 10/10 PASS（含 cache_hit 3）

=== 汇总 ===
PASS: 252
FAIL: 0
SKIP: 0
全部通过
```

**项目史上第一次 self_check 全仓 FAIL=0**（之前 238/239 因 pipeline AC-8 cache_hit fixture pollution，本 change 直接修掉）。

## 已知未解决问题

- `test_pipeline_e2e.py::_seed_bronze` 同名 fixture 未跟修（spec risk 表已显式 accept；follow-up `test-fixture-isolation-other-files-*`）
- pipeline_cache 显式 cleanup 在 `_delete_repo_cascade` 保留作向后兼容；如未来去掉 downgrade 支持可移除（不阻塞）

## 下一步

- 准备 stage 4 review：spawn `claude-agent:stage9-followup-cleanup-20260518-stage4-reviewer-v1`
- summary.md stage=`coding_review` status=`in_progress`
