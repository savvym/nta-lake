---
change_id: stage9-followup-cleanup-20260518
version: 1
env: dev
deployed_at: 2026-05-18T11:40:00Z
commit_sha: TBD-on-stage-7-commit
verifier: claude-agent:stage9-followup-cleanup-20260518-stage9-verifier-v1
verdict: PASS
---

# Deploy Verification v1

> 本 change 有部署面（DB schema migration 0005 + 测试代码改），按 `.harness/rules/development-process.md` § "阶段 9 Quality Gate (i) verdict=PASS 默认" 走真 deploy_verify（不走 self-attest 替代）。

## 部署拓扑

- **PG**：docker `dataplat-pg-test` (postgres:16) → host:5433；alembic head 已升到 **0005**（含 0005 migration 真 apply）
- **MinIO**：docker `dataplat-minio-test` → host:9100，bucket `dataplat-blobs`（本 change 不动）
- **Redis**：docker `dataplat-redis-test` → host:6379（本 change 不动）
- **API**：本 change 不重启 API（model FK 改动随 ORM 序列化在下次启动生效；pytest 用 in-process ASGITransport 立即可见）
- **Worker**：不重启（本 change 不动 worker 代码）

env 配置：`/tmp/dataplat-env.sh`。

## 验证矩阵

| ID | kind | 验收项 | 验证方式 | 实际 | 证据 |
|---|---|---|---|---|---|
| DEP-1 | static | alembic head 升到 0005 | `cd apps/api && uv run alembic current` | `0005` | [evidence](#dep-1) |
| DEP-2 | **behavioral** | FK constraint delete_rule 在 DB 真切换到 CASCADE | `docker exec dataplat-pg-test psql ... -c "SELECT delete_rule ... WHERE constraint_name='pipeline_cache_output_commit_hash_fkey'"` | `CASCADE` | [evidence](#dep-2) |
| DEP-3 | **behavioral** | alembic downgrade 0004 + 再 upgrade head 干净跑通（可逆性） | `alembic downgrade 0004 && alembic upgrade head` | 两步退码 0 + delete_rule 反向切换正确 | [evidence](#dep-3) |
| AC-4 | **behavioral** | `test_pipeline_orchestrator.py` 10/10 PASS（含 cache_hit 3） | `uv run pytest -q apps/api/tests/test_pipeline_orchestrator.py` | `10 passed in 6.67s` | [evidence](#ac-4) |
| DEP-4 | **behavioral** | 全仓 `bash scripts/_self_check.sh` FAIL=0（项目史上首次） | 全仓 self_check | `PASS: 252 FAIL: 0` | [evidence](#dep-4) |

## 证据

### DEP-1

```text
$ cd apps/api && DATAPLAT_DATABASE_URL=postgresql+asyncpg://dataplat:dataplat@localhost:5433/dataplat \
  uv run alembic current
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
0005
```

### DEP-2

```text
$ docker exec dataplat-pg-test psql -U dataplat -d dataplat -tA -c \
    "SELECT delete_rule FROM information_schema.referential_constraints \
     WHERE constraint_name='pipeline_cache_output_commit_hash_fkey';"
CASCADE
```

### DEP-3

```text
$ DATAPLAT_DATABASE_URL=... uv run alembic downgrade 0004
INFO  Running downgrade 0005 -> 0004, pipeline_cache.output_commit_hash FK RESTRICT → CASCADE
$ docker exec ... -c "SELECT delete_rule ..."
RESTRICT  # ← downgrade 后回到 RESTRICT，正确
$ DATAPLAT_DATABASE_URL=... uv run alembic upgrade head
INFO  Running upgrade 0004 -> 0005
$ docker exec ... -c "SELECT delete_rule ..."
CASCADE  # ← re-upgrade 后回 CASCADE，可逆性验证通过
```

### AC-4

```text
$ DATAPLAT_DATABASE_URL=... DATAPLAT_JWT_SECRET=... DATAPLAT_MINIO_ENDPOINT=... \
  DATAPLAT_MINIO_ACCESS_KEY=dataplat DATAPLAT_MINIO_SECRET_KEY=dataplat-secret \
  DATAPLAT_REDIS_URL=... DATAPLAT_LLM_PROVIDER=fake \
  uv run pytest -q apps/api/tests/test_pipeline_orchestrator.py
..........                                                               [100%]
10 passed in 6.67s
```

含 stage 9 后曾 FAIL 的 3 个 cache_hit 测试全 PASS：
- `test_cache_hit_skips_processor`
- `test_cache_hit_updates_ref`
- `test_cache_hit_writes_audit_fields`

### DEP-4

```text
$ DATAPLAT_PG_PORT=5433 DATAPLAT_MINIO_PORT=9100 DATAPLAT_MINIO_ACCESS_KEY=dataplat \
  DATAPLAT_MINIO_SECRET_KEY=dataplat-secret DATAPLAT_REDIS_PORT=6379 \
  bash scripts/_self_check.sh

=== global :: reviewer-lint ===
PASS  reviewer-lint  reviewer 字段独立性守门
=== global :: ac-kind-lint ===
PASS  ac-kind-lint  AC 分层规约守门
=== stage9-followup-cleanup-20260518 :: 4 AC ===
PASS  AC-1..AC-4 全部

=== 汇总 ===
PASS: 252
FAIL: 0
SKIP: 0
全部通过（FAIL=0；SKIP 不阻塞）。
```

## 风险评估

- [x] 涉及 schema 不兼容？**否，但有可逆迁移**。alembic 0005 仅 ALTER FK constraint（DROP + ADD），不改表结构、不动数据。可 `alembic downgrade 0004` 干净回滚到 RESTRICT。dev 已验证可逆性。
- [x] 涉及不可回滚操作？**否**。
- [x] 需要 follow-up？**是**：
  - `test-fixture-isolation-other-files-*`：test_pipeline_e2e.py 同名 fixture 隐患（spec risk 表已 accept）
  - 本 change 同时 follow-up #1（`harness-ac-kind-backfill-*`）的实证：本 change 自身按新规约 dogfood 成功（kind=behavioral 2 条都真跑）

## Verdict

**PASS**

理由：DB schema 0005 已 apply + delete_rule=CASCADE 实测 + alembic 可逆性验证 + pytest 10/10 含曾 FAIL 的 3 个 cache_hit 测试全 PASS + 全仓 self_check 252/252 FAIL=0（项目史上首次）。

## 处理动作

- ✅ PASS → 进入阶段 10 用户确认（在 zhhdzhang 显式授权 "按 1,2,3,4 你自行启动" 范围内）。
- 同步：把全部产物 + 实代码改动一起 commit；summary.md stage 9=done / stage 10=done。
