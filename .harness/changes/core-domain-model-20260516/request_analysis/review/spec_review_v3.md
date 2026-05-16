---
change_id: core-domain-model-20260516
target: spec.md
target_version: 1
review_version: 3
reviewer: claude-agent:core-domain-model-stage2-reviewer
reviewed_at: 2026-05-16T21:52:28Z
verdict: APPROVED
---

# Spec Review v3

> 评审基准：用户在 v2 反馈中**就地修改** spec.md（version 字段仍为 1）。本评审视为对 v2-修订后 spec 的复检。

## v2 MUST FIX 关闭情况

| v2 # | 状态 | 复检证据 |
|---|---|---|
| 1 AC-2 双 cd 回归 | ✅ CLOSED | 命令改为 subshell 隔离 `(cd ... && python -c "合法") && ! (cd ... && python -c "非法") 2>/dev/null`。在 `/tmp/ac2_v3/` mock 仓库（含真实 Pydantic Repository 模型）实跑，**exit 0**；两 subshell 各自独立 PWD，互不影响 |

## v2 SHOULD FIX 关闭情况（用户承诺全消化）

| v2 # | 状态 | 复检证据 |
|---|---|---|
| 1 AC-13/15 pg_isready SKIP 探针 | ⚠ **spec 已声明 / self_check 实现待 stage 3 落地** | spec AC-13 行 73 + AC-15 行 75 命令前置 `pg_isready -h localhost -p ${DATAPLAT_PG_PORT:-5432} -q && ...`；描述文字注明 "pg_isready 失败 → SKIP"。**但 `scripts/_self_check.sh` 当前 `run_ac` 只有 PASS/FAIL 两态**（行 34-49 无 SKIP 通道）；用户在反馈中承诺 "T-12 实施时记 SKIP 而非 FAIL"——契约清晰在 spec、落地在 T-12 → **本轮 spec 评审可接受**，但记入 stage 3/4 复检点（见下方 §Stage 3 carry-over） |
| 2 风险表 +2 关键风险 | ✅ CLOSED | 行 89 新增 "Pydantic v2 与 SQLAlchemy ORM 类型不一致（UUID/datetime tz-aware）" + 行 90 新增 "domain ↔ protocols 循环 import"；两条均含具体缓解措施（`Mapped[uuid.UUID]` + `timezone=True`；protocols 只 import 具体 domain 子模块） |
| 3 AC-9 Tree 拆表 | ✅ CLOSED | 行 38 显式声明 "Tree 落两张表：trees(hash, repo_id, created_at) + tree_entries(tree_hash FK, position, name, mode, entry_type, target_hash)"；理由完整 |
| 4 AC-16 ruff 范围收窄 | ⚠ **命令收窄但描述未同步** | 行 76 命令收窄到 `apps/api packages/core` ✓；但行 45 §范围列的 AC-16 描述仍写 "`uv run ruff check apps/api packages/core packages/sdk-py worker`"——**描述 vs 命令内部矛盾**。`_self_check.sh` 只执行验证方式列（行 76），不读描述（行 45），不影响机械化门禁通过；但内部漂移可读性差，记入 SHOULD FIX |
| 5 AC-10 isasyncgenfunction | ✅ CLOSED | 行 70 命令含 `import inspect; ...; assert inspect.isasyncgenfunction(get_session), '...'`；在 `/tmp/ac10_v3b/` mock 真实 async generator 实跑 exit 0；mock 普通函数实跑 `AssertionError`（非 0） |
| 6 AC-14/15 单条 shell 合成 | ✅ CLOSED | 行 74 / 75 改为 `(cd ... && pytest ...) && [ "$(...)" -ge N ]` 单条可执行；在 `/tmp/ac14_v3/` 真实 pytest 模拟实跑：6 测试 exit 0，2 测试 exit 1，区分准确 |

## 抽样验证（v3 命令实跑结果汇总）

| AC | 命令 | 验证结果 |
|---|---|---|
| AC-2（subshell） | `(cd packages/core && python -c "...合法...") && ! (cd packages/core && python -c "...非法...") 2>/dev/null` | exit 0 ✓ |
| AC-4（config_hash 64-hex） | `... assert len(...)==64 and all(c in '0123456789abcdef' for c in ...)` | exit 0 ✓ |
| AC-10（async gen 探测） | `import inspect; ...; assert inspect.isasyncgenfunction(get_session), '...'` | async gen exit 0；普通函数 AssertionError 非 0 ✓ |
| AC-13（pg_isready 守门） | `pg_isready ... -q && (cd apps/api && export DATAPLAT_DATABASE_URL=... && uv run alembic upgrade head && ...)` | bash -n exit 0；pg_isready 失败时主命令不执行 ✓ |
| AC-14（pytest + collect 单条）| `(cd packages/core && pytest -q --tb=no tests/) && [ "$(... pytest --collect-only ...)" -ge 6 ]` | 6 测试 exit 0；2 测试 exit 1 ✓ |
| 字面 `...` 全仓扫描 | `grep DATAPLAT_DATABASE_URL=\\.\\.\\.` | 无输出 ✓ |
| Subtype 跨文件用词一致 | `grep -E "Subtype" spec.md tasks.md` | AC-2 / AC-14 / T-1 三处契约可一致解读 ✓ |
| AC-8 ↔ T-3 import 集合 | `grep -oE "(SourceAdapter\|Processor\|...)" spec.md tasks.md \| sort -u` | 两侧 8 元素集合完全相同 ✓ |

## 问题列表

### MUST FIX

无。

### SHOULD FIX（不阻塞 verdict；建议进入 stage 3 前或编码评审时一并处理）

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | spec.md AC-16 §范围（行 45） vs 验证方式（行 76） | 描述写 `ruff check apps/api packages/core packages/sdk-py worker`，命令已收窄到 `apps/api packages/core`——内部矛盾。`_self_check.sh` 只跑命令不读描述，机械化门禁通过，但 stage 4 编码评审会指出描述漂移。 | 把 §范围 AC-16 文字同步收窄到 "ruff check apps/api packages/core"。 |
| 2 | spec.md AC-13/15 SKIP 语义落地（行 73, 75） | spec 已声明 "pg_isready 失败 → SKIP"，但当前 `scripts/_self_check.sh` 的 `run_ac` 只有 PASS/FAIL 两态。**实现落地依赖 T-12 修改 self_check 加 SKIP 通道**——tasks T-12 description 当前仍写 "17 AC 自检；FILTER 接受 core-domain-model"，未要求"加 SKIP 通道"。 | tasks T-12 description 显式补 "T-12 修改 `_self_check.sh` 加 `run_ac_skip <id> <reason>` 函数 + `SKIPPED` 计数；AC-13/15 命令前置 `pg_isready` 失败时走 SKIP 通道，不计 FAIL"。stage 3 实施时 carry。 |
| 3 | spec.md v1 沿留 4 条 SHOULD FIX（用户已承诺在 stage 3/4 / 7 closure 记入 summary §Deferred） | 风险表追加 Lineage N 跳查询性能 / 引用追加 bootstrap-monorepo / AC-11 revision id 约定 / tasks NICE 矩阵双列等。 | 进入 stage 3 前在 summary.md §Deferred 项一次性登记，保留追溯链。 |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | spec.md §待澄清问题（行 110-113） | 仅 2 条且全 `[x]`；现 v3 新增的"AC-13/15 SKIP 通道实现落地点 = T-12"是隐式契约，未在待澄清记录。 | 追加一条 `- [x] AC-13/15 在 Postgres 不可用时由 self_check.sh 走 SKIP 通道，实现归 T-12（见 SHOULD FIX #2）`。 |

## 与 design.md 一致性

- 与 v2 评审结论同：Subtype 完整覆盖 §2.2；config_hash 与 §4.4 差异已显式声明；async session 强约束 §11.7 落实；依赖矩阵兼容。
- 新增：Tree 拆 trees+tree_entries 两表（行 38）与 design.md §4.4 概念一致（Tree 含 entries 列表，平展到 SQL 即两张表），且 spec 给出"平展索引便于查询/diff"理由——比 v2 更明确。

## Stage 3 carry-over（评审接受但记账）

以下事项 spec 已契约清晰，但实现落地依赖后续 stage：

1. **AC-13/15 SKIP 通道实现**：归 T-12（见 SHOULD FIX #2）。
2. **风险表新增的 Pydantic↔ORM 类型一致性**：归 T-7（`Mapped[uuid.UUID]` + `timezone=True` 实现）+ T-10/T-11（专门覆盖时区往返单测）。
3. **风险表新增的 domain↔protocols 循环 import 防护**：归 T-3（protocols 只 import 具体子模块，不导整个 domain；不让 domain/__init__.py 反向 import protocols）。
4. v1 沿留的 tasks SHOULD FIX 1-6（T-7 字段命名分歧 / T-9 索引外键清单 / T-6/T-8 alembic env.py + models/__init__.py re-export / process_tasks reason 字段对称 / AC 覆盖矩阵补全 / T-11 测试隔离策略）：用户承诺 stage 3/4 期间或 stage 7 closure 时加入 summary §Deferred。

## Verdict

APPROVED（MUST FIX 数 = 0）

> 说明：v1 → v2 → v3 累计 5 条 MUST FIX 全部消化（AC-13/15 字面 `...` / AC-14/15 静默吞错 / AC-2 Subtype 漂移 / AC-4 config_hash 格式 / AC-2 双 cd 回归 / AC-8↔T-3 8-import 集合）。6 条 v2 SHOULD FIX 4 条完全 CLOSED，2 条 spec 已契约清晰但 carry 到 stage 3 实施（AC-13/15 SKIP 落地 / AC-16 描述同步）。**stage 2 整体可以进入 stage 3**。

## 复检指引

无需 v4。进入 stage 3 前 Generator 自检：

1. summary.md §阶段进度 stage 1 / 2 状态推进 + 列 review v1/v2/v3 链接 + verdict。
2. summary.md §Deferred 项登记 v1 沿留 SHOULD FIX 4 条（防遗忘）。
3. tasks T-12 description 补 "加 SKIP 通道" 一句（SHOULD FIX #2）；可在 stage 3 第一个 commit 一并修。

## 防复发记账

本变更 stage 2 共经历 3 轮评审、累计 5 条 MUST FIX、4 次实证"AC 命令未在 spec 阶段实跑校验"（bootstrap U+200B / v1 字面 `...` / v2 AC-2 双 cd / v2 AC-14/15 中文叙述非 shell）。已纳入用户 [[project-followup-harness-lint]] 记忆，未来 `harness-tighten-ac-grep-<yyyymmdd>` 变更必须在 spec 模板里强制 Generator 写完 spec 后实跑每条 AC 命令。本评审在该规则落地前以人工实跑兜底；规则落地后此类回归应消失。
