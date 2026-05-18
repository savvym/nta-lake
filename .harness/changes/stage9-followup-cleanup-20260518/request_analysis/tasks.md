---
change_id: stage9-followup-cleanup-20260518
version: 3
authored_at: 2026-05-18T11:30:00Z
prior_version: 2
prior_review: request_analysis/review/tasks_review_v2.md
---

# Tasks

> **v3 修订说明**：闭 tasks_review_v2.md 同型 MUST FIX 联动（T-6 AC-3 grep 改 awk 状态机）。

## v1 review 闭环表

| # | 类别 | 位置 | v2 状态 |
|---|---|---|---|
| MUST #1 | T-6 联动 spec AC-1 grep | **CLOSED**：T-6 description 引用 spec v2 新 awk 状态机 pattern |
| SHOULD #1 | T-2 alembic 高层 API | **CLOSED**：T-2 description 明示 `op.drop_constraint` + `op.create_foreign_key` |
| SHOULD #2 | T-3 缺前置 alembic current | **CLOSED**：T-3 第一步加 alembic current 期望 0004 (head) |
| SHOULD #3 | T-5/spec AC-4 数字 | **CLOSED**：T-5 description 明示"4 sync + 6 async = 10"；spec v2 AC-4 同步 |
| NTH #1 | T-5 depends_on | **CLOSED**：T-5 depends_on 改 [T-1, T-3, T-4] 显式 |
| NTH #2 | uuid 前缀字串形态 | **CLOSED**：T-4 description 改用 HTML 注释 `<!-- fixture-uuid ... -->` 防御性 |

## 任务清单

```yaml
tasks:
  - id: T-1
    title: 改 apps/api/dataplat_api/models/pipeline.py 的 output_commit_hash FK 为 CASCADE
    description: |
      apps/api/dataplat_api/models/pipeline.py:88 PipelineCacheORM.output_commit_hash
      mapped_column ForeignKey("commits.hash", ondelete="RESTRICT") → ondelete="CASCADE"
    depends_on: []
    estimated_stage: coding
    covers_ac: [AC-1]
    status: pending
    commits: []

  - id: T-2
    title: 新建 alembic 0005 migration ALTER FK constraint RESTRICT → CASCADE
    description: |
      apps/api/alembic/versions/0005_pipeline_cache_fk_cascade.py。
      用 **alembic 高层 API**（与 0004 风格一致，不用裸 op.execute SQL）：
        upgrade():
          op.drop_constraint(
              "pipeline_cache_output_commit_hash_fkey",
              "pipeline_cache",
              type_="foreignkey",
          )
          op.create_foreign_key(
              "pipeline_cache_output_commit_hash_fkey",
              "pipeline_cache",
              "commits",
              ["output_commit_hash"],
              ["hash"],
              ondelete="CASCADE",
          )
        downgrade(): 反向（CASCADE → RESTRICT）
      revision="0005"; down_revision="0004"; branch_labels=None.
    depends_on: []
    estimated_stage: coding
    covers_ac: [AC-1, AC-2]
    status: pending
    commits: []

  - id: T-3
    title: alembic upgrade head + downgrade 0004 + 再 upgrade head 三连真跑
    description: |
      在 dev 本机（PG 5433）跑：
        cd apps/api
        # 0. 前置检查：当前 alembic head 是 0004
        DATAPLAT_DATABASE_URL=postgresql+asyncpg://dataplat:dataplat@localhost:5433/dataplat \
          uv run alembic current
        # 期望输出含 "0004 (head)"；如果不是，先 `alembic upgrade 0004` 调整
        # 1. upgrade to 0005
        DATAPLAT_DATABASE_URL=... uv run alembic upgrade head
        # 2. downgrade back to 0004
        DATAPLAT_DATABASE_URL=... uv run alembic downgrade 0004
        # 3. re-upgrade to 0005
        DATAPLAT_DATABASE_URL=... uv run alembic upgrade head
      验证：
        三步退码 0；
        upgrade 后查 information_schema:
          docker exec dataplat-pg-test psql -U dataplat -d dataplat -c \
            "SELECT delete_rule FROM information_schema.referential_constraints \
             WHERE constraint_name='pipeline_cache_output_commit_hash_fkey';"
        期望 delete_rule = 'CASCADE'
    depends_on: [T-2]
    estimated_stage: coding
    covers_ac: [AC-2]
    status: pending
    commits: []

  - id: T-4
    title: 改 _seed_bronze 加 uuid 前缀
    description: |
      apps/api/tests/test_pipeline_orchestrator.py::_seed_bronze 函数内部：
        # 在 r_blob upload 之前
        unique_content = f"<!-- fixture-uuid {uuid.uuid4().hex} -->\n".encode() + content
        r_blob = await c.post(f"/repos/{owner}/{name}/blobs", content=unique_content)
      保持外部 `content: bytes` 参数语义不变；现有 6 个调用点全自动受益。
      用 HTML 注释 `<!-- ... -->` 而非 markdown H1 `# ...`：防御性写法，markdown-normalize
      处理 HTML 注释行为更可预测（多数 normalize 直接保留或 strip，不当 H1 标题处理）。
      注意：测试断言依赖 _seed_bronze 返回的 commit_hash，content 只在 seed 期被 hashed，
      不被任何 assertion 读取（v1 reviewer 实读 6 处 callsite 确认）。
    depends_on: []
    estimated_stage: coding
    covers_ac: [AC-3]
    status: pending
    commits: []

  - id: T-5
    title: 真跑 test_pipeline_orchestrator.py 全部测试
    description: |
      DATAPLAT_DATABASE_URL=postgresql+asyncpg://dataplat:dataplat@localhost:5433/dataplat \
      DATAPLAT_JWT_SECRET=test-secret-not-prod-x32-bytes-xxxxx \
      DATAPLAT_MINIO_ENDPOINT=http://localhost:9100 \
      DATAPLAT_MINIO_ACCESS_KEY=dataplat \
      DATAPLAT_MINIO_SECRET_KEY=dataplat-secret \
      DATAPLAT_REDIS_URL=redis://localhost:6379/0 \
      DATAPLAT_LLM_PROVIDER=fake \
      uv run pytest -q apps/api/tests/test_pipeline_orchestrator.py
      期望：10 passed（4 个 sync 单元 + 6 个 @pytestmark_int 集成）；
      含 stage 9 后曾 FAIL 的 3 个 cache_hit 测试全 PASS：
        test_cache_hit_skips_processor / test_cache_hit_updates_ref /
        test_cache_hit_writes_audit_fields
    depends_on: [T-1, T-3, T-4]
    estimated_stage: unit_test
    covers_ac: [AC-4]
    status: pending
    commits: []

  - id: T-6
    title: scripts/_self_check.sh 加本 change block run_stage9_followup_cleanup
    description: |
      加 `run_stage9_followup_cleanup()`，含 AC-1..AC-4 验证：
        - AC-1（**用 spec v2 awk 状态机 pattern**）：
            awk '/^class PipelineCacheORM/{p=1;next} p && /^class /{exit} p' \
                apps/api/dataplat_api/models/pipeline.py | grep -q 'ondelete="CASCADE"'
            + ls apps/api/alembic/versions/0005_*.py >/dev/null 2>&1
            + grep -q "CASCADE" apps/api/alembic/versions/0005_*.py
            + grep -q 'ondelete="RESTRICT"' apps/api/alembic/versions/0004_pipeline_orchestrator.py
        - AC-2（行为型，PG 探针）：alembic current → 期望 0005；
            docker exec dataplat-pg-test psql -U dataplat -d dataplat -c \
              "SELECT delete_rule FROM information_schema.referential_constraints \
               WHERE constraint_name='pipeline_cache_output_commit_hash_fkey';" \
            | grep -q "CASCADE"
        - AC-3（**用 awk 状态机锚定 _seed_bronze 函数体**，同 spec v3 AC-3 pattern）：
            awk '/^async def _seed_bronze/{p=1;next} p && /^async def |^def /{exit} p' \
                apps/api/tests/test_pipeline_orchestrator.py \
              | grep -qE "uuid\.uuid4\(\)\.hex.*content|unique_content.*=.*uuid"
        - AC-4（行为型，PG+MinIO+Redis 三探针）：
            dry run pytest -q test_pipeline_orchestrator.py，期望 10 passed
      在 main 添加调用（pipeline-orchestrator-mvp block 之后、harness-ac-behavioral-tier-20260518 之前）。
    depends_on: [T-1, T-2, T-4]
    estimated_stage: coding
    covers_ac: [AC-1, AC-2, AC-3, AC-4]
    status: pending
    commits: []
```

## 阶段任务（必备占位）

```yaml
process_tasks:
  - id: P-spec-review
    estimated_stage: request_analysis_review
    status: pending

  - id: P-code-review
    estimated_stage: coding_review
    status: pending

  - id: P-test-review
    estimated_stage: unit_test_review
    status: pending

  - id: P-ci
    estimated_stage: ci_result
    status: self-attest
    notes: "项目无 remote 长期未决（同 change #1）"

  - id: P-deploy
    estimated_stage: deployment
    status: pending
    notes: "有部署面（DB migration 0005），必须真跑 deploy_verify v1 不能 self-attest"

  - id: P-user-confirm
    estimated_stage: user_confirmation
    status: pending
```

## DAG 健全性

```text
T-1 ──┐
T-2 ──┴──→ T-3 ──┐
T-4 ──┐         ├──→ T-5
T-1 ──┴──────────┘
T-1/T-2/T-4 → T-6
```

无环。T-5 是行为型终点（pytest 真跑），T-6 是 self_check block。
T-5 显式 depends [T-1, T-3, T-4]：T-1 model 改 + T-3 alembic 三连 + T-4 fixture 改都必须先完成。

## 验收覆盖矩阵

| AC | kind | 关联任务 |
|---|---|---|
| AC-1 | static | T-1, T-2, T-6 |
| AC-2 | **behavioral** | T-2, T-3, T-6 |
| AC-3 | static | T-4, T-6 |
| AC-4 | **behavioral** | T-5, T-6 |

每条 AC 至少一个 T-* 关联。**behavioral AC 数：2（AC-2 + AC-4）**，满足规约。
