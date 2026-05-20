---
change_id: platform-north-star-pivot-20260520
version: 1
authored_at: 2026-05-20T15:00:00Z
status: draft
ac_kind_lint: exempt
ac_kind_lint_exempt_reason: |
  纯文档 / 治理 change（仅改 .harness/design.md + .harness/rules/* + CLAUDE.md 指针 + scripts/lint），
  无业务代码改动；reviewer 跑 `git diff --stat origin/main..HEAD` 验证。
  虽然 exempt，本 change 仍自带 1 条 behavioral AC（design.md 结构 lint 脚本），
  作为后续 change 引用本 doc 时的可机械化基线。
---

# Spec：北极星 pivot —— "数据加工厂"取代"data 上加 git"

## 背景

到 2026-05-20 闭环 22 个 change（21 dataplat + 1 harness meta），platform demo 跑通了 PDF→MD → JSON sample → SFT 的轴线。在这个节点跟用户做了 4 轮深聊（见 § 决策日志），暴露出 **design.md 的根本定位偏移**：

- design.md §1.2 / §2.2 把平台定位为"data 上加 git"（Asset + Repo + Commit + Tree + Blob + Ref + Lineage DAG），核心隐喻是 lakeFS / Pachyderm
- **业界已经证伪**这条路：lakeFS / Pachyderm 商业上都没起来；客户不要"data git"，要 **lakehouse + lineage**
- 实际 demo 路径里，没人用过 branch / merge / cherry-pick / rollback；commit 在用户眼里就是 snapshot
- 现有 Processor 抽象（repo→repo）跟"行级血缘 / 行级 stats / 行级过滤"完全错位 —— design.md §3.2 写了 `Document.source: SourceRef`，但代码里没人填它
- Asset / `manifest.yaml` 在 design.md 里写了，**3 个月没人去落地**，这本身就是信号

跟用户深聊后达成共识：换北极星。新北极星：

> **一个开箱即用的 LLM 训练数据工厂：插 Adapter 把世界变成 bronze 文件，跑 Loader 把 bronze 变成 silver 表，串 Operator 把表精炼成 gold 表。每行自带 source_ref + stats + lineage_ops 可追溯。重 lineage、轻 versioning，重 schema、轻 git。**

参考实现：data-juicer（算子库）+ The Stack（代码 corpus 形态）+ Dolma / FineWeb（web 数据形态）。

## 问题陈述

design.md 当前版本在 6 个具体地方与新北极星冲突：

| # | 现 design.md 写的 | 新北极星该是的 |
|---|---|---|
| C-1 | §1.2 "以 Asset 而非文件为最小语义单位" | Asset 抽象删除；bronze 用文件树；silver/gold unit 是 row |
| C-2 | §2.2 概念表含 Asset / manifest.yaml | 删 Asset / manifest.yaml；新增 Loader / Operator / Stats |
| C-3 | §3.1 Bronze 要求 `manifest.yaml` | bronze 只要文件树 + dataset-card.yaml |
| C-4 | §3.2 / §3.3 Silver/Gold 推荐 Parquet | **强制** Parquet/JSONL + schema 注册 + 每行 `source_ref` + 每行 `stats` 必填 |
| C-5 | §4.2 Processor = repo→repo 单一抽象 | 拆为三层：Adapter (external→bronze) / Loader (bronze→silver row) / Operator (row→row) |
| C-6 | §4.3 Recipe = nodes[] of Processor | Recipe = 1 个 Loader + N 个 Operator 链 |
| C-7 | §4.4 Commit.parents 是 list（DAG） | parent 是 `str \| None`（线性 snapshot 单链）；branch / merge / cherry-pick **永不实现** |

此外 CLAUDE.md / .harness/rules/ 目前没有"永不做清单"，导致下次 change 仍可能向 git-data 方向漂移。

## 范围

In scope（纯文档 / 治理）：

- **D-1 重写 design.md**：把上面 7 条冲突全部消解，结构按新北极星重新组织
- **D-2 新增 § 永不做清单**：branch / merge / cherry-pick / rollback / row-level diff / blob→blob lineage / Asset / manifest.yaml —— 这些条目附带"为什么不做 + 用户想要 X 时该往哪指"
- **D-3 新增 § 三层算子模型**：Adapter / Loader / Operator 的 Protocol 草图（接口签名 + 输入输出契约 + 例子表），但**不写代码实现**
- **D-4 新增 § stats-first 设计**：silver/gold row 必含 `stats: dict[str, float|str|bool]`；Operator 显式声明 `reads_stats: [...]` / `writes_stats: [...]`
- **D-5 新增 § 行级血缘**：每行必含 `source_ref: {repo, snapshot, path, blob_sha}` + `lineage_ops: [{name, version, config_hash}]`；查询接口草图
- **D-6 新增 § 迁移路径**：把目前已闭环的 5 个 processor（pdf-mineru / llm-qa-gen / llm-summarize / markdown-normalize + adapter-firecrawl）按新模型重分类（哪些是 Loader / 哪些是 Operator-chain），并标记"什么时候要重写"
- **D-7 新增 § 与业界的关系**：明确 data-juicer / The Stack / Dolma / lakeFS 的借鉴 vs 划清界限
- **D-8 新增 `.harness/rules/data-not-code-pivot.md`**：把"永不做清单"做成 rule 文件，所有未来 change 在 stage 2 评审时必须确认不违反
- **D-9 更新 CLAUDE.md**：在"关键文件导航"表加一行指向新 design.md § 北极星；在"硬性约束"加一条引用 data-not-code-pivot rule
- **D-10 新增 `scripts/lint/check_design_north_star.sh`**：design.md 结构 lint 脚本（验证 § 北极星 / § 三层算子 / § 永不做清单 / § 迁移路径 都存在且非空）
- **D-11 self_check 新增 `run_platform_north_star_pivot` block**：6 条 AC 含 D-10 的 behavioral 调用

## 非范围

显式不做：

- **任何业务代码改动**：不动 apps/api、apps/web、worker/src、packages/core。Loader/Operator 的 Protocol 只是 design.md 里的草图，**不**落到 packages/core/protocols.py
- **API/UI 词汇 rename**（Commit→Snapshot）：留给 `api-snapshot-rename-*` 单独做
- **Schema 强制化**（silver/gold 必须 parquet + source_ref）：留给 `silver-schema-enforce-*` 单独做
- **pdf-mineru 改 Loader**：留给 `loader-refactor-pdf-mineru-*` 单独做
- **Operator Protocol 实现**：留给 `operator-protocol-*` 单独做
- **回写老 change**：21 个已闭环 change 的 spec.md / coding_report.md **不改动**；它们是"first-generation Processors"，新 design.md § 迁移路径表标注归类即可
- **delete old design.md sections 整段**：保留为 § "deprecated 设计（v1，仅供历史参考）"，给老 change 引用还能找到原文

## 验收标准

| ID | kind | 描述 | 验证方式 | 期望 |
|---|---|---|---|---|
| AC-1 | static | design.md 含 § 北极星 + 一句话定位 + ≥ 4 条对应硬约束 bullet | `awk '/^## 北极星/,/^## [^#]/' .harness/design.md \| grep -qE '数据加工厂\|data prep' && [ "$(awk '/^## 北极星/,/^## [^#]/' .harness/design.md \| grep -cE '^- ')" -ge 4 ]` | grep 命中 + bullet ≥ 4 |
| AC-2 | static | design.md 含 § 三层算子模型 + 三个子节（Adapter / Loader / Operator）+ 每节有 Protocol 草图 + 例子 | `for k in Adapter Loader Operator; do awk "/^### $k/,/^### [^#]/" .harness/design.md \| grep -qE 'Protocol\|protocol\|class ' \|\| exit 1; done` | 三节都命中 |
| AC-3 | static | design.md 含 § 永不做清单 + ≥ 7 条粗体 bullet（branch / merge / cherry-pick / rollback / row-diff / blob→blob lineage / Asset / manifest.yaml 至少覆盖 7 项） | `[ "$(awk '/^## 永不做/,/^## [^#]/' .harness/design.md \| grep -cE '^- \*\*')" -ge 7 ]` | ≥ 7 条 |
| AC-4 | static | design.md 含 § stats-first + Operator 接口声明 `reads_stats` / `writes_stats` | `awk '/^## stats-first/,/^## [^#]/' .harness/design.md \| grep -qE 'reads_stats' && awk '/^## stats-first/,/^## [^#]/' .harness/design.md \| grep -qE 'writes_stats'` | 两个 grep 都命中 |
| AC-5 | static | design.md 含 § 行级血缘 + `source_ref` + `lineage_ops` 字段定义 | `awk '/^## 行级血缘/,/^## [^#]/' .harness/design.md \| grep -qE 'source_ref' && awk '/^## 行级血缘/,/^## [^#]/' .harness/design.md \| grep -qE 'lineage_ops'` | 两个字段都命中 |
| AC-6 | static | design.md 含 § 迁移路径 + 表格涵盖 5 个 processor | `for p in pdf-mineru llm-qa-gen llm-summarize markdown-normalize firecrawl; do awk '/^## 迁移路径/,/^## [^#]/' .harness/design.md \| grep -q "$p" \|\| exit 1; done` | 5 个名字都命中 |
| AC-7 | static | `.harness/rules/data-not-code-pivot.md` 存在 + 含"永不做"硬约束 + 引用 design.md | `test -f .harness/rules/data-not-code-pivot.md && grep -q '永不做' .harness/rules/data-not-code-pivot.md && grep -q 'design.md' .harness/rules/data-not-code-pivot.md` | 三条都成立 |
| AC-8 | static | CLAUDE.md 指针更新：含一行指向 design.md § 北极星 + 一条硬性约束引用 data-not-code-pivot.md | `grep -q '北极星' CLAUDE.md && grep -q 'data-not-code-pivot' CLAUDE.md` | 两个 grep 都命中 |
| AC-9 | behavioral | `scripts/lint/check_design_north_star.sh` 存在且可独立运行 + 当前 design.md 上 exit 0 | `bash scripts/lint/check_design_north_star.sh` | exit 0 + stdout 含 `OK: design.md north-star structure complete` |
| AC-10 | static | self_check 含 `run_platform_north_star_pivot` 块 + dispatcher + full 调用链（≥ 3 次出现） | `[ "$(grep -c 'run_platform_north_star_pivot' scripts/_self_check.sh)" -ge 3 ]` | grep ≥ 3 次 |

## 风险

| 风险 | 概率 | 影响 | 缓解 |
|---|---|---|---|
| 老 change 引用了 design.md 旧 anchor（如 §11.3 §monorepo） | 中 | 锚点 404 | § "deprecated 设计（v1）"保留旧锚点 |
| 新 design.md 跟 .harness/rules/coding-style.md 冲突 | 低 | 评审困惑 | reviewer stage 2 必查交叉引用，本 spec § "交叉引用清单"已明示 |
| Loader/Operator Protocol 草图被误读为"已经落地" | 中 | 后续 change 跳过实现 | § 三层算子开头加显眼标记"本节为契约草图，实现见 follow-up `operator-protocol-*` / `loader-refactor-*`" |
| 永不做清单太硬，未来需要松绑 | 低 | 改 design 要再走一个 change | design 本身就是受版本控制的；松绑就走 pivot-v2 change，正常流程 |

## 交叉引用清单（reviewer 必查）

stage 2 reviewer 应确认下列文件**没有**被本 change 改动 / 但被本 change**引用**：

- `.harness/rules/development-process.md`（十阶段流程，不动）
- `.harness/rules/coding-style.md`（不动）
- `.harness/rules/engineering-structure.md`（不动）
- `.harness/skills/*/SKILL.md`（不动）
- 21 个已闭环 change 的 spec.md / coding_report.md / summary.md（不动）
- packages/core/ / apps/api/ / apps/web/ / worker/src/ 任何 .py / .ts / .tsx（不动）

被本 change 引用但未改动的：

- `.harness/harness.md`（方法论参考，design.md § 与业界的关系会提及）
- design.md 中的老章节（保留为 § "deprecated 设计（v1）"）

## 决策日志（本 change 由这 4 轮对话沉淀而来）

| 时间（会话） | 决策 | 出处 |
|---|---|---|
| 2026-05-20 ~14:30 | 用户提"process 粒度应该指向文件" | 触发 asset vs blob-lineage vs per-file 三框架分析 |
| 2026-05-20 ~14:45 | 用户问"业界怎么做代码 CPT"；学到 The Stack 行级、Dolma row-embedded provenance | 撤回 BlobDerivation 表方案；转向 row-embedded source_ref |
| 2026-05-20 ~14:55 | 用户提"data 是流不是代码"；学到 lakeFS / Pachyderm 没起来 | 砍 branch / merge / cherry-pick；commit→snapshot 心智 |
| 2026-05-20 ~15:00 | 用户认可 data-juicer 算子模型 + stats-first | 三层算子（Adapter / Loader / Operator）落地 |

## 后续 change 清单（本 change 之外）

依赖本 change 完成后才能开工：

1. **`api-snapshot-rename-*`**：API/UI 词汇 Commit→Snapshot；删 branches 复数 API
2. **`operator-protocol-*`**：落 Operator Protocol + Registry + 第一个标杆算子（如 lang-id-filter）
3. **`silver-schema-enforce-*`**：silver 强制 parquet + schema 注册 + source_ref/stats 必填
4. **`loader-refactor-pdf-mineru-*`**：把 pdf-mineru 重写为 Loader（输出 parquet rows）
5. **`operator-suite-mvp-*`**：一次加 3-5 个标杆 Operator（lang-id / perplexity / minhash-dedup）
6. **`recipe-yaml-v2-*`**：Pipeline YAML 支持新形态（loader + operators[]）
7. **`web-pdf-mineru-ui-*`**（被本 change 推迟）：基于新 Loader / Operator 模型重做 UI

排序：1 / 2 并行 → 3 / 4 → 5 → 6 → 7
