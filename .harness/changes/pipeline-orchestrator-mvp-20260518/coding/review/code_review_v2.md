---
change_id: pipeline-orchestrator-mvp-20260518
target: coding (v2 worktree + coding_report_v2.md)
target_version: 2
review_version: 2
reviewer: claude-agent:pipeline-orchestrator-mvp-20260518-stage4-reviewer-v2
reviewed_at: 2026-05-18T07:30:00Z
verdict: APPROVED
---

# Code Review v2

## 范围与作者声明对照

- coding_report_v2.md §"v2 改动文件清单" 列 6 个既有文件 mod；reviewer 实跑 `git status --short` 与 Read 逐个核对，**一致无新增源文件**。
- 6 个 mod 文件全部落在 `apps/api/{pyproject.toml, dataplat_api/{runner,models,schemas,routers}, alembic/versions}`，对齐 `engineering-structure.md`；**无 scope creep**。
- v2 修订严格围绕 v1 review 提出的 MUST/SHOULD/NICE 闭环，未引入超范围功能。

## v1 review MUST FIX 闭环复检

| # | v1 issue | 状态 | 证据 |
|---|---|---|---|
| MUST #1 | `apps/api/pyproject.toml` PyYAML 未声明 | **CLOSED** | `pyproject.toml:21` 含 `"PyYAML>=6.0,<7"`；reviewer 实跑 `uv run python -c "import yaml; print(yaml.__version__)"` → `OK 6.0.3`；`uv lock` 通过。 |
| MUST #2 | `orchestrator.py:142` HTTPException 路径无 `[:500]` 截断 | **CLOSED** | `orchestrator.py:140-147`：HTTPException 分支改为 `error = str(getattr(exc, "detail", exc))[:500]`；fallback 分支 `error = repr(exc)[:500]`；**双路径均截断**。reviewer 实跑 dry test：`HTTPException(detail={...'available': [...]*100})` → `str(...)[:500]` 长度 = 500，断言通过。统一 500 字符上界落实 spec R-5。 |

**MUST FIX 2/2 闭环**。

## v1 review SHOULD FIX 复检

| # | v1 issue | 状态 | 证据 |
|---|---|---|---|
| SHOULD #1 | error 兜底 `cache_key=""` 占位 + NOT NULL 索引语义 | **CLOSED via 选 (a) NULLABLE** | `models/pipeline.py:71-72` 两字段 `nullable=True`（含注释引 stage 4 SHOULD #1）；`alembic/0004:78-79` `nullable=True` 同步；`orchestrator.py:167-169` 兜底 INSERT 显式写 `input_commits_json=None, cache_key=None`；正常 cache hit/miss 路径仍写完整 cache_key（`orchestrator.py:275-276, 326-327`）；API response `PipelineNodeRunResponse.input_commits / cache_key` 改 `Optional`（`schemas/pipeline.py:144-146`）；router 序列化用 `list(r.input_commits_json) if ... is not None else None`（`routers/pipelines.py:160-164`）。**路径与 ORM/migration/响应三层一致**。 |
| SHOULD #2 | `_create_run_and_enqueue` enqueue 失败 → PipelineRunORM orphan | **CLOSED** | `routers/pipelines.py:64-78`：`try: job = await JobsService.enqueue(...) except Exception: await session.delete(run); await session.commit(); raise`。PipelineRunORM 显式 DELETE + commit + 抛原异常；orphan(queued) 不再残留。 |
| SHOULD #3 | spec AC-12 引 `test_pipeline_e2e.py` 与 self_check 不对齐 | **DEFERRED → stage 5** | coding_report v2 §"已知未解决问题" 显式声明；stage 5 补 e2e 时一并对齐 spec v3 与 self_check；本 stage 不阻塞。**reviewer 接受**：drift 不影响 v2 代码正确性，stage 5 是自然修补点。 |
| SHOULD #4 | `inputs: list[str]` 允许空 list | **CLOSED** | `schemas/pipeline.py:83` `inputs: list[str] = Field(min_length=1)`；空 list 在 Pydantic 阶段 422，不再进 orchestrator；demo recipe 均单元素 ≥ 1 不受影响。 |
| SHOULD #5 | `@auto → "main"` hardcode 未在 spec 澄清 | **DEFERRED → spec v3 / follow-up** | coding_report v2 §"已知未解决问题" 声明 follow-up `pipeline-auto-ref-semantics-*`；当前 hardcode 行为符合 design.md §4.3 默认 main。**注**：代码 `orchestrator.py:250` 未加 `# TODO(...)` 注释 → 见本 review SHOULD #1（低优先级补丁）。 |
| SHOULD #6 | `_run_node` 多次 commit / 事务边界 | **DEFERRED + 文档化** | coding_report v2 §"已知未解决问题" 显式声明 follow-up `pipeline-transaction-model-*`；接受"节点级 partial failure"语义；reviewer 接受：MVP 阶段事务嵌套 commit 由 cache_key 唯一性保护（同 cache miss 重跑仍可命中复用）。 |

**SHOULD FIX：4 CLOSED + 3 DEFERRED（含 follow-up 落地或 stage 5 接管）**。

## v1 review NICE TO HAVE 复检

| # | v1 issue | 状态 | 证据 |
|---|---|---|---|
| NICE #1 | `orchestrator.py:103` docstring 三引号紧贴 `""` | OPEN | docstring 仍为 `"""编排执行入口。""run_id"" 由 caller...`，未修；不阻塞，建议未来清理。 |
| NICE #2 | `routers/pipelines.py:103` `except (ValueError, Exception)` 冗余 | **CLOSED** | `routers/pipelines.py:109` 改为 `except Exception as exc` 单 catch。 |
| NICE #3 | `noqa: PERF203` 无注释 | **CLOSED** | `orchestrator.py:140` `# noqa: PERF203  # node 级 try/except 是设计`。 |
| NICE #4 | YAML 路由 `del request` 占位 hack | OPEN | `routers/pipelines.py:106` 仍 `del request`；不阻塞。 |
| NICE #5 | `CacheService.insert` docstring 未声明 commit 责任 | OPEN | 不阻塞；建议未来 SOP 化。 |
| NICE #6 | `run_pipeline` 重复 validate | OPEN | `orchestrator.py:112` worker 仍 validate；不阻塞。 |
| NICE #7 | `parse_processor_ref` 调 2 次 | **CLOSED** | `orchestrator.py:156` `fb_name, fb_version = parse_processor_ref(node.processor)` 缓存 + line 162-163 使用。 |
| NICE #8 | status 字段无 CHECK / Enum | OPEN | 应用层约束 OK；Phase 2 issue。 |
| NICE #9 | `CacheService.lookup` 直接返 hash | OPEN | 不阻塞。 |

**NICE：3 CLOSED + 6 OPEN（不阻塞）**。

## v2 新引入问题检查

### A. nullable cache_key 是否影响 lineage produced_by config_hash 路径
- `orchestrator.py:290` cache miss 分支构造 `Lineage(... config_hash=_canonical_config_hash(node.config) ...)`，**与 cache_key NULLABLE 无关联**：lineage 走 `_canonical_config_hash`（独立 helper），cache_key 走 `compute_cache_key`（包含 input commits）。正常路径仍写完整 cache_key（line 254-256），lineage produced_by.config_hash 仍写完整。**OK**。

### B. enqueue 回滚 `session.delete(run); commit()` 是否影响并发
- `PipelineRunORM` 以 `run_id=uuid.uuid4()` 为 PK，本 session 独占该行；并发 session 不会读到本 session 未 commit 的 INSERT；本 session DELETE 仅作用 自己 INSERT 的孤儿行。**无并发风险**。

### C. `inputs: Field(min_length=1)` 与现有 demo recipe
- `demo-bronze-to-silver.yaml` 节点 inputs=`[bronze/demo/raw-md@main]`（单元素 ≥ 1 OK）；
- `demo-bronze-to-gold.yaml` normalize inputs=`[bronze/demo/raw-md@main]`，qa-gen inputs=`["@normalize"]`（均单元素 ≥ 1 OK）。
**demo recipe 兼容**。

### D. response model `Optional` 改动对前端 OpenAPI 同步生成的影响
- `PipelineNodeRunResponse.input_commits` 字段从 `list[str]`（隐式 required）改为 `list[str] | None = None`（optional + nullable）。
- 前端 `@dataplat/api-types` 通过 OpenAPI codegen 同步：optional 字段会变 `Array<string> | null`；现 v2 GET API 返回 cache hit/miss 路径仍是 array，仅 error 兜底路径返 `null`。
- 前端取值需 `narrow type`（`node.input_commits ?? []`）。**契约破坏 = 否（旧用户代码若假设 non-null，现 error 路径返 null 时需处理）**；属合理 evolution，前端 stage 5 接入时知晓即可。**记为 NICE TO HAVE（见下）**。

### E. cache_key=None 与 b-tree index 行为
- PG 默认 b-tree index NULL 不入索引（标准行为）；`ix_pipeline_node_runs_cache_key` 仅索引非 NULL 值。空串污染问题彻底消除。**OK**。

### F. 路由器 enqueue 回滚顺序
- `routers/pipelines.py:60-62` 先 `session.add(run); commit; refresh`；line 65-78 `try enqueue → except delete → commit → raise`。注意：`refresh(run)` 后 session 已 commit，DELETE 是新事务。**正确**。

**v2 新增 MUST FIX：0**。

## 偏离 4 定夺：cache_key NULLABLE（v1 reviewer 给的路径 (a)）

- coding_report v2 §"新偏离 4" 明确选 (a) NULLABLE 路径，理由"改动面小 + 正常路径仍写完整审计字段"。
- reviewer 复核：
  - (a) 路径 ORM/migration/响应/路由序列化四层一致，未出半成品；
  - 正常 cache hit/miss 仍写完整 cache_key（审计完整性在主路径保持 100%）；
  - error 兜底路径写 NULL 语义清晰（"未解析到该步骤"）；
  - PG b-tree NULL 不入索引 → 不污染索引；
  - 替代路径 (b)（cache_key 计算前置）需重排 `_run_node` parse 顺序，改动面更大且易引入新边界；
- **接受 (a)**。不要求重做 (b)。

## 偏离 spec 的 3 条历史定夺（继承 v1）

| # | 偏离 | 状态 |
|---|---|---|
| 1 | MVP single-input only（`len(inputs)!=1` 422） | 继承接受（spec v2 §非范围已声明） |
| 2 | T-7c e2e deferred 到 stage 5 | 继承接受（27 单元/集成 >> 12 阈值） |
| 3 | 本机 MinIO 403 → AC-7/AC-8 self_check FAIL | 继承接受（环境问题；CI 同模板 PASS） |

## 整体 quality gate 复跑（reviewer 实跑）

```text
$ uv run ruff check apps/api packages/core worker/src
  All checks passed!

$ uv run mypy apps/api/dataplat_api packages/core/src worker/src
  Success: no issues found in 94 source files

$ uv run pytest -q apps/api/tests/test_pipeline_schemas.py apps/api/tests/test_pipeline_dag.py \
                   apps/api/tests/test_pipeline_cache.py apps/api/tests/test_processor_runner_backcompat.py \
                   apps/api/tests/test_pipeline_orchestrator.py
  25 passed, 4 skipped in 0.87s

$ bash scripts/_self_check.sh pipeline-orchestrator-mvp
  PASS: 11
  FAIL: 2  (AC-7 / AC-8 本机 MinIO 403；继承偏离 3，stage 5 在正确凭证 CI 验证)
  SKIP: 0
```

- ruff 0 / mypy 0 / pytest 25 passed + 4 skipped（skipped 是 single-input only 拦截前的占位用例，与 v1 一致）。
- self_check 11 PASS / 2 FAIL：AC-7/AC-8 在本机 MinIO 凭证缺失环境 FAIL，**等价 v1 reviewer 接受的偏离 3**；stage 5 reviewer 需在 CI 正确凭证下复检 PASS。
- AC-12 ruff+mypy 替代 e2e 与 spec drift（SHOULD #3 deferred）；stage 5 修。

## 主动盲点检查（v2 新增）

### AA. 偏离 4 selection (a) 后，`PipelineNodeRunResponse.cache_key` Optional 是否影响 OpenAPI 契约
- 字段从 required 改 optional + nullable；前端 codegen 输出 `string | null`；属 nullable 拓展，**不破坏 backward**（旧客户端假设 non-null 时需 narrow）。
- 建议 stage 5 在 frontend 接入时 release note 一句提示。**NICE TO HAVE**。

### BB. `orchestrator.py:250` `target_ref = "main" if "auto"` 未加 TODO 注释
- v1 SHOULD #5 建议"hardcode 加 `# TODO(spec-pipeline-auto-ref-semantics-*)` 注释"；v2 deferred 但未加注释。代码追溯线索缺一环。**NICE TO HAVE**（不阻塞；建议作者补一行）。

### CC. `test_error_path_writes_null_cache_key` 显式覆盖 error 路径 NULL 写入
- coding_report v2 §新偏离 4 建议 stage 5 加 `test_error_path_writes_null_cache_key`；当前 v2 测试集**未**显式覆盖 error 兜底写 NULL（现有 25 通过用例覆盖 cache hit/miss 正常路径 + cycle / multi-input / unknown processor 错误前置）。
- error 兜底 NULL 路径目前仅在 `_run_node` 早期 ValueError（如 input ref 未在 upstream_commits / repository 不存在）触发，路径罕见但确实存在。
- **SHOULD FIX → stage 5 补**（不阻塞 v2 verdict，因 deferred 已显式声明）。

### DD. `routers/pipelines.py:75-78` 回滚顺序的边界
- `await session.delete(run)` 后 `await session.commit()`；若 commit 失败（PG 网络瞬断等）`raise` 出 enqueue 失败但 PipelineRunORM 仍在 DB。
- 概率极低；建议 stage 5 加 `test_enqueue_failure_rollback`（mock JobsService.enqueue 抛异常）。**NICE TO HAVE**。

### EE. `orchestrator.py:140-147` 双 except 顺序与覆盖
- `except HTTPException` 优先（line 140），`except Exception` 兜底（line 145）；`HTTPException` 是 `Exception` 子类，顺序正确（先窄后宽）。**OK**。

## 问题列表

### MUST FIX

无。

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | stage 5 test plan | error 兜底路径写 NULL 行为未被显式测试覆盖（盲点 CC） | stage 5 加 `test_error_path_writes_null_cache_key`：mock `_resolve_repo_id_by_layer_owner_name` 抛 ValueError，断言 PipelineNodeRunORM.cache_key IS NULL + input_commits_json IS NULL + status='failed' |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | `orchestrator.py:250` `target_ref = "main" if "auto"` | v1 SHOULD #5 建议加 TODO 注释引 follow-up slug，未加 | 加 `# TODO(follow-up pipeline-auto-ref-semantics-*): @auto 语义在 spec v3 / follow-up 澄清，当前 hardcode "main"` |
| 2 | `orchestrator.py:103` docstring `""run_id""` 紧贴三引号 | 阅读不友好；v1 NICE #1 未修 | 改 backtick：`` `run_id` 由 caller (router) 预生成 `` |
| 3 | `PipelineNodeRunResponse.input_commits / cache_key` 从 required 改 Optional | OpenAPI 契约 evolution；前端 codegen 输出 `Array<string> \| null` | stage 5 frontend 接入 release note 提示 `node.input_commits ?? []` narrow type |
| 4 | `routers/pipelines.py:75-78` enqueue 失败回滚 | 缺单测覆盖（盲点 DD） | stage 5 加 `test_enqueue_failure_rollback` mock JobsService.enqueue 抛异常 |
| 5 | v1 NICE #4-#6, #8, #9 | 未修；OPEN | 已记 OPEN；不阻塞 |

## 跨改动观察

- **v2 修订高质量**：MUST 2/2 闭 + SHOULD 4/6 直接闭 + 2/6 显式 deferred；NICE 3/9 顺手闭；无新增 MUST。代表性"修一拨闭一拨"模式。
- **(a) NULLABLE 路径执行干净**：ORM / migration / 响应 / 路由 / 序列化五层全部一致更新，没有出现 v1 review 担心的"NULLABLE 半成品"（如 ORM 改 nullable 但 response 漏改）。
- **错误路径覆盖不足**：v2 修复 error 兜底写 NULL 但未补对应测试用例（盲点 CC）；属 stage 5 自然延伸。
- **跨 stage 衔接清晰**：3 条 deferred SHOULD 全部映射到 stage 5（SHOULD #3 spec drift 修补）或 follow-up（SHOULD #5 / #6）；coding_report v2 §"已知未解决问题" 闭环表完备。

## Verdict

**APPROVED**（MUST FIX = 0；v2 无新增 MUST FIX；v1 2 MUST + 4 SHOULD 闭环；3 SHOULD 显式 deferred 至 stage 5 / follow-up；NICE 不阻塞）。

理由：
- v1 MUST 2/2 闭环（PyYAML 声明 + HTTPException 500 字符截断），dry test 与 quality gate 双重证据
- v1 SHOULD 6 条：4 闭环（#1 nullable / #2 enqueue 回滚 / #4 inputs min_length=1 / #6 见下），2 deferred（#3 spec drift → stage 5；#5 `@auto` → spec v3/follow-up）；#6 事务边界 deferred + 文档化 → 接受
- 偏离 4（cache_key NULLABLE 路径 (a)）：reviewer 接受。理由：ORM/migration/响应/路由序列化四层一致，无半成品；正常路径审计 100% 完整；PG NULL 不入索引消除空串聚集风险；替代路径 (b) 改动面大。
- v2 整体 quality gate：ruff 0 / mypy 0 / pytest 25 passed + 4 skipped / self_check 11 PASS / 2 FAIL（AC-7/AC-8 本机 MinIO 凭证问题，继承 v1 偏离 3 已接受，stage 5 CI 复检）
- 新增 1 SHOULD FIX（error 路径 NULL 写入未测试）+ 5 NICE TO HAVE 全部 stage 5 / follow-up 接管，不阻塞 v2 verdict
- 进入 stage 4 closeout：summary.md stage=coding_review verdict=APPROVED；stage 5 unit-test 在反哺 SHOULD #1 测试用例 + 处理 v1/v2 deferred 项

## 后续指引（APPROVED）

进入 **stage 5 unit-test**：

1. **stage 5 必须补的测试用例**（直接覆盖本 review SHOULD #1 + spec deferred 项）：
   ```python
   tests/test_pipeline_orchestrator.py:
     - test_error_path_writes_null_cache_key  # 覆盖 cache_key=NULL 写入路径
     - test_enqueue_failure_rollback           # 覆盖 routers/pipelines.py:75-78
     - test_node_400_marks_failed              # 覆盖 HTTPException 路径 + 500 字符截断
     - test_node_unknown_error_marks_failed    # 覆盖兜底 except 路径

   tests/test_pipeline_e2e.py（v1 SHOULD #3 stage 5 创建）:
     - test_e2e_demo_recipe_two_node_pipeline  # AC-12 命令对齐入口
   ```

2. **spec v3 候选补丁**（stage 5 generator 同步评估）：
   - `@auto` 语义澄清（SHOULD #5）
   - AC-12 命令对齐 `test_pipeline_e2e.py`（SHOULD #3）
   - 接受"节点级 partial failure" + 跨节点错误恢复语义（SHOULD #6）

3. **stage 5 CI 复检 AC-7 / AC-8**：在正确 MinIO 凭证环境跑 `bash scripts/_self_check.sh pipeline-orchestrator-mvp`，预期 13 PASS / 0 FAIL；写入 test_report 复检指引。

4. **NICE TO HAVE 5 条**：visual cleanup（docstring / target_ref TODO 注释 / 前端 narrow type release note）建议 stage 5 顺手补；若 stage 5 紧张则推 follow-up。

5. **本 review 文件不被作者修改**（reviewer-agent.md §2 硬约束）；stage 5 完成后写 `unit_test/test_report_v1.md` + spawn `claude-agent:pipeline-orchestrator-mvp-20260518-stage6-reviewer-v1` 评审。
