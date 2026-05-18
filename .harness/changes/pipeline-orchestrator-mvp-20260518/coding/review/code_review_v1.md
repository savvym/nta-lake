---
change_id: pipeline-orchestrator-mvp-20260518
target: coding (worktree 改动 + coding_report_v1.md)
target_version: 1
review_version: 1
reviewer: claude-agent:pipeline-orchestrator-mvp-20260518-stage4-reviewer-v1
reviewed_at: 2026-05-18T08:35:00Z
verdict: REVISION REQUIRED
---

# Code Review v1

## 范围与作者声明对照

- coding_report_v1.md §"改动文件清单" 列 12 新源文件 + 9 测试/数据文件 + 7 修改文件。reviewer 实跑 `git status --short` + 逐文件 Read 确认与声明一致。
- 改动均落在 `apps/api/dataplat_api/{schemas,models,runner,routers,jobs,services,storage}`、`apps/api/alembic/versions`、`apps/api/tests`、`recipes/examples`、`scripts`，全部对齐 `engineering-structure.md` §顶层布局；**无 scope creep**。
- `apps/api/dataplat_api/main.py` 仅追加 `include_router(pipelines_router)`，符合 §"分层不写 SQL" 约束。
- `apps/web/`、`packages/sdk-py/`、`plugins/` 等本 change 非范围目录均无改动。

## v2 SHOULD FIX 复检（来自 spec_review_v2 / tasks_review_v2 + v2 修订说明共 6 条）

| # | v2 SHOULD issue | 状态 | 证据 |
|---|---|---|---|
| 1 | `RefService.upsert_ref` 命名修正（v2 SHOULD #1） | **CLOSED** | `services/ref.py:34-52` 新增 `upsert_ref(session, repo_id, name, commit_hash)`；`services/commit.py:194-197` 改调 helper。orchestrator cache hit 路径 `orchestrator.py:257-259` 调 `RefService.upsert_ref`。 |
| 2 | `input_commits_json` + `cache_key` NOT NULL（v2 SHOULD #2） | **CLOSED** | `models/pipeline.py:70-71` 两字段 `nullable=False`；`alembic/0004:77-78` 同步；`ix_pipeline_node_runs_cache_key` 索引 line 86-90。 |
| 3 | `tests/test_processor_runner_backcompat.py`（v2 SHOULD #3） | **CLOSED** | 文件存在；2 用例验签名 + 位置（required 在 lineage 前）。 |
| 4 | `Recipe` field_validator（v2 SHOULD #4） | **CLOSED** | `schemas/pipeline.py:85-102` 三 validator `_check_processor` / `_check_inputs` / `_check_output`。schema 早抛错路径用 `test_invalid_input_ref_raises_validation_error` 等覆盖。 |
| 5 | `HTTPException` / `Exception` 双 catch（v2 SHOULD #5） | **PARTIAL — 见 MUST FIX #2** | `orchestrator.py:140-145`：HTTPException → `error = str(getattr(exc, "detail", exc))`；其他 → `error = repr(exc)[:500]`。但 truncation 仅作用 fallback 路径，HTTPException 的 detail 可能是 dict（如 `processor_runner.py:70-73` 抛的 404 detail 是 dict），`str(dict)` 输出不限长；spec R-5 写明的"500 字符截断"对 HTTPException 路径未生效。 |
| 6 | YAML 入口拆两路由（v2 SHOULD #6） | **CLOSED** | `routers/pipelines.py:76-108` JSON 与 YAML 双路由；URL `POST /pipelines/runs` + `POST /pipelines/runs:from-yaml`。 |

## 3 条偏离 spec 的定夺

| # | 偏离 | reviewer 定夺 | 理由 |
|---|---|---|---|
| 1 | MVP single-input only（`validate_recipe` 拦 `len(inputs)!=1`） | **接受** | spec v2 §非范围（spec.md:70）已显式声明"Recipe 节点编排 Adapter / 多源 processor 拆 follow-up `multi-input-processor-*`"；validate_recipe 拦截到位（`orchestrator.py:79-84` 抛 ValueError "single-input only"）；`test_multi_input_rejected`（`test_pipeline_orchestrator.py:118-133`）真覆盖；现有 `markdown-normalize` / `llm-qa-gen` 单源足够 demo recipe 跑通。**注**：schema validator `_check_inputs` 不拦长度（见 SHOULD #4），长度校验在 orchestrator 层；router 调 `validate_recipe` 提前到 enqueue 前（`routers/pipelines.py:44-50`）已 422 拦掉，工程上 OK。 |
| 2 | T-7c e2e deferred 到 stage 5 | **接受** | coding_report §偏离 2 论据成立：T-7b 4 集成测试覆盖 lineage / cache hit 全字段断言路径；e2e demo recipe 与之 ≥90% 重叠。AC-12 ≥12 阈值：当前 6+5+6+2+8 单元/集成 ≈ 27，远超 12，**不悬空**。spec AC-12 命令引 `tests/test_pipeline_e2e.py` 但 stage 5 e2e 补到该路径即可，本 stage 不阻塞——见 SHOULD #3 spec/self_check drift。 |
| 3 | 本机 MinIO 403 → AC-7/AC-8 self_check FAIL | **接受为环境问题，不阻塞 code review** | reviewer 实查 `scripts/_self_check.sh:1154-1158` AC-7/AC-8 用 `run_ac_skipif_no_pg_minio_redis` 包裹；同问题在 processor-framework / commit-api / firecrawl 等既有 change 的集成 AC 都用相同模板，未单独 FAIL（同环境同凭证下 PASS）。**但要求 stage 5 reviewer 在正确凭证 CI 环境验证 AC-7/AC-8 PASS** + 写入 test_report 复检指引。 |

## 每条 AC ↔ 实现对照

| AC | 描述 | 实现位置 | 结论 |
|---|---|---|---|
| AC-1 | Recipe schema + YAML/JSON loader | `schemas/pipeline.py:76-121`（Recipe / RecipeNode / field_validator / `load_recipe`） + `parse_input_ref` / `parse_output_ref` / `parse_processor_ref` | PASS |
| AC-2 | DAG topo + 环检测 | `runner/dag.py:14-64` Kahn + `cycle detected` ValueError；`build_node_deps` line 67-81 | PASS |
| AC-3 | cache_key 确定性 + 顺序无关 | `runner/cache.py:33-49` `compute_cache_key` + `sort_keys=True` + `sorted(inputs_commits)` | PASS（含 v2 修订 `_canonical_config_hash` helper 暴露） |
| AC-4 | 3 表 + migration 0004 + index | `models/pipeline.py:23-92` + `alembic/0004` 含 `pipeline_runs/pipeline_node_runs/pipeline_cache` + 3 索引 | PASS |
| AC-5 | ProcessorRunner.run lineage 默认 None | `runner/processor_runner.py:63` `lineage: Lineage \| None = None` | PASS |
| AC-6 | run_pipeline coroutine + 三参数 | `runner/orchestrator.py:95-106` `async def run_pipeline(session, store, recipe, author_id, run_id)` | PASS |
| AC-7 | cache miss lineage 字段级写入 | `orchestrator.py:281-309` 构造 `Lineage(produced_by, inputs[InputRef(repo, commit)], run_id=str(run_id), env={})` 调 ProcessorRunner.run；测试 `test_lineage_written_on_cache_miss` line 401-453 字段级 assert `kind/name/inputs[0].commit/run_id` 全覆盖 | PASS（env={} 是 spec v2 §非范围接受的 deferred） |
| AC-8 | cache hit 三断言 | `orchestrator.py:254-278` cache_lookup 命中 → 不调 ProcessorRunner / `RefService.upsert_ref` / 写 `input_commits_json + cache_key`；测试 `test_cache_hit_skips_processor`（call_count==0）/ `test_cache_hit_updates_ref`（ref 指向命中 commit）/ `test_cache_hit_writes_audit_fields`（两字段非空）三断言齐备 | PASS |
| AC-9 | POST / GET /pipelines/runs 在 OpenAPI | `routers/pipelines.py:36, 76-160` + `main.py:18, 47` include_router | PASS |
| AC-10 | jobs.dispatch + run_pipeline_job | `jobs/service.py:27` `_TASK_DISPATCH["pipeline"]` + `jobs/tasks.py:228` `run_pipeline_job(job_id: str)` | PASS |
| AC-11 | demo recipe 全 Processor，无 raw-upload | `recipes/examples/demo-bronze-to-silver.yaml` 单节点 `markdown-normalize@0.1`；`demo-bronze-to-gold.yaml` 两节点 `markdown-normalize → llm-qa-gen`；无 `processor: raw-upload`；inputs 引 `bronze/demo/raw-md@main`（fixture 预 seed） | PASS |
| AC-12 | ruff + mypy + pytest ≥ 12 | coding_report 声明 ruff/mypy 全 PASS；本 change 新增测试 ≥27（≥12） | **PARTIAL — 见 SHOULD #3**：spec AC-12 命令引 `tests/test_pipeline_e2e.py`，但 stage 3 没建该文件；self_check AC-12 用 `ruff + mypy` 替代，与 spec 命令不一致 |
| AC-13 | self_check 段 + dispatch | `scripts/_self_check.sh:1133-1173` `run_pipeline_orchestrator_mvp()` 13 条 + `case "pipeline-orchestrator-mvp" \| "pipeline-orchestrator-mvp-20260518"` dispatch line 1308-1310 | PASS |

## 主动盲点检查

### A. `validate_recipe` 多源拦截顺序 + empty inputs

`validate_recipe`（orchestrator.py:65-93）顺序：`build_node_deps → topo_sort → 遍历 nodes 检查 inputs 长度 + processor`。但 `topo_sort` 先于长度检查；若用户传 `len(inputs) == 0`（schema 不拦：`inputs: list[str]` 允许 []），`build_node_deps` 返 `{"id": ..., "deps": []}`，`topo_sort` PASS；接着遍历命中 `len != 1` 抛"single-input only"——能拦但语义是混的（empty inputs 应是 schema 422 而非 orchestrator 内 ValueError）。**SHOULD FIX**（见 SHOULD #4）。

### B. `target_ref="auto"` → `"main"` hardcode

`orchestrator.py:246`：`target_ref = out_parts["ref"] if out_parts["ref"] != "auto" else "main"`。design.md §4.3 `@auto` 语义未在本 change spec 内明确写"`@auto = main`"——属工程取巧。**SHOULD FIX**（见 SHOULD #5）。

### C. cache hit 时 commit dedup 与 cache 写入

`orchestrator.py:310` cache miss 分支调 `ProcessorRunner.run` 拿到 `(commit, _dedup, _result)`——若 `_dedup is True`（commit 已存在），仍写 cache_key → 旧 commit。第二次同 cache_key 直接 hit 复用同 commit。语义正确。**未检查** `_dedup` 标志：cache hit 与 commit dedup 之间的差异在 `pipeline_node_runs` 没字段记录。**NICE TO HAVE**。

### D. error 分支 `cache_key=""` 字面值 + DB 索引语义

`orchestrator.py:165` 兜底 INSERT failed node_run 时 `cache_key=""` + `input_commits_json=[]`。`models/pipeline.py:71` `cache_key NOT NULL + index`——空串聚集 + 业务侧需 `len > 0` 区分"真 cache_key"。tasks_review_v2 SHOULD #4 已提示但本实现走第三条路径（占位空串）未在 tasks v2 锁定。**SHOULD FIX**（见 SHOULD #1）。

### E. PyYAML 未声明依赖

`schemas/pipeline.py:16` `import yaml  # type: ignore[import-untyped]`；reviewer 实查 `apps/api/pyproject.toml:6-22` **未声明** `PyYAML`；`uv.lock` 含 pyyaml 6.0.3 但是间接依赖。任何隔离环境 / `pip install dataplat-api` 都会 ImportError。违反 coding-style.md §0 完整性约束 + engineering-structure §"多语言 workspace" 隐含"每包声明自己直接依赖"。**MUST FIX #1**。

### F. routers `create_pipeline_run_from_yaml` `(ValueError, Exception)` 双 catch

`routers/pipelines.py:103` `except (ValueError, Exception) as exc`——`ValueError` 是 `Exception` 子类，第一项被第二项覆盖；写法冗余。**NICE TO HAVE**：去 ValueError；或区分 `yaml.YAMLError` 与 `ValidationError`。

### G. `PipelineRunResponse.input_commits` 与 ORM `input_commits_json` 命名

API 暴露 `input_commits`；ORM `input_commits_json`。OpenAPI 给前端的字段 `input_commits`——前端用 `@dataplat/api-types` 自动同步，不破坏契约。两个命名（API list[str] vs DB JSONB）的差异是合理的。NOT AN ISSUE。

### H. `_run_node` 内多次 commit + 事务边界

`orchestrator.py:277, 328` cache hit / miss 分支各 commit 一次；外层 catch error 再 commit（`orchestrator.py:179`）；`ProcessorRunner.run` 内部 `CommitService.create_commit → session.commit()`（`services/commit.py:199`）——每节点 cache miss commit 三次（commit_service / cache.insert pending / node_run）。若 cache.insert 之后 node_run insert 之前异常，cache 表写入但审计行缺失。**SHOULD FIX**（见 SHOULD #6）。

### I. `orchestrator.py:103` 文档字符串错误

`"""编排执行入口。""run_id"" 由 caller...` —— 三引号紧贴 `""`，可读性差；ast.parse OK 但 IDE / pydoc 渲染丢失加粗。**NICE TO HAVE**：改 backtick 或加空行。

### J. `_create_run_and_enqueue` enqueue 失败 → PipelineRunORM orphan

`routers/pipelines.py:53-72` 路由器 INSERT PipelineRunORM(queued) 后调 `JobsService.enqueue`；`JobsService.enqueue` 失败时只 DELETE JobORM，不知道 pipeline_run 存在。结果：pipeline_run.status=queued 永久残留，worker 永远不跑，GET API 永远返 queued。**SHOULD FIX**（见 SHOULD #2）。

### K. `validate_recipe` 在 orchestrator 内被重复调用

`routers/pipelines.py:45` 调 → 422；`orchestrator.py:112` worker 内再调一次 → set run.status=failed。同 schema 校验跑两次，无害但浪费 commit。**NICE TO HAVE**。

### L. CacheService.insert docstring 未声明 caller 负责 commit

`runner/cache.py:65-77` `CacheService.insert` 只 `session.add()` 不 `session.commit()`；语义未在 docstring 说明。**NICE TO HAVE**。

## 问题列表

### MUST FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | `apps/api/pyproject.toml:6-22`（dependencies）+ `schemas/pipeline.py:16` | **PyYAML 未声明直接依赖**：`schemas/pipeline.py` 直接 `import yaml`；`apps/api/pyproject.toml` 未声明 `PyYAML`。当前在 monorepo workspace 下经其他包间接装上 pyyaml 6.0.3 故 OK，但任何隔离环境 / `pip install dataplat-api` 都会 ImportError。违反 coding-style.md §0 依赖完整性 + engineering-structure §"多语言 workspace" 隐含"每包声明自己直接依赖"。 | 在 `apps/api/pyproject.toml` `dependencies` 追加 `"PyYAML>=6.0,<7"`；同步 `uv.lock`。 |
| 2 | `runner/orchestrator.py:141-145` 与 spec R-5 缓解承诺 | **HTTPException error truncation 缺失**：spec R-5（spec.md:118）承诺"HTTPException → `error=str(exc.detail)`；其他 → `error=repr(exc)[:500]`"——但 `processor_runner.py:67-74` 抛的 404 HTTPException `detail` 是 dict（含 `detail` + `available` 字段，long processor 列表时可达数百字符）；`str(dict)` 不截断；spec R-5 内"500 截断"对 HTTPException 路径未生效，可能在 detail 含大 list 时让 `pipeline_node_runs.error` / `pipeline_runs.error` Text 字段累计写入异常长数据，影响后续 GET API JSON 序列化与日志可读性。 | `orchestrator.py:142` 改为 `error = str(getattr(exc, "detail", exc))[:500]`，统一双路径 500 截断；同步在 stage 5 补 `test_node_400_marks_failed` / `test_node_unknown_error_marks_failed`（tasks v2 T-7b 列出但当前未实现）。 |

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | `runner/orchestrator.py:154-170` error 兜底 INSERT + `models/pipeline.py:71` | **`cache_key=""` 占位与 NOT NULL 约束语义混乱**：error 兜底用空字符串占位；索引上空串聚集 + 业务侧需 `len > 0` 区分"真 cache_key"。tasks_review_v2 SHOULD #4 已显式提示但未明确选 (a) NULLABLE 或 (b) 早算 cache_key；本实现是第三条路径未在 tasks v2 锁定。 | 二选一：(a) migration 0004 改 `cache_key` 为 nullable，error 路径写 NULL；(b) `_run_node` 把 cache_key 计算移到 try 之外（parse input + parse processor_ref 之后），error 兜底 INSERT 可拿到。建议 (b)；input_commits_json 同步改写为已解析值。 |
| 2 | `routers/pipelines.py:39-73` `_create_run_and_enqueue` | **enqueue 失败时 PipelineRunORM 残留 orphan**：路由器先 INSERT PipelineRunORM(queued) 再调 `JobsService.enqueue`；`JobsService.enqueue` 内若 RQ enqueue 失败只 DELETE JobORM，不感知 pipeline_run 存在。结果：pipeline_run.status=queued 永久残留。 | `_create_run_and_enqueue` 包 `try/except`：`enqueue` 异常时 `await session.delete(run); await session.commit(); raise`；或在 spec v3 显式接受 orphan + 由 `pipeline-cancel-api-*` follow-up 接管 GC。 |
| 3 | `scripts/_self_check.sh:1169-1170` AC-12 与 spec AC-12 不对齐 | spec AC-12 命令引 `tests/test_pipeline_e2e.py`（spec.md:89），但 stage 3 未建该文件；self_check AC-12 替换为 "ruff + mypy"——与 spec 命令 drift，stage 5 reviewer 复检会发现。 | 二选一：(a) stage 5 补 `tests/test_pipeline_e2e.py`；self_check AC-12 同步加 `pytest --collect-only ≥ 12`；(b) spec v3 修订 AC-12 命令删 `test_pipeline_e2e.py`，明示 e2e 推 stage 5；同步 self_check。 |
| 4 | `schemas/pipeline.py:81` `inputs: list[str]` | **`inputs` 允许空列表**：Pydantic `list[str]` 允许 []；`_check_inputs` validator 只校验每元素格式不拦空。结果：用户能提交 `inputs: []` 通过 schema 校验，到 orchestrator 才抛 `len != 1`——422 是 router 调 validate_recipe 拦的，但 schema 本身不拦增加了 orchestrator 心智负担。 | `RecipeNode.inputs` 改 `Annotated[list[str], Field(min_length=1)]` 或 `_check_inputs` 加 `if not v: raise ValueError("inputs 不能为空")`；同步 stage 5 加 `test_empty_inputs_rejected`。 |
| 5 | `runner/orchestrator.py:246` `target_ref="auto" → "main"` | **`@auto` 语义在 spec 内未澄清**：design.md §4.3 提 `@auto` 但本 change spec 没明确写"`@auto` 等价 `main`"。当前 hardcode 是工程取巧。 | spec v3（或 follow-up `pipeline-auto-ref-semantics-*`）澄清 `@auto` 语义（候选：默认 main；或自动生成唯一 ref `run-<run_id-short>`）；当前 hardcode 加 `# TODO(spec-pipeline-auto-ref-semantics-*)` 注释或在 spec §"待澄清问题"加一条 deferred。 |
| 6 | `runner/orchestrator.py:_run_node` 多次 commit | **cache.insert + node_run.insert 不在同一事务**：CacheService.insert add 后由 caller commit；若 cache.insert 之后 node_run insert 之前异常，cache 表写入但审计行缺失——后续命中复用 commit 但审计行缺失。 | `_run_node` cache miss 分支用 `async with session.begin_nested()` 或单一末位 commit；或在 docstring 显式标注当前事务边界与接受语义。 |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | `runner/orchestrator.py:103` docstring | `"""编排执行入口。""run_id"" 由 caller`：三引号紧贴 `""` 阅读不友好 | 改 backtick 引用或加空行 |
| 2 | `routers/pipelines.py:103` `except (ValueError, Exception)` | ValueError 是 Exception 子类，冗余 | 去 ValueError；或细分 yaml.YAMLError / ValidationError |
| 3 | `runner/orchestrator.py:140` `noqa: PERF203` | for 内 try/except 触发 ruff PERF203，noqa 合理但无注释 | 加 `# noqa: PERF203  # node 级 try/except 是设计` |
| 4 | `routers/pipelines.py:95, 100` `del request` | 占位 hack | 改 `Body(..., media_type="text/yaml")` 单参 |
| 5 | `runner/cache.py:65-77` `CacheService.insert` docstring | 未声明 "caller 负责 commit" | docstring 补一行 |
| 6 | `runner/orchestrator.py:112-122` `run_pipeline` 重复校验 | router 已 validate；worker 再 validate 一次浪费 | worker 跳过 validate_recipe，假设 router 已校验 |
| 7 | `runner/orchestrator.py:158-170` 兜底 INSERT failed node_run `parse_processor_ref` 调 2 次（line 159, 160） | 已解析；可缓存 | 解一次：`name, version = parse_processor_ref(node.processor)` |
| 8 | `models/pipeline.py:31, 66` `status` 字段无 CHECK / Enum 约束 | 仅应用层约束 | Phase 2 加 CHECK 或 PG Enum |
| 9 | `runner/cache.py:55-63` `CacheService.lookup` returns `str \| None` | 直接返 hash 字符串，丢失 metadata（如 created_at） | 现状可接受；如未来需要"cache 命中年龄"再扩 |

## 跨改动观察

- **依赖声明完整性**：`PyYAML` 是直接依赖但未在 `apps/api/pyproject.toml` 声明——本仓库历史变更中类似问题（间接依赖被直接使用）应该开 follow-up `dependency-declaration-audit-*`：跑 `pipdeptree`-style 扫描，所有 `import X` 必须在对应 pyproject.toml 显式声明。
- **事务边界 + commit 频度**：本 change 的 orchestrator + processor + jobs 路径形成"嵌套 commit 三层"模式（router commit → orchestrator commit → ProcessorRunner.commit → CacheService.add + commit → node_run commit），跨节点错误恢复语义需在 spec v3 / follow-up `pipeline-transaction-model-*` 显式定义；当前 MVP 接受"节点级 partial failure"但未文档化。
- **`@auto` 语义**：是 spec 内 design 引用 vs 实现的鸿沟典型——spec 把"照搬 design.md §4.3 示例"当作澄清，但 design.md 自身未把 `@auto` 行为写实；类似的 design ↔ spec ↔ 实现链路应在未来 spec template 加"design 引用项展开"自审。

## Verdict

**REVISION REQUIRED**（MUST FIX 数 = 2）

理由：
- v2 SHOULD FIX 6 条复检：5 CLOSED + 1 PARTIAL（SHOULD #5 HTTPException 路径 truncation 缺失 → MUST FIX #2）
- 3 条偏离 spec：全部接受（MVP single-input / T-7c deferred / 本机 MinIO 403）
- 13 AC 实现对照：11 PASS + 1 PARTIAL（AC-12 self_check 与 spec 命令 drift → SHOULD #3）；AC-1~AC-11 实现均落到位
- **2 个 MUST FIX 阻塞 APPROVED**：
  - MUST #1 PyYAML 未声明直接依赖：影响生产部署完整性
  - MUST #2 HTTPException error truncation 未生效：违 spec R-5 承诺
- 6 条 SHOULD FIX 集中在 error 路径鲁棒性 + 事务边界 + spec 语义 drift；建议在 v2 修订或显式 deferred 到 stage 5/follow-up
- 9 条 NICE TO HAVE 不阻塞

stage 4 reviewer 建议 generator 进入 v2 修订；不接受 self-attest skip MUST FIX。

## 复检指引（REVISION REQUIRED）

stage 3 generator 修 v2 后请按顺序复检：

1. **MUST #1 PyYAML 依赖**：
   ```bash
   grep -E "PyYAML|pyyaml" apps/api/pyproject.toml   # 期望命中
   uv lock --check                                    # 期望 0
   uv run python -c "import yaml; print(yaml.__version__)"  # 期望打印 6.x
   ```

2. **MUST #2 HTTPException 截断**：
   ```bash
   grep -E 'getattr\(exc.*detail.*exc\)\)?\[:500\]|str\(.*detail.*\)\[:500\]' apps/api/dataplat_api/runner/orchestrator.py
   # 等价 dry-test：
   uv run python -c "
   from fastapi import HTTPException
   exc = HTTPException(status_code=404, detail={'detail': 'p@1 不存在', 'available': ['x@1','y@2'] * 100})
   err = str(getattr(exc, 'detail', exc))[:500]
   assert len(err) <= 500
   print('OK', len(err))
   "
   ```

3. **SHOULD FIX 6 条**：作者在 coding_report v2 §"已知未解决问题" 显式列每条的 deferred 决策或修复状态；特别 SHOULD #1（cache_key 错路兜底）应在本 stage 4 闭环（涉及 migration / ORM）。

4. **整套 quality gate 复跑**：
   ```bash
   cd apps/api && uv run ruff check dataplat_api && uv run mypy dataplat_api
   cd apps/api && uv run pytest -q tests/test_pipeline_schemas.py tests/test_pipeline_dag.py tests/test_pipeline_cache.py tests/test_processor_runner_backcompat.py tests/test_pipeline_orchestrator.py
   bash scripts/_self_check.sh pipeline-orchestrator-mvp
   ```

5. **本 review 文件不被作者修改**（reviewer-agent.md §2 硬约束）；作者修 coding 后写 `coding_report_v2.md` + spawn `claude-agent:pipeline-orchestrator-mvp-20260518-stage4-reviewer-v2` 复检。
