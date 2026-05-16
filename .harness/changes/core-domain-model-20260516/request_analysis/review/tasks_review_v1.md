---
change_id: core-domain-model-20260516
target: tasks.md
target_version: 1
review_version: 1
reviewer: claude-agent:core-domain-model-stage2-reviewer
reviewed_at: 2026-05-16T21:34:47Z
verdict: REVISION REQUIRED
---

# Tasks Review v1

## 检查清单结论

> 引用 `.harness/skills/expert-reviewer/SKILL.md` §1（plan 模式 tasks.md）。

- [x] 每个任务粒度合理（1-3 小时）——12 个 T-* 都是单/小组文件级，30-90 min/个；T-9 alembic 0001 略大但可接受。
- [x] depends_on 形成 DAG，无环（拓扑：T-1/T-4 是 source；T-2→T-1；T-3→T-2；T-5/T-6→T-4；T-7→T-6；T-8/T-9→T-7；T-10→T-2；T-11→T-9；T-12→T-10,T-11；无回边）。
- [x] 评审 / 单测 / CI 阶段对应任务都有（7 个 P-* 齐全，含 skip + self-confirm）。
- [x] 没有"做完整个系统"类目标任务——每个 T-* 对应具体文件/配置。
- [~] 每条 AC 都有 T-* 覆盖——名义 17/17；但 T-1 与 spec AC-2 在 Subtype 是否 Literal 上不一致（见 MUST FIX #1，与 spec_review MUST FIX #3 联动）。

## 问题列表

### MUST FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | tasks.md T-1（行 15）vs spec.md AC-2（行 31） | T-1 description 写 "Subtype Literal 拆 Bronze/Silver/Gold"，明示要做 Literal；但 spec AC-2 只列 `subtype` 为 Repository 字段，无 Literal 约束；AC-14(e) 又要测 "Subtype Literal 严格校验"。三处不一致，T-1 实施者无法判断采何种类型。**与 spec_review_v1 MUST FIX #3 同根，需在 v2 一并对齐**。 | 与 spec v2 同步：若 spec 选 Literal，T-1 description 把字面 Literal 值列出（如 `BronzeSubtype = Literal["pdf","webpage","book","image-set"]`，Silver / Gold 同）；若 spec 选 free str，删 T-1 "Literal 拆 Bronze/Silver/Gold" 字样。 |
| 2 | tasks.md T-3（行 30-32） vs spec.md AC-8（行 37, 68） | T-3 description 含 8 个类型：`SourceAdapter / Processor / RunContext / IngestResult / ProcessResult / RepoView / RepoSelector / RepoSpec`，但 spec AC-8 验证命令只 `from ... import SourceAdapter / Processor / RunContext`，不校验后 5 个。实施者若只交付 3 个 Protocol，AC-8 PASS 但 T-3 description 未完成；stage 4 评审无机械化判据。 | 二选一：(a) AC-8 命令补全 8 个 import（推荐——design.md §4.1/§4.2 这些数据类是 Protocol 签名必需）；(b) T-3 description 收缩到 3 个 Protocol，5 个数据类挪到独立 sub-task 或 spec 显式 defer。 |

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | tasks.md T-7（行 62-66） | description "commits.lineage_json JSONB" 与 spec AC-3（行 32）"`lineage: Lineage \| None`"在 ORM 字段命名上分歧：Pydantic 字段 `lineage` vs SQLAlchemy 列 `lineage_json`？两者应一致或显式 `alias`，否则 ORM↔Pydantic 转换易踩坑。 | T-7 description 显式声明 "ORM 列名 `lineage`（与 Pydantic 一致），列类型 `JSONB`；ORM→Pydantic 走 `Lineage.model_validate(row.lineage)`"。 |
| 2 | tasks.md T-9（行 78-83） | description "手写；6 张表 + 索引 + 外键约束"，但未列哪些索引 / 外键。stage 4 评审无具体核对项；spec AC-13 也只校验"6 张表存在 + revision=0001"，alembic 几百行差异在 review 视野外。 | T-9 description 列必需索引：`repositories(owner,name)` 唯一；`refs(repo_id,name)` 唯一；`commits(repo_id, created_at)`；`tree_entries(tree_hash)`；外键：`commits.tree_hash→trees.hash`、`refs.commit_hash→commits.hash`、`commits.repo_id→repositories.id`、`tree_entries.tree_hash→trees.hash`。 |
| 3 | tasks.md T-8（行 70-73）+ T-6 | env.py `target_metadata = Base.metadata` 依赖`models/__init__.py` 先 import 所有表模块，否则 `Base.metadata` 不含全 6 张表，alembic autogen/upgrade 行为不可预测。T-6 / T-7 description 未要求 `models/__init__.py` re-export。 | T-6 description 加 "`models/__init__.py` 必须 `from .repository import *` / `.commit` / `.tree` / `.refs` / `.blob`，确保 `Base.metadata.tables` 含 6 张表"；或 T-8 env.py 显式 import 列表。这是 alembic + multi-file ORM 已知坑。 |
| 4 | tasks.md §process_tasks（行 113-139） | 上一变更 review 已提"所有 process_tasks 字段对称（含 reason）"的 SHOULD FIX。本变更 P-push / P-ci / P-deploy / P-user-confirm 都有 reason，但 P-spec-review / P-code-review / P-test-review 仍无 reason 字段，**未吸收上次评审反馈**。 | 三个 review task 补 `reason: ""` 或简短理由（如 `"Stage 2/4/6 标准评审"`），保持字段对称。 |
| 5 | tasks.md §AC 覆盖矩阵 AC-13（行 170） | 只列 T-9，但 AC-13 要求 `alembic upgrade head` 真实跑通——需 T-8（env.py async）+ T-9（migration）+ docker-compose（来自 bootstrap）。AC-15 只列 T-11 同问题（缺 T-7 / T-9 依赖）。 | 矩阵补：AC-13 → T-7, T-8, T-9；AC-15 → T-7, T-9, T-11。 |
| 6 | tasks.md T-11（行 95-99） | "docker-compose Postgres"——是否在 conftest.py 起容器？还是依赖外部 `make up`？测试隔离与并发清理策略未定。 | T-11 description 显式 "依赖外部 `make up` 已起 Postgres；每个测试用 `BEGIN ... ROLLBACK` 事务包裹或 truncate；不在 fixture 里启动容器"。 |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | tasks.md §AC 覆盖矩阵（行 156-174） | 单列"关联任务"，未区分"产物任务"vs"测试任务"——与上一变更 NICE-HAVE #1 同。AC-9 列 T-6+T-7，AC-11 列 T-8+T-9 全是产物。 | 拆双列 `产物任务` / `测试任务`，与 bootstrap-monorepo 评审建议一致。 |
| 2 | tasks.md T-10（行 86-91） | 列 6 个测试文件名，spec AC-14 列 6 个场景（a-f）；文件↔场景映射不显式。 | T-10 加映射表："test_repository.py → AC-14(a)；test_commit.py → AC-14(b)；test_blob.py → AC-14(c)；test_tree.py → AC-14(d)；test_layer_literal.py → AC-14(e)；test_lineage.py → AC-14(f)"。 |
| 3 | tasks.md §阶段任务 P-deploy reason（行 137） | "schema 迁移实跑视作充分；无运行时部署面"——与 bootstrap-monorepo 同模板，合理；建议 summary §关键决策追加一句"P-deploy skip 复用 bootstrap 范式"。 | summary.md §关键决策追加一条。 |
| 4 | tasks.md T-12（行 102-107） | "FILTER 接受 core-domain-model"，但未要求"重新审视 AC-13/15 在 self_check 内的 SKIP vs FAIL 语义"（见 spec SHOULD FIX #1）。 | T-12 加 "Postgres 未起时 AC-13/15 应 SKIP（不计 FAIL），打印明确 `SKIP: postgres unavailable`"。 |

## DAG 与覆盖矩阵实测

- 拓扑排序成功：T-1 → T-2 → T-3 / T-10；T-4 → T-5 / T-6 → T-7 → T-8 / T-9 → T-11 → T-12；无环。
- 名义覆盖 17/17；但 AC-13 / AC-15 矩阵关联任务不充分（见 SHOULD FIX #5）。
- process_tasks 7 项覆盖 stage 2-10 全部阶段。

## 风险评估补充

- T-6（DeclarativeBase）+ T-7（6 表）+ T-8（env.py）形成关键路径，任一失败 AC-9/11/13/15 全雪崩；实施时先 `python -c "from dataplat_api.models import Base; print(len(Base.metadata.tables))"`（=6）再开 T-8/T-9。
- T-4（pyproject 加依赖）独立可与 T-1/T-2 并行；coding 阶段第一个跑（uv lock 慢）。
- T-3 在依赖链上是叶子但 description 内容最重（8 个类型）；时间预估应高于 90 min，建议 v2 拆 T-3a（3 Protocol）/ T-3b（5 data class）。

## Verdict

REVISION REQUIRED（MUST FIX 数 = 2）

> 说明：T-1 Subtype 与 spec_review_v1 MUST FIX #3 同根；Generator 在 v2 中需保证 spec ↔ tasks 一致。

## 复检指引

Generator 修完 tasks_v2.md（与 spec_v2.md 同步）后自检：

1. T-1 与 spec AC-2 + AC-14(e) Subtype 用词一致：
   ```bash
   grep -nE "Subtype" .harness/changes/core-domain-model-20260516/request_analysis/{spec.md,tasks.md}
   # 三处（AC-2 / AC-14 / T-1）就 Subtype 是 Literal 还是 str 给出同一答案
   ```
2. T-3 与 spec AC-8 import 列表一致：
   ```bash
   for f in spec.md tasks.md; do
     grep -oE "(SourceAdapter|Processor|RunContext|IngestResult|ProcessResult|RepoView|RepoSelector|RepoSpec)" \
       .harness/changes/core-domain-model-20260516/request_analysis/$f | sort -u
     echo "---"
   done
   # 两个集合相同；若 spec 收缩到 3 个，tasks T-3 description 同步收缩。
   ```
3. DAG 复检：
   ```bash
   python3 -c "
   import yaml,re
   t=open('.harness/changes/core-domain-model-20260516/request_analysis/tasks.md').read()
   block=re.search(r'\`\`\`yaml\n(tasks:.*?)\n\`\`\`',t,re.S).group(1)
   d=yaml.safe_load(block)
   ids={x['id'] for x in d['tasks']}
   for x in d['tasks']:
       for dep in x.get('depends_on',[]):
           assert dep in ids, f'{x[\"id\"]} -> {dep} missing'
   print('DAG OK')
   "
   ```
4. process_tasks 字段对称：
   ```bash
   python3 -c "
   import yaml,re
   t=open('.harness/changes/core-domain-model-20260516/request_analysis/tasks.md').read()
   block=re.search(r'\`\`\`yaml\n(process_tasks:.*?)\n\`\`\`',t,re.S).group(1)
   d=yaml.safe_load(block)
   for p in d['process_tasks']:
       assert {'id','estimated_stage','status','reason'} <= set(p), f'{p[\"id\"]} 字段缺失'
   print('process_tasks 对称 OK')
   "
   ```
5. AC 覆盖矩阵：AC-13 行含 T-7/T-8/T-9，AC-15 行含 T-7/T-9/T-11。

提交 v2 后开 `tasks_review_v2.md`。
