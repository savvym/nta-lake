---
change_id: core-domain-model-20260516
target: spec.md
target_version: 1
review_version: 2
reviewer: claude-agent:core-domain-model-stage2-reviewer
reviewed_at: 2026-05-16T21:45:28Z
verdict: REVISION REQUIRED
---

# Spec Review v2

> 评审基准：用户在 v1 反馈中**就地修改** spec.md（version 字段仍为 1），未单独建 spec_v2。本评审视为对"修订后 spec v1"的复检。

## v1 MUST FIX 关闭情况

| v1 # | 状态 | 复检证据 |
|---|---|---|
| 1 AC-13/15 字面 `...` | ✅ CLOSED | `grep DATAPLAT_DATABASE_URL=\\.\\.\\.` 无输出；命令改为 `export DATAPLAT_DATABASE_URL=...full-url... && uv run alembic upgrade head && uv run alembic current` 链式复用，bash -n 通过 |
| 2 AC-14/15 awk 静默吞错 | ✅ CLOSED | 改为 `uv run pytest -q --tb=no` 依赖退出码 + `pytest --collect-only -q \| grep -cE "^tests/"` 取计数；在 `/tmp/ac14_check/` 模拟 6 个测试，grep -c = 6，pytest 退出码语义可靠 |
| 3 AC-2 Subtype Literal 三方契约漂移 | ⚠ **部分 CLOSED + 新引入回归 bug**（见本轮 MUST FIX #1） | spec 显式列出 BronzeSubtype/SilverSubtype/GoldSubtype + Union 别名 + ValidationError 反逻辑；与 tasks T-1 文字一致。**但 AC-2 命令含两次 `cd packages/core`，第二次必失败** |
| 4 AC-4 config_hash 格式 | ✅ CLOSED | 统一为纯 64-hex；命令含 `assert len(...)==64 and all(c in '0123456789abcdef' for c in ...)`；在 mock pydantic 模型上跑通 exit 0 |

## 抽样验证（v2 命令实跑 syntax + 行为）

在 `/tmp/ac{2,4,13,14}_check/` 用真实 Python + Pydantic 跑修复后命令：

| AC | 合法路径 | 反例路径 |
|---|---|---|
| AC-2（合法构造）| `Repository(...subtype='pdf'...)` 成功，`assert r.subtype=='pdf'` exit 0 | — |
| AC-2（反逻辑）| — | `! python -c "Repository(...subtype='bogus-subtype'...)"` exit 0（Pydantic 抛 ValidationError，`!` 反转为 0）✓ |
| AC-2（**整条命令**）| **FAIL**（见 MUST FIX #1） | 第一段 `cd packages/core` 后已在 packages/core，第二段 `&& cd packages/core` 触发 `No such file or directory`，`&&` 链断裂 |
| AC-4 | ProducedBy 构造 + 64-hex 断言 exit 0 ✓ | — |
| AC-13 | `export DATAPLAT_DATABASE_URL=...full URL...` 后 `$DATAPLAT_DATABASE_URL` 真值正确 ✓ | — |
| AC-14 | `pytest --collect-only \| grep -c` 返回 6（在 mock tests/test_a.py 上） | — |

## 问题列表

### MUST FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | spec.md AC-2 验证方式（行 62） | 命令两次 `cd packages/core`：第一段 `cd packages/core && uv run python -c "..."` 后 shell 已在 `packages/core/`，第二段 `&& cd packages/core && ! uv run python -c "..."` 再次 `cd packages/core` 会 `bash: cd: packages/core: No such file or directory`，`&&` 链断裂导致反逻辑命令永不执行，AC-2 在 self_check 中必 FAIL。实测：`bash -c 'cd packages/core && echo "1: $PWD" && cd packages/core && echo "2: $PWD"'` 第二次 cd 失败。**这是 v1 → v2 修复过程中新引入的回归**——v1 命令只 cd 一次，v2 复制粘贴增加反逻辑命令时漏改 cd 路径。**与 bootstrap-monorepo MUST FIX #1（U+200B）+ 本变更 v1 MUST FIX #1（字面 ...）构成同一类问题的第四次实证：spec AC 命令未被实跑验证**。 | 三选一：(a) 用 subshell 隔离两段：``(cd packages/core && uv run python -c "...合法...") && ! (cd packages/core && uv run python -c "...非法...") 2>/dev/null``；(b) 第二段不再 cd，直接 `&& ! uv run python -c "..."`（因前段已在 packages/core）；(c) 把两段拆为两条独立 AC（AC-2a 合法 / AC-2b 反逻辑），各自一行命令——更利于 self_check.sh 编排。建议 (a) 或 (c)。 |

### SHOULD FIX（v1 沿留 + v2 新增；未阻塞 verdict，但建议在进入 stage 3 前处理或在 summary deferred 记录）

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | spec.md AC-13 文字（行 73） | "（需先 `make up`，或在 5432 已被占用时用本机已存在的 Postgres / `PORT=5433` 替代）" 加了端口可替代但 self_check.sh 不会感知 PORT 变量。Postgres 未起时 AC-13 仍 FAIL 而非 SKIP，与 v1 SHOULD FIX #1 同。 | T-12 实施 self_check block 时加 `pg_isready -h localhost -p ${DATAPLAT_PG_PORT:-5432}` 探针；未起标 SKIP。**强烈建议进入 stage 3 之前 spec 明确"Postgres 不可用 → SKIP"语义，否则 stage 8 自检永远红灯**。 |
| 2 | spec.md §风险表（行 81-88） | v1 SHOULD FIX #2 提出的两条关键风险（Pydantic↔SQLAlchemy 类型一致性 / core.domain↔protocols 循环 import）**未追加**。风险表仍 6 条。stage 3 编码评审会问"这些已知坑为何未在风险表"。 | 风险表追加这两条；若刻意 deferred，在 summary §Deferred 项显式记录。 |
| 3 | spec.md AC-9 Tree 拆表（行 38） | v1 SHOULD FIX #3 提出"Tree 拆 trees+tree_entries 两表 vs JSONB"决策未在 spec 主文点名，**未在 v2 修复**。 | §范围或 AC-9 加 "Tree 拆 trees+tree_entries 两表" 一句。 |
| 4 | spec.md AC-16 ruff 范围（行 45） | v1 SHOULD FIX #4 提出 ruff 全仓 lint 易被上一变更遗留阻塞，**未在 v2 调整**。 | 收窄到 `apps/api packages/core`，或在风险表声明"依赖 bootstrap lint clean"。 |
| 5 | spec.md AC-10 get_session 签名（行 39） | v1 SHOULD FIX #5 提出补 `inspect.isasyncgenfunction` 断言，**未在 v2 修复**。 | AC-10 命令追加 `import inspect; assert inspect.isasyncgenfunction(get_session)`。 |
| 6 | spec.md AC-14/15 验证方式格式（行 74-75）| 验证方式列写"`<cmd-A>` 退出码 0 且 collected ≥ N（用 `<cmd-B>` 取数）"——是中文"两条命令合取 + 一段取数说明"，非单一可执行 shell 表达。T-12 实施 self_check block 时需自行合成，留下歧义。 | 合成单条：``cd packages/core && uv run pytest -q --tb=no tests/ && [ $(uv run pytest --collect-only -q tests/ 2>&1 \| grep -cE "^tests/") -ge 6 ]``（AC-15 同改）。便于 run_ac 一行调用。 |

### NICE TO HAVE（v1 沿留）

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | spec.md §关键决策 lineage N 跳查询性能 | v1 NICE #1 未追加 | 风险表或非范围一行 |
| 2 | spec.md §引用追加 bootstrap-monorepo | v1 NICE #2 未追加 | §引用补一行 |
| 3 | spec.md AC-11 revision id `0001` 约定 | v1 NICE #3 未追加 | AC-11 文字加一行 |

## 与 design.md 一致性

- §2.2 Subtype 现严格按 design 列举字面值（BronzeSubtype/SilverSubtype/GoldSubtype + Union），完整覆盖 §2.2 表列项 + 略多（pdf-collection / webpage-collection / dialog-corpus / image-text-pairs / rlhf-pref 为合理扩展）。
- §4.4 lineage config_hash 与 spec 选择"纯 64-hex"已显式声明差异并指引 cas-storage 处理前缀化，可接受。
- 其余与 v1 评审结论一致，依赖矩阵 OK。

## Verdict

REVISION REQUIRED（MUST FIX 数 = 1）

> 说明：4 条 v1 MUST FIX 中 3 条已完全修复，1 条（AC-2 Subtype）修复时新引入 cd 双重 bug。这是 v1 review 末尾 "AC 命令实跑校验未生效" 洞察的**第四次实证**——用户在反馈中已承诺把这条规则纳入 [[project-followup-harness-lint]] 记忆。Reviewer 接受这条 follow-up 安排，但**本轮仍需机械化 fence**：AC-2 命令必须在 self_check.sh 中真的能跑通才能进入 stage 3。

## 复检指引

Generator 修完 spec_v3 后自检：

1. AC-2 命令在 shell 中实跑（**这是本轮唯一阻塞项**）：
   ```bash
   # 模拟仓库根，确保 packages/core 存在
   cd /tmp && mkdir -p repo_check/packages/core && cd repo_check
   # 把 spec AC-2 验证方式列的命令完整复制到这里，bash 解析必须不报 "No such file or directory"
   bash -c '<paste AC-2 command>'
   # 期望：exit 0 或具体业务报错（如 "uv: command not found"），但**绝不能是 cd 路径错误**
   ```
2. AC-14/15 单条合成可执行（SHOULD FIX #6）：
   ```bash
   # 在仓库根跑：
   bash -c "<paste AC-14 verification command>"
   # 命令本身退出码必须有意义，不能要求人工合成
   ```
3. SHOULD FIX 1-5 至少在 summary §Deferred 项显式登记（用户可拒不修，但需留痕）。

提交 v3 后开 `spec_review_v3.md`。

## 防复发记账

本变更 v1 → v2 修复过程出现"修一个 bug 引入另一个 bug"（AC-2 cd 双重）——已被纳入 [[project-followup-harness-lint]] 记忆：未来 `harness-tighten-ac-grep-<yyyymmdd>` 变更必须在 spec 模板里强制"Generator 写完 spec 后在临时目录把每条 AC 命令实跑一遍"作为门禁。本评审接受用户的 follow-up 承诺，但**本轮仍以机械化判据 fence**。
