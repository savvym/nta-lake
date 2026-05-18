---
change_id: pipeline-orchestrator-mvp-20260518
version: 2
authored_at: 2026-05-18T06:01:20Z
revised_at: 2026-05-18T06:30:00Z
status: draft
prior_review: request_analysis/review/spec_review_v1.md
---

# Spec：Pipeline 编排引擎 MVP — Recipe + DAG + cache_key + REST + 端到端 demo

> **v2 修订说明**（闭 spec_review_v1.md 的 3 个 MUST FIX + 高价值 SHOULD）：
>
> - MUST #1：在 §问题陈述、AC-8、R-6 显式 cache hit 时**更新 target_repo ref**；ORM 字段补 `input_commits_json` + `cache_key`（落在 tasks.md v2 T-2）
> - MUST #2：选 (b) 路径——**env 字段不在本 MVP 写入**；R-2 缓解栏改写为 deferred，AC-7 维持 `produced_by + inputs + run_id` 三字段；起 follow-up `lineage-env-field-*`
> - MUST #3：tasks.md v2 T-4 暴露 `_canonical_config_hash` helper；本 spec 在 R-3 显式约束 `produced_by.config_hash` 来源
> - 实质矛盾（来自 tasks_review_v1 MUST #2）：**demo recipe 首节点改为已存在 bronze ref**，不再用 raw-upload as processor node；AC-11 grep 去 raw-upload；fixture 预 seed bronze 由 tasks.md T-8 处理
> - SHOULD #1（pipeline 失败/取消/超时）：DELETE API 加进 §非范围
> - SHOULD #2（并发 race）：加 R-7 显式 accept（MVP 单 worker 进程）+ follow-up slug
> - SHOULD #5（AC-7 grep 弱）：AC-7 验证命令加字段级 assert
> - SHOULD #6（R-1 引用 test_processor_runner_smoke 未列于 T-7）：tasks.md v2 T-7 加该用例

## 背景

[盘点 2026-05-18 与用户对齐] dataplat 截至本日已 closed 18 个变更，repo / commit / blob CAS、Adapter / Processor 框架、LLM 网关、SDK / CLI、Web UI 主页面、auth、jobs (RQ + subprocess) 均落地。但 design.md §9 Phase 1 MVP 收官需要的"1 个端到端流水线 PDF→text-corpus→SFT"未达成——根因是缺少 **Pipeline 编排引擎**：没有 Recipe loader、没有 DAG 调度、没有 cache_key 复用、没有 `/pipelines/runs` API、`recipes/examples/` 只有 `.gitkeep`。

design.md §4.3 已明确给出 YAML DSL 形态、§5.3 给出 `cache_key = hash(inputs_commits, processor_version, config)` 缓存契约、§8 取舍表选择 "(a) k8s Job 自研编排" 即 MVP 自研最小调度，不引入 Dagster/Prefect。本变更把这块补齐。

## 问题陈述

1. **DAG 表达缺失**：worker 只能跑单个 processor（POST /process 单步），无法表达"上游→下游→下游"依赖。
2. **Lineage 写入断裂**：commit.lineage_json 字段虽存在，但 ProcessorRunner / AdapterRunner 调用 CommitService.create_commit 时一律传 `lineage=None`（`apps/api/dataplat_api/runner/processor_runner.py:130`、`apps/api/dataplat_api/runner/adapter_runner.py:109`）——design.md §4.4 "好处第 3 条：血缘 = commit lineage 字段的 DAG" 根本没落地。本 change 必须在 orchestrator 路径上修复 processor 侧；adapter 侧单独 follow-up `adapter-lineage-bugfix-*`。
3. **节点级幂等缺失**：同一份 Bronze 跑两次产两份重复 Silver commit（blob 级 CAS 去重了，commit/tree 仍重复创建）。
4. **审计可恢复性缺失**（v2 补）：cache 命中复用旧 commit 时，必须把"本次输入快照 (input_commits + cache_key)"持久化到 `pipeline_node_runs`，否则下游审计无法重放 cache_key 验证它命中的是否还是同一份输入；缺这一步等价于"cache hit 不可证伪"。

## 范围

In scope（AC 编号即范围条目，详细验证见"验收标准"段）：

- AC-1: Recipe Pydantic schema + YAML/JSON 双入口 loader
- AC-2: DAG 拓扑排序 + 环检测（`runner/dag.py`）
- AC-3: cache_key 计算函数确定性（`runner/cache.py`，canonical JSON + sha256，inputs_commits 顺序无关）
- AC-4: 3 张表 + Alembic migration 0004：`pipeline_runs` / `pipeline_node_runs` / `pipeline_cache`
- AC-5: ProcessorRunner.run 签名扩 `lineage: Lineage | None = None` 参数（向后兼容）
- AC-6: PipelineOrchestrator.run_pipeline 协程（`runner/orchestrator.py`）
- AC-7: 节点 cache miss 时 commit.lineage_json 写入 `produced_by + inputs + run_id`（env 字段 deferred 到 `lineage-env-field-*`）
- AC-8: 节点 cache hit 时跳过 ProcessorRunner 调用，复用 `pipeline_cache.output_commit_hash`；**同时更新 target_repo 的 output ref 指向该 commit**；且 `pipeline_node_runs` 写入 `input_commits_json + cache_key` 字段供审计
- AC-9: POST /pipelines/runs + GET /pipelines/runs/{run_id} 路由注册（含节点状态列表）
- AC-10: jobs._TASK_DISPATCH 新增 `pipeline` 类型 + `run_pipeline_job` worker 函数
- AC-11: demo recipe 文件 `recipes/examples/demo-bronze-to-gold.yaml` 与 `demo-bronze-to-silver.yaml`
- AC-12: 后端 pytest ≥ 12 条 + ruff + mypy 通过
- AC-13: scripts/_self_check.sh 跑通所有 AC 验证命令

## 非范围

显式不做（避免 scope creep）：

- 新 processor 实现（pdf-to-text / html-to-md / dedup / chunker / corpus-merge）：拆到下一 change `core-processors-mvp-*`
- Pipeline UI tab / run 详情页 / Pipelines 列表页：拆到下一 change `pipeline-ui-tab-*`
- Lineage DAG 可视化 (React Flow)：Phase 2
- 节点级并行 / IterativeProcessor map-over-records 并发：Phase 2（design.md §5.3）
- Pipeline recipe 自身作为 artifact 进 repo 版本化（design.md §4.3 "Pipeline 也作为 artifact"）：下一 change
- 预算与限流（per-pipeline cost cap）：Phase 2
- 修补 AdapterRunner 的 lineage=None bug：本 change 只在 ProcessorRunner 路径上补齐（orchestrator 节点跑的都是 processor）；AdapterRunner 单独 follow-up `adapter-lineage-bugfix-*`
- 既有模块（repo / commit / blob / auth / adapter / processor / llm）的后端测试基线补齐：单独 change `backend-test-baseline-*`
- 取消 / 暂停 / 超时配置：MVP 由底层 RQ job timeout 兜底；`DELETE /pipelines/runs/{id}` 取消 API 推到 `pipeline-cancel-api-*`
- Recipe 节点级 retry 策略：MVP 失败即标记节点 failed + run failed
- CLI 命令 `dataplat pipeline run`：design.md §7.3 有此命令但拆到下一 change，本 change 只暴露 REST API
- **lineage.env 字段写入**（v2 补）：MVP 不写 env；commit.lineage_json["env"] 字段由 `lineage-env-field-*` 补全（lineage_json 是 JSONB，向后兼容增加 env 字段不破坏既有读者）
- **Recipe 节点编排 Adapter**（v2 补）：MVP orchestrator 只调 ProcessorRegistry；Recipe 节点 `processor` 字段必须是 Processor 名；Bronze 数据由测试 fixture 预 seed 或外部 POST /ingest 先行产出，再被 orchestrator 引用为 `inputs: ["bronze/<owner>/<name>@<ref>"]`。Adapter 节点编排推到 `pipeline-adapter-node-*`

## 验收标准

每条 AC 都附"一行式"验证命令；命令可塞进 `scripts/_self_check.sh`。所有 `! grep` 模式均配 `test -f` 前置且不吞 stderr（SKILL §6 反哺）。所有 Python -c 命令已 dry-parse（SKILL §8 反哺）。

| ID | 描述 | 验证方式 | 期望 |
|---|---|---|---|
| AC-1 | Recipe Pydantic schema 存在；含 `name` + `nodes[].id/processor/inputs/config/output`；支持 YAML 文本与 dict 两路 load | `test -f apps/api/dataplat_api/schemas/pipeline.py && cd apps/api && uv run python -c "from dataplat_api.schemas.pipeline import Recipe, RecipeNode; r=Recipe(name='demo', nodes=[RecipeNode(id='n1', processor='p@1', inputs=['silver/foo/bar@main'], config={}, output='silver/foo/baz@auto')]); assert r.nodes[0].id == 'n1'"` | 退码 0 |
| AC-2 | DAG 拓扑排序 + 环检测：`topo_sort([{id,deps}])` 返回 list[str]；含环输入 raise ValueError | `test -f apps/api/dataplat_api/runner/dag.py && cd apps/api && uv run python -c "from dataplat_api.runner.dag import topo_sort; assert topo_sort([{'id':'a','deps':[]},{'id':'b','deps':['a']}]) == ['a','b']; import pytest; pytest.raises(ValueError, lambda: topo_sort([{'id':'a','deps':['b']},{'id':'b','deps':['a']}]))"` | 退码 0 |
| AC-3 | cache_key 函数：canonical JSON + sha256；inputs_commits 顺序无关；config 键序无关 | `test -f apps/api/dataplat_api/runner/cache.py && cd apps/api && uv run python -c "from dataplat_api.runner.cache import compute_cache_key; k1=compute_cache_key(['a','b'],'p','v',{'k':1,'j':2}); k2=compute_cache_key(['b','a'],'p','v',{'j':2,'k':1}); assert k1==k2 and len(k1)==64"` | 退码 0；两次结果同 64 字符 hex |
| AC-4 | 3 表 + migration 0004：`pipeline_runs` / `pipeline_node_runs` / `pipeline_cache` 在同一 migration | `test -f apps/api/alembic/versions/0004_pipeline_orchestrator.py && grep -q "pipeline_runs" apps/api/alembic/versions/0004_pipeline_orchestrator.py && grep -q "pipeline_node_runs" apps/api/alembic/versions/0004_pipeline_orchestrator.py && grep -q "pipeline_cache" apps/api/alembic/versions/0004_pipeline_orchestrator.py` | 退码 0 |
| AC-5 | ProcessorRunner.run 签名含 `lineage` 参数（向后兼容，默认 None） | `cd apps/api && uv run python -c "from dataplat_api.runner.processor_runner import ProcessorRunner; import inspect; p=inspect.signature(ProcessorRunner.run).parameters; assert 'lineage' in p and p['lineage'].default is None"` | 退码 0 |
| AC-6 | PipelineOrchestrator.run_pipeline 是 coroutine；签名含 `recipe, author_id, run_id` 三参数 | `test -f apps/api/dataplat_api/runner/orchestrator.py && cd apps/api && uv run python -c "from dataplat_api.runner.orchestrator import PipelineOrchestrator; import inspect; sig=inspect.signature(PipelineOrchestrator.run_pipeline); assert inspect.iscoroutinefunction(PipelineOrchestrator.run_pipeline); assert all(n in sig.parameters for n in ('recipe','author_id','run_id'))"` | 退码 0 |
| AC-7 | 节点 cache miss 时 commit.lineage_json 字段级断言：`produced_by.kind == "processor"` / `produced_by.name == <processor>` / `inputs[0].commit == <upstream hash>` / `run_id == str(pipeline_run_id)`；env 字段 deferred 不验 | `test -f apps/api/tests/test_pipeline_orchestrator.py && grep -q "test_lineage_written_on_cache_miss" apps/api/tests/test_pipeline_orchestrator.py && grep -qE 'produced_by.{0,8}name|lineage_json\[.produced_by.\]' apps/api/tests/test_pipeline_orchestrator.py && grep -qE 'inputs.{0,8}commit|lineage_json\[.inputs.\]' apps/api/tests/test_pipeline_orchestrator.py && grep -q "run_id" apps/api/tests/test_pipeline_orchestrator.py && cd apps/api && uv run pytest -q tests/test_pipeline_orchestrator.py::test_lineage_written_on_cache_miss` | pytest 通过 + 3 个字段级 grep 命中 |
| AC-8 | 节点 cache hit 时三条断言：(a) ProcessorRunner.run.call_count == 0；(b) target_repo 的 output ref 更新指向 cache 命中的 commit；(c) pipeline_node_runs 行的 `input_commits_json` 与 `cache_key` 字段非空（审计可恢复） | `test -f apps/api/tests/test_pipeline_orchestrator.py && grep -q "test_cache_hit_skips_processor" apps/api/tests/test_pipeline_orchestrator.py && grep -q "test_cache_hit_updates_ref" apps/api/tests/test_pipeline_orchestrator.py && grep -q "input_commits_json" apps/api/tests/test_pipeline_orchestrator.py && cd apps/api && uv run pytest -q apps/api/tests/test_pipeline_orchestrator.py -k cache_hit` | pytest 通过（含 ref 更新与字段写入断言） |
| AC-9 | POST /pipelines/runs + GET /pipelines/runs/{run_id} 在 OpenAPI 中暴露 | `cd apps/api && uv run python -c "from dataplat_api.main import app; s=app.openapi(); paths=set(s['paths'].keys()); assert '/pipelines/runs' in paths and '/pipelines/runs/{run_id}' in paths"` | 退码 0 |
| AC-10 | jobs._TASK_DISPATCH 含 'pipeline' + `run_pipeline_job(job_id)` 函数存在 | `cd apps/api && uv run python -c "from dataplat_api.jobs.service import JobsService; from dataplat_api.jobs.tasks import run_pipeline_job; import inspect; assert 'pipeline' in JobsService._TASK_DISPATCH and 'job_id' in inspect.signature(run_pipeline_job).parameters"` | 退码 0 |
| AC-11 | 两份 demo recipe 文件存在且节点全为 Processor（不含 adapter as processor 节点）；inputs 引用既存 bronze ref（fixture 预 seed） | `test -f recipes/examples/demo-bronze-to-gold.yaml && test -f recipes/examples/demo-bronze-to-silver.yaml && grep -q "markdown-normalize" recipes/examples/demo-bronze-to-gold.yaml && grep -q "llm-qa-gen" recipes/examples/demo-bronze-to-gold.yaml && grep -q "markdown-normalize" recipes/examples/demo-bronze-to-silver.yaml && grep -q "bronze/" recipes/examples/demo-bronze-to-silver.yaml && ! grep -qE "^\s*processor:\s*raw-upload" recipes/examples/demo-bronze-to-gold.yaml && ! grep -qE "^\s*processor:\s*raw-upload" recipes/examples/demo-bronze-to-silver.yaml` | 退码 0；正向 grep 命中 + 反向 grep 配 test -f 前置确保文件存在 |
| AC-12 | 后端 pytest 收集 ≥ 12 条新增 pipeline 测试 + ruff + mypy 通过 | `[ "$(cd apps/api && uv run pytest --collect-only -q tests/test_pipeline_schemas.py tests/test_pipeline_dag.py tests/test_pipeline_cache.py tests/test_pipeline_orchestrator.py tests/test_pipeline_e2e.py 2>&1 \| grep -cE 'test_pipeline_.*\.py::')" -ge 12 ] && cd apps/api && uv run ruff check dataplat_api && uv run mypy dataplat_api` | ≥ 12 + 两工具退码 0 |
| AC-13 | scripts/_self_check.sh 含本 change 段且 AC-1~AC-12 各有对应 grep / python -c 行 | `test -f scripts/_self_check.sh && grep -q "pipeline-orchestrator-mvp-20260518" scripts/_self_check.sh` | 退码 0 |

**AC ↔ 测试覆盖矩阵**（每条 AC 至少一个测试或 self_check grep 覆盖）：

| AC | 覆盖测试 / 检查 |
|---|---|
| AC-1 | tests/test_pipeline_schemas.py (≥3：valid recipe, missing required field, inputs ref 格式) + self_check |
| AC-2 | tests/test_pipeline_dag.py (≥3：linear, branching, cycle raise) + self_check |
| AC-3 | tests/test_pipeline_cache.py (≥3：determinism, order independence, config canonicalization) + self_check |
| AC-4 | self_check grep migration + tests/test_pipeline_orchestrator.py 建 run 时 INSERT |
| AC-5 | tests/test_pipeline_orchestrator.py::test_processor_runner_accepts_lineage + self_check |
| AC-6 | tests/test_pipeline_orchestrator.py::test_run_pipeline_signature + self_check |
| AC-7 | tests/test_pipeline_orchestrator.py::test_lineage_written_on_cache_miss + self_check |
| AC-8 | tests/test_pipeline_orchestrator.py::test_cache_hit_skips_processor + ::test_cache_hit_updates_ref + ::test_cache_hit_writes_audit_fields + self_check |
| AC-9 | self_check OpenAPI 字符串检查 + tests/test_pipeline_e2e.py 真调路由 |
| AC-10 | self_check JobsService._TASK_DISPATCH 检查 + tests/test_pipeline_e2e.py 走 enqueue 路径 |
| AC-11 | self_check grep recipe yaml 关键字 + tests/test_pipeline_e2e.py 解析 demo recipe |
| AC-12 | self_check pytest collect-only + ruff + mypy |
| AC-13 | self_check 自递归（递归调用自身可被 scripts/_self_check.sh 检测） |

## 风险

| 风险 | 概率 | 影响 | 缓解（含 AC 关联） |
|---|---|---|---|
| R-1 ProcessorRunner 签名扩 lineage 破坏既有 POST /process 路由调用 | 低 | 中 | lineage 默认值 None 向后兼容；**AC-5** grep 验 default is None；**T-7** 测试清单显式包含 `tests/test_processor_runner_backcompat.py::test_processor_runner_smoke` 用例（v2 修订：从 test_pipeline_orchestrator.py 提到独立文件，与 R-1 一一对应） |
| R-2 cache_key 命中误判：不同 env（python/model 版本）但同 input/config 命中旧 commit | 中 | 中 | 决策接受：env 不入 cache_key（关键决策表第 3 条）；**v2 修订**：env 字段在本 MVP 不写入 commit.lineage_json，由 follow-up `lineage-env-field-*` 补；本风险的 env 维度审计能力 deferred；MVP 风险残留：用户须知 cache hit 不感知 model/python 升级；用 follow-up 上线前在 demo / 文档显式提示 |
| R-3 Recipe 引用未知节点 / 循环依赖 / 引用不存在 processor 提交期未挡住 | 中 | 高 | POST /pipelines/runs handler 入口串行：(1) Pydantic schema 校验 + RecipeNode 字段级 field_validator（**AC-1**，v2：早抛错）；(2) `topo_sort` 抛 ValueError → 422（**AC-2**）；(3) 每节点 `ProcessorRegistry.get` 预检 → 422；**AC-12 / T-7** 测试覆盖三条错误路径：test_unknown_processor / test_cycle / test_unknown_node_ref（同时 `lineage.produced_by.config_hash` 来源约束：必须调 T-4 暴露的 `_canonical_config_hash(config)`，禁止把整体 cache_key 当 config_hash 写——v2 修订对应 spec_review_v1 MUST FIX #3） |
| R-4 demo recipe 依赖 LLM Gateway 真调用 → 测试不稳定且耗费 | 中 | 中 | tests/test_pipeline_e2e.py 用 monkeypatch 替换 `dataplat_api.llm.factory.get_llm_gateway` 返回 mock；同时 ship `demo-bronze-to-silver.yaml` 作为零 LLM 依赖路径（**AC-11** 两份均 grep 校验）；两份 demo 节点均为 Processor，bronze 输入由 fixture 预 seed（v2 修订对应 tasks_review_v1 MUST FIX #2） |
| R-5 pipeline_run 长跑 / worker 进程异常退出后 run.status 停留 running；节点抛 HTTPException 在 worker 上下文中 traceback 被吞 | 中 | 中 | MVP 接受 stale run：由 RQ job timeout 兜底；orchestrator 内 `catch (HTTPException, Exception)`：HTTPException → `error=str(exc.detail)`；其他 → `error=repr(exc)[:500]`（v2 SHOULD FIX #5 修订）；**T-7** 含 test_node_400_marks_failed / test_node_unknown_error_marks_failed；DELETE /pipelines/runs（取消）API 推到 `pipeline-cancel-api-*` |
| R-6 commit 父子链断裂 + cache hit 路径下 target_repo ref 更新语义未定义 | 中 | 中 | **v2 修订（MUST FIX #1 闭）**：orchestrator 内显式策略：(a) cache miss → 调 ProcessorRunner 拿到新 commit，ProcessorRunner 已有 ref→parent 自动接链逻辑保证 commit.parents = [target_repo.ref 当前 commit]；(b) cache hit → **不**产新 commit，但 **MUST 更新 target_repo 的 output ref 指向 cached commit_hash**，使后续以 `repo@<ref>` 引用 target_repo 的下游节点拿到一致状态；(c) `pipeline_node_runs` 必写 `input_commits_json + cache_key + output_commit_hash` 三字段（审计可恢复 cache_key 验真）；**AC-8** 覆盖 (a)(b)(c) 三断言；**T-7** 含 test_parent_chain（cache miss 链）+ test_cache_hit_updates_ref + test_cache_hit_writes_audit_fields |
| R-7（v2 新增）多 run 并发写同 target ref 的 race | 中 | 中 | MVP 接受：单 worker 进程串行（RQ 默认）下不发生；多 worker 进程时由 CommitService.create_commit 内 ref 更新的行级 lock 兜底（既有逻辑）；若 race 仍发生表现为后写覆盖先写，与 design.md §4.4 类 Git ref 语义一致（force-update 风格）；**spec 不加 AC，显式标 deferred**；follow-up `pipeline-ref-locking-*` 可演进为乐观锁 / `--if-current-ref` 头 |

## 受影响模块

新增：

- `apps/api/dataplat_api/schemas/pipeline.py`
- `apps/api/dataplat_api/models/pipeline.py`
- `apps/api/dataplat_api/runner/dag.py`
- `apps/api/dataplat_api/runner/cache.py`
- `apps/api/dataplat_api/runner/orchestrator.py`
- `apps/api/dataplat_api/routers/pipelines.py`
- `apps/api/alembic/versions/0004_pipeline_orchestrator.py`
- `apps/api/tests/test_pipeline_schemas.py`
- `apps/api/tests/test_pipeline_dag.py`
- `apps/api/tests/test_pipeline_cache.py`
- `apps/api/tests/test_pipeline_orchestrator.py`
- `apps/api/tests/test_pipeline_e2e.py`
- `recipes/examples/demo-bronze-to-gold.yaml`
- `recipes/examples/demo-bronze-to-silver.yaml`

修改：

- `apps/api/dataplat_api/runner/processor_runner.py`（加 `lineage` 参数）
- `apps/api/dataplat_api/jobs/service.py`（_TASK_DISPATCH 加 `pipeline`）
- `apps/api/dataplat_api/jobs/tasks.py`（加 `run_pipeline_job`）
- `apps/api/dataplat_api/main.py`（include_router）
- `apps/api/dataplat_api/models/__init__.py`（export 3 个新 ORM）
- `scripts/_self_check.sh`（追加本 change 段）

## 不受影响但易混淆的模块

- `apps/api/dataplat_api/adapters/`：本 change **不**修改 Adapter 框架；**v2 修订**：demo recipe 节点全为 Processor，**不**编排 Adapter；bronze 数据由 e2e test fixture 通过既有 POST /ingest 路径预先 seed，与 orchestrator 解耦。AdapterRunner 的 lineage=None bug 单独 follow-up `adapter-lineage-bugfix-*`，不在本 change 范围。
- `apps/api/dataplat_api/llm/`：LLM Gateway **不**改；测试用 monkeypatch mock，不引入新 provider。
- `apps/web/`：本 change 完全**不动**前端；UI tab 拆到下一 change。
- `packages/sdk-py/`：CLI **暂不**加 `dataplat pipeline run` 命令；只暴露 REST API，CLI 拆到下一 change。

## 待澄清问题

> 阶段 1 评审前必须清零，或显式标记 deferred。

- [x] Processor 范围：是否在本 change 新增 pdf-to-text 等 — 用户确认**不在本 change**
- [x] UI 范围：是否在本 change 加 Pipeline tab — 用户确认**不在本 change**
- [x] 测试覆盖：是否顺手补齐既有模块测试 — 用户确认**只覆盖本 change 新增**
- [x] cache_key 是否纳入 env 版本 — 决策表第 3 条：**不纳入**，env 由 lineage.env 字段单独记录
- [x] Recipe DSL 形态 — 直接照搬 design.md §4.3 示例（`@version` / `@node-id` / `@auto`）

## 引用

- `.harness/design.md` §1.1 目标、§3 三层规范、§4.3 Pipeline / Recipe、§4.4 类 Git CAS、§5.3 处理执行模型、§8 取舍表（处理引擎 / Schema / LLM）、§9 Phase 1 路线图
- `.harness/changes/processor-framework-20260517/`（ProcessorRunner / Registry / DbRepoView 已落地）
- `.harness/changes/rq-worker-skeleton-20260517/`（JobsService / _TASK_DISPATCH 模式）
- `.harness/changes/commit-api-mvp-20260517/`（CommitService.create_commit 接受 Lineage）
- `.harness/changes/core-domain-model-20260516/`（Lineage / ProducedBy / InputRef pydantic 模型）
- `packages/core/src/dataplat_core/domain/lineage.py`
- `.harness/skills/request-analysis/SKILL.md` §"跨 AC 一致性自审清单"（9 条 generator 自查）
