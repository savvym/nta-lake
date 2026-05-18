---
change_id: pipeline-orchestrator-mvp-20260518
target: spec.md
target_version: 1
review_version: 1
reviewer: claude-agent:pipeline-orchestrator-mvp-20260518-stage2-reviewer-v1
reviewed_at: 2026-05-18T06:15:00Z
verdict: REVISION REQUIRED
---

# Spec Review v1

## 检查清单结论

> 引用 `.harness/skills/expert-reviewer/SKILL.md` §1 plan-mode spec 6 条 + `.harness/skills/request-analysis/SKILL.md` "跨 AC 一致性自审清单" 9 条。

| # | 项 | 结论 | 备注 |
|---|---|---|---|
| SKILL §1.1 | 背景写明了为什么现在做 | PASS | §背景明确"design.md §9 Phase 1 MVP 收官需要端到端 pipeline"且引 §4.3 §5.3 §8 |
| SKILL §1.2 | 问题陈述对外部读者可理解 | PASS | 三条问题：DAG 缺失 / lineage 断裂 / 节点幂等 缺；引用具体文件行号 |
| SKILL §1.3 | 范围 / 非范围都有 | PASS | 13 条 in-scope + 10 条 out-of-scope；each out-of-scope 指明 follow-up change 名 |
| SKILL §1.4 | 验收标准可演示且可机械化 | PARTIAL | 13 AC 全数有一行式命令 + dry-parse 通过；但 AC-7 内容覆盖不完整（见 MUST FIX #2） |
| SKILL §1.5 | 风险有缓解或显式 accept | PARTIAL | 6 条风险，但 R-2 / R-6 缓解 ↔ AC 链路不闭环（见 MUST FIX #2 #1） |
| SKILL §1.6 | 没有把已有架构当新提案 | PASS | 显式引 design.md §4.3 §4.4 §5.3 §8；关键决策表 6 条标"design.md §x" |
| SKILL §1.7 | 待澄清问题已清零或显式 deferred | PASS | 5 项全 `[x]` |
| AC自审 §1 | schema↔hash↔idempotency↔fixture | PASS | cache_key 输入集 = `inputs_commits + processor_name + processor_version + config`，对齐 design.md §5.3 |
| AC自审 §2 | 事务边界三处一致 | PASS | spec 未声明强事务边界（节点级 commit）；无矛盾 |
| AC自审 §3 | AC 一行式可执行 | PASS | 13/13 |
| AC自审 §4 | 风险 ↔ AC 测试列表 | FAIL | R-2 "lineage.env 必落入" 未在 AC-7 列；R-1 引用 test_processor_runner_smoke 不在 T-7 测试清单（见 SHOULD FIX #6） |
| AC自审 §5 | commit 父子链 | PARTIAL | R-6 显式覆盖；但 cache hit 路径下 ref 更新语义未定义（见 MUST FIX #1） |
| AC自审 §6 | 反向 grep + test -f | PASS | 无 `! grep` 模式；AC-4 / AC-7 / AC-11 均带 `test -f` 前置；无 `2>/dev/null` 吞 stderr |
| AC自审 §7 | process_tasks 6 条 | PASS | tasks.md T-9~T-14 完整 stage-2/4/6/7/9/10 |
| AC自审 §8 | AC 命令 dry-parse | PASS | 6 个 `python -c` + 1 个 bash 复合命令本 reviewer 真跑 `compile()` / `bash -n` 全部退码 0 |
| AC自审 §9 | summary.md frontmatter 无占位符 | PASS | 已脱离 `_template/`（change_id / title / owner / started_at 全实值） |

## 问题列表

### MUST FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | spec.md §问题陈述、§验收标准 AC-8、§风险 R-6 | **cache hit 路径下 target_repo ref 更新语义未定义**：spec 说"cache hit → 跳过 ProcessorRunner.run，复用 `pipeline_cache.output_commit_hash`"；但**没说**这一刻 target_repo 的 ref（如 `silver/foo/baz@main`）是否要更新指向那个旧 commit。两种选择都有副作用：(a) 更新 ref → 用户后续用 `repo@main` 拉到的就是上一轮 cache 命中的旧数据，看起来正确；但 `pipeline_node_runs` 没记录"我新更新了 ref 到这个 commit"，审计链不完整。(b) 不更新 ref → 下一个走 `repo@main`（非 `@node-id`）引用 target_repo 的节点会拿到 ref 现在指的 commit（可能是上次失败 / 上次未 cache 路径产生），与 `@node-id` 路径不一致。这是 G 类盲点："cache hit 复用旧 commit 但 pipeline_node_runs 表怎么记 input_commits？审计可恢复性？" | 在 spec.md AC-8 或 R-6 显式增段："cache hit 时 orchestrator MUST/MUST NOT 更新 target_repo ref"。推荐 (a) + 在 `pipeline_node_runs` 加 `input_commits_json text` 字段（T-2 schema 已有 output_commit_hash 但**没有 input_commits**），让审计可恢复 cache_key 输入；并新增 `test_cache_hit_updates_ref` 测试。 |
| 2 | spec.md §验收标准 AC-7、§风险 R-2 缓解栏 | **风险 R-2 缓解 ↔ AC 链路断裂**：R-2 缓解明文写"**lineage.env 必落入** commit.lineage_json"，但 AC-7 只断言 lineage 含 "`produced_by + inputs + run_id`"，**未含 env**。`grep -q "env"` 也不在 AC-7 验证命令中。SKILL §"跨 AC 一致性自审清单"第 4 条直接禁此模式："每条风险若声称'测试覆盖'作缓解，必须在 AC 测试列表里列出对应测试编号；否则缓解措施未落地"。design.md §4.4 lineage 示例字段含 `env: {python, model}`。若不在 MVP 写入 env，必须把 R-2 缓解栏改成"env 字段 deferred；MVP 不写入"；若要写入则 AC-7 必须显式包含。 | 二选一：(a) 改 AC-7 描述加 "+ env"，并把测试 `test_lineage_written_on_cache_miss` 的断言扩到验证 `lineage_json["env"]` 非空（grep 关键字 + pytest assert）；(b) 改 R-2 缓解栏删除 "lineage.env 必落入"，改为"env 字段在本 MVP 不写入；follow-up `lineage-env-field-*` 补"。 |
| 3 | tasks.md T-5 §"未命中"分支构造 Lineage 部分 | **lineage.produced_by.config_hash 来源描述错误**：T-5 写 "`config_hash=compute_cache_key 的 config 部分 sha256`"，但 `compute_cache_key(inputs_commits, processor_name, processor_version, config) -> str` 返回的是**整个 key 的 sha256**，并不暴露"config 部分"。按字面照搬会让实现者要么 (a) 把 cache_key 当 config_hash 写（错：值含 inputs+processor）；(b) 自己另写 canonical(config) → sha256（对，但 T-4 cache.py 没暴露此函数）。这是会污染 design.md §4.4 lineage 字段语义的实现陷阱。 | tasks.md T-4 暴露 `_canonical_config_hash(config: dict) -> str`（或类似 helper），让 T-5 显式调用；并在 spec AC-7 测试增 `assert lineage_json["produced_by"]["config_hash"] != cache_key` 防 regress。 |

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | spec.md §非范围 + §风险 R-5 | **pipeline 失败 / 取消 / 超时语义太薄**：R-5 只覆盖"worker 进程异常退出 → run.status 停留 running" 由 RQ timeout 兜底。但未覆盖：(a) 节点中途抛 HTTPException(400) → orchestrator 怎么向上传？目前 ProcessorRunner.run 直接 raise HTTPException；jobs/tasks.py 的 run_pipeline_job 是同步 wrapper，HTTPException 在 worker 进程里没意义，会被 traceback 吞。(b) 用户调 `DELETE /pipelines/runs/{id}`（取消）—spec 没列此 API 也没显式标 deferred。 | 在 §非范围段显式标 "DELETE /pipelines/runs（取消）→ deferred"；在 R-5 缓解栏补充："节点抛 HTTPException 在 orchestrator 内 catch 转为 PipelineNodeRunORM(status=failed, error=detail)；测试 `test_node_400_marks_failed` 覆盖"；或在 R-3（已覆盖未知 processor/cycle）扩展一条到 AC。 |
| 2 | spec.md §问题陈述 §3 / §风险 全段 | **并发 race：两个 pipeline run 同时往同 `silver/foo/baz@auto` 写**没有任何风险条目讨论。MVP 串行 worker 可能掩盖，但 RQ worker 进程数 > 1 即触发；CommitService.create_commit 内部是否有 ref 行级锁本 spec 未引证。 | 新增 R-7（或并入 R-6）："多 run 并发写同 ref → race"；缓解：MVP accept（worker 单进程）+ 加 follow-up `pipeline-ref-locking-*`；或在 AC 显式 deferred。 |
| 3 | tasks.md T-2 PipelineNodeRunORM 字段 | **审计缺字段**：当前列 `cache_hit / output_commit_hash`，但未列 `input_commits_json`（cache hit 时输入快照丢失，无法重放 cache_key 验真）。配合 MUST FIX #1 一并补。 | 加 `input_commits_json JSONB`；同时考虑 `cache_key str(64)` 字段直接落表，便于 SQL 排查 cache 命中分布。 |
| 4 | tasks.md T-5 / T-7 | **任务粒度过粗**：T-5 同时含 ProcessorRunner sig 改动 + orchestrator 主路径 + cache miss / hit / parent_chain / error 四个分支；T-7 同时含 5 个 test_pipeline_*.py 文件 ≥ 14 用例 + e2e 真起 PG/MinIO/Redis。两者各自远超 1-3 小时。SKILL §1 plan-mode tasks 第 1 条 "每个任务粒度合理（1-3 小时）" 与历史 change 风格不一致（commit-api-mvp 平均 5-6 个 T-*）。 | 将 T-5 拆为 T-5a（ProcessorRunner sig + 兼容性测试）+ T-5b（orchestrator cache miss + lineage 构造）+ T-5c（cache hit + ref 更新策略）；将 T-7 拆为 T-7a（单元 schema/dag/cache）+ T-7b（orchestrator branch tests）+ T-7c（e2e demo）。 |
| 5 | spec.md §AC-7 | **AC-7 测试断言只用 `grep -q "produced_by"` + `grep -q "lineage_json"` 不够强**：grep 命中关键字 ≠ 断言字段真写入。pytest -k lineage 跑了某条用例就 PASS，但断言可能是 `assert lineage is not None`（空跑式）。 | AC-7 验证命令再加一条：从 commit 表读出 `lineage_json`，断言 `json["produced_by"]["name"] == "markdown-normalize"`、`json["inputs"][0]["commit"] == <known hash>`、`json["run_id"] == str(run_id)` 三个具体字段；或在 AC-7 描述中明确指向 `tests/test_pipeline_orchestrator.py::test_lineage_written_on_cache_miss` 用例名 + 该用例的核心断言 grep。 |
| 6 | spec.md §风险 R-1 | **R-1 提及 `test_processor_runner_smoke` 测试用例，但 tasks.md T-7 测试清单未列**。缓解未着陆。 | 把 `test_processor_runner_smoke`（验既有 POST /process 调用不破坏）加进 T-7 `tests/test_pipeline_orchestrator.py` 用例清单，或改放到独立 `tests/test_processor_runner_backcompat.py`。 |
| 7 | tasks.md T-1 module 辅助函数 | **`parse_input_ref` / `parse_output_ref` 仅模块级辅助**，没在 Recipe Pydantic schema 内做 validator 强校验。结果是 schema 通过但 `topo_sort(build_node_deps(recipe))` 期才报错——错误暴露点滞后。 | 加 `@field_validator("inputs", "output")` 验格式（含 `@`、形如 `<layer>/<owner>/<name>@<ref>` 或 `@<node-id>`）；AC-1 测试加 `invalid_input_ref_raises_validation_error` 用例。 |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | spec.md §AC-9 | OpenAPI 仅 grep 路径存在；未验响应 schema 含 `node_runs[]` 字段 | 加 `grep -q "PipelineRunResponse" packages/api-types/openapi.json` 或 OpenAPI dict 字段断言 |
| 2 | spec.md §AC-3 | cache_key 仅测一层 dict canonicalization；未测嵌套 dict / list-in-config | 加 `compute_cache_key(..., {"nested": {"b":2,"a":1}, "list":[3,1,2]})` 顺序断言（注：list 顺序是否纳入 canonical 需先定义） |
| 3 | spec.md §AC-11 demo recipe grep | 仅 grep processor 字面名 `raw-upload` / `markdown-normalize` / `llm-qa-gen`；未验 inputs/output ref 形态 | 增 `grep -q "@auto" recipes/examples/demo-bronze-to-gold.yaml` / `grep -q "@node-id" 形态` |
| 4 | spec.md §背景段尾 | "AdapterRunner 的 lineage=None bug 单独 follow-up" 未指明 follow-up change slug | 起名 `adapter-lineage-bugfix-*` 放进 §非范围段或 summary.md deferred 表 |

## Verdict

**REVISION REQUIRED**（MUST FIX 数 = 3 > 0）

理由：
- MUST FIX #1（cache hit ref 语义）是真实实现路径分歧，将在 stage 3 编码期暴露并回退 stage 1
- MUST FIX #2（R-2 ↔ AC-7 链路断裂）是 SKILL §跨 AC 自审第 4 条直接禁的模式
- MUST FIX #3（config_hash 来源错误）会导致实现者按字面照搬污染 design.md §4.4 lineage 语义

其余 SHOULD FIX 7 项不阻塞 verdict 但建议在 v2 一并修；若 author 选择 deferred，须在 summary.md "Deferred 项" 表写明并加 follow-up change slug。

## 复检指引

作者修完 spec_v2 / tasks_v2 后自检：

1. **MUST FIX #1** 闭环：
   ```bash
   grep -nE "cache hit.*ref|更新 ref|不更新 ref" .harness/changes/pipeline-orchestrator-mvp-20260518/request_analysis/spec.md
   # 期望：在 AC-8 或 R-6 命中至少一行明示策略
   grep -q "input_commits_json" .harness/changes/pipeline-orchestrator-mvp-20260518/request_analysis/tasks.md
   # 期望：T-2 ORM 字段含 input_commits_json
   ```

2. **MUST FIX #2** 闭环（二选一）：
   ```bash
   # 选 (a)：AC-7 描述含 env
   grep -E "AC-7.*env|env.*AC-7|lineage.env" .harness/changes/pipeline-orchestrator-mvp-20260518/request_analysis/spec.md
   # 选 (b)：R-2 缓解栏删除 lineage.env 必落入
   ! grep -q "lineage.env 必落入" .harness/changes/pipeline-orchestrator-mvp-20260518/request_analysis/spec.md
   ```

3. **MUST FIX #3** 闭环：
   ```bash
   grep -E "_canonical_config_hash|canonical_config|config_hash.*helper" .harness/changes/pipeline-orchestrator-mvp-20260518/request_analysis/tasks.md
   # 期望：T-4 暴露 helper；T-5 引用 helper 而非 "compute_cache_key 的 config 部分"
   ```

4. 全量 dry-parse（SKILL §跨 AC §8）：
   ```bash
   grep -oE 'python -c "[^"]+"' .harness/changes/pipeline-orchestrator-mvp-20260518/request_analysis/spec.md | while read cmd; do
     payload=$(echo "$cmd" | sed -E 's|^python -c "||; s|"$||')
     python3 -c "compile(r'''$payload''', '<ac>', 'exec')" || echo "SyntaxError: $cmd"
   done
   ```

提交 v2 后开 `spec_review_v2.md`；reviewer 字段 `claude-agent:pipeline-orchestrator-mvp-20260518-stage2-reviewer-v2`。
