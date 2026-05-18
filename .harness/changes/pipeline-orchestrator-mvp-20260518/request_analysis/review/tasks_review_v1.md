---
change_id: pipeline-orchestrator-mvp-20260518
target: tasks.md
target_version: 1
review_version: 1
reviewer: claude-agent:pipeline-orchestrator-mvp-20260518-stage2-reviewer-v1
reviewed_at: 2026-05-18T06:15:00Z
verdict: REVISION REQUIRED
---

# Tasks Review v1

## 检查清单结论

> 引用 `.harness/skills/expert-reviewer/SKILL.md` §1 plan-mode tasks 4 条 + `.harness/skills/request-analysis/SKILL.md` "跨 AC 一致性自审清单" 第 7 条 process_tasks 6 条。

| # | 项 | 结论 | 备注 |
|---|---|---|---|
| SKILL §1 tasks.1 | 每个任务粒度合理（1-3 小时） | FAIL | T-5 / T-7 远超（见 SHOULD FIX #1） |
| SKILL §1 tasks.2 | depends_on 形成 DAG，无环 | PASS | 显式画依赖图：T-1/T-2/T-3/T-4 → T-5 → T-6 → T-7 → T-8 → T-12 → T-13 → T-14；T-9 独立挂 spec v1；无环 |
| SKILL §1 tasks.3 | 评审 / 单测 / CI 阶段对应任务存在 | PASS | T-9 (stage-2) / T-10 (stage-4) / T-11 (stage-6) / T-12 (stage-7) / T-13 (stage-9) / T-14 (stage-10) 六条完整 |
| SKILL §1 tasks.4 | 没有"做完整个系统"类目标性任务 | PARTIAL | T-5 描述近似"实现整个 orchestrator"；T-7 描述近似"写所有测试"——粒度问题导致 |
| AC 自审 §7 | process_tasks 6 条 stage-2/4/6/7/9/10 | PASS | `grep -cE "estimated_stage: stage-(2\|4\|6\|7\|9\|10)" tasks.md` = 6 |
| 任务 ↔ AC 矩阵覆盖 | 每条 AC 至少一个非 process_tasks 任务覆盖 | PASS | tasks.md §AC 覆盖矩阵列 13 AC × ≥1 任务 = ✓ |

## 问题列表

### MUST FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | tasks.md T-5 §"未命中"分支构造 Lineage 部分 | **lineage.produced_by.config_hash 来源描述错误**（与 spec_review_v1 MUST FIX #3 同源问题，落在 tasks.md 段）：T-5 字面写 "`config_hash=compute_cache_key 的 config 部分 sha256`"。但 T-4 定义的 `compute_cache_key(inputs_commits, processor_name, processor_version, config) -> str` 返回的是整体 sha256，并不暴露"config 部分"。实现者按字面照搬要么 (a) 把 cache_key 直接当 config_hash（错：含 inputs + processor）；(b) 自己另写 canonical(config) → sha256（对，但 T-4 没暴露 helper）。这会污染 design.md §4.4 lineage 字段语义。 | T-4 显式暴露 `_canonical_config_hash(config: dict) -> str`（或 `canonicalize_config(config) -> bytes` + sha256 调用方做）；T-5 改为 "`config_hash=_canonical_config_hash(node.config)`"；T-7 在 `test_pipeline_orchestrator.py::test_lineage_written_on_cache_miss` 加断言 `lineage_json["produced_by"]["config_hash"] != cache_key`。 |
| 2 | tasks.md T-8 demo recipe + T-7 e2e 用例 | **demo-bronze-to-silver.yaml / demo-bronze-to-gold.yaml 首节点为 raw-upload Adapter**（spec.md AC-11 grep `raw-upload`），但 T-5 orchestrator 只跑 Processor（"每节点 ProcessorRegistry.get(name, version) 预检"——AdapterRegistry 不在调用路径）。结果是：(a) demo recipe 加载即 ProcessorRegistry.get('raw-upload', ...) → None → 422；(b) AC-11 grep 验"raw-upload"在文件中存在，AC 通过但 demo 跑不起来；(c) AC-12 `test_pipeline_e2e.py` 跑 demo-bronze-to-silver 必失败。这是会让 stage 3 整个 e2e AC 死锁的实质矛盾。 | 二选一：(a)（推荐，scope 最小）：demo recipe 首节点改为已有 bronze ref → markdown-normalize → silver；inputs[0] 引 `bronze/<owner>/<name>@main`（fixture 预先 seed 一个 bronze commit）；AC-11 grep 改 `markdown-normalize` 等只验 Processor 名；T-7 `test_pipeline_e2e.py` fixture 预跑 raw-upload Adapter 单独 seed bronze。(b)：orchestrator 扩支持 adapter node（需新 T-5 子任务 + 改 RecipeNode schema 加 `kind: adapter\|processor` 字段 + spec 扩 in-scope）—会扩 scope，不推荐 MVP。 |

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | tasks.md T-5 / T-7 | **任务粒度过粗**：T-5 同时含 (a) 改 ProcessorRunner sig (b) 写整个 orchestrator (c) cache miss 分支（含 lineage 构造） (d) cache hit 分支（含 ref 更新策略） (e) error 分支 (f) parent chain 维护。T-7 一次性写 5 个 test 文件 ≥ 14 用例 + e2e 真起 PG/MinIO/Redis worker。每个都远 > 3 小时，违反 SKILL §1 plan-mode tasks 第 1 条。peer change processor-framework v1 也有类似过粗但当时被通过；本 change scope 更大，应拆细以便 stage 3 progress 可追溯。 | 将 T-5 拆为：T-5a ProcessorRunner sig + 既有 /process 回归测试；T-5b orchestrator 入口校验（schema/topo/registry 预检）；T-5c cache miss 分支（含 lineage 构造）；T-5d cache hit 分支（含 ref 更新策略，见 spec MUST FIX #1）；T-5e error / failed 分支。T-7 拆为 T-7a 单元（schema/dag/cache）3 文件、T-7b orchestrator 分支测试、T-7c e2e demo。 |
| 2 | tasks.md T-2 `PipelineNodeRunORM` 字段集 | **审计缺字段**：当前 ORM 含 `cache_hit / output_commit_hash`，但**不含 `input_commits_json`**（cache hit 时丢失输入快照，无法重放 cache_key 验真）；不含 `cache_key` 列（无法 SQL 聚合命中率统计）。配合 spec MUST FIX #1 一并补。 | 加 `input_commits_json JSONB NOT NULL`（cache hit 也得写）+ `cache_key str(64) NOT NULL`（cache hit 也得写）两列；migration 0004 同步加；T-7 测试断言两字段读出非空。 |
| 3 | tasks.md T-7 测试用例清单 | **R-1 引用 `test_processor_runner_smoke` 测试，但 T-7 未列**。spec.md 风险缓解依赖此用例存在；缓解链路断裂。 | 把 `test_processor_runner_smoke`（验既有 POST /process 在 ProcessorRunner.run 加 lineage 参数后回归不破）加进 `tests/test_pipeline_orchestrator.py` 或独立 `tests/test_processor_runner_backcompat.py`；同步 spec AC-5 覆盖测试名加引用。 |
| 4 | tasks.md T-1 Recipe schema | **`parse_input_ref` / `parse_output_ref` 仅模块级辅助**，没在 Recipe / RecipeNode 内做 `@field_validator` 强校验。结果是 Pydantic schema 通过 → topo 阶段才报错，错误暴露点滞后；POST /pipelines/runs 入口 422 错误信息不够具体。 | 在 RecipeNode 加 `@field_validator("inputs", mode="after")` 和 `@field_validator("output")` 调 parse_* 校验格式（含 `@`、形如 `<layer>/<owner>/<name>@<ref>` 或 `@<node-id>`）；T-7 `test_pipeline_schemas.py` 加 `invalid_input_ref_raises_validation_error` 用例（≥1）。 |
| 5 | tasks.md T-5 step 4 "节点异常" 分支 | **异常类型未细化**：ProcessorRunner.run 当前会 raise HTTPException(400)（apps/api/.../processor_runner.py:108）。orchestrator 在 worker subprocess 里 catch HTTPException 然后写 PipelineNodeRunORM(status=failed)——HTTPException 在 worker 上下文里没意义（无 FastAPI request scope），detail 字段提取易丢。 | T-5 异常分支描述改为："catch (HTTPException, Exception) 两路；HTTPException → error=str(exc.detail)；其他 → error=repr(exc)[:500]"；T-7 加 `test_node_400_marks_failed` / `test_node_unknown_error_marks_failed` 两用例。 |
| 6 | tasks.md T-6 POST handler `body` 类型 | `body: {recipe: Recipe \| str(yaml)}` 联合类型在 FastAPI 自动生成 OpenAPI 较丑（discriminated union 需额外配置） | 推荐拆 `POST /pipelines/runs` 接 JSON `RecipeCreateRequest{recipe: Recipe}` + 单独 `POST /pipelines/runs:from-yaml` 接 `text/yaml` 文本入口；或保留单入口但用 `recipe: Recipe \| Annotated[str, ...]` 配 discriminator。 |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | tasks.md T-2 `PipelineRunORM.recipe_json` vs `recipe_name` | 两字段未说语义关系（recipe_name 是冗余索引还是主名？） | 注释 "recipe_name = recipe_json.name 冗余字段（便于 SQL 索引查询）"；或去掉 recipe_name |
| 2 | tasks.md T-9 ~ T-14 | 6 条 process_tasks 都标 estimated_stage 但没标 estimated_hours | 加 `estimated_hours: 0.5-1` 每条，便于全 change 工时估算 |
| 3 | tasks.md §任务依赖图 ASCII | 图右下挂的 │ 没有真正连到 T-9~T-14，视觉容易误读 | 改为分两层：实现层（T-1~T-8）+ 流程层（T-9~T-14）；或 mermaid |
| 4 | tasks.md T-3 `build_node_deps` | 函数同时存在于 T-3 描述中但归属归 dag.py；T-1 schema.py 里 `parse_input_ref` 与之耦合 | 注明 `build_node_deps` 调 `schemas.pipeline.parse_input_ref`；或把它移到 schemas/pipeline.py 与 parse_* 同模块 |

## Verdict

**REVISION REQUIRED**（MUST FIX 数 = 2 > 0）

理由：
- MUST FIX #1（config_hash 来源错误）与 spec MUST FIX #3 同源；实现者按字面照搬 tasks.md 即破坏 design.md §4.4 lineage 语义
- MUST FIX #2（demo recipe 首节点是 Adapter 但 orchestrator 只跑 Processor）是会让 stage 3 e2e AC 整体死锁的实质矛盾——非范围里也没声明本 change 包含 Adapter 编排

其余 SHOULD FIX 6 项建议在 v2 一并修；其中 #1（粒度）/ #2（ORM 字段缺）若 deferred 须 summary.md 写明 + 起 follow-up slug。

## 复检指引

作者修完 tasks_v2 后自检：

1. **MUST FIX #1** 闭环：
   ```bash
   grep -E "_canonical_config_hash|canonicalize_config" .harness/changes/pipeline-orchestrator-mvp-20260518/request_analysis/tasks.md
   # 期望：T-4 暴露 helper；T-5 引用 helper
   ! grep -E "compute_cache_key 的 config 部分" .harness/changes/pipeline-orchestrator-mvp-20260518/request_analysis/tasks.md
   # 期望：原误导措辞已删（注：此命令在 bash 内 `!` 是 history expansion，需在 shell function / script 内或前缀 `set +H`）
   ```

2. **MUST FIX #2** 闭环（demo recipe）：
   ```bash
   # 选 (a) 推荐：demo 不再以 raw-upload 为节点 processor
   ! grep -E "^\s*processor:\s*raw-upload" .harness/changes/pipeline-orchestrator-mvp-20260518/request_analysis/tasks.md
   # 同时 spec AC-11 grep 必须同步删 "raw-upload"
   ! grep -E "raw-upload" .harness/changes/pipeline-orchestrator-mvp-20260518/request_analysis/spec.md
   # 选 (b)：orchestrator 扩支持 adapter node（需 spec 同步扩 scope）
   grep -E "adapter|Adapter" .harness/changes/pipeline-orchestrator-mvp-20260518/request_analysis/tasks.md
   ```

3. **SHOULD FIX #1** 闭环（任务粒度）：
   ```bash
   grep -cE "^## T-" .harness/changes/pipeline-orchestrator-mvp-20260518/request_analysis/tasks.md
   # 期望：≥ 18（拆细后；当前 14）
   ```

4. **SHOULD FIX #2** 闭环（ORM 字段）：
   ```bash
   grep -q "input_commits_json" .harness/changes/pipeline-orchestrator-mvp-20260518/request_analysis/tasks.md
   grep -q "cache_key" .harness/changes/pipeline-orchestrator-mvp-20260518/request_analysis/tasks.md
   ```

5. process_tasks 6 条 stage-2/4/6/7/9/10 不退化：
   ```bash
   grep -cE "estimated_stage: stage-(2|4|6|7|9|10)" .harness/changes/pipeline-orchestrator-mvp-20260518/request_analysis/tasks.md
   # 期望：≥ 6
   ```

提交 v2 后开 `tasks_review_v2.md`；reviewer 字段 `claude-agent:pipeline-orchestrator-mvp-20260518-stage2-reviewer-v2`。
