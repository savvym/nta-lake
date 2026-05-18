---
change_id: pipeline-orchestrator-mvp-20260518
version: 2
authored_at: 2026-05-18T06:01:20Z
revised_at: 2026-05-18T06:35:00Z
prior_review: request_analysis/review/tasks_review_v1.md
---

# Tasks v2

> v2 修订要点（闭 tasks_review_v1.md 2 MUST FIX + 多 SHOULD FIX）：
>
> - MUST #1（config_hash 来源错误）：T-4 暴露 `_canonical_config_hash(config: dict) -> str` helper；T-5 拆分后的 T-5c 显式引用 helper，禁止用 `compute_cache_key` 返回值当 config_hash
> - MUST #2（demo recipe 首节点是 raw-upload Adapter）：T-8 改为 fixture 预 seed bronze；demo recipe 节点全为 Processor；AC-11 grep 删 raw-upload
> - SHOULD #1（粒度过粗）：T-5 拆为 T-5a~T-5e；T-7 拆为 T-7a~T-7c
> - SHOULD #2（ORM 字段缺）：T-2 加 `input_commits_json JSONB` + `cache_key str(64)` 两字段；migration 0004 同步加
> - SHOULD #3（R-1 引用 test_processor_runner_smoke 未列）：T-7a 显式列入 `tests/test_processor_runner_backcompat.py`
> - SHOULD #4（schema 校验滞后）：T-1 加 RecipeNode field_validator；T-7a 加 invalid_input_ref 用例
> - SHOULD #5（异常类型未细化）：T-5e 细化 catch (HTTPException, Exception) 双路；T-7b 加 test_node_400_marks_failed
> - SHOULD #6（POST body 类型丑）：T-6a/T-6b 双入口拆分

## T-0 抽 `RefService.upsert_ref` helper（v2 SHOULD #1 闭环）

- 修改 `apps/api/dataplat_api/services/ref.py`：加 `@staticmethod async def upsert_ref(session, repo_id: uuid.UUID, name: str, commit_hash: str) -> RefORM`，逻辑同 `services/commit.py:192-209` 内联块
- 修改 `apps/api/dataplat_api/services/commit.py:192-209`：把内联 ref upsert 改为 `await RefService.upsert_ref(session, repo_id, payload.ref, commit_hash)`
- 不破坏既有 commit-api / repo-files-tab 测试（这两 change 已 closed）
- depends_on: 无 / estimated_stage: stage-3 / AC: 支撑 AC-8

## T-1 Recipe Pydantic schema + 字段级 validator + YAML/JSON loader

- 新建 `apps/api/dataplat_api/schemas/pipeline.py`：
  - `RecipeNode`：`id: str` / `processor: str`（形如 `name@version`） / `inputs: list[str]` / `config: dict[str, Any] = {}` / `output: str`；`extra="forbid"`
  - **v2 加**：`@field_validator("inputs", mode="after")`：每元素必须 `parse_input_ref(s)` 成功；非 `@<node-id>` / `<layer>/<owner>/<name>@<ref>` 形态 → raise ValueError → Pydantic 422
  - **v2 加**：`@field_validator("output")` / `@field_validator("processor")` 同上
  - `Recipe`：`name: str` / `nodes: list[RecipeNode]`；`extra="forbid"`
  - `load_recipe(data: str | dict) -> Recipe`：YAML 文本走 `yaml.safe_load` → Recipe.model_validate；dict 直接 model_validate
  - 模块级辅助：`parse_input_ref(ref: str) -> tuple[Literal["node","repo"], ...]`、`parse_output_ref(ref: str)`、`parse_processor_ref(ref: str) -> tuple[str, str]`
- depends_on: 无 / estimated_stage: stage-3 / AC: AC-1

## T-2 models/pipeline.py 3 ORM + Alembic 0004 migration（v2 加字段）

- 新建 `apps/api/dataplat_api/models/pipeline.py`：
  - `PipelineRunORM(id UUID PK, recipe_name str, recipe_json JSONB, status str(queued|running|succeeded|failed), error str|null, created_by str, started_at TZ, completed_at TZ|null)`
  - `PipelineNodeRunORM(id UUID PK, run_id UUID FK→pipeline_runs.id ON DELETE CASCADE, node_id str, processor_name str, processor_version str, config_json JSONB, status str, cache_hit bool default false, output_commit_hash str(64)|null, error str|null, started_at TZ|null, completed_at TZ|null, input_commits_json JSONB NOT NULL, cache_key str(64) NOT NULL)`
    - **v2 加**：`input_commits_json` + `cache_key` 两字段 NOT NULL；cache hit 也必写
  - `PipelineCacheORM(cache_key str(64) PK, output_commit_hash str(64) FK→commits.hash, created_at TZ default now)`
- 更新 `apps/api/dataplat_api/models/__init__.py` 导出 3 个新 ORM
- 新建 `apps/api/alembic/versions/0004_pipeline_orchestrator.py`：down_revision = 0003；upgrade 建 3 张表 + 索引（`pipeline_node_runs.run_id` idx、`pipeline_node_runs.cache_key` idx）；downgrade 反向 drop
- depends_on: 无 / estimated_stage: stage-3 / AC: AC-4, AC-8

## T-3 runner/dag.py 拓扑排序 + 环检测

- 新建 `apps/api/dataplat_api/runner/dag.py`：
  - `topo_sort(nodes: list[dict]) -> list[str]`：输入 `[{"id": str, "deps": list[str]}]`；Kahn 算法；剩余入度非零 → `raise ValueError(f"cycle detected involving: {remaining}")`
  - 公开 `build_node_deps(recipe: Recipe) -> list[dict]`：把 `RecipeNode.inputs` 中 `@<node-id>` 形式抽出为 deps；`repo@version` 不入 deps；调用 `schemas.pipeline.parse_input_ref` 复用解析逻辑
  - 无副作用，纯函数
- depends_on: T-1 / estimated_stage: stage-3 / AC: AC-2

## T-4 runner/cache.py cache_key 函数 + canonical_config_hash helper（v2）

- 新建 `apps/api/dataplat_api/runner/cache.py`：
  - `_canonical_json(obj) -> bytes`：`json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()`
  - **v2 加**：`_canonical_config_hash(config: dict) -> str`：`sha256(_canonical_json(config)).hexdigest()`；公开（_前缀按约定可被 cache.py 外部 import）；**T-5c 必须调用此 helper 构造 `lineage.produced_by.config_hash`**，禁止直接用 cache_key
  - `compute_cache_key(inputs_commits: list[str], processor_name: str, processor_version: str, config: dict) -> str`：对 `{"inputs": sorted(inputs_commits), "processor": f"{processor_name}@{processor_version}", "config": config}` 做 canonical JSON + sha256 hex
  - `CacheService.lookup(session, cache_key) -> str | None`、`CacheService.insert(session, cache_key, output_commit_hash)`
- depends_on: 无 / estimated_stage: stage-3 / AC: AC-3, AC-7

## T-5a ProcessorRunner 扩 lineage 参数（向后兼容）

- 修改 `apps/api/dataplat_api/runner/processor_runner.py`：
  - `run` 签名末尾追加 `lineage: Lineage | None = None`
  - 把 `CommitCreate(..., lineage=None, ...)` 改为 `CommitCreate(..., lineage=lineage, ...)`
- 兼容性：默认 None → 既有 /process router 调用不破
- depends_on: 无 / estimated_stage: stage-3 / AC: AC-5

## T-5b PipelineOrchestrator 入口校验（schema/topo/registry 预检）

- 新建 `apps/api/dataplat_api/runner/orchestrator.py`：
  - `PipelineOrchestrator.run_pipeline(session, store, recipe: Recipe, author_id: str, run_id: uuid.UUID) -> PipelineRunORM`
  - 步骤 1：`topo_sort(build_node_deps(recipe))` → ValueError 转 caller 422
  - 步骤 2：每节点 `ProcessorRegistry.get(name, version)` 预检 → 缺失抛 ValueError（caller 转 422）
  - 步骤 3：INSERT `PipelineRunORM(status=running, started_at=now)`
- depends_on: T-1, T-2, T-3 / estimated_stage: stage-3 / AC: AC-6

## T-5c PipelineOrchestrator cache miss 分支（含 lineage 构造）

- 在 T-5b 基础上加：
  - 解析当前节点 `inputs`：`@<node-id>` 取上游 node_run.output_commit_hash；`<layer>/<owner>/<name>@<ref>` 走 `RepoService` + `RefService` 解析 commit hash
  - 计算 `cache_key = compute_cache_key(inputs_commits, processor.name, processor.version, node.config)`
  - `CacheService.lookup` → None：
    - **构造 Lineage**：`Lineage(produced_by=ProducedBy(kind="processor", name=processor.name, version=processor.version, config_hash=_canonical_config_hash(node.config)), inputs=[InputRef(repo=<resolved repo qualified id>, commit=<hash>) for ...], run_id=str(run_id), env={})`
      - **v2 修订**：`config_hash` 来源 `_canonical_config_hash(node.config)`（T-4 helper），**不**用 cache_key
      - `env={}`（v2 修订）：deferred；follow-up `lineage-env-field-*` 补
    - 调 `ProcessorRunner.run(..., lineage=lineage, ref=<target ref>)` 拿 `(commit, dedup, result)`
    - `CacheService.insert(cache_key, commit.hash)`
    - INSERT `PipelineNodeRunORM(cache_hit=false, output_commit_hash=commit.hash, status=succeeded, input_commits_json=sorted(inputs_commits), cache_key=cache_key)`
- depends_on: T-4, T-5a, T-5b / estimated_stage: stage-3 / AC: AC-7

## T-5d PipelineOrchestrator cache hit 分支（含 ref 更新）

- 在 T-5b 基础上加（与 T-5c 平行）：
  - `CacheService.lookup(cache_key) → hit_commit_hash`：
    - **不**调 ProcessorRunner
    - **MUST 更新 target_repo 的 output ref**：调 `RefService.upsert_ref(session, target_repo_id, output_ref_name, hit_commit_hash)`（沿用既有 ref upsert 逻辑）
    - INSERT `PipelineNodeRunORM(cache_hit=true, output_commit_hash=hit_commit_hash, status=succeeded, input_commits_json=sorted(inputs_commits), cache_key=cache_key)`
  - 测试断言 `ProcessorRunner.run` mock 的 `call_count == 0` 在 T-7b
- depends_on: T-2, T-4, T-5b / estimated_stage: stage-3 / AC: AC-8

## T-5e PipelineOrchestrator error / failed 分支

- 在 T-5b 基础上加：
  - 节点执行抛异常 → `catch (HTTPException, Exception)` 双路：
    - HTTPException → `error = str(getattr(exc, "detail", exc))`
    - 其他 → `error = repr(exc)[:500]`
  - INSERT `PipelineNodeRunORM(status=failed, error=..., input_commits_json=...|null, cache_key=...|null)`；UPDATE `PipelineRunORM(status=failed, completed_at=now, error=...)`；break loop
  - 全部节点 succeeded → UPDATE `PipelineRunORM(status=succeeded, completed_at=now)`
- depends_on: T-5b, T-5c, T-5d / estimated_stage: stage-3 / AC: AC-6

## T-6a routers/pipelines.py POST/GET 路由 (JSON 入口) + main include

- 新建 `apps/api/dataplat_api/routers/pipelines.py`：
  - `POST /pipelines/runs`：body Pydantic `RecipeCreateRequest{recipe: Recipe}`；admin only；schema 校验 + topo + processor 预检 → 422 on error；INSERT `PipelineRunORM(status=queued)` + enqueue → 返 202 + `{run_id}`
  - `GET /pipelines/runs/{run_id}`：返 `PipelineRunResponse{run, node_runs[]}`（含每节点 cache_hit / output_commit_hash / input_commits_json / cache_key / status）
- 修改 `apps/api/dataplat_api/main.py`：include pipelines_router
- depends_on: T-2, T-5b / estimated_stage: stage-3 / AC: AC-9

## T-6b routers/pipelines.py YAML 入口（v2 SHOULD #6）

- 在 T-6a 基础上加：`POST /pipelines/runs:from-yaml`（admin）；body `text/yaml` 文本；内部 `load_recipe(body) → Recipe`；其余同 T-6a
- depends_on: T-6a / estimated_stage: stage-3 / AC: AC-9

## T-6c jobs dispatch + run_pipeline_job worker 入口

- 修改 `apps/api/dataplat_api/jobs/service.py`：`_TASK_DISPATCH` 加 `"pipeline": "dataplat_api.jobs.tasks.run_pipeline_job"`
- 修改 `apps/api/dataplat_api/jobs/tasks.py`：新增 `run_pipeline_job(job_id: str)` sync-RQ 入口（沿 `run_process_job` 模式）：从 jobs 表读 payload → 取 run_id + recipe_json → asyncio.run + 独立 async engine + `PipelineOrchestrator.run_pipeline` + swallow exception → `mark_failed`
- depends_on: T-5e, T-6a / estimated_stage: stage-3 / AC: AC-10

## T-7a 单元测试（schema / dag / cache / backcompat）

- `tests/test_pipeline_schemas.py`（≥ 4 用例）：
  - valid_recipe / missing_required_field / invalid_input_ref_raises_validation_error / invalid_output_ref_raises_validation_error
- `tests/test_pipeline_dag.py`（≥ 3）：linear / branching_merge / cycle_raises_valueerror
- `tests/test_pipeline_cache.py`（≥ 4）：determinism / inputs_order_independence / config_canonicalization / canonical_config_hash_neq_cache_key（v2 防 regress）
- `tests/test_processor_runner_backcompat.py`（≥ 1，v2 SHOULD #3）：test_processor_runner_smoke 验既有 POST /process 调用路径在 ProcessorRunner 加 lineage 参数后回归不破
- depends_on: T-1, T-3, T-4, T-5a / estimated_stage: stage-3 / AC: AC-1, AC-2, AC-3, AC-5

## T-7b orchestrator 分支测试

- `tests/test_pipeline_orchestrator.py`（≥ 7 用例）：
  - test_lineage_written_on_cache_miss（字段级 assert：produced_by.kind/name、inputs[0].commit、run_id）
  - test_cache_hit_skips_processor（mock ProcessorRunner.run, assert call_count == 0）
  - test_cache_hit_updates_ref（cache hit 后 target_repo.ref 指向 cached commit）
  - test_cache_hit_writes_audit_fields（PipelineNodeRunORM.input_commits_json / cache_key 非空）
  - test_unknown_processor（POST 阶段返 422）
  - test_cycle（POST 阶段返 422）
  - test_unknown_node_ref（POST 阶段返 422）
  - test_node_400_marks_failed（节点抛 HTTPException(400) → node_run.status=failed, error 含 detail）
  - test_node_unknown_error_marks_failed（节点抛 ValueError → node_run.status=failed, error 含 repr）
  - test_parent_chain（cache miss 链 commit2.parents == [commit1]）
- depends_on: T-5c, T-5d, T-5e, T-6c / estimated_stage: stage-3 / AC: AC-6, AC-7, AC-8

## T-7c e2e 测试（demo recipe 跑通）

- `tests/test_pipeline_e2e.py`（≥ 1）：
  - test_demo_bronze_to_silver_e2e：fixture 预 seed bronze（用 raw-upload Adapter 单独 POST /ingest 产 bronze commit；不在 recipe 节点里）→ 走 POST /pipelines/runs:from-yaml 提交 demo-bronze-to-silver.yaml → 轮询直到 succeeded → 验 silver repo 的 ref 指向 commit；commit.lineage_json 字段断言
  - 用 monkeypatch 替换 LLM gateway（如使用 demo-bronze-to-gold.yaml 走过 llm-qa-gen 节点）
- depends_on: T-7b, T-8 / estimated_stage: stage-3 / AC: AC-12

## T-8 demo recipes（v2 修订）+ codegen + ruff + mypy + self_check 段

- 新建 `recipes/examples/demo-bronze-to-silver.yaml`：单节点 `markdown-normalize@0.1`，inputs `bronze/<owner>/<name>@main`（**节点不含 raw-upload**；bronze 由 e2e fixture 预 seed）；output `silver/<owner>/normalized-text@auto`
- 新建 `recipes/examples/demo-bronze-to-gold.yaml`：两节点链 `markdown-normalize → llm-qa-gen`；inputs 首节点引 bronze ref，第二节点 `@<node-id>` 链上；output 末节点 `gold/<owner>/sft@auto`
- `make codegen`：同步 `packages/api-types/openapi.json` + `generated.ts`
- `uv run ruff check apps/api packages/core worker/src` 全 PASS
- `uv run mypy apps/api/dataplat_api packages/core/src worker/src` 全 PASS
- 修改 `scripts/_self_check.sh`：追加 `run_pipeline_orchestrator_mvp` 段（13 AC + filter + 接入总入口）
- depends_on: T-1, T-2, T-3, T-4, T-5a, T-5b, T-5c, T-5d, T-5e, T-6a, T-6b, T-6c, T-7a, T-7b / estimated_stage: stage-3 / AC: AC-11, AC-12, AC-13

## process_tasks

## T-9 stage-2 spec/tasks review

- spawn 独立 reviewer agent；reviewer 字段 `claude-agent:pipeline-orchestrator-mvp-20260518-stage2-reviewer-v{N}`（v1 已完成，v2 复检即将提交）
- depends_on: 当前 spec/tasks 版本完
- estimated_stage: stage-2

## T-10 stage-4 coding review

- spawn 独立 reviewer agent；reviewer 字段 `claude-agent:pipeline-orchestrator-mvp-20260518-stage4-reviewer-v1`
- depends_on: T-1~T-8 全 done
- estimated_stage: stage-4

## T-11 stage-5/6 test_report + unit-test review

- 产出 `unit_test/test_report_v1.md`；spawn 独立 reviewer agent；reviewer 字段 `claude-agent:pipeline-orchestrator-mvp-20260518-stage6-reviewer-v1`
- depends_on: T-7a, T-7b, T-7c
- estimated_stage: stage-6

## T-12 stage-7 CI

- 本地 `bash scripts/_self_check.sh` 全 PASS；push 分支 → GitHub Actions ci.yml 通过；产出 `ci_result/ci_result_v1.md`
- depends_on: T-8, T-11
- estimated_stage: stage-7

## T-13 stage-9 deploy verify

- 重启 API + worker；跑 demo-bronze-to-silver.yaml 端到端；产 `deployment/deploy_verify_v1.md`
- depends_on: T-12
- estimated_stage: stage-9

## T-14 stage-10 close + 反哺 SKILL（如有）

- 更新 summary.md status=done + close 元数据；反哺流程坑到 `.harness/skills/`
- depends_on: T-12, T-13
- estimated_stage: stage-10

## 任务依赖图

```
实现层（stage-3）：

T-1 (schema+validator) ─┐
T-2 (model+migration) ──┼─→ T-5b (orchestrator 入口校验) ─┐
T-3 (dag) ──────────────┘                                  │
                                                           │
T-4 (cache + canonical_config_hash) ─→ T-5c (cache miss) ──┤
                                       T-5d (cache hit)  ──┤
T-5a (ProcessorRunner sig + lineage) ─────────────────────→ T-5c
                                                           │
                            T-5e (error 分支) ←── T-5c+T-5d ┤
                                                           │
                            T-6a (POST/GET JSON) ←─ T-5b ───┘
                            T-6b (YAML 入口)  ←─ T-6a
                            T-6c (jobs dispatch) ←─ T-5e, T-6a
                                                           │
                            T-7a (单元 + backcompat) ←─ T-1,T-3,T-4,T-5a
                            T-7b (orchestrator branch) ←─ T-5c,T-5d,T-5e,T-6c
                            T-7c (e2e) ←─ T-7b, T-8
                                                           │
                            T-8 (demo recipe + codegen + self_check) ←─ 全部
                            
流程层（stage-2/4/6/7/9/10）：

T-9 (stage-2 v2 review) ←── 当前 spec/tasks v2
T-10 (stage-4 review) ←── T-8 全 done
T-11 (stage-6 review) ←── T-7a/b/c
T-12 (stage-7 CI) ←── T-8, T-11
T-13 (stage-9 deploy) ←── T-12
T-14 (stage-10 close) ←── T-12, T-13
```

## AC 覆盖矩阵

| AC | 关联任务 |
|---|---|
| AC-1 | T-1, T-7a |
| AC-2 | T-3, T-7a |
| AC-3 | T-4, T-7a |
| AC-4 | T-2 |
| AC-5 | T-5a, T-7a |
| AC-6 | T-5b, T-5e, T-7b |
| AC-7 | T-4, T-5c, T-7b |
| AC-8 | T-2, T-5d, T-7b |
| AC-9 | T-6a, T-6b |
| AC-10 | T-6c |
| AC-11 | T-8 |
| AC-12 | T-7a, T-7b, T-7c, T-8 |
| AC-13 | T-8 |

13 AC × ≥1 非 process_tasks 任务覆盖 ✓
