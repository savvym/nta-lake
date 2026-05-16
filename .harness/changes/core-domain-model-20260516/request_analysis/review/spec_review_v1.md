---
change_id: core-domain-model-20260516
target: spec.md
target_version: 1
review_version: 1
reviewer: claude-agent:core-domain-model-stage2-reviewer
reviewed_at: 2026-05-16T21:34:47Z
verdict: REVISION REQUIRED
---

# Spec Review v1

## 检查清单结论

> 引用 `.harness/skills/expert-reviewer/SKILL.md` §1（plan 模式 spec.md）。

- [x] 背景写明了为什么现在做（§背景 5 条空白）。
- [x] 问题陈述 + 目标可被外部读者理解。
- [x] 范围 / 非范围都有（14 项 in-scope + 6 项 out-of-scope）。
- [~] 每条 AC 可机械化——主体可行，AC-13 / AC-15 命令含字面 `...` bug（MUST FIX #1）。
- [~] 风险有缓解措施——6 条但缺关键风险（SHOULD FIX #2）。
- [x] 没有把 design.md 当新提案（§范围严格收敛到"模型 + ORM + 迁移"）。
- [x] 待澄清问题已清零（2 项全 `[x]`）。

## 抽样验证结论

挑 8 条 AC 在 `/tmp/ac_check/` mock 目录里实跑命令 syntax（不要求 PASS，验证 syntax + 边界）：

| AC | 命令 syntax | 现实结果 |
|---|---|---|
| AC-1 | OK | 6 文件 for 循环正确，齐全 exit 0 / 缺 exit 1 |
| AC-2 | OK | bash -n 解析通过，inline -c 字符串无引号嵌套问题 |
| AC-9 | OK | 7 模块 for 循环；与 design.md §11.3 backend 私有 ORM 一致 |
| AC-11 | OK | 3 文件 test + glob `versions/0001_*.py` |
| AC-12 | OK | tomllib 解析 + 3 依赖断言 |
| AC-13 | **BUG**（MUST FIX #1）| `DATAPLAT_DATABASE_URL=...` 字面赋值，第二段 `alembic current` 用 URL `...` 必失败 |
| AC-14 | 边缘 bug（MUST FIX #2）| 空 pytest 输出时 awk 无 block，`exit` 默认 0 → 静默 PASS |
| AC-15 | 双重 bug | 与 AC-13 同字面 `...` + 与 AC-14 同 awk 漏洞 |

## 问题列表

### MUST FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | spec.md AC-13（行 73）+ AC-15（行 75） | 命令字符串含 `DATAPLAT_DATABASE_URL=...`，bash 把 `...` 当字面字符串赋值，asyncpg 收到 URL `...` 直接 `InvalidArgumentError`。stage 8 自检通过 `bash scripts/_self_check.sh` 复制粘贴执行必失败。与 bootstrap-monorepo MUST FIX #1（命令 vs 真实可执行）同性质。 | 把第二段 `DATAPLAT_DATABASE_URL=...` 改回完整 URL，或命令开头 `export DATAPLAT_DATABASE_URL=postgresql+asyncpg://dataplat:dataplat@localhost:5432/dataplat`，后续两段共享。AC-15 同改。 |
| 2 | spec.md AC-14 / AC-15 验证方式（行 74-75） | `pytest -q ... \| grep -E "^[0-9]+ passed" \| awk '{n=$1; exit (n<6)}'`——当 pytest 因 collection error / import 错误 / fatal crash 不输出 `N passed` 行时，grep 输出为空，awk 无 block 被执行，**`exit` 默认 0**，脚本视作 PASS。即"完全失败的测试 = AC 通过"。已在 `/tmp` 实测确认（empty input → awk exit 0）。 | 改用 `set -o pipefail` + 依赖 pytest 自身退出码（`uv run pytest -q --tb=no tests/`），或在 awk 末尾加 `END { if (NR==0) exit 1 }`。 |
| 3 | spec.md AC-2（行 31, 62） vs AC-14(e)（行 43） vs tasks T-1 | AC-2 描述 `Layer` 与 `Visibility` 是 Literal，但**未把 `Subtype` 定义为 Literal**；AC-14(e) 要测"Layer/**Subtype** Literal 严格校验拒绝未知值"；tasks T-1 description 又写"Subtype Literal 拆 Bronze/Silver/Gold"。三处不一致，stage 4 评审无判据。 | 二选一：(a) AC-2 显式加入 Subtype Literal（按 design.md §2.2 列：拆 BronzeSubtype/SilverSubtype/GoldSubtype 或单一联合 Literal）；(b) 删 AC-14(e) 中"Subtype"，把 T-1 description 改成 `subtype: str`。建议 (a)，与 design.md §2.2 一致。 |
| 4 | spec.md AC-4（行 33, 64） vs design.md §4.4（行 341） | `ProducedBy.config_hash` 在 design.md 是 `"sha256:..."` 字符串（带 `sha256:` 前缀），AC-4 命令用 `'c'*64`（纯 hex 无前缀）。spec 未声明字段格式——是 `sha256:<64hex>` 还是纯 `<64hex>`？stage 4 实施时不知按哪种校验。 | AC-4 字段描述显式声明格式（推荐：纯 `<64hex>`，与 `Commit.hash` / `BlobRef.sha256` 风格统一；前缀化 sha256 留给后续 cas-storage）；命令追加格式断言，例 `assert len(l.produced_by.config_hash)==64 and all(c in '0123456789abcdef' for c in l.produced_by.config_hash)`。 |

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | spec.md AC-13（行 73） | "需先 `make up`" 写在第二列文字里，scripts/_self_check.sh 不会自动 `make up`；若 CI 等价层未起 Postgres，AC-13 永远 FAIL 且无清晰错误信号。 | 在 self_check 本变更 block 开头加 `pg_isready -h localhost -p 5432 -U dataplat` 探针；未起时 AC-13/15 标 `SKIP` 而非 FAIL（区分"集成测试环境缺失"与"实现错误"）。或 spec 显式声明 "AC-13/15 不入 self_check 默认集，单独 integration 子集"。 |
| 2 | spec.md §风险表（行 81-88） | 缺 2 条关键风险：(a) **Pydantic v2 严格类型与 SQLAlchemy 列类型不一致**（如 ORM `Mapped[uuid.UUID]` vs Pydantic `id: str`；ORM `Mapped[datetime]` 时区 vs Pydantic naive；JSONB 列 vs 嵌套 BaseModel 序列化）——AC-15 ORM smoke 会触雷；(b) **core/domain 与 core/protocols 循环 import**（T-3 Protocol 字段引用 domain；若 domain 反向引用 protocols 则成环）。 | 风险表追加这两条，给出缓解：(a) 显式 type 映射表（ORM ↔ Pydantic ↔ JSON repr），在 T-7 description 加入；(b) 约束 `protocols.* from .domain import ...`，禁止反向；用 `from __future__ import annotations` + `TYPE_CHECKING` 守门。 |
| 3 | spec.md §范围 AC-9（行 38） | AC-9 列 ORM 模块含 `tree.py`；AC-13 要求 6 张表（含 `tree_entries`），但 spec 主文未点名"Tree 拆 trees + tree_entries 两表"（design.md §4.4 概念是 Tree 含 entries 列表）。stage 4 评审会问"为何不是 trees.entries_json JSONB"。 | §范围或 AC-9 加 "Tree 拆 trees + tree_entries 两表，便于将来按 entry 索引；commits.lineage 用 JSONB 不拆，参见 §关键决策"。 |
| 4 | spec.md AC-16（行 45） | `uv run ruff check apps/api packages/core packages/sdk-py worker` 把 `packages/sdk-py` / `worker` 纳入 lint，但本变更范围内不动这两个目录；若上一变更遗留任何小问题，本变更被无故阻塞。 | 二选一：(a) ruff 范围收窄到 `apps/api packages/core`；(b) 若坚持全仓 lint，在 §风险表声明"依赖上一变更 lint clean"。 |
| 5 | spec.md AC-10（行 39） | `get_session()` 是 FastAPI dependency 还是普通 async generator？AC-10 命令只校验 import 成功，未验证它是 `AsyncGenerator[AsyncSession, None]`。 | AC-10 命令追加 `import inspect; assert inspect.isasyncgenfunction(get_session)`。 |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | spec.md §关键决策（summary 行 60） | "Lineage 用 JSONB 嵌 commit 行——N 跳上游查询性能权衡"仅在 summary，未在 spec 风险表。stage 4 评审者可能问"何时拆 lineage_edges 表"。 | spec §非范围或风险表加 "Lineage N 跳查询性能：`commits.lineage_json` 行数 > 10k 时考虑衍生 lineage_edges 表（留给 lineage-graph 变更）"。 |
| 2 | spec.md §受影响模块（行 100） | 列 `Makefile 不变`，但 AC-13 假设 `make up` 已存在；建议显式说"docker-compose dev 由 bootstrap-monorepo 提供，本变更复用"。 | §引用追加 `.harness/changes/bootstrap-monorepo-20260516/`。 |
| 3 | spec.md AC-11（行 40） | `versions/0001_initial_schema.py` 文件名约定（4 位数 + snake）未显式说明；alembic 默认是 hash revision id。 | AC-11 文字加 "revision id = `0001`（手工指定），便于线性 history"。 |

## 与 design.md 一致性

- §2.2 Repository / Commit / Tree / Blob / Ref / Lineage / Subtype 全覆盖（AC-1~AC-7）；Subtype 类型语义不严见 MUST FIX #3。
- §4.4 Commit lineage 嵌入式 JSON 与 spec §关键决策（commits.lineage JSONB）一致；`config_hash` 格式与 §4.4 表述有出入（MUST FIX #4）。
- §4.1 / §4.2 SourceAdapter / Processor / RunContext 三 Protocol 在 AC-8 + tasks T-3 覆盖（T-3 还含 5 个数据类，见 tasks_review）。
- §11.7 第 1 条 async session 强约束被 AC-10 / AC-11 落实（async engine + async alembic env）。
- §11.2 后端技术栈对齐：sqlalchemy 2.0 + alembic + asyncpg + pydantic v2。
- **依赖兼容性独立核验**：sqlalchemy 2.0.x 原生支持 asyncpg；alembic 1.13 兼容 SA 2.0；asyncpg 0.29+ 支持 Postgres 16；docker-compose.dev.yml 用 postgres:16 完全匹配。依赖矩阵 OK。

## Verdict

REVISION REQUIRED（MUST FIX 数 = 4）

## 复检指引

Generator 修完 spec_v2.md 后自检：

1. AC-13 / AC-15 字面 `...` 移除：
   ```bash
   grep -nE "DATAPLAT_DATABASE_URL=\\.\\.\\." .harness/changes/core-domain-model-20260516/request_analysis/spec.md
   ```
   应无输出。
2. AC-14 / AC-15 awk 空输入语义：
   ```bash
   echo "" | awk '{n=$1; exit (n<6)} END {if (NR==0) exit 1}'
   echo "$?"  # 必须为 1
   ```
3. Subtype 在 AC-2 / AC-14(e) / tasks T-1 用词一致：
   ```bash
   grep -nE "Subtype" .harness/changes/core-domain-model-20260516/request_analysis/{spec.md,tasks.md}
   # 三处对 Subtype 是 Literal 还是 str 给出同一答案
   ```
4. ProducedBy.config_hash 格式有显式规定（纯 hex64 或 sha256: 前缀），AC-4 命令含格式断言。
5. §风险表条目数 ≥ 8（追加 Pydantic↔ORM 类型一致性 + protocols/domain 循环 import）。

提交 v2 后开 `spec_review_v2.md`。
