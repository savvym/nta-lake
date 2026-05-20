---
change_id: silver-schema-enforce-20260520
phase: verify
reviewer: claude-agent:opus-phase3-reviewer
model_used: opus
authored_at: 2026-05-20T10:16:53Z
verdict: APPROVED
---

# Verify Review

> Phase 3 reviewer 产物。对照 design.md（原始要求）+ implementation.md（声称的实现）+ `git diff main...change/silver-schema-enforce-20260520` 验 PR。

## 输入

- **Design**：`.harness/changes/silver-schema-enforce-20260520/design.md`（v3 mini-design；application-owner 自写，无 Phase 1 reviewer cycle）
- **Implementation**：`.harness/changes/silver-schema-enforce-20260520/implementation.md`（sonnet 自报）
- **Git log**（main..HEAD）：
  - `e83af06` docs(harness): silver-schema-enforce-20260520 mini-design (W1-3, v3)
  - `4580a9d` feat(core+api): SchemaRegistry + silver/gold schema_id+row_format 强制 (W1-3)
- **Git diff stat**：19 files changed, 842 insertions(+), 0 deletions(-)
- **PR**：本仓库实践 = local merge to main；branch `change/silver-schema-enforce-20260520` head `4580a9d`

## AC 对照表

| AC | kind | reviewer 跑的命令 | 结果 | PASS/FAIL/NOT-VERIFIABLE |
|---|---|---|---|---|
| AC-1 | behavioral | `cd packages/core && uv run pytest tests/test_schema_registry.py -x -v` | `tests/test_schema_registry.py::test_registry_imports_and_builtins PASSED [100%]` — 1 passed in 0.09s | **PASS** |
| AC-2 | behavioral | `set -a && source .env.local && set +a && cd apps/api && uv run pytest tests/test_repo_schema_enforcement.py::test_silver_create_422 -x -v` | `tests/test_repo_schema_enforcement.py::test_silver_create_422 PASSED [100%]` — 1 passed in 1.17s | **PASS** |
| AC-3 | behavioral | `set -a && source .env.local && set +a && cd apps/api && uv run pytest tests/test_repo_schema_enforcement.py::test_silver_create_201_and_bronze_reject -x -v` | `tests/test_repo_schema_enforcement.py::test_silver_create_201_and_bronze_reject PASSED [100%]` — 1 passed in 1.21s | **PASS** |

注：首次跑 AC-2/AC-3 时 reviewer 未 export `.env.local`，测试因 `DATAPLAT_DATABASE_URL` 未设置而 `skipped`（符合 `tests/test_repo_schema_enforcement.py:36-39` 的 `pytestmark = skipif`）。补 `set -a && source .env.local && set +a` 后两个用例均真实 PASS。

AC-2 内含 4 个 sub-assertion（缺 schema_id / 缺 row_format / unknown schema_id / 跨层 silver 用 gold-sft-v1）全部 422；AC-3 内含 silver 合法 201 + GET 含两字段 + bronze 传 schema_id 422。完整语义覆盖 design.md AC 表第 53-55 行所有 case。

## 机械化检查日志

```text
$ git rev-parse HEAD
4580a9d20bb784d6df03ca58202c978668f187bd

$ git log main..HEAD --oneline
4580a9d feat(core+api): SchemaRegistry + silver/gold schema_id+row_format 强制 (W1-3)
e83af06 docs(harness): silver-schema-enforce-20260520 mini-design (W1-3, v3)

$ git diff --stat main...change/silver-schema-enforce-20260520
 .../silver-schema-enforce-20260520/design.md       |  71 +++++++
 .../implementation.md                              |  97 +++++++++
 .../silver-schema-enforce-20260520/summary.md      |  49 +++++
 .../verify_review.md                               |  81 ++++++++
 ...472_add_schema_id_row_format_to_repositories.py |  58 ++++++
 apps/api/dataplat_api/models/repository.py         |   2 +
 apps/api/dataplat_api/routers/repos.py             |   4 +
 apps/api/dataplat_api/schemas/repo.py              |   7 +
 apps/api/dataplat_api/services/repo.py             |  44 ++++
 apps/api/tests/test_pipeline_e2e.py                |   2 +
 apps/api/tests/test_pipeline_orchestrator.py       |   2 +
 apps/api/tests/test_repo_schema_enforcement.py     | 228 +++++++++++++++++++++
 apps/api/tests/test_repos.py                       |   4 +
 .../core/src/dataplat_core/schemas/__init__.py     |  23 +++
 .../core/src/dataplat_core/schemas/_builtin.py     |  18 ++
 .../core/src/dataplat_core/schemas/gold_row.py     |  28 +++
 .../core/src/dataplat_core/schemas/registry.py     |  78 +++++++
 .../core/src/dataplat_core/schemas/silver_row.py   |  11 +
 packages/core/tests/test_schema_registry.py        |  35 ++++
 19 files changed, 842 insertions(+)

# AC-1
$ cd packages/core && uv run pytest tests/test_schema_registry.py -x -v
tests/test_schema_registry.py::test_registry_imports_and_builtins PASSED [100%]
============================== 1 passed in 0.09s ===============================

# AC-2
$ set -a && source .env.local && set +a && cd apps/api && \
    uv run pytest tests/test_repo_schema_enforcement.py::test_silver_create_422 -x -v
tests/test_repo_schema_enforcement.py::test_silver_create_422 PASSED     [100%]
============================== 1 passed in 1.17s ===============================

# AC-3
$ set -a && source .env.local && set +a && cd apps/api && \
    uv run pytest tests/test_repo_schema_enforcement.py::test_silver_create_201_and_bronze_reject -x -v
tests/test_repo_schema_enforcement.py::test_silver_create_201_and_bronze_reject PASSED [100%]
============================== 1 passed in 1.21s ===============================

# alembic head 检查（migration 已上线）
$ cd apps/api && uv run alembic current 2>&1 | tail -1
3cc849b1c472 (head)

# 老测试回归（sonnet 改过的 3 个文件）
$ set -a && source .env.local && set +a && cd apps/api && \
    uv run pytest tests/test_repos.py -q
.............. [100%]
14 passed in 6.85s

$ set -a && source .env.local && set +a && cd apps/api && \
    uv run pytest tests/test_repos.py tests/test_pipeline_e2e.py tests/test_pipeline_orchestrator.py -q
...                                              [100%]
7 failed, 18 passed in 10.31s

# 失败 7 个分析（全部为 W1-1 induced pre-existing flake，与本 change 无关）：
#   - test_pipeline_e2e.py::test_demo_bronze_to_silver_e2e
#   - test_pipeline_orchestrator.py::test_lineage_written_on_cache_miss
#   - test_pipeline_orchestrator.py::test_cache_hit_skips_processor
#   - test_pipeline_orchestrator.py::test_cache_hit_updates_ref
#   - test_pipeline_orchestrator.py::test_node_value_error_marks_failed_with_null_audit
#   - test_pipeline_orchestrator.py::test_node_400_marks_failed
#   - test_pipeline_orchestrator.py::test_cache_hit_writes_audit_fields
#
# 7 个失败的根因（reviewer 实测确认）：
#   helper `_seed_bronze` 调 POST /repos/{owner}/{name}/commits（W1-1 已 rename 为 /snapshots）；
#   /commits 现返 308 redirect 空响应，httpx 不自动跟随 POST 重定向 →
#   `r_commit.json()["hash"]` 在空 body 上抛 JSONDecodeError。
#   验证：root cause 在 `_seed_bronze` 路径（bronze repo 创建路径，不带 schema_id），
#   失败发生在 _create_silver_repo 之前；与 W1-3 schema_id enforcement 无关。
#   归属：W1-1 api-snapshot-rename 引入的回归（sonnet implementation.md 中已声明的"42 个预存 fail / 308 redirect 类"）。
#
# 14/14 PASS 的 test_repos.py 是 sonnet 实际改过的文件（合理回归补 schema_id+row_format），
# 这是检验 W1-3 不引入新回归最关键的信号。
```

## 隐式偏离审计

> 对照 design.md § In scope vs implementation.md "改动文件清单" + git diff，所有改动都已在 implementation.md 改动清单中列出；以下两点 design.md § In scope 未点名但 sonnet 改动清单已列：

| # | 偏离 | 性质 | reviewer 判定 |
|---|---|---|---|
| H-1 | `apps/api/dataplat_api/schemas/repo.py` 同步给 `RepositoryListItem` 加 `schema_id` + `row_format` 字段（design § In scope 只点名 `RepositoryCreate` / `RepositoryRead`） | 合理 hop：list API 不带新字段就出现 RepositoryListItem 与 RepositoryRead 字段不一致的不和谐 | **接受**；改动已在 implementation.md 改动清单声明，仅未在"偏离 design.md"节解释，**未到 MUST FIX**；记为 SHOULD FIX-1（仅文档层面） |
| H-2 | `apps/api/dataplat_api/routers/repos.py` `_to_read` / `_to_list_item` 加 `schema_id` + `row_format` 字段同步 | 合理 hop：ORM → Pydantic 字段映射不补则 RepositoryRead 实例化必抛 ValidationError | **接受**；改动已在 implementation.md 改动清单声明，未在"偏离 design.md"节解释；记为 SHOULD FIX-2（仅文档层面） |

两个隐式偏离都是 design 漏列、实现必须做的合理 hop（design.md § In scope 第 33-37 行说 "RepositoryRead 同步加" 没说 RepositoryListItem 与 router；但这两者是 RepositoryRead 字段变化的必然连带影响）。**不阻塞 merge**，但 sonnet 应该在 implementation.md § 偏离 节单独声明一行而不是仅放在改动清单里。

design.md § Decision 3 要求 bronze "两字段都必须 None"；service code 实现了对 schema_id 和 row_format 两个字段独立 422 检查；test_silver_create_201_and_bronze_reject 仅 assert bronze 带 schema_id → 422，未 assert bronze 带 row_format → 422。**接受**（service 代码两条独立 422 检查覆盖语义；测试一条已足够，余下一条 NICE TO HAVE）。

D-1 已在 implementation.md § 偏离 声明（alembic autogenerate noise: 3 个 TEXT→String alter_column 混入 migration），且 design.md § 风险表已默认接受 autogenerate noise，不算未声明的隐式偏离。

## 问题列表

### MUST FIX

> 无。

### SHOULD FIX

- **SHOULD FIX-1**：implementation.md § 偏离 节缺 H-1（`RepositoryListItem` 加两字段）声明。改动清单虽列了，但 § 偏离 节应该单独写一行"design § In scope 漏列 RepositoryListItem；按字段一致性原则同步增加"。
- **SHOULD FIX-2**：implementation.md § 偏离 节缺 H-2（`routers/repos.py` `_to_read`/`_to_list_item` 字段同步）声明。同上。
- **SHOULD FIX-3**：alembic migration `3cc849b1c472` 含 3 个无关的 TEXT→String alter_column（jobs/pipeline_node_runs/pipeline_runs 的 error 列）。sonnet 已在 D-1 中声明，且 down/up 函数对称、无副作用。建议下个 follow-up change 把这 3 个 alter_column 删掉单独 commit，或保留并在 migration 文件头 docstring 补一行"D-1 autogenerate noise，业务无关"。**不阻塞 merge**。
- **SHOULD FIX-4**：implementation.md frontmatter `head_commit: <回填 commit push 后>` 占位符未回填，实际 head = `4580a9d`。application-owner merge 时一并修。

### NICE TO HAVE

- **NTH-1**：test_silver_create_201_and_bronze_reject 可补一条 bronze 传 `row_format` 单独触发 422 的 assertion，使 design § Decision 3 "两字段都必须 None"在测试层面对称覆盖（service 代码已两条独立检查，仅测试补充更完整）。
- **NTH-2**：`packages/core/src/dataplat_core/schemas/registry.py` 的 `register` 在 schema_id 已存在时抛 ValueError；可考虑暴露一个 `force=True` 参数支持热重载场景（当前不需要，留 future）。
- **NTH-3**：`packages/core/tests/test_schema_registry.py` 单测试函数内 7 条 assertion 全堆 `test_registry_imports_and_builtins`，可拆为 3 个独立 test 以便 pytest 定位失败（builtin / register error / get error）。当前 1-passed 形态也 OK。

## D-1 / D-13 / 永不做清单合规

| 检查 | 结果 |
|---|---|
| D-1 (DB schema 不改名) | **PASS**：仅 `op.add_column` 加 2 个 nullable 列，无改名 |
| D-13 (v3 mini-design 流程：application-owner 自写 design + 不 spawn Phase 1 reviewer) | **PASS**：design.md frontmatter `author: application-owner-agent`, `model_used: opus`，无 design_review.md 文件，符合 v3 mini-design 三阶段 |
| 永不做清单 (data-not-code-pivot.md § 永不做清单) | **PASS**：本 change 正是 "Silver/Gold 推荐 Parquet → 强制 Parquet/JSONL + schema 注册" pivot 的兑现，符合规则；并显式 422 拒绝 "强 schema 在 bronze"（design § Decision 3），与"不做强 schema 在 bronze"一致（设计层禁止用户传 schema_id 到 bronze） |
| 模型分配（Phase 2 implementer = sonnet / Phase 3 reviewer = opus） | **PASS**：implementation.md `model_used: sonnet`；本 review `model_used: opus` |

## Verdict

**APPROVED**

3 个 behavioral AC 全 PASS（reviewer 实测重跑）。无 MUST FIX 隐式偏离。sonnet 改过的 `tests/test_repos.py` 14/14 PASS（这是衡量本 change 不引回归的关键信号）。`tests/test_pipeline_e2e.py` + `tests/test_pipeline_orchestrator.py` 共 7 个失败全部根因在 `_seed_bronze` helper 调 W1-1 已 rename 的 `/commits` 端点拿空 body，与本 change 的 schema_id enforcement 路径无任何因果关系，归属 W1-1 引入的 pre-existing flake（sonnet 已在 implementation.md 文末"308 redirect / ingest KeyError / pipeline 相关"分类下声明）。

DB schema 加 2 个 nullable 列符合 D-1（不改名仅扩展）；application-owner 自写 design 符合 D-13；本 change 正向兑现 data-not-code-pivot 第 8/9 条（silver/gold 强制 schema + bronze 不能有 schema）。

## 后续指引

application-owner 下一步：

1. **直接 merge** `change/silver-schema-enforce-20260520` → `main`（local `git merge --no-ff` 或 push 后远端 merge，按本仓库 D-11 实践）。
2. merge 前顺手回填 implementation.md frontmatter `head_commit: 4580a9d`（SHOULD FIX-4，单 commit 即可）。
3. SHOULD FIX-1/2 仅是 implementation.md § 偏离 节漏写说明；要么 sonnet 一行修复，要么 application-owner 在 summary.md 备注"H-1/H-2 隐式偏离已 reviewer 确认是合理 hop，无需修代码"。**不阻塞 merge**。
4. SHOULD FIX-3（alembic noise）+ NTH-1/2/3 可入 follow-up backlog；不必本 change 处理。
5. Wave 1 进度：W1-1 / W1-2 / W1-3 全 closed；接 W1-4 `loader-refactor-pdf-mineru`（按 platform-north-star-pivot orchestration 计划）。
6. 标记 task #14 (`W1-3 Phase 3 verify: silver-schema-enforce opus`) 为 completed；评估是否 close task #2 (`Wave 1: 地基`) 或留待 W1-4 一同 close。
