---
change_id: stage9-followup-cleanup-20260518
version: 3
authored_at: 2026-05-18T11:30:00Z
status: draft
prior_version: 2
prior_review: request_analysis/review/spec_review_v2.md
---

> **v3 修订说明**：闭 spec_review_v2.md 的 1 MUST FIX（同型 v1 MUST #1 —— AC-3 跨行 grep -A 15 窗口不够长，应改 awk 状态机）+ 1 SHOULD（AC-2 同步 alembic current 前置）。

## v2 review 闭环表

| # | 类别 | v2 问题 | v3 状态 |
|---|---|---|---|
| MUST #1 | AC-3 同型跨行盲点（与 v1 MUST #1 同型） | `grep -A 15 "async def _seed_bronze"` 窗口短于函数体到 unique_content 注入位置（约 27 行） | **CLOSED**：改 awk 状态机 `awk '/^async def _seed_bronze/{p=1;next} p && /^async def \|^def /{exit} p'` |
| SHOULD #1 | AC-2 缺 alembic current 前置 | spec 未与 tasks T-3 第 0 步对齐 | **CLOSED**：AC-2 验证扩展含前置 `alembic current` 期望 `0004` |

# Spec：stage 9 余波合并修复（pipeline_cache FK CASCADE + test fixture 撞 commit hash 隔离）

> **v2 修订说明**：闭 spec_review_v1 的 1 MUST FIX + 3 SHOULD FIX + 3 NICE TO HAVE。

## v1 review 闭环表

| # | 类别 | 位置 | v1 问题 | v2 状态 |
|---|---|---|---|---|
| MUST #1 | AC-1 grep pattern 永远 fail | AC-1 | `grep -A 2 "output_commit_hash.*ForeignKey"` 同行匹配，但 model 文件 output_commit_hash 与 ForeignKey 跨第 86/88 行不在一行 | **CLOSED**：改用 awk 状态机锚定 PipelineCacheORM 类范围：`awk '/^class PipelineCacheORM/{p=1;next} p && /^class /{exit} p' pipeline.py \| grep -q 'ondelete="CASCADE"'`；本机 dry-run 验证：pre-T-1（当前 RESTRICT）的 grep 在新 pattern 下命中 RESTRICT，post-T-1（改 CASCADE）命中 CASCADE |
| SHOULD #1 | FK CASCADE 决策漏 nullable=False 硬约束 | 决策表 | 只说"语义无意义" | **CLOSED**：决策表加"`PipelineCacheORM.output_commit_hash` nullable=False，SET NULL 物理违反 NOT NULL，必须先改 nullable=True 才能用 SET NULL，超出本 change scope" |
| SHOULD #2 | risk 表漏 test_pipeline_e2e.py 同名 fixture 隐患 | 风险表 | 只在"不受影响模块"段轻提 | **CLOSED**：risk 表新增一行 + 显式 accept + follow-up `test-fixture-isolation-other-files-*` |
| SHOULD #3 | AC-4 描述 vs 期望数字打架 | AC-4 | 描述说"7 集成测试"，期望 ≥10 | **CLOSED**：AC-4 描述改"`test_pipeline_orchestrator.py` 全部 10 个测试 PASS（4 个 sync 单元 + 6 个 @pytestmark_int 集成；含 stage 9 后曾 FAIL 的 3 个 cache_hit）" |
| NTH #1 | _seed_bronze 决策措辞模糊 | 决策表 | "不依赖 raw content 字串" | **CLOSED**：改为"测试断言依赖 _seed_bronze 返回的 commit_hash，content 只在 seed 期被 hashed，不被任何 assertion 读取" |
| NTH #2 | AC-1 0005 文件 glob 脆弱 | AC-1 | `test -f apps/api/alembic/versions/0005_*.py` 多匹配会 too many arguments | **CLOSED**：改用 `ls .../0005_*.py >/dev/null 2>&1 && ...` |
| NTH #3 | 0004 grep RESTRICT 裸 | AC-1 | 未来无关字串可误命中 | **CLOSED**：加 `ondelete="..."` 前缀锚定 |

## 背景

`pipeline-orchestrator-mvp-20260518` stage 9 第一次真跑端到端 demo 时抓到 3 个真 bug。其中 2 个收尾在 deploy_verify_v1.md follow-up 表里待处理：

1. **`pipeline_cache.output_commit_hash` FK 缺 CASCADE**：`apps/api/dataplat_api/models/pipeline.py:88` 与 `alembic/versions/0004_pipeline_orchestrator.py:99` 都设 `ondelete="RESTRICT"`。导致 stage 9 e2e 脚本清理步骤 `DELETE /repos/demo/normalized-md` 触发 `ForeignKeyViolationError: pipeline_cache_output_commit_hash_fkey`，HTTP 500。pipeline 主路径未触发，AC 没覆盖。
2. **`test_pipeline_orchestrator._seed_bronze` 用 hardcoded byte content 撞 commit hash**：`apps/api/tests/test_pipeline_orchestrator.py` 第 406/478/532/589/654/703 行用 `b"x\n"` / `b"hello\r\nworld\r\n"` 等固定 content。**`commits.hash` 是全局 sha256 PK 不带 repo_id**，本机 dev 跑过 stage 9 demo（同 content）后再跑 pytest 必撞 unique constraint，self_check 从 226/226 退到 238/239。CI clean DB 不显问题但脆弱。

本 change 是同名 change #1 `harness-ac-behavioral-tier-20260518` 的"治标"配对——后者治 AC 假象（grep 假象），本 change 修两个具体 bug。

## 问题陈述

- **Bug 1 影响**：任何尝试删 `pipeline_cache.output_commit_hash` 引用过的 commit / repo 都会 500。stage 9 e2e 清理路径、未来 GC / quota 实现都会撞。
- **Bug 2 影响**：本机开发体验：用户跑过一次 demo → pytest 必撞。CI 看不到。隐蔽性高。

## 范围

In scope（**4 条 AC，含 2 条 behavioral**）：

- **AC-1**：alembic 0005 migration 改 `pipeline_cache_output_commit_hash_fkey` 的 `ondelete` 从 `RESTRICT` → `CASCADE`；同步 `apps/api/dataplat_api/models/pipeline.py::PipelineCacheORM.output_commit_hash` mapped_column。
- **AC-2**：alembic upgrade head 到 0005 干净（dev 本机 5433 PG）；downgrade 0005→0004 也干净（FK 切回 RESTRICT）。
- **AC-3**：`apps/api/tests/test_pipeline_orchestrator.py::_seed_bronze` 内部给 content 前缀 `uuid.uuid4().hex + " "` 字串后再上传 blob；所有 6 个调用点自动受益。
- **AC-4**：跑 `test_pipeline_orchestrator.py` 全部测试 PASS（特别是 `test_cache_hit_skips_processor` / `test_cache_hit_updates_ref` / `test_cache_hit_writes_audit_fields` 三个 stage 9 后 FAIL 的）。

## 非范围

- **不**改 `commits.hash` PK 语义（加 repo_id 范围 hash 是大改，spec 范围超出本 change；follow-up `commits-hash-scoped-by-repo-*`）。
- **不**重写 0004 migration（已落地 dev，不允许改写历史）。
- **不**普查所有测试文件的 fixture（stage 9 实证只有 `test_pipeline_orchestrator.py` 撞；其他文件不动；follow-up `test-fixture-isolation-other-files-*` 待累积证据）。
- **不**做 cache 失效语义（CASCADE 是物理删除，不需要"标记失效再清理"机制）。
- **不**做 ON DELETE 触发器 / 应用层 hooks。

## 验收标准

**AC kind 二分**：static = grep / test -f / dry-import；behavioral = HTTP / pytest 集成 / migration 真跑。

| ID | kind | 描述 | 验证方式 | 期望 |
|---|---|---|---|---|
| AC-1 | static | model + 0005 migration 含 `ondelete="CASCADE"` 给 `pipeline_cache_output_commit_hash_fkey`；0004 保留 `ondelete="RESTRICT"` 不动 | `test -f apps/api/dataplat_api/models/pipeline.py && awk '/^class PipelineCacheORM/{p=1;next} p && /^class /{exit} p' apps/api/dataplat_api/models/pipeline.py \| grep -q 'ondelete="CASCADE"' && ls apps/api/alembic/versions/0005_*.py >/dev/null 2>&1 && grep -q "CASCADE" apps/api/alembic/versions/0005_*.py && grep -q 'ondelete="RESTRICT"' apps/api/alembic/versions/0004_pipeline_orchestrator.py` | 全 grep 命中 |
| AC-2 | **behavioral** | alembic upgrade 0004→0005 + downgrade 0005→0004 干净跑通；FK constraint 在 DB 里真切换 | `cd apps/api && export DATAPLAT_DATABASE_URL=postgresql+asyncpg://dataplat:dataplat@localhost:5433/dataplat && uv run alembic current 2>&1 \| grep -q "0004" && uv run alembic upgrade head && uv run alembic downgrade 0004 && uv run alembic upgrade head && docker exec dataplat-pg-test psql -U dataplat -d dataplat -tA -c "SELECT delete_rule FROM information_schema.referential_constraints WHERE constraint_name='pipeline_cache_output_commit_hash_fkey';" \| grep -q "CASCADE"` | 前置 alembic current = 0004；三连 upgrade/downgrade/upgrade 退码 0；最终 delete_rule = CASCADE |
| AC-3 | static | `_seed_bronze` 函数体含 uuid 前缀逻辑 | `test -f apps/api/tests/test_pipeline_orchestrator.py && awk '/^async def _seed_bronze/{p=1;next} p && /^async def \|^def /{exit} p' apps/api/tests/test_pipeline_orchestrator.py \| grep -qE "uuid\.uuid4\(\)\.hex.*content\|unique_content.*=.*uuid"` | grep 命中（awk 状态机锚定 _seed_bronze 函数体内，避免跨行短窗口同型缺陷） |
| AC-4 | **behavioral** | `test_pipeline_orchestrator.py` 全部 10 个测试 PASS（4 个 sync 单元 + 6 个 @pytestmark_int 集成；含 stage 9 后曾 FAIL 的 3 个 cache_hit 测试） | `DATAPLAT_DATABASE_URL=postgresql+asyncpg://dataplat:dataplat@localhost:5433/dataplat DATAPLAT_JWT_SECRET=test-secret-not-prod-x32-bytes-xxxxx DATAPLAT_MINIO_ENDPOINT=http://localhost:9100 DATAPLAT_MINIO_ACCESS_KEY=dataplat DATAPLAT_MINIO_SECRET_KEY=dataplat-secret DATAPLAT_REDIS_URL=redis://localhost:6379/0 DATAPLAT_LLM_PROVIDER=fake uv run pytest -q apps/api/tests/test_pipeline_orchestrator.py 2>&1 \| tail -3` | `10 passed in Xs`（含 `test_cache_hit_skips_processor` / `test_cache_hit_updates_ref` / `test_cache_hit_writes_audit_fields` 三个）|

**Behavioral AC 数：2（AC-2 + AC-4）**，满足 ≥1 condition。

## 风险

| 风险 | 概率 | 影响 | 缓解 |
|---|---|---|---|
| 0005 migration upgrade 在已有 pipeline_cache 数据上 ALTER FK 失败 | 低 | 中 | PostgreSQL ALTER TABLE DROP CONSTRAINT + ADD CONSTRAINT 模式（不带 NOT VALID + VALIDATE 二段优化，因 dev 数据量小）；先 dry run 在临时 DB |
| `_seed_bronze` 加 uuid 前缀后断言失败（如测试 hardcode 期望 content hash） | 低 | 中 | 已实读 6 个调用点断言：测试断言依赖 `_seed_bronze` 返回的 commit_hash，content 只在 seed 期被 hashed，不被任何 assertion 读取；如有依赖（实测无）则单独修该测试 |
| stage 9 残留的 pipeline_cache 行干扰 0005 downgrade（downgrade 时若 cache 表非空，新加 RESTRICT 不会失败但语义反向） | 低 | 低 | downgrade 仅作为 rollback 路径，dev 不依赖；不在 AC-2 强制 downgrade 后跑业务路径 |
| FK CASCADE 引入"误删 cache" 风险（管理员删 commit 时 cache 自动消失） | 低 | 低 | 按设计：cache_key 指向无效 commit 无意义；CASCADE 是正确语义。无业务流程依赖"删 commit 但保留 cache" |
| **`test_pipeline_e2e.py` 同名 `_seed_bronze` 未跟修**（v1 reviewer SHOULD #2 实证） | 低 | 中 | **本 change 显式 accept**：stage 9 未 trigger 撞（该文件 raw 与 demo 不同），CI 单跑也不撞；隐患是未来同测试多次重跑撞自己（同 content 第二次进 db 必撞 commits.hash PK）；follow-up `test-fixture-isolation-other-files-*` 待累积证据再处理 |

## 受影响模块

- `apps/api/dataplat_api/models/pipeline.py`（model FK ondelete=CASCADE）
- `apps/api/alembic/versions/0005_*.py`（**新建**，ALTER FK constraint）
- `apps/api/tests/test_pipeline_orchestrator.py`（`_seed_bronze` 加 uuid 前缀）

## 不受影响但易混淆的模块

- `apps/api/alembic/versions/0004_pipeline_orchestrator.py`：保留原状，不改写。
- 其他 `commits.hash` 引用的表（`refs.commit_hash` / `pipeline_node_runs.output_commit_hash`）的 FK 不动 —— 它们各自的语义不同，本 change scope 只修 pipeline_cache。
- 其他测试 fixture（`test_pipeline_e2e.py::_seed_bronze` 也存在，但已用 ASGITransport 在 in-process app 跑，且 stage 9 没 trigger 撞 —— **保留不动**，避免 scope creep；如未来累积证据再 follow-up）。

## 待澄清问题

无（v1 启动时已澄清）。

## 引用

- `.harness/changes/pipeline-orchestrator-mvp-20260518/deployment/deploy_verify_v1.md` § "需要 follow-up"
- `.harness/changes/harness-ac-behavioral-tier-20260518/request_analysis/spec.md`（同期 meta-change 的 AC 分层规约，本 change dogfood）
- `.harness/skills/request-analysis/SKILL.md` § "AC 分层规约" — 本 change 应用新规约
- design.md §4.4 类 Git CAS：commit hash 全局 unique 设计（**不**在本 change 范围内改）
