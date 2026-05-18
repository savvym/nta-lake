---
change_id: pipeline-orchestrator-mvp-20260518
target: tasks.md
target_version: 2
review_version: 2
reviewer: claude-agent:pipeline-orchestrator-mvp-20260518-stage2-reviewer-v2
reviewed_at: 2026-05-18T07:00:00Z
verdict: APPROVED
---

# Tasks Review v2

## v1 MUST FIX 复检

| # | v1 issue | 状态 | 证据 |
|---|---|---|---|
| 1 | T-5 描述 `config_hash=compute_cache_key 的 config 部分 sha256`（compute_cache_key 不暴露 config 部分） | **CLOSED** | (a) T-4 暴露 `_canonical_config_hash(config: dict) -> str`（tasks.md:56）；(b) T-5c 描述显式 `config_hash=_canonical_config_hash(node.config)` 并明示"禁止直接用 cache_key"（tasks.md:84-85）；(c) T-7a 加 `canonical_config_hash_neq_cache_key`（v2 防 regress 测试，tasks.md:136）；(d) 原误导措辞 `compute_cache_key 的 config 部分` 已删除（reviewer 实跑 `grep -E "compute_cache_key 的 config 部分" tasks.md` 退码 1） |
| 2 | demo recipe 首节点 = raw-upload Adapter，但 orchestrator 只跑 Processor → e2e AC 死锁 | **CLOSED via 选 (a)** | (a) T-8 demo recipe 描述改"首节点 markdown-normalize；inputs `bronze/<owner>/<name>@main`（节点不含 raw-upload；bronze 由 e2e fixture 预 seed）"（tasks.md:164）；(b) T-7c fixture 描述"用 raw-upload Adapter 单独 POST /ingest 产 bronze commit；不在 recipe 节点里"（tasks.md:158）；(c) AC-11 反向 grep `! grep -qE "^\s*processor:\s*raw-upload"` 两份 recipe 文件（spec.md:88）；(d) spec.md §非范围加 "Recipe 节点编排 Adapter（v2 补）→ follow-up `pipeline-adapter-node-*`"（spec.md:70）；(e) reviewer 实跑 `grep -E "raw-upload" tasks.md` 仅命中 fixture seed 描述与 v2 修订说明，非 demo recipe 节点 |

（tasks_review_v1 的 SHOULD FIX 1/2/3/4/5/6 在 tasks v2 同步关闭；详 §SHOULD FIX 复检小节。）

### tasks_review_v1 SHOULD FIX 复检

| # | v1 SHOULD issue | 状态 | 证据 |
|---|---|---|---|
| 1 | T-5/T-7 粒度过粗 | CLOSED | T-5 拆 T-5a~T-5e（sig + 入口校验 + cache miss + cache hit + error 五段，tasks.md:61-110）；T-7 拆 T-7a~T-7c（单元 + orchestrator branch + e2e，tasks.md:131-160）；T-6 拆 T-6a/b/c；总任务数 22（v1 = 14），`grep -cE "^## T-" tasks.md = 22` reviewer 实跑确认 |
| 2 | ORM 缺 `input_commits_json` / `cache_key` 字段 | CLOSED | T-2 PipelineNodeRunORM 加 `input_commits_json JSONB NOT NULL` + `cache_key str(64) NOT NULL`（tasks.md:37）；migration 0004 同步加索引 `pipeline_node_runs.cache_key idx`（tasks.md:41）；T-7b `test_cache_hit_writes_audit_fields` 验非空 |
| 3 | R-1 引用 test_processor_runner_smoke 但 T-7 未列 | CLOSED | T-7a 显式列 `tests/test_processor_runner_backcompat.py`（≥ 1，v2 SHOULD #3）包含 `test_processor_runner_smoke`（tasks.md:137）；spec R-1 缓解栏同步引用（spec.md:114） |
| 4 | parse_input_ref 仅模块辅助，无 field_validator | CLOSED | T-1 加 `@field_validator("inputs", mode="after")` / `@field_validator("output")` / `@field_validator("processor")`（tasks.md:26-27）；T-7a 加 `invalid_input_ref_raises_validation_error` + `invalid_output_ref_raises_validation_error`（tasks.md:134） |
| 5 | T-5 异常类型未细化（HTTPException 在 worker 上下文丢 detail） | CLOSED | T-5e 拆出 error 分支并明示 `catch (HTTPException, Exception)` 双路：`HTTPException → error=str(getattr(exc, "detail", exc))`；其他 `error=repr(exc)[:500]`（tasks.md:106-108）；T-7b 加 `test_node_400_marks_failed` / `test_node_unknown_error_marks_failed`（tasks.md:150-151） |
| 6 | POST body Union 类型丑 | CLOSED | T-6a JSON 入口 + T-6b YAML 入口（`POST /pipelines/runs:from-yaml`）双入口拆分（tasks.md:115, 122） |

## 检查清单结论

> 引用 `.harness/skills/expert-reviewer/SKILL.md` §1 plan-mode tasks 4 条 + `.harness/skills/request-analysis/SKILL.md` "跨 AC 一致性自审清单" 第 7 条 process_tasks 6 条。

| # | 项 | 结论 | 备注 |
|---|---|---|---|
| SKILL §1 tasks.1 | 每个任务粒度合理（1-3 小时） | PASS | T-5 / T-7 / T-6 已拆细：T-5a~e 五个、T-6a~c 三个、T-7a~c 三个；reviewer 估每任务 1-3h 范围内（T-7c e2e 可能略超但属合理；e2e 难拆得更细） |
| SKILL §1 tasks.2 | depends_on 形成 DAG，无环 | PASS | 依赖图（tasks.md:212-243）：T-1/T-2/T-3 → T-5b → T-5c/T-5d → T-5e → T-6a → T-6b/T-6c；T-4 → T-5c/T-5d；T-5a → T-5c；T-7a → T-1/T-3/T-4/T-5a；T-7b → T-5c/T-5d/T-5e/T-6c；T-7c → T-7b/T-8；T-8 → ALL；T-9~T-14 process_tasks；reviewer 手动追溯无环 |
| SKILL §1 tasks.3 | 评审 / 单测 / CI 阶段对应任务存在 | PASS | T-9 (stage-2) / T-10 (stage-4) / T-11 (stage-6) / T-12 (stage-7) / T-13 (stage-9) / T-14 (stage-10) 六条完整；reviewer 实跑 `grep -cE "estimated_stage: stage-(2\|4\|6\|7\|9\|10)" tasks.md = 6` |
| SKILL §1 tasks.4 | 没有"做完整个系统"类目标性任务 | PASS | 拆细后每个 T 描述聚焦单一可交付物（sig / 入口校验 / cache miss / cache hit / error / JSON 路由 / YAML 路由 / jobs dispatch / 单元 / branch / e2e / demo + lint） |
| AC 自审 §7 | process_tasks 6 条 stage-2/4/6/7/9/10 | PASS | 6/6 |
| 任务 ↔ AC 矩阵覆盖 | 每条 AC ≥1 非 process_tasks 任务覆盖 | PASS | tasks.md §AC 覆盖矩阵列 13 AC × ≥1 任务（tasks.md:247-261）；reviewer 实查无遗漏 AC |

## 问题列表

### MUST FIX

无。

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | tasks.md T-5d "调 `RefService.update_ref`" | **RefService.update_ref 当前不存在**：reviewer 实查 `apps/api/dataplat_api/services/ref.py:16` `class RefService` 当前**仅**暴露 `get_by_name`；既有 ref upsert 逻辑实际嵌在 `CommitService.create_commit` (commit.py:192-209)。stage 3 coder 按字面照搬会撞 AttributeError。 | T-5d 改为二选一：(a) 同步在 RefService 新增 `upsert_ref(session, repo_id, name, commit_hash)` helper（把 CommitService 内联逻辑抽公共）并在 T-5d 任务体描述这一同步抽取；(b) 显式说 "T-5d 内 orchestrator 调既有 `CommitService` 的 ref upsert 抽出的私有 `_upsert_ref` 静态方法" 或 "T-5d 在 orchestrator 内 inline 一段 `select + add/update` ref 逻辑"。建议 (a)，便于后续 race 优化时单点修改 |
| 2 | tasks.md T-6c `run_pipeline_job` 描述 | **`mark_failed` 来源未引**：T-6c 写 "swallow exception → `mark_failed`"，但 `mark_failed` 函数 / 方法路径未指明（`JobsService.mark_failed` 还是 `jobs.tasks.mark_failed`？）；与既有 rq-worker-skeleton change 风格保持一致即可，但 stage 3 implementer 需自行考古。 | T-6c 显式引 "`from dataplat_api.jobs.service import JobsService; await JobsService.mark_failed(job_id, error_text)`" 或对应路径；预跑一次防 stage 4 review 打回 |
| 3 | tasks.md T-7c | **fixture 预 seed bronze 路径**写得抽象："fixture 预 seed bronze（用 raw-upload Adapter 单独 POST /ingest 产 bronze commit；不在 recipe 节点里）"——但 e2e 测试中 fixture 是 `conftest.py` 级别还是测试函数内 `@pytest.fixture` 局部？是否需新建 `tests/conftest_pipeline.py`？coder 自由发挥的空间大。 | T-7c 加一行约束："fixture 命名 `bronze_seeded_repo`，作用域 function；用既有 `test_client` 调 `POST /ingest`；返回 `(repo_id, bronze_commit_hash)`"；或引用某个既有 e2e 测试作为参考 |
| 4 | tasks.md T-2 / T-7b | **T-2 PipelineNodeRunORM `cache_key NOT NULL`** 但 T-5e error 分支描述 "input_commits_json=...\|null, cache_key=...\|null"（tasks.md:108），含 `\|null`——若 NOT NULL 则 error 路径 INSERT 会 IntegrityError。 | 二选一：(a) T-2 PipelineNodeRunORM `cache_key str(64) NULL`（即允许 NULL，仅 succeeded 节点必填）；(b) T-5e error 分支保证总能算 cache_key（在节点开始时就计算并缓存，error 也写）。建议 (b)，审计更完整；同步更新 T-5e 描述 |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | tasks.md T-2 `recipe_name` vs `recipe_json` | 字段语义关系未注释（冗余索引还是主名） | 注释 "recipe_name = recipe_json.name 冗余字段（便于 SQL 索引 / 报表查询）" |
| 2 | tasks.md process_tasks T-9~T-14 | 缺 `estimated_hours` | 加 `estimated_hours: 0.5-1` 每条 |
| 3 | tasks.md §依赖图 ASCII | 视觉略乱，箭头方向不统一 | 改为 mermaid 或两层水平排版 |
| 4 | tasks.md T-3 `build_node_deps` 归属 | dag.py 内函数但调 schemas.pipeline.parse_input_ref；耦合方向 dag → schemas（向下层调，OK） | 现状可接受；如未来 schemas → dag 反向 import 出现，则需把 parse_* 与 build_node_deps 同模块 |
| 5 | tasks.md T-7b 用例计数 | 列 10 用例但 ≥ 7（用例多于规约下限）；AC-12 ≥ 12 全部测试合计需 ≥ 12，当前 T-7a 4+3+4+1 = 12，T-7b 10，T-7c 1 → 总 23，远超 ≥ 12 | OK；如未来按需删减需更新 AC-12 |

## Verdict

**APPROVED**（MUST FIX 数 = 0）

理由：
- v1 全部 2 MUST FIX 真闭环：config_hash 来源经 T-4 helper + T-5c 引用 + T-7a 防 regress 三道防线；demo recipe 路径选 (a)，不引入 adapter 节点扩 scope
- v1 全部 6 SHOULD FIX 真闭环（粒度 / ORM 字段 / R-1 测试 / field_validator / 异常细化 / YAML 入口）
- v2 任务粒度合理：22 任务（实现 16 + process_tasks 6），每个聚焦单一可交付物
- 依赖 DAG 无环；AC 覆盖矩阵 13×≥1 全覆盖
- 4 条 SHOULD FIX 建议 stage 3 前快速澄清（特别 #1 RefService.update_ref 命名、#4 cache_key NOT NULL ↔ error 路径冲突）；不阻塞 verdict

## 复检指引

stage 3 编码前作者可自检：

1. **MUST FIX 全闭环 reverify**：
   ```bash
   grep -E "_canonical_config_hash" .harness/changes/pipeline-orchestrator-mvp-20260518/request_analysis/tasks.md  # 期望 ≥ 3 行命中（T-4 定义 + T-5c 调用 + T-7a 测试）
   set +H  # 防 ! 被 history expansion 吃
   ! grep -qE "compute_cache_key 的 config 部分" .harness/changes/pipeline-orchestrator-mvp-20260518/request_analysis/tasks.md  # 应退码 1（grep 未命中），! 取反 = 0
   ! grep -qE "^\s*processor:\s*raw-upload" .harness/changes/pipeline-orchestrator-mvp-20260518/request_analysis/tasks.md  # demo recipe 节点不含 raw-upload as processor
   ```

2. **任务粒度不退化**：
   ```bash
   grep -cE "^## T-" .harness/changes/pipeline-orchestrator-mvp-20260518/request_analysis/tasks.md  # 期望 ≥ 18（v2 = 22）
   grep -cE "estimated_stage: stage-(2|4|6|7|9|10)" .harness/changes/pipeline-orchestrator-mvp-20260518/request_analysis/tasks.md  # 期望 = 6
   ```

3. **SHOULD #1 RefService.update_ref 命名澄清**：建议在 stage 3 开始前用 5 分钟决策"抽 RefService.upsert_ref helper"还是"orchestrator 内 inline"，避免 coder 撞墙后回退 stage 1。

4. **SHOULD #4 cache_key NOT NULL ↔ error 路径**：决策 cache_key 字段是否 NULLABLE；建议在 T-2 schema 阶段就锁定，避免 migration 0004 改了一遍又一遍。

进入 stage 3 后 coder 按 T-1 → T-2 → T-3 → T-4 → T-5a → T-5b → T-5c/T-5d 并行 → T-5e → T-6a → T-6b/T-6c → T-7a/T-7b → T-8 → T-7c 顺序推进；每个 T 完成后 commit + update tasks.md 状态。
