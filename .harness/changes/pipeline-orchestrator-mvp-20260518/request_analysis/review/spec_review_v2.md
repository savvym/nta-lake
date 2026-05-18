---
change_id: pipeline-orchestrator-mvp-20260518
target: spec.md
target_version: 2
review_version: 2
reviewer: claude-agent:pipeline-orchestrator-mvp-20260518-stage2-reviewer-v2
reviewed_at: 2026-05-18T07:00:00Z
verdict: APPROVED
---

# Spec Review v2

## v1 MUST FIX 复检

| # | v1 issue | 状态 | 证据 |
|---|---|---|---|
| 1 | cache hit ref 语义未定义 + ORM 缺 `input_commits_json` 字段；审计不可恢复 | **CLOSED** | (a) spec §问题陈述 §3.4（v2 补）显式提"审计可恢复性缺失"；(b) AC-8 三断言：`ProcessorRunner.run.call_count == 0` / target_repo ref 更新到 cache 命中 commit / `pipeline_node_runs.input_commits_json + cache_key` 非空（spec.md:85）；(c) R-6 标题改为"commit 父子链断裂 + cache hit 路径下 target_repo ref 更新语义未定义"，缓解栏明示 (a)(b)(c) 三策略（spec.md:119）；(d) tasks.md T-2 PipelineNodeRunORM 加 `input_commits_json JSONB NOT NULL` + `cache_key str(64) NOT NULL`（tasks.md:37）；(e) tasks.md T-5d 实现描述含 "MUST 更新 target_repo 的 output ref" + INSERT 写入两字段（tasks.md:97-98）；(f) T-7b 加 `test_cache_hit_updates_ref` / `test_cache_hit_writes_audit_fields`（tasks.md:145-146） |
| 2 | R-2 缓解写"lineage.env 必落入"但 AC-7 不验 env（链路断裂） | **CLOSED via 选 (b)** | R-2 缓解栏（spec.md:115）改写为"env 字段在本 MVP 不写入 commit.lineage_json，由 follow-up `lineage-env-field-*` 补；本风险的 env 维度审计能力 deferred"；AC-7（spec.md:84）维持 `produced_by + inputs + run_id` 三字段并明示"env 字段 deferred 不验"；§非范围（spec.md:69）显式加"lineage.env 字段写入（v2 补）"+ follow-up slug；§v2 修订说明（spec.md:15）一致 |
| 3 | tasks.md T-5 "config_hash=compute_cache_key 的 config 部分" 措辞错误 | **CLOSED** | tasks.md T-4 加 `_canonical_config_hash(config: dict) -> str` helper（tasks.md:56）；T-5c 描述 `config_hash=_canonical_config_hash(node.config)` 并明示"禁止直接用 cache_key"（tasks.md:84-85）；spec R-3 缓解栏新增约束"`lineage.produced_by.config_hash` 来源约束：必须调 T-4 暴露的 `_canonical_config_hash(config)`"（spec.md:116）；tasks T-7a 加 `canonical_config_hash_neq_cache_key`（防 regress 测试，tasks.md:136） |

（spec_review_v1 的 SHOULD FIX 1/2/3/5/6 在 spec v2 同步关闭；SHOULD FIX 4/7 在 tasks v2 关闭，详 tasks_review_v2。）

## 检查清单结论

> 引用 `.harness/skills/expert-reviewer/SKILL.md` §1 plan-mode spec 6 条 + `.harness/skills/request-analysis/SKILL.md` "跨 AC 一致性自审清单" 9 条。

| # | 项 | 结论 | 备注 |
|---|---|---|---|
| SKILL §1.1 | 背景写明了为什么现在做 | PASS | §背景明确"design.md §9 Phase 1 MVP 收官"；引 §4.3 §5.3 §8 |
| SKILL §1.2 | 问题陈述对外部读者可理解 | PASS | 4 条问题（v2 加 #4 审计可恢复性）；含具体文件行号 `processor_runner.py:130` `adapter_runner.py:109`（reviewer 独立验证：两行号属实） |
| SKILL §1.3 | 范围 / 非范围都有 | PASS | 13 AC + 11 条非范围（v2 加 lineage.env / Recipe 节点编排 Adapter）；each out-of-scope 有 follow-up slug |
| SKILL §1.4 | 验收标准可演示且可机械化 | PASS | 13 AC 全数有一行式命令；7 个 `python -c` reviewer 真跑 `compile()` 全 0；bash 复合 `! grep` 配 `test -f` 前置无沉默通过风险 |
| SKILL §1.5 | 风险有缓解或显式 accept | PASS | 7 条风险（v2 加 R-7）；R-2 R-6 ↔ AC 链路 v2 已修复；R-7 显式标 deferred + `pipeline-ref-locking-*` follow-up |
| SKILL §1.6 | 没有把已有架构当新提案 | PASS | §引用列 design.md §1.1 §3 §4.3 §4.4 §5.3 §8 §9 + 5 个 prior change；关键决策表 6 条 |
| SKILL §1.7 | 待澄清问题已清零或显式 deferred | PASS | 5 项全 `[x]` |
| AC自审 §1 | schema↔hash↔idempotency↔fixture | PASS | cache_key 输入集 `inputs_commits + processor_name + processor_version + config`（对齐 design.md §5.3）；fixture seed 路径走既有 POST /ingest，AC-11 反向 grep 配 test -f 不留沉默通过 |
| AC自审 §2 | 事务边界三处一致 | PASS | 节点级 commit；orchestrator 不引强事务跨节点；T-5e error 分支 INSERT failed + UPDATE run failed 同 session 同步 |
| AC自审 §3 | AC 一行式可执行 | PASS | 13/13 |
| AC自审 §4 | 风险 ↔ AC 测试列表 | PASS | R-1 → AC-5 + T-7a backcompat；R-2 → 决策表 + follow-up；R-3 → AC-1 AC-2 + T-7b 三错误路径；R-4 → AC-11 + e2e；R-5 → T-7b test_node_400 / unknown_error；R-6 → AC-8 三断言 + T-7b test_parent_chain；R-7 → 显式 deferred |
| AC自审 §5 | commit 父子链 | PASS | R-6 缓解栏 (a) cache miss 路径靠 ProcessorRunner.ref→parent 自动接链；(b) cache hit 路径 ref upsert；T-7b test_parent_chain 兜底 |
| AC自审 §6 | 反向 grep + test -f | PASS | AC-11 唯一 `! grep` 模式：`! grep -qE "^\s*processor:\s*raw-upload"` 前接 `test -f recipes/examples/demo-bronze-to-{gold,silver}.yaml` 两条，无沉默通过；AC-7 `grep -qE 'produced_by.{0,8}name\|lineage_json\[.produced_by.\]'` 提供两种字段访问写法兼容（grep 正则中 `[.produced_by.]` 在字符类内点 = 任意字符，仍能命中 `lineage_json["produced_by"]`、`lineage_json['produced_by']`、`lineage_json.produced_by` 等；正则虽稍宽但覆盖目的，可接受） |
| AC自审 §7 | process_tasks 6 条 | PASS | tasks.md T-9~T-14 完整 stage-2/4/6/7/9/10；`grep -cE "estimated_stage: stage-(2\|4\|6\|7\|9\|10)" tasks.md = 6` reviewer 实跑确认 |
| AC自审 §8 | AC 命令 dry-parse | PASS | 7 个 `uv run python -c` reviewer 独立用 `compile(payload, '<ac>', 'exec')` 全部退码 0；AC-11/AC-13 bash 复合用 `bash -n` 验证 syntax 0 |
| AC自审 §9 | summary.md frontmatter 无占位符 | PASS | summary.md 已脱离 `_template/`；change_id / title / owner / started_at 全实值（注：summary.md owner=`application-owner-agent` 是 owner 字段非 reviewer 字段，不被 reviewer-lint 黑名单覆盖；本 review reviewer 字段合规） |

## 问题列表

### MUST FIX

无。

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | spec.md §R-6 缓解栏 / tasks.md T-5d | **RefService.update_ref 实际不存在**：T-5d 写"调 `RefService.update_ref(target_repo_id, output_ref_name, hit_commit_hash)`（沿用既有 ref upsert 逻辑）"，但 reviewer 实查 `apps/api/dataplat_api/services/ref.py:16` `class RefService` 当前**仅**暴露 `get_by_name`；既有 ref upsert 逻辑实际嵌在 `CommitService.create_commit`（services/commit.py:192-209）。stage 3 实现者会被命名误导。 | tasks.md T-5d 改"调 `RefService.upsert_ref(session, target_repo_id, output_ref_name, hit_commit_hash)`（本 change 在 T-5d 同步在 RefService 加 upsert_ref helper，把 CommitService 内联的 ref upsert 逻辑抽公共）"；或改"直接 `INSERT ... ON CONFLICT DO UPDATE` 在 orchestrator 内"。不阻塞 spec/tasks，建议 v3 同步澄清。 |
| 2 | spec.md AC-12 命令尾段 | **命令链 cwd 副作用**：`[ "$(cd apps/api && ... \| grep -cE ...)" -ge 12 ] && cd apps/api && uv run ruff check dataplat_api && uv run mypy dataplat_api`——`[ ... ]` 内 `$()` 子 shell 不污染外层 cwd，OK；外层 `cd apps/api && uv run ruff && uv run mypy` 三条 `&&` 链 cwd 一致也 OK。但若用户在 `scripts/_self_check.sh` 内复用，应包裹 `(cd apps/api && ...)` 子 shell 防 cwd 污染主流程。 | T-8 在 `_self_check.sh` 段把 AC-12 命令包裹 `(cd apps/api && ...)` 子 shell；spec 不强制修。 |
| 3 | spec.md AC-7 grep `'produced_by.{0,8}name\|lineage_json\[.produced_by.\]'` | **正则稍宽**：`[.produced_by.]` 在 grep -E 字符类内 = 任意单字符（含 `.`），可被 `lineage_json[Xproduced_byX]` 这类无意义字符串假命中；但实际测试代码不可能出现此字符串，所以工程实际无沉默通过风险。属"正则不收敛"但"无伪命中"。 | 可选改用 `grep -qE 'lineage_json\["produced_by"\]\|lineage_json\.produced_by\|produced_by\.name'`；不阻塞。 |
| 4 | spec.md §R-7 缓解栏 | R-7 "多 worker 进程时由 CommitService.create_commit 内 ref 更新的行级 lock 兜底（既有逻辑）"——reviewer 实查 commit.py:192-209 ref upsert 逻辑**没有行级 lock**（用 `select` + `if existing: update / else: add`，竞态窗口存在；只靠 `IntegrityError` rollback 兜底重读）。语义描述夸大。 | R-7 缓解栏改"`CommitService.create_commit` 的 ref upsert 走 `select + add/update + IntegrityError rollback retry` 模式（commit.py:192-209，commit_hash PK 兜底；ref name 多写场景表现为后写覆盖先写，与 design.md §4.4 类 Git ref 语义一致）"——把"行级 lock"这词去掉，避免误导。 |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | spec.md AC-9 | OpenAPI 仅验路径存在，未验响应 schema 含 `node_runs[]` 字段 | 加 `grep -q "PipelineRunResponse" packages/api-types/openapi.json` |
| 2 | spec.md AC-3 | cache_key 测一层 + 二层 dict（spec 描述"config 键序无关"），未明示 list-in-config 顺序是否纳入 canonical | T-7a `tests/test_pipeline_cache.py` 加 list-in-config 测试，断言"`config={"list":[1,2]}` ≠ `config={"list":[2,1]}`"（明示 list 顺序敏感语义） |
| 3 | spec.md §AC-11 | demo recipe inputs/output ref 形态未 grep | 增 `grep -qE "@auto" recipes/examples/demo-bronze-to-gold.yaml` |
| 4 | spec.md §背景段尾 | adapter-lineage-bugfix follow-up 未起 slug；spec.md §非范围内有 `adapter-lineage-bugfix-*`，背景段 §问题陈述 #2 也提"adapter 侧单独 follow-up `adapter-lineage-bugfix-*`"，OK。NICE 评论："follow-up slug 命名一致" | 无需改 |

## Verdict

**APPROVED**（MUST FIX 数 = 0）

理由：
- v1 全部 3 MUST FIX 真闭环（spec §问题陈述/AC-8/R-6/T-2/T-5c/T-5d/T-7b 完整链路）
- v2 修订说明明示选 (b) 路径 deferred env 字段，路径选择一致
- demo recipe 不再含 raw-upload as processor 节点，fixture 预 seed 路径与 orchestrator 解耦
- 9 条跨 AC 自审 reviewer 独立复核全 PASS；7 个 `python -c` dry-parse 全 0；AC-11 反向 grep 配 `test -f` 不留沉默通过
- 4 条 SHOULD FIX 均不阻塞 verdict；建议作者 stage 3 编码前快速过一遍（特别是 SHOULD #1 RefService.update_ref 命名）

## 复检指引

stage 3 进入前作者可自检以下：

1. **MUST FIX 全闭环 reverify**：
   ```bash
   grep -nE "cache hit.*ref|更新 target_repo ref" .harness/changes/pipeline-orchestrator-mvp-20260518/request_analysis/spec.md  # 期望 ≥3 行命中
   grep -q "input_commits_json" .harness/changes/pipeline-orchestrator-mvp-20260518/request_analysis/tasks.md  # 期望命中
   grep -nE "_canonical_config_hash" .harness/changes/pipeline-orchestrator-mvp-20260518/request_analysis/tasks.md  # 期望 ≥3 行命中
   ! grep -qE "^\s*processor:\s*raw-upload" .harness/changes/pipeline-orchestrator-mvp-20260518/request_analysis/tasks.md  # demo recipe 部分不含 raw-upload as processor（fixture 上下文里出现 raw-upload Adapter 是 OK 的）
   ```

2. **全量 dry-parse**：
   ```bash
   python3 -c "
   import re
   c = open('.harness/changes/pipeline-orchestrator-mvp-20260518/request_analysis/spec.md').read()
   for i, m in enumerate(re.finditer(r'uv run python -c \"([^\"]+)\"', c), 1):
       compile(m.group(1), f'<ac-{i}>', 'exec')
   print('all python -c compile 0')
   "
   ```

3. **SHOULD #1 RefService.update_ref 命名澄清**（stage 3 前最好同步澄清，避免 coder 撞墙）

进入 stage 3 编码后，coder 应按 tasks.md T-1~T-8 顺序实现；coder agent 自身 spawn 时附带本 review 文件路径以保持一致认知。
