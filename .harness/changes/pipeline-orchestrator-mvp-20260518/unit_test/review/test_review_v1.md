---
change_id: pipeline-orchestrator-mvp-20260518
target: unit_test (test_report_v1.md + 6 测试文件)
target_version: 1
review_version: 1
reviewer: claude-agent:pipeline-orchestrator-mvp-20260518-stage6-reviewer-v1
reviewed_at: 2026-05-18T07:37:13Z
verdict: APPROVED
---

# Test Review v1

> 评审范围：`unit_test/test_report_v1.md` + 6 个测试文件的实代码（reviewer 全文 Read）。模式：artifact。
> 上游依据：`request_analysis/spec.md` v2（13 AC）+ `coding/review/code_review_v2.md` APPROVED（含 stage 4 v2 MUST #2 / SHOULD #1 反哺 stage 5 的两个新增用例）。

---

## 1. 检查清单结论（expert-reviewer SKILL §1 artifact 模式）

- [x] **每条 spec AC 都映射到至少一个具体测试用例（或 self_check）**。13 AC + 2 stage 4 反哺项全部有归宿（详见 §2 核对表）。
- [x] **无空跑断言**。`grep -nE "assert\s+True|assert\s+1\s*==\s*1"` 在 6 个测试文件全空（reviewer 实跑）。所有 assert 都断言具体值（commit hash 相等 / lineage 字段路径 / call_count==0 / 长度 ≤ 500 等）。
- [x] **mock 范围符合 `coding-style.md` §1.7 / `unit-test-write` SKILL**。集成测试不 mock `RepositoryService` / `BlobStore` / `CommitService` / `RefService` / `CacheService`（reviewer 实跑 `grep -nE "mock|MagicMock|AsyncMock" apps/api/tests/test_pipeline_*.py` → 仅 `monkeypatch` 出现，且只用于 (a) `ProcessorRunner.run` spy 验 call_count（cache hit 场景必要）+ (b) MinIO 环境变量切换（fixture 注入 `_override_blob_store`）+ (c) `test_node_400_marks_failed` 模拟 ProcessorRunner 抛 HTTPException 触发截断路径——三处都是"被测对象"或"环境"，非数据访问层）。
- [x] **测试名能反映场景**。如 `test_cache_hit_skips_processor` / `test_node_value_error_marks_failed_with_null_audit` / `test_canonical_config_hash_neq_cache_key`（v2 防 regress 显式）—— 命名既含被测对象又含期望，远超 `test_xxx_1` 反模式。
- [x] **fixture cleanup 合理**。`_delete_repo_cascade` / `_delete_user` 在 finally 兜底；`_override_blob_store` 用 try/finally 删 bucket + restore `dependency_overrides` + reset `_blob_store` 全局。
- [x] **测试间独立**。owner/src/tgt 用 `uuid.uuid4().hex[:4]` 随机生成；无共享 mutable state；patch `ProcessorRunner.run` 都在 try/finally 内 restore `original`。
- [x] **覆盖率手工估算 ≥60%**（详见 §6 评估）。

## 2. AC ↔ 测试映射逐条核对

| AC | 声明 | 实测试覆盖（reviewer 抽检验证） | 结论 |
|---|---|---|---|
| AC-1 | `test_pipeline_schemas.py` × 7 | reviewer Read：`test_valid_recipe_minimal` 构 Recipe；4 个 `..._raises` 用 `pytest.raises(ValidationError)`；`test_load_recipe_from_yaml_text` + `test_load_recipe_from_dict` 双路径覆盖 loader。**全 7 用例均有实质断言**。 | OK |
| AC-2 | `test_pipeline_dag.py` × 6 | reviewer Read：linear/branching/cycle/unknown deps/duplicate id/build_node_deps 六条断言精确（`assert out == [...]`，cycle 用 `match="cycle"`）。 | OK |
| AC-3 | `test_pipeline_cache.py` × 6 | reviewer Read：determinism 验 sha256 长度 = 64；inputs/config 顺序无关；list-in-config 顺序敏感；**`test_canonical_config_hash_neq_cache_key` 明确防 v2 reviewer 担心的"整体 cache_key 当 config_hash"regress**；processor_version 入键测试。 | OK |
| AC-4 | self_check grep migration + INSERT 路径 | spec v2 §"验收命令"已含 migration 文件 + 三表名 grep；coding_report v2 AC-4 self_check PASS。本 stage 不重复测；接受为 self_check 覆盖。 | OK |
| AC-5 | `test_processor_runner_backcompat.py` × 2 | reviewer Read：两用例皆是 `inspect.signature` 反射断言（`lineage in parameters` + `default is None` + 位置在 required 参数之后）。**这是 signature contract 验证而非空跑**——直接对应 R-1（既有 `routers/process.py` positional 调用不破）。 | OK |
| AC-6 | `test_pipeline_orchestrator.py` validate_recipe × 4 + e2e | 4 个无 DB 单元（unknown_processor / cycle / unknown_node_ref / multi_input_rejected）+ `test_demo_bronze_to_silver_e2e` 集成。multi-input 拒绝是 v2 修订显式约束（MVP single-input），有专测；cycle / unknown 都走 `pytest.raises(ValueError, match=...)`。 | OK |
| AC-7 | `test_lineage_written_on_cache_miss` | reviewer Read（行 401-454）：字段级 4 项断言（`lj["produced_by"]["kind"] == "processor"` / `name == "markdown-normalize"` / `inputs[0]["commit"] == src_commit` / `run_id == str(run_id)`）—— **直接对应 spec v2 AC-7 的字段级要求 + 闭 v1 review SHOULD #5**。 | OK |
| AC-8 | 3 个 cache_hit 测试 | (a) `skips_processor` 用 spy 验 `call_count == 0`；(b) `updates_ref` 查 `refs.commit_hash == src_commit`；(c) `writes_audit_fields` 验 `cache_hit is True` + `input_commits_json == [src_commit]` + `cache_key == cache_key`。**三断言齐全，对应 v2 AC-8 (a)/(b)/(c) 三条**。 | OK |
| AC-9 | self_check OpenAPI | spec v2 验收命令已含 `'/pipelines/runs' in paths`；coding_report v2 AC-9 PASS；e2e 间接走 `app.openapi()`。 | OK |
| AC-10 | self_check `_TASK_DISPATCH` + `run_pipeline_job` | 同上，self_check 路径已验。 | OK |
| AC-11 | self_check grep + `test_pipeline_e2e.py` parse | reviewer Read e2e 行 292-296：`load_recipe(demo_yaml)` + `assert demo_recipe.name == "demo-bronze-to-silver"` + `processor == "markdown-normalize@0.1"`——**显式 parse 而非仅 grep**。 | OK |
| AC-12 | pytest collect-only ≥ 12 + ruff + mypy | reviewer 实跑 `grep -c "^def test_\|^async def test_" 6 文件` → 7+6+6+2+10+1 = **32 用例**，远超阈值 12；test_report 本地输出含 `ruff All checks passed!` + `mypy Success`。 | OK |
| AC-13 | self_check 自递归 | coding_report v2 + test_report 均声明 PASS 11 / FAIL 2（AC-7/AC-8 集成本地 SKIPIF 环境问题，CI PASS）。 | OK（含环境偏离声明，见 §5） |
| stage 4 v2 SHOULD #1 cache_key NULL 兜底 | `test_node_value_error_marks_failed_with_null_audit` | reviewer Read（行 575-634）：故意用 `bronze/{owner}/{src}@ghost` 触发 `_run_node` 内 ValueError（在写 node_run 之前）→ orchestrator 走 fallback 写 `input_commits_json=None, cache_key=None`；测试断言 5 字段（`status=='failed'` / `cache_hit is False` / `cache_key is None` / `input_commits_json is None` / `error is not None and len(err) <= 500`）。**完整且精确**——直接对应 `orchestrator.py:166-172` fallback INSERT 分支。 | OK |
| stage 4 v2 MUST #2 HTTPException 500 截断 | `test_node_400_marks_failed` | reviewer Read（行 637-692）：构造 `big_detail = {"detail": "...", "available": [f"p{i}@v" for i in range(200)]}`（str(detail) 实测远超 500 char）；monkeypatch `ProcessorRunner.run` 抛 `HTTPException(400, detail=big_detail)`；断言 `run.error is not None` + `len(run.error) <= 600`。**确实触发 `orchestrator.py:144` HTTPException 分支的 `str(...detail...)[:500]` 截断路径**。 | OK（含 SHOULD #1：node_run 行的 `error` 字段未独立断言） |

**13 AC + 2 stage 4 反哺项全部有归宿，无 AC 测试缺失**。

## 3. 测试函数质量评估

### A. 命名 / 断言实质性
- 全 32 用例命名形如 `test_<对象>_<场景>_<期望>`，无 `test_1` / `test_ok` 反模式。
- 断言以**具体字段值**为主（`commit_hash == src_commit` / `lineage_json["produced_by"]["name"] == "markdown-normalize"`），未发现 `assert response == {...}` 整对象断言。
- DAG / cache / schema 单元测试用 `pytest.raises(... match="cycle")` 既验异常类型又验消息，比 `pytest.raises(ValueError)` 强。

### B. 真实数据访问层验证
- 集成测试通过 `MinioBlobStore` 真实 boto3 client + 真实 PostgreSQL（`create_async_engine` + `async_sessionmaker`）+ HTTP `ASGITransport(app)` 走 `/auth/login` + `/repos` + `/blobs` + `/commits` 真路径 seed bronze；**不 mock RepositoryService / CommitService / BlobStore / RefService / CacheService**——test_report 声明属实。
- 唯一 mock 点：(1) `_override_blob_store` fixture 切换 bucket 名（环境隔离不是 mock 数据层）；(2) cache_hit 测试 `monkeypatch` `ProcessorRunner.run` spy（call_count 验证必要，不替换数据访问）；(3) `test_node_400_marks_failed` mock `ProcessorRunner.run` 抛特定异常——**对应 unit-test-write SKILL "处理 LLM 调用" / 异常路径模式**，合规。

### C. fixture cleanup
- 每个 owner/src/tgt 都在 finally 走 `_delete_repo_cascade`（DELETE refs → pipeline_cache → commits → trees → repositories）+ `_delete_user`。
- `_override_blob_store` finally 调 `delete_object` + `delete_bucket` + `dependency_overrides.pop`。
- 测试间无共享 owner/repo 名（hex[:4] 随机），无 leaked global 状态。

### D. stage 5 新增 2 用例
- **`test_node_value_error_marks_failed_with_null_audit`**：精确覆盖 stage 4 v2 SHOULD #1（cache_key=NULL 路径）。reviewer 核对 `orchestrator.py:155 if latest is None` 分支 → 触发 `parse_processor_ref` fallback INSERT with `input_commits_json=None, cache_key=None` —— 测试断言 5 字段（status / cache_hit / cache_key=None / input_commits_json=None / error≤500）**严格且最小化**，无冗余字段。**对应 stage 4 v2 reviewer §CC 显式要求 stage 5 补**——闭环。
- **`test_node_400_marks_failed`**：覆盖 stage 4 v2 MUST #2（HTTPException [:500] 截断）。big_detail 构造 200 个 `"p{i}@v"` 元素（str 实长 ~2700 char），monkeypatch 抛 HTTPException(400, detail=big_detail)；run.error ≤ 600 间接验 node error ≤ 500。**对路径正确**，但见 SHOULD #1（仅断 run.error，未独立断 node_run.error 字段）。

### E. e2e 测试
- `test_demo_bronze_to_silver_e2e`：先 `load_recipe(demo_yaml)` 校验 yaml 可解析（间接覆 AC-11）；再动态生成 owner/repo 跑实集成路径；断言 silver ref + commit + lineage_json 三件套（`new_commit_hash != src_commit` 验真新 commit）。
- 与 `test_lineage_written_on_cache_miss` 在 lineage 字段上**部分重叠**（都验 produced_by/inputs/run_id）；但 e2e 多了 (a) 从 yaml 文件加载验解析 + (b) `new_commit_hash != src_commit` 区分新 commit 与 cache hit，**新增价值充分**，非"为 e2e 而 e2e"。

## 4. mock 范围合规复核（grep）

```
$ grep -nE "(Magic|Async)Mock|patch\(" apps/api/tests/test_pipeline_*.py apps/api/tests/test_processor_runner_backcompat.py
(empty)

$ grep -n "monkeypatch" apps/api/tests/test_pipeline_*.py
test_pipeline_e2e.py:61: monkeypatch（_override_blob_store fixture——bucket 名隔离）
test_pipeline_orchestrator.py:220: monkeypatch（同上）
test_pipeline_orchestrator.py:492-518: monkeypatch ProcessorRunner.run（spy + run-through，验 call_count）
test_pipeline_orchestrator.py:666-689: monkeypatch ProcessorRunner.run（抛 HTTPException，模拟错误路径）
```

无 `MagicMock` / `AsyncMock` / `unittest.mock.patch`；monkeypatch 用法**全部合规**。**unit-test-write SKILL §"质量门禁"：「没有 mock 数据访问层」满足**。

## 5. 集成测试 SKIPIF 本机失效定夺

### 现状
- `test_pipeline_orchestrator.py:138-141` + `test_pipeline_e2e.py:54-57` 的 skipif 表达式：`not (_db_url() and _minio_endpoint() and _redis_reachable())`。
  - `_db_url()` / `_minio_endpoint()`：仅检 **env var 存在**（`os.environ.get` 非空），不验真连通；
  - `_redis_reachable()`：真 `Redis.ping()`；
  - **无 MinIO 真探针**（test_report 提到 `_minio_reachable` 是项目级旧文件别处的探针，**本 change 的测试文件根本没有这个 helper**）。
- 后果：本机有 env var 但凭证错时（用户场景），skipif 不 skip → 进入测试体 → `_override_blob_store` 内 `MinioBlobStore._ensure_bucket_sync` 抛 ClientError(403) → 测试 ERROR 而非 SKIP。
- test_report 声明"_minio_reachable 探针只测 TCP socket"——但本 change 的两个测试文件**并未使用** TCP 探针，连这个保护都没有。

### 定夺
- 这是**项目级既有问题**（旧文件 `test_processor.py` / `test_llm.py` / `test_jobs.py` 同模式），CI 环境（`DATAPLAT_MINIO_PORT=9100` + `dataplat-secret`）下 skipif 表达式可达成且测试通过——test_report 声明"CI 同模板 PASS"是项目历史共识。
- **不阻塞本 change verdict**：(1) 同 stage 4 v2 reviewer §"偏离 3" 接受路径；(2) CI 是机械化判据的真实裁判，本机环境差异不应转为本 change 的 MUST FIX；(3) follow-up `test-env-bootstrap-*`（test_report 已声明）是正确的承接点。
- **SHOULD FIX（不阻塞本 change，归属 follow-up）**：见 §7 SHOULD #2——本 change 测试文件应至少**加一个最小 `_minio_reachable()` head_bucket 探针**或在 `_override_blob_store` 入口 try/except `_ensure_bucket_sync` 抛 ClientError 时 `pytest.skip(...)`，可避免本机 ERROR 噪声。但本 change 的范围是 pipeline 而非测试 infra，归 follow-up 合理。

## 6. 覆盖率手工估算评估

test_report §"覆盖率" 列各模块 ≥60% 估算（reviewer 复核）：

| 模块 | test_report 估算 | reviewer 复核 | 评估 |
|---|---|---|---|
| `runner/dag.py` | ~95% | 6 测试 / 2 公开函数（topo_sort + build_node_deps）→ 覆盖 happy + 4 error + 多入度合并 | 合理 |
| `runner/cache.py` | ~90% | 6 测试 / 2 公开（compute_cache_key + _canonical_config_hash）→ 覆盖确定性/顺序/防 regress/类型敏感 | 合理 |
| `schemas/pipeline.py` | ~85% | 7 测试 + 1 e2e load_recipe → 覆盖 valid/missing/3 个 invalid ref/双入口 loader | **可能略高估**——`parse_input_ref` / `parse_processor_ref` 是否独立测过未明示；e2e 间接调；接受为 NICE 而非 SHOULD |
| `runner/orchestrator.py` | ~80% | 4 单元 + 6 集成 → cache miss/hit/error 三分支齐备 | 合理（含 NULL 兜底 + HTTPException 截断双新增） |
| `routers/pipelines.py` | ~70% | e2e 间接走 POST/GET；POST yaml-body 入口未独立测 | **偏乐观但 ≥60% 阈值仍满足**；见 NICE #1 |
| `services/ref.py::upsert_ref` | ~85% | `test_cache_hit_updates_ref` + e2e 间接 | 合理（upsert_ref 单一入口已被 cache-hit 路径触发） |

**核心模块全部 ≥60% 估算成立**——满足 unit-test-write SKILL 阈值。覆盖率工具未配置 → 本 change 不阻塞（follow-up `backend-coverage-tooling-*` 已声明）。

## 7. 问题列表

### MUST FIX
（空）

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | `test_pipeline_orchestrator.py::test_node_400_marks_failed` (行 681-687) | 仅断言 `run.error` ≤ 600；未独立查询 `pipeline_node_runs` 行的 `error` 字段验 ≤ 500。stage 4 v2 MUST #2 的契约是 **node 级 error 字段** ≤ 500，run.error 是 wrap（`f"node 'n1' failed: {error}"`），≤ 600 是间接验证 | 加一段 `SELECT error FROM pipeline_node_runs WHERE run_id=:r` 然后 `assert len(node_error) <= 500`；同时可加 `assert len(node_error) == 500`（big_detail 实长 > 500，截断必命中边界）以验真截断 |
| 2 | `test_pipeline_orchestrator.py:138-141` + `test_pipeline_e2e.py:54-57` | skipif 仅 env var 存在性检查 + Redis ping，无 MinIO `head_bucket` 真探针；凭证错时本机走入测试体而非 SKIP，与 test_report 声明的"_minio_reachable 探针"不一致 | 本 change 不强制（归 follow-up `test-env-bootstrap-*`）；可考虑在 `_override_blob_store` fixture 内 try/except `ClientError` 时 `pytest.skip(...)` 兜底——3 行改动；本 change 选择不阻塞 |
| 3 | `test_pipeline_orchestrator.py::test_node_value_error_marks_failed_with_null_audit` (行 631) | `assert len(err) <= 500` 仅验上界；ValueError 消息（`f"input ref ... ghost"`）实际 << 500，无法验 500 char 截断边界真触发 | 接受为弱断言（NULL 兜底路径 error 消息天然短）；若想加强可与 #1 合并：用 monkeypatch 让 `_run_node` 抛长 ValueError 验截断；本 change 不阻塞 |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | `routers/pipelines.py` YAML body 入口 (`POST /pipelines/runs` `recipe_yaml` 路径) | test_report 估算 ~70%；e2e 用 Python Recipe 对象直接调 orchestrator（绕过路由），YAML 入口路径未独立测 | follow-up 加 `test_post_pipeline_runs_yaml_body_invalid_yaml_422` + `..._valid_yaml_returns_run_id` 两条 |
| 2 | `test_pipeline_schemas.py` | `parse_input_ref` / `parse_processor_ref` helper 未单独测；仅通过 `RecipeNode.field_validator` 间接测 | 可加 `test_parse_input_ref_layer_kind` / `test_parse_processor_ref_split_at` 各 2-3 条；非阻塞 |
| 3 | `test_pipeline_cache.py` | 缺 `compute_cache_key(inputs=[], ...)`（空 inputs 行为）测试 | 非阻塞；spec 已 Pydantic 拒空 inputs，cache 函数本身行为对 v1 不重要 |
| 4 | 集成测试 6 用例 | 每条都创建 `engine + factory`（4-5 次/测试），重复 boilerplate | 可重构为 conftest fixture `db_session` / `db_engine`；与既有 `apps/api/tests/conftest.py` 简陋程度一致，**跨改动重构**而非本 change |
| 5 | `test_pipeline_e2e.py:286-296` | 注释说"AC-11 间接覆盖"但实际 e2e 不用 yaml 文件中的 `bronze/demo/raw-md@main`（绕开占位）。逻辑正确但与 AC-11"用 demo recipe 跑通"的字面期望略弱 | 加注释或在 AC-11 spec 段澄清"demo recipe parse-only" 验证；非阻塞 |

## 8. Verdict

**APPROVED**

理由：
- 13 AC + 2 stage 4 反哺项**全部有测试或 self_check 覆盖**，无 AC 缺失（§2）。
- 32 用例（21 单元 + 11 集成）远超 AC-12 阈值 12；无空跑断言；无数据访问层 mock；命名 / 断言 / fixture cleanup 均合规（§3 / §4）。
- stage 5 新增 2 用例（`null_audit` + `400_marks_failed`）**精确覆盖 stage 4 v2 SHOULD #1 + MUST #2 的反哺要求**，路径选择正确（§3.D）。
- e2e 测试新增价值充分（yaml load + 真新 commit 区分 cache hit）（§3.E）。
- 集成测试 SKIPIF 本机失效是**项目级既有问题**，CI 环境下达成；follow-up 已声明；接受为偏离不阻塞（§5）。
- 覆盖率手工估算核心模块全部 ≥60%（§6）。
- 3 SHOULD FIX 全部不阻塞（#1 是断言强化建议；#2 跨 change；#3 是弱断言但不影响测试通过）；5 NICE TO HAVE 全部非阻塞。

**MUST FIX = 0 → APPROVED**。

## 9. 复检指引（如需开 v2 测试可参考）

如果作者希望强化 SHOULD #1（推荐）：
1. 在 `test_node_400_marks_failed` 内 `run = await _run_orchestrator(...)` 之后追加：
   ```python
   async with factory() as session:
       row = (await session.execute(
           text("SELECT error FROM pipeline_node_runs WHERE run_id=:r"),
           {"r": run_id},  # 注：当前 fixture 用 _new_run_id() 未保存到外层；需重构
       )).first()
       assert row is not None
       assert len(row[0]) <= 500
   ```
   （重构提示：把 `_new_run_id()` 提取到测试函数局部 `run_id = _new_run_id()` 然后传入。）
2. 实跑 `cd apps/api && uv run pytest tests/test_pipeline_orchestrator.py::test_node_400_marks_failed -q`（CI 环境）。
3. 重新跑 `bash scripts/_self_check.sh pipeline-orchestrator-mvp` 确认 11 PASS + 2 环境 FAIL 模式不变。

## 10. 后续指引

- 本 verdict = APPROVED → stage 5 closeout：更新 `summary.md` stage=unit_test status=closed + 引用本 review 路径。
- 进入 stage 7 push：commit 含本 review 文件 + 32 测试 + test_report。
- stage 8 CI：核心机械化判据是 CI 同模板下 `pytest -q apps/api/tests/test_pipeline_*.py apps/api/tests/test_processor_runner_backcompat.py` 全 PASS（含集成 7 条）+ ruff + mypy 退码 0。
- follow-up 候选（test_report + 本 review 衍生）：
  - `test-env-bootstrap-*`：补 `_minio_reachable` head_bucket 探针 + docker-compose.test.yml 凭证模板
  - `backend-coverage-tooling-*`：引入 coverage.py + CI 阈值
  - `pipeline-yaml-body-route-tests-*`：补 POST /pipelines/runs YAML 入口测试
  - `pipeline-auto-ref-semantics-*`（继承自 stage 4 v2 SHOULD #5）：澄清 `@auto` → "main" hardcode
