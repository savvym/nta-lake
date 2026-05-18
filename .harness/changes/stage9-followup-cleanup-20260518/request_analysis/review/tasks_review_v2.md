---
change_id: stage9-followup-cleanup-20260518
target: tasks.md
target_version: 2
review_version: 2
reviewer: claude-agent:stage9-followup-cleanup-20260518-stage2-reviewer-v2
reviewed_at: 2026-05-18T10:30:00Z
verdict: REVISION REQUIRED
---

# Tasks Review v2

## v1 MUST FIX / SHOULD / NICE 复检

| # | v1 类别 | v1 issue 摘要 | v2 状态 | 证据 |
|---|---|---|---|---|
| MUST #1 | tasks.md T-6 description "AC-1：grep model + 0005 migration CASCADE"（联动 spec v1 MUST FIX-1） | **CLOSED** | tasks v2 T-6 description 第 137-142 行明示 "AC-1（**用 spec v2 awk 状态机 pattern**）" 并完整列出 awk 状态机 + ls + grep 4 条命令。与 spec v2 AC-1 验证命令一致（reviewer diff 复核）。**不**再 inline 写死老 pattern |
| SHOULD #1 | T-2 描述用裸 SQL，未明示 alembic 高层 API | **CLOSED** | tasks v2 T-2 description 第 44-58 行明示用 `op.drop_constraint(name, table, type_="foreignkey")` + `op.create_foreign_key(name, source_table, referent_table, local_cols, remote_cols, ondelete="CASCADE")`，参数顺序与命名符合 alembic 文档标准签名（reviewer 比对 alembic.operations.Operations 文档：drop_constraint(name, table_name=None, type_=None, schema=None) + create_foreign_key(constraint_name, source_table, referent_table, local_cols, remote_cols, ...)）。参数完整正确 |
| SHOULD #2 | T-3 缺前置 alembic current 检查 | **CLOSED** | tasks v2 T-3 description 第 72-75 行加 "# 0. 前置检查：当前 alembic head 是 0004" + `uv run alembic current` + 期望 `0004 (head)` + 失败处理提示 `先 alembic upgrade 0004 调整`。前置逻辑清晰 |
| SHOULD #3 | T-5 ≥10 与 spec AC-4 "7 集成测试" 数字打架 | **CLOSED** | tasks v2 T-5 description 明示 "4 个 sync 单元 + 6 个 @pytestmark_int 集成"；spec v2 AC-4 同步改为同表述（reviewer 实测 grep -cE "^(async )?def test_" = 10）。spec / tasks 数字一致 |
| NTH #1 | T-5 depends_on 缺 T-1 显式 | **CLOSED** | tasks v2 T-5 depends_on 改为 `[T-1, T-3, T-4]`。reviewer DAG 复核：T-5→T-1 / T-5→T-3→T-2 / T-5→T-4，无环（T-5 是终点之一，T-6 也是终点）。覆盖矩阵段同步显示 T-5 关联 AC-4 |
| NTH #2 | T-4 uuid 前缀字串形态（`#` 是 markdown H1 前缀） | **CLOSED**（措辞合理但前提需复核） | tasks v2 T-4 description 第 99-103 行改用 `f"<!-- fixture-uuid {uuid.uuid4().hex} -->\n".encode()` HTML 注释前缀 + 注释 "markdown-normalize 处理 HTML 注释行为更可预测（多数 normalize 直接保留或 strip，不当 H1 标题处理）"。**reviewer 实读 `apps/api/dataplat_api/processors/markdown_normalize.py` 复核**：当前 normalize 只做 4 规则（CRLF→LF / 行尾空白 / 多于 2 连续空行折叠 / BOM 去除），**不解析 markdown 语法**，所以 `#` 和 `<!-- -->` 在 silver content 中都**字面保留**——v2 "更可预测"措辞略夸大（当下无区别）。但若未来加 markdown→HTML 渲染或更严 normalize 规则，HTML 注释更可能被识别为可 strip 而 `#` 会保留为 H1——**防御性写法成立**，措辞建议精化 |

v1 全部 6 条 issue 真闭环。**但 v2 引入 1 个新 MUST FIX（T-6 description AC-3 验证命令将照搬 spec v2 AC-3 同型 bug，详下），verdict 仍 REVISION REQUIRED**。

## 检查清单结论

- [x] 每个任务粒度合理（1-3 小时）：T-1（model 1 行改）/ T-2（migration 新建 ~30 行）/ T-3（3 条 alembic + SQL 查 + alembic current 前置）/ T-4（_seed_bronze 函数体加 unique_content 一行 + content 引用改名）/ T-5（pytest 真跑）/ T-6（self_check block）—— 全在合理范围
- [x] depends_on 无环（reviewer DAG 复核见下）
- [x] 包含评审 / 单测 / CI / deploy / user-confirm：process_tasks 6 条齐全。CI = self-attest（无 remote）；deploy = pending（有 schema 改，不允 self-attest）
- [x] 没有 "做完整个系统" 类目标任务
- [ ] 每条 AC 都有 T-* 覆盖 — 覆盖矩阵段已列 AC-1..AC-4 全有 T-* 关联；**但 T-6 description AC-3 验证命令将照搬 spec AC-3 同型 grep 窗口缺陷**（见 MUST FIX-1）

## 设计合理性评估

### 1. T-5 depends_on 改 [T-1, T-3, T-4] 后 DAG 仍无环

**reviewer DAG 复核**：

| 节点 | depends_on | 关系 |
|---|---|---|
| T-1 | `[]` | 起点 |
| T-2 | `[]` | 起点 |
| T-3 | `[T-2]` | T-2 → T-3 |
| T-4 | `[]` | 起点 |
| T-5 | `[T-1, T-3, T-4]` | T-1 / T-3 / T-4 → T-5（终点） |
| T-6 | `[T-1, T-2, T-4]` | T-1 / T-2 / T-4 → T-6（终点） |

从 T-5 反向 BFS：T-1（起点）/ T-3→T-2（起点）/ T-4（起点）—— 三条独立路径汇于 T-5，无环。
从 T-6 反向 BFS：T-1（起点）/ T-2（起点）/ T-4（起点）—— 三条独立路径汇于 T-6，无环。
图中无 cycle。覆盖矩阵段第 195-198 行画图同样无环。

### 2. T-2 alembic 高层 API 参数完整正确性

**完整正确**。reviewer 参考 alembic.operations.Operations 标准 API 签名：

- `op.drop_constraint(constraint_name, table_name, type_=None, schema=None)`
- `op.create_foreign_key(constraint_name, source_table, referent_table, local_cols, remote_cols, onupdate=None, ondelete=None, deferrable=None, initially=None, match=None, source_schema=None, referent_schema=None, **dialect_kw)`

tasks v2 T-2 调用：

```python
op.drop_constraint(
    "pipeline_cache_output_commit_hash_fkey",   # constraint_name
    "pipeline_cache",                            # table_name
    type_="foreignkey",                          # type_
)
op.create_foreign_key(
    "pipeline_cache_output_commit_hash_fkey",   # constraint_name
    "pipeline_cache",                            # source_table
    "commits",                                   # referent_table
    ["output_commit_hash"],                      # local_cols
    ["hash"],                                    # remote_cols
    ondelete="CASCADE",                          # ondelete
)
```

参数 1-1 对应。constraint_name 在 0005 与 stage 9 错误日志中显示的 `pipeline_cache_output_commit_hash_fkey` 一致（也与 0004 隐式 FK 默认名一致）。表名 / 列名 / referent / ondelete 全对。`type_="foreignkey"` 是 drop_constraint 必填参数（否则 alembic 不知 drop FK / unique / pk）。**完整且正确**。

### 3. T-3 alembic current 前置

**合理**。`uv run alembic current` 输出形态：`<revision> (head)`（如 `0004 (head)`）；若 db 在其他 revision，输出仅 revision 无 `(head)` 标签。grep `0004 (head)` 是机敏的对齐检查。**但 spec v2 AC-2 命令未照搬此前置**（详 spec_review_v2 SHOULD FIX-1）。tasks 与 spec 在此点上的一致性轻微缺失。

### 4. T-4 uuid 前缀字串形态：`<!-- fixture-uuid -->` vs `# fixture-uuid`

**reviewer 实读 `apps/api/dataplat_api/processors/markdown_normalize.py` 复核**：

- normalize 规则：CRLF→LF / `[ \t]+(\n|$)` 行尾空白去除 / `\n{3,}` → `\n\n` / BOM 去除
- 没有 markdown 语法解析（不会把 `# foo` 渲染为 H1 标签；不会把 `<!-- foo -->` strip）
- **当下两种前缀在 silver content 字面等价**（normalize 后都保留原字面）

所以 v2 注释 "markdown-normalize 处理 HTML 注释行为更可预测" 在**当下** processor 实现下**轻微夸大**——两种前缀产生的 silver 内容字面相同（除非 trailing whitespace 因素，但两个前缀都无尾空白）。

但**防御性写法仍然成立**：若未来 normalize 加 markdown→HTML 渲染或更严规则（如 mdx parsing），HTML 注释更可能被 strip 视为无意义元数据，而 `#` 会被解释为 H1 污染 silver。措辞建议精化为 "防御性：若未来 normalize 加 markdown 语法解析，HTML 注释比 `#` 标题更可能被 strip"。**不阻塞 v2 通过**，作 NICE TO HAVE 记录。

### 5. T-6 description 引用 spec v2 AC-1 awk pattern

**AC-1 一致**。reviewer diff 复核：

- spec v2 AC-1 命令第一段：`awk '/^class PipelineCacheORM/{p=1;next} p && /^class /{exit} p' apps/api/dataplat_api/models/pipeline.py | grep -q 'ondelete="CASCADE"'`
- tasks v2 T-6 AC-1 验证：`awk '/^class PipelineCacheORM/{p=1;next} p && /^class /{exit} p' apps/api/dataplat_api/models/pipeline.py | grep -q 'ondelete="CASCADE"'`

字面一致（除 `\` 行延续不同形态）。awk 状态机模式从 spec → tasks 准确传递。

### 6. T-6 description AC-3 验证命令将照搬 spec v2 AC-3 同型 bug（**新 MUST FIX**）

**这是 v2 引入的新 MUST FIX**，与 spec_review_v2 MUST FIX-1 联动。

tasks v2 T-6 description 第 148 行 "AC-3：grep _seed_bronze 内含 uuid.uuid4().hex 前缀字串" — 抽象一句话，但 self_check block 实现时**会从 spec v2 AC-3 命令照搬具体 grep 形态**（这是 T-6 与 spec 的契约）。spec v2 AC-3 命令 `grep -A 15 "async def _seed_bronze" ... | grep -qE "uuid..."` 有同型窗口缺陷：

- `async def _seed_bronze` 在第 261 行
- 合理 T-4 实施位置（unique_content 行）= 第 288 行
- 距离 27 行；`-A 15` 窗口不够 → grep 永远 fail（reviewer 已 dry-run 验证）

T-6 若照搬此命令，self_check block 永远报 AC-3 fail，整个 stage9-followup-cleanup block PASS rate = 75%（3/4 AC）。

**建议**：等 spec v3 修完 AC-3（用 awk 状态机或扩窗口 -A 35），T-6 description 显式 inline 引用新 pattern；或加备注 "AC-3 grep pattern 等 spec v3 校准后照搬，不在此 inline 写死"。

## 问题列表

### MUST FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| MUST FIX-1 | tasks.md T-6 description "AC-3：grep _seed_bronze 内含 uuid.uuid4().hex 前缀字串" | 联动 spec_review_v2 MUST FIX-1：spec v2 AC-3 命令 `grep -A 15 "async def _seed_bronze"` 窗口（15 行）短于 _seed_bronze 函数体到合理 T-4 注入位置距离（27 行），永远 fail。T-6 self_check block 实现时会照搬这个 grep pattern → AC-3 持续 fail。reviewer dry-run 验证：python 注入合理 T-4 后跑 AC-3 命令 → exit=1（fail，应 pass） | 等 spec v3 修完 AC-3 grep pattern（用 awk 状态机 `awk '/^async def _seed_bronze/{p=1;next} p && /^async def \|^def /{exit} p' ...` 或扩窗口 `-A 35`）后，T-6 description 同步引用新 pattern；或现在显式加备注 "AC-3 grep pattern 等 spec v3 校准后照搬，不 inline 写死"，避免提前固化 |

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| SHOULD FIX-1 | tasks.md T-3 vs spec AC-2 一致性 | T-3 description 加 alembic current 前置（响应 v1 SHOULD #2），但 spec AC-2 命令未加。两文件在此点上不一致 → self_check 用 spec AC-2 命令跑 self_check 时未做前置，dev db 状态非 0004 时直接 fail；T-3 手动跑会 fail 在前置而非业务路径 | 联动 spec_review_v2 SHOULD FIX-1。tasks T-3 可保持原样；要求 spec v3 AC-2 命令同步加前置（或在 spec AC-2 期望表显式注 "假设 dev db baseline = 0004（详 tasks T-3 第 0 步）"） |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| NTH-1 | tasks.md T-4 description 第 102 行注释 "markdown-normalize 处理 HTML 注释行为更可预测" | reviewer 实读 markdown_normalize.py 复核：当前 processor 只做 4 规则（CRLF / 行尾空白 / 多空行 / BOM），**不解析 markdown 语法** → `#` 和 `<!-- -->` 在 silver 字面等价。注释 "更可预测" 在当下轻微夸大；防御性写法仍成立但理由需精化 | 注释改为 "防御性：若未来 markdown-normalize 加语法解析（如 markdown→HTML 渲染或 mdx parsing），HTML 注释更可能被 strip 为无意义元数据，而 `#` 会被解释为 H1 污染 silver" |
| NTH-2 | tasks.md T-6 description AC-3 抽象一句话 | "AC-3：grep _seed_bronze 内含 uuid.uuid4().hex 前缀字串" 没有写具体命令，依赖 spec AC-3 → 易传递 spec 的同型 bug（详 MUST FIX-1） | T-6 description 直接 inline 列 AC-3 具体命令（与 AC-1/AC-2 风格一致），让 self_check 实现者一目了然，不再二次跳到 spec AC-3 |

## Verdict

**REVISION REQUIRED**

理由：MUST FIX-1（T-6 description AC-3 验证命令将照搬 spec v2 AC-3 同型 bug）是阻塞型——self_check block 会持续报 AC-3 fail，整个 change PASS rate < 100%；必须等 spec v3 修完 AC-3 后 tasks v3 T-6 同步。MUST FIX 数：1 → verdict 唯一判据未通过。

v1 全部 6 个 issue 真闭环（含 T-2 高层 API 参数完整正确性 reviewer 比对 alembic 文档复核；T-5 DAG reviewer 复核无环；T-4 HTML 注释 reviewer 实读 markdown_normalize.py 复核）。修复质量好。本轮新 MUST FIX 是 v1 reviewer / spec generator 视野盲区（spec v2 修 AC-1 同型未类比检查 AC-3），下一轮 v3 修完即可通过。

## 复检指引

Generator 修 v3 后自查：

1. **依赖图 DAG 校验**：手画或机械列每个 T-* 的 depends 关系，确认无环（v2 已 PASS）。
2. **覆盖矩阵**：每条 AC 至少一个非 process_tasks T-* 关联（v2 已 PASS）。
3. **process_tasks 完整**：6 条齐全（v2 已 PASS）。
4. **T-6 description AC-3 验证命令**：联动 spec v3 AC-3 新 pattern；inline 列具体命令（不依赖 spec 跳转）。两轮 dry-run（pre-T-4 fail / post-T-4 pass）确认。
5. **T-3 vs spec AC-2 一致性**：spec AC-2 同步加 alembic current 前置；或 spec AC-2 期望表注 "假设 db baseline = 0004"。
6. **T-4 markdown-normalize 注释措辞精化**（NICE TO HAVE，不阻塞）。

提交 v3 后开 `tasks_review_v3.md` 复检 MUST FIX-1 状态 + 全部 AC dry-run 命令真跑两轮。
