---
change_id: stage9-followup-cleanup-20260518
target: tasks.md
target_version: 3
review_version: 3
reviewer: claude-agent:stage9-followup-cleanup-20260518-stage2-reviewer-v3
reviewed_at: 2026-05-18T11:45:00Z
verdict: APPROVED
---

# Tasks Review v3

## v2 MUST FIX / SHOULD / NICE 复检

| # | v2 类别 | v2 issue 摘要 | v3 状态 | 证据 |
|---|---|---|---|---|
| MUST FIX-1 | T-6 description AC-3 抽象一句话 → 会照搬 spec v2 AC-3 同型 grep 窗口 bug，self_check 持续 fail | **CLOSED** | tasks v3 T-6 description 第 148-151 行已**显式 inline 列出 AC-3 awk 状态机命令**：`awk '/^async def _seed_bronze/{p=1;next} p && /^async def \|^def /{exit} p' apps/api/tests/test_pipeline_orchestrator.py \| grep -qE "uuid\.uuid4\(\)\.hex.*content\|unique_content.*=.*uuid"`，与 spec v3 AC-3 字面完全一致（reviewer diff 比对：除 `\` 行延续不同形态，pattern 一致）。命令注释 "用 awk 状态机锚定 _seed_bronze 函数体，同 spec v3 AC-3 pattern" 明示 pattern 来源。spec v3 dry-run 双轮已验证 pre fail / post pass |
| SHOULD FIX-1 | T-3 vs spec AC-2 一致性（T-3 加 alembic current 前置 / spec AC-2 v2 未加） | **CLOSED** | spec v3 AC-2 验证命令第 73 行同步加前置 `uv run alembic current 2>&1 \| grep -q "0004"` + 后置 information_schema 断言 `SELECT delete_rule FROM information_schema.referential_constraints` → grep CASCADE。**spec 与 tasks T-3 第 0 步前置完全对齐**。tasks T-3 自身未变，依然合理 |
| NICE TO HAVE-1 | T-4 description 第 102 行 "markdown-normalize 处理 HTML 注释行为更可预测" 措辞略夸大 | OPEN（v3 未改，不阻塞） | tasks v3 T-4 description 第 102-103 行未动；reviewer v2 已实读 markdown_normalize.py 复核仍当下字面等价；防御性写法成立但理由可精化为 "防御性：若未来 normalize 加 markdown 语法解析，HTML 注释更可能被 strip 为元数据" |
| NICE TO HAVE-2 | T-6 description AC-3 抽象一句话 → 二次跳到 spec AC-3 | **CLOSED**（与 MUST FIX-1 同时闭合） | tasks v3 T-6 已 inline AC-3 awk 命令，self_check 实现者一目了然，不再二次跳 spec |

v2 全部 1 MUST FIX + 1 SHOULD FIX + 1/2 NICE TO HAVE 真闭环。

## 检查清单结论

- [x] 每个任务粒度合理（1-3 小时）：T-1（model 1 行改）/ T-2（migration ~30 行）/ T-3（三连 + alembic current 前置 + information_schema 查询）/ T-4（_seed_bronze 函数体加 unique_content 一行 + content 引用改名）/ T-5（pytest 真跑）/ T-6（self_check block）—— 全在合理范围
- [x] depends_on 无环（DAG 复核见下）
- [x] 包含评审 / 单测 / CI / deploy / user-confirm：process_tasks 6 条齐全（reviewer 实测 `grep -cE "estimated_stage: stage-(2\|4\|6\|7\|9\|10)\|estimated_stage: (request_analysis_review\|coding_review\|unit_test_review\|ci_result\|deployment\|user_confirmation)" tasks.md` = 6）
- [x] 没有 "做完整个系统" 类目标任务
- [x] 每条 AC 都有 T-* 覆盖（AC-1→T-1/T-2/T-6；AC-2→T-2/T-3/T-6；AC-3→T-4/T-6；AC-4→T-5/T-6）
- [x] T-6 description AC-3 验证命令**显式 inline awk 状态机**，与 spec v3 AC-3 字面一致

## 设计合理性评估

### 1. T-5 depends_on DAG 无环复核（v2 已 PASS，v3 沿用）

```
T-1 ──┐
T-2 ──┴──→ T-3 ──┐
T-4 ──┐         ├──→ T-5
T-1 ──┴──────────┘
T-1/T-2/T-4 → T-6
```

- T-5 反向 BFS：T-1（起点）/ T-3→T-2（起点）/ T-4（起点）—— 三条独立路径汇 T-5，无环
- T-6 反向 BFS：T-1（起点）/ T-2（起点）/ T-4（起点）—— 三条独立路径汇 T-6，无环

图中无 cycle。覆盖矩阵段同步显示 T-5/T-6 关联正确。

### 2. T-2 alembic 高层 API 参数（v2 已 PASS，v3 沿用）

`op.drop_constraint(name, table, type_="foreignkey")` + `op.create_foreign_key(name, source, referent, [local], [remote], ondelete="CASCADE")` 标准签名；constraint_name 与 stage 9 错误日志一致。完整且正确。

### 3. T-3 alembic current 前置（v2 已 PASS）

`uv run alembic current` 输出 `<revision> (head)`；grep `0004 (head)` 是机敏对齐检查。spec v3 AC-2 同步加前置，对齐完成。

### 4. T-4 uuid 前缀字串形态：HTML 注释 vs `#`（v2 NTH-1 仍 open，不阻塞）

`f"<!-- fixture-uuid {{uuid.uuid4().hex}} -->\n".encode()` 形态合理；markdown_normalize.py 当前不解析 markdown 语法两种前缀字面等价，防御性写法仍成立。注释措辞可精化，但不阻塞。

### 5. T-6 AC-1 / AC-3 awk 状态机一致性（v3 关键修复）

reviewer diff 比对 spec v3 与 tasks v3 T-6：

**AC-1（reviewer 实测）**：

- spec v3 第 72 行：`awk '/^class PipelineCacheORM/{p=1;next} p && /^class /{exit} p' apps/api/dataplat_api/models/pipeline.py | grep -q 'ondelete="CASCADE"'`
- tasks v3 T-6 第 138-139 行：`awk '/^class PipelineCacheORM/{p=1;next} p && /^class /{exit} p' apps/api/dataplat_api/models/pipeline.py | grep -q 'ondelete="CASCADE"'`

字面一致 ✓

**AC-3（reviewer 实测）**：

- spec v3 第 74 行：`awk '/^async def _seed_bronze/{p=1;next} p && /^async def \|^def /{exit} p' apps/api/tests/test_pipeline_orchestrator.py | grep -qE "uuid\.uuid4\(\)\.hex.*content|unique_content.*=.*uuid"`
- tasks v3 T-6 第 148-151 行：`awk '/^async def _seed_bronze/{p=1;next} p && /^async def |^def /{exit} p' apps/api/tests/test_pipeline_orchestrator.py | grep -qE "uuid\.uuid4\(\)\.hex.*content|unique_content.*=.*uuid"`

字面一致 ✓（除行延续 `\` 形态）

**AC-2（reviewer 实测）**：

- spec v3 AC-2 含前置 alembic current + 三连 + information_schema 后置
- tasks v3 T-6 AC-2 行为型验证含 alembic current 期望 0005（reviewer 注：tasks T-6 用 `current → 0005` 期望，spec AC-2 用前置 `current → 0004` + 后置 information_schema 验证 CASCADE。两者契合 self_check 跑时机：self_check 是部署完成后跑，db 此时应在 0005；spec AC-2 期望 0004 baseline 是 T-3 手动跑前的状态）—— **时机正确，无矛盾**

**AC-4（reviewer 实测）**：

- spec v3 AC-4 期望 `10 passed`
- tasks v3 T-6 AC-4 注释 "dry run pytest -q test_pipeline_orchestrator.py，期望 10 passed"（reviewer 注：T-6 self_check block 通常不真跑 pytest 而是探针 PG+MinIO+Redis 三服务存活；具体实现细节在 stage 3 coding 时确定）

AC-1/AC-3 awk pattern 完美一致；AC-2/AC-4 时机正确；同型 v1 bug 不会再传递。

### 6. v3 是否引入新缺陷？

reviewer 全文 diff 排查：

- **T-1/T-2/T-3/T-4/T-5 任务体未动**，仅 T-6 description AC-3 行替换为 awk pattern + 注释更新
- **T-6 AC-1 / AC-2 / AC-3 / AC-4 验证片段无相互覆盖错位**
- **covers_ac / depends_on / process_tasks / 阶段任务 全未动**，DAG 健全
- **frontmatter version=3 / prior_version=2 / prior_review=tasks_review_v2.md** — 版本链规范

**reviewer 确认：v3 不引入新缺陷**。

## 问题列表

### MUST FIX

无。

### SHOULD FIX

无。

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| NTH-1 | tasks.md T-4 description 第 102 行 "markdown-normalize 处理 HTML 注释行为更可预测" | 措辞略夸大（当前 normalize 不解析 markdown 语法两种前缀字面等价）；防御性写法成立但理由可精化（v2 NTH-1 沿用） | 改为 "防御性：若未来 normalize 加 markdown 语法解析（如 markdown→HTML 渲染或 mdx parsing），HTML 注释更可能被 strip 为无意义元数据，而 `#` 会被解释为 H1 污染 silver"；不阻塞 v3 通过 |

## Verdict

**APPROVED**

理由：MUST FIX 数 = 0 → verdict 唯一判据满足。v2 全部 1 MUST FIX（T-6 AC-3 同型 bug）+ 1 SHOULD FIX（T-3 vs spec AC-2 一致性）+ 1/2 NICE TO HAVE 真闭环（reviewer diff 复核 spec v3 AC-3 / AC-1 与 tasks v3 T-6 字面一致；spec v3 AC-2 加前置 + 后置）。v3 不引入新缺陷。DAG 无环 / process_tasks 6 条齐全 / AC 覆盖矩阵完整 / T-6 description AC-3 显式 inline awk pattern 与 spec v3 同步。可进入 stage 3 coding。

## 复检指引

stage 3 generator 开始 coding 前自查：

1. **DAG 校验**：T-1/T-2/T-4 全是起点；T-3 依赖 T-2；T-5 依赖 [T-1, T-3, T-4]；T-6 依赖 [T-1, T-2, T-4]；无环（v3 已 PASS）
2. **覆盖矩阵**：AC-1→T-1/T-2/T-6；AC-2→T-2/T-3/T-6；AC-3→T-4/T-6；AC-4→T-5/T-6（v3 已 PASS）
3. **process_tasks 完整**：P-spec-review / P-code-review / P-test-review / P-ci / P-deploy / P-user-confirm 全有（v3 已 PASS）
4. **T-6 description AC-3 awk pattern**：与 spec v3 AC-3 字面一致（v3 已 PASS；reviewer 双轮 dry-run 验证 pre fail / post pass）
5. **T-3 vs spec AC-2 一致性**：spec v3 AC-2 已加前置 + 后置（v3 已 PASS）
6. **T-4 注释措辞精化**（NICE TO HAVE，不阻塞，可在 v4 或 close 时补）
