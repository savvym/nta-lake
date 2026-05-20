---
change_id: platform-north-star-pivot-20260520
review_of: coding/coding_report_v1.md
reviewer: claude-stage4-reviewer
version: 1
authored_at: 2026-05-20T18:30:00Z
verdict: APPROVED
---

# Code Review v1

## 机械化检查清单

| # | 检查项 | 结果 | 证据 / 备注 |
|---|---|---|---|
| M-1 | `git log --oneline main..HEAD` 应为 3 个 commit | PASS | 1459f81 / 57bb1a4 / 6167bd4 三个 commit |
| M-2 | `git diff --name-only main...HEAD` 含 5 个核心文件 + change 内 markdown | PASS | 18 文件；5 个核心文件全部在列 |
| M-3 | `bash scripts/_self_check.sh platform-north-star-pivot` 10/10 PASS | PASS | 实跑：PASS 10 / FAIL 0 / SKIP 0 |
| M-4 | `bash scripts/lint/check_design_north_star.sh` exit 0 | PASS | stdout: "OK: design.md north-star structure complete" |
| M-5 | `grep -c run_platform_north_star_pivot scripts/_self_check.sh` ≥ 3 | PASS | 实际计数 5（函数定义 + AC-10 内 grep + AC-10 bash -c + dispatcher + full）|
| M-6 | `grep -n "^## " .harness/design.md \| head -25` 前 7 个是新顶层节 | PASS | 行 8-344：北极星/三层算子模型/stats-first 设计/行级血缘/永不做清单/迁移路径/与业界的关系 |
| M-7 | AC-2 awk `\$0 ~ "^### "k` 双引号 escape 真实跑通 | PASS | 直接执行 bash -c 命令：AC-2 PASS |
| M-8 | extract_section 函数 flag-based 避坑 | PASS | 无 `/start/,/end/` 闭区间 pattern，全部 flag-based |
| M-9 | 负面用例：删掉 § 北极星 → lint exit 1 | PASS | 用 /tmp fixture 验证：exit 1 + "FAIL: design.md 缺少 § '北极星' 顶层节" |
| M-10 | 负面用例：内容 < 100 字节 → lint exit 1 | PASS | fixture 中 stub 正文 → exit 1 + "正文太短" |
| M-11 | `grep -n "\bsub\b" scripts/lint/check_design_north_star.sh` 无残留 | PASS | 无任何 `\bsub\b` 匹配；脚本用 `subname` 变量 |
| M-12 | §1-4 deprecated quote 块格式：标题文字不动 | PASS | 验证：行 348/374/451/563 的二级标题文字与 v0.2 相同 |
| M-13 | §5-11 无 deprecated 标记 | PASS | grep Deprecated 仅命中行 350/376/453/565 |
| M-14 | design.md 版本号 v0.3 | PASS | 行 3："版本：v0.3" |
| M-15 | 无业务代码改动（apps/api/apps/web/worker/packages/core） | PASS | `git diff --name-only main...HEAD` 无 .py/.ts/.tsx |
| M-16 | dispatcher 位置：platform-north-star-pivot 在 web-jobs-list-page 之后 | PASS | 行 1983-1988：case 顺序正确 |
| M-17 | full 链位置：run_platform_north_star_pivot 在 run_web_jobs_list_page 之后、run_harness_ac_behavioral_tier 之前 | PASS | 行 2070/2072/2074 顺序正确 |

---

## A. design.md 改动质量

### A-1 § 北极星

- **一句话定位**：`PASS` — "一个开箱即用的 LLM 训练数据工厂 (data prep platform)：插 Adapter 把世界变成 bronze 文件…" 含关键词，与 AC-1 正则 `LLM 训练数据.{0,5}工厂|data prep` 匹配
- **4 条硬约束**：`PASS` — Bronze=文件树 / Silver+Gold=表 / Lineage=双层 / 永不做 git 数据语义，4 条齐全
- **反边界**：`PARTIALLY PASS` — 实际 4 条（branch/merge/rollback/blob 派生图），不是 coding_report 声称的"6 条"。但 spec T-1 description 只要求"4 条硬约束"，tasks.md 也未明确要求 N 条反边界。4 条覆盖主要场景，与 § 永不做清单 的 9 条 + 用户指向形成合力，评审不阻塞。coding_report 第 29 行"6 条反边界"是笔误（实为 4 条）。
- **reviewer checkpoint 提示**：`PASS` — 行 28 有 `> ⚠ 本节是后续所有 change 的判定基线…约束源文件：data-not-code-pivot.md`

### A-2 § 三层算子模型

- **Adapter/Loader/Operator 三个子节**：`PASS`
- **Protocol 草图签名合理性**：`PASS`
  - `SourceAdapter.ingest(spec, workspace, ctx) -> IngestResult`：合理，workspace 是临时工作区，平台负责 commit
  - `Loader.load(snapshot, config, ctx) -> Iterator[Row]`：合理，输入明确，输出行流
  - `Operator.apply(rows, config, ctx) -> Iterator[Row]`：合理，`kind` 字段明确 mapper/filter/deduplicator/selector/expander 五类语义
  - `reads_stats` / `writes_stats` 显式声明：合理，支持编译期校验
- **例子**：`PASS` — 每节含具体例子（firecrawl-adapter / pdf-mineru-loader / lang-id-filter 等），对标 data-juicer
- **Recipe 新形态**：`PASS` — YAML 示例从 nodes[] of Processor 改为 1 Loader + N Operators，与 spec C-6 一致
- **契约草图声明**：`PASS` — 行 34 有显眼 `> ⚠ 本节为契约草图。Protocol 签名仅在 design.md 中…尚未落到 packages/core/protocols.py`

### A-3 § stats-first 设计

- **reads_stats / writes_stats**：`PASS` — Operator Protocol 中显式声明两个字段；`LangIdFilter` / `PerplexityFilter` / `MinhashDedup` 三个例子具体展示
- **编译期校验说明**：`PASS` — 行 203-206 明确："如果 OperatorB.reads_stats=['perplexity'] 但前面没有任何 Operator 在 writes_stats 里写过 perplexity，编译失败"
- **Row schema 强制部分**：`PASS` — `id / source_ref / lineage_ops / stats` 四个强制字段，`stats: dict[str, float|int|str|bool]` 动态 keys 设计合理

### A-4 § 行级血缘

- **source_ref**：`PASS` — `{repo, snapshot, path, blob_sha, span?}` 定义完整；"每个 Loader 产出每行时必须填"约束明确
- **lineage_ops**：`PASS` — `{name, version, config_hash, snapshot, ts}` 定义完整；expander 场景说明合理
- **反向查询 API 草图**：`PASS` — 3 个 endpoint 草图合理：`GET /lineage/row/{...}` / `GET /lineage/reverse?bronze_blob_sha=` / `GET /lineage/operator-stats`
- **与 commit 级 lineage 关系**：`PASS` — 行 273-278 明确"两层共存不冲突"，并说明粒度差异

### A-5 § 永不做清单

- **9 条 bullet**：`PASS` — branch/merge/cherry-pick/rollback/row-level diff/blob 派生图/Asset/silver 文件树/bronze 强 schema，每条附"用户想要 X 时往哪指"
- **spec 要求覆盖**：`PASS` — AC-3 要求 ≥7 条，实际 9 条；D-2 列出的所有禁令均覆盖
- **末尾审计提示**：`PASS` — "违反任何一条 → reviewer 在 stage 2 必须 MUST FIX 打回"

### A-6 § 迁移路径

- **5 个 processor 重分类**：`PASS`
  - firecrawl → Adapter（已对齐，无需重写）`PASS`
  - pdf-mineru → Loader `PASS`
  - markdown-normalize → Operator(Mapper) `PASS`
  - llm-summarize → Operator(Mapper) `PASS`
  - llm-qa-gen → Operator(Expander) `PASS`
- **迁移策略合理性**：`PASS` — "不强制立刻重写"，给出具体 follow-up change 名
- **21 个已闭环 change 处理**：`PASS` — "不回写"策略明确

### A-7 § 与业界的关系

- **7 行对照表**：`PASS` — data-juicer/The Stack/Dolma/lakeFS/Iceberg/DataHub/HF 7 行全覆盖
- **Fair 评估**：`PASS` — lakeFS/Pachyderm 标"不借鉴"并给出理由（商业证伪），Iceberg 标"思路借鉴"但不上后端，表述公允
- **总结段**：`PASS` — 给出"为什么不直接用 data-juicer"说明

### A-8 deprecated quote 块

- **二级标题文字不动**：`PASS` — `## 1. 目标与设计原则` / `## 2. 核心概念与领域模型` / `## 3. 数据分层规范` / `## 4. 关键抽象的接口设计` 标题文字完全未变
- **§5-11 未过度标记**：`PASS` — §5-11 均无 deprecated 标记，与 D-2 trade-off 说明一致
- **deprecated 内容精确性**：`PASS` — §1 标 1.2 弃用，§2 标 Asset/manifest/Processor 弃用，§3 标 manifest 和推荐→强制变化，§4 标 Processor/nodes-DAG/parents-list 弃用

### A-9 版本号与版本 header

- **v0.3**：`PASS`
- **Header 说明**：`PARTIAL PASS` — Header 写"v0.2 及之前的章节移至文末 § 12 'Deprecated 设计（v1）'"，但实际实现是在 §1-4 原地插入 deprecated quote 块，**没有 § 12 标题**。Header 表述与实现不符（声称移至 § 12，实际保留原位）。属于文字描述不准确，不影响功能。

---

## B. .harness/rules/data-not-code-pivot.md

| 维度 | 结果 | 备注 |
|---|---|---|
| § 永不做清单与 design.md 一致 | PASS | 拷贝 9 条；措辞略有精简（每条无"用户想要"子指引），但核心禁令完全一致 |
| 旧→新术语对照表 | PASS | 含 Processor/Commit/Recipe/Asset/manifest.yaml/Lineage/Silver-Gold-Parquet 7 行 |
| reviewer 必查项 4 条 checkbox | PASS | 含 v2 词汇 / 永不做清单 / silver/gold 形态 / Processor 接口扩展判断 |
| SHOULD-FIX-3 R-6(c) 落地 | PASS（见 SHOULD FIX 复核节） | |
| 松绑流程 | PASS | 4 步流程明确：禁止单个 change 偷偷松绑 → 新建 pivot-v2 change → 走 10 阶段 |
| 历史节 | PASS | 记录创建时间和背景 |

---

## C. CLAUDE.md

| 维度 | 结果 | 备注 |
|---|---|---|
| 新增"理解平台北极星"行 | PASS | 正确指向 `.harness/design.md#北极星`，描述精确含三层算子/stats-first/行级血缘/永不做清单 |
| 硬性约束第 6 条 | PASS | 引用路径 `.harness/rules/data-not-code-pivot.md` 正确；文案明确列出 10 条禁令短名 |
| anchor 正确性 | PASS | GFM anchor `#北极星` 对应标题 `## 北极星`，无转义问题 |

---

## D. lint 脚本质量

| 维度 | 结果 | 备注 |
|---|---|---|
| exit 0 + "OK" | PASS | 实跑验证 |
| 负面用例 exit 1 | PASS | 两种 fixture（无标题 / stub 正文）均产生明确 FAIL 信息 |
| flag-based awk extract_section | PASS | `awk '$0 == "## " t { found=1; next } found && /^## / { exit } found'` 正确避开闭区间陷阱 |
| subname 变量（无 gawk sub 冲突） | PASS | `grep -n "\bsub\b"` 无命中；循环变量为 `subname` |
| SECTIONS 数组 6 项（未含"与业界的关系"） | PASS（有说明价值的观察）| 6 项与 AC-9 spec 一致；`与业界的关系` 未纳入 lint 检查，这是有意取舍（该节无 Protocol 草图需验证），可接受 |
| 三级标题子节检查 awk `$0 ~ "^### "k{found=1}` | PASS | 实跑 Adapter/Loader/Operator 均正确找到 Protocol/class 签名 |

---

## E. self_check block

| 维度 | 结果 | 备注 |
|---|---|---|
| 10 AC 全用 flag-based awk | PASS | AC-1/2/3/4/5/6 全部用 `found && /^## /{exit} /^## X/{found=1} found` 形式 |
| dispatcher 位置 | PASS | web-jobs-list-page(1984) → platform-north-star-pivot(1987) → harness-ac-behavioral-tier(1990) |
| full 链位置 | PASS | run_web_jobs_list_page(2070) → run_platform_north_star_pivot(2072) → run_harness_ac_behavioral_tier(2074) |
| AC-10 自递归 ≥ 3 次 | PASS | `grep -c run_platform_north_star_pivot` = 5（函数定义 + AC-10 内 grep 命令 + AC-10 bash -c 内嵌 + dispatcher + full） |
| bash -c 内双引号 escape | PASS | 直接执行 AC-2 命令确认无引号失效，结果 PASS |

---

## SHOULD FIX 复核（spec v2 reviewer 给出的 3 条）

### SHOULD FIX #1 — locale 漂移（AC-1 `.{0,5}` UTF-8 vs C locale）

**状态：NOT RESOLVED（acceptably 未做）**

证据：`grep "LC_ALL" scripts/_self_check.sh | grep "AC-1"` → 无命中。AC-1 grep 未加 `LC_ALL=C.UTF-8`。
评估：在 GNU grep (glibc) 环境下 `.{0,5}` 在 UTF-8 locale 正确按 Unicode codepoint 计数（已验证实际 design.md 文本 `LLM 训练数据工厂` 命中无问题）。busybox grep 环境有潜在脆性，但本项目运行在标准 Linux 开发环境。属于低风险 NTH，可接受。

### SHOULD FIX #2 — R-5/R-6 未传导到 T-5/T-7/T-8 task description

**状态：PARTIALLY RESOLVED（实现层已满足，task 描述未更新）**

证据：
- T-5 描述原文"name / current 形态 / 新形态 / 何时重写"，实现表中 `当前形态` 列描述了旧 Processor 术语（R-6(b) 已在实现中体现），但未按 spec_review_v2 建议加"currently 使用旧术语"列名。
- T-7 描述原文未提及"标题文字不动 + 顶端插 quote 块"的 R-5 具体格式，但 coding_report D-1 trade-off 和实际实现均符合 R-5 方案。
- T-8 描述原文"永不做清单 + 评审必须确认不违反"，实现中 rule 文件含完整 reviewer 必查项（见 SHOULD FIX #3 验证）。
tasks.md 描述未回写，但这在 spec § 非范围"不回写老 change"的精神下可接受（tasks.md 已历史锁定）。

### SHOULD FIX #3 — R-6(c) reviewer checkpoint 归属

**状态：RESOLVED**

证据：`.harness/rules/data-not-code-pivot.md` § reviewer 必查项 第一条 checkbox：
> `[ ] spec 用 v2 词汇引用 design.md（Loader / Operator / Snapshot / source_ref / stats / lineage_ops）；用旧术语必须有理由`

这正是 R-6(c) 要求的"reviewer 必须查 v2 词汇"的执行触发点。rule 文件是 stage 2 reviewer 的必读文档，这条 checkbox 在评审流程中有明确触达路径。coding_report 声称"已在 data-not-code-pivot.md § reviewer 必查项 落地" — 验证属实。

---

## 问题列表

### MUST FIX

无。

### SHOULD FIX

| # | 文件:行 | 问题 | 建议 |
|---|---|---|---|
| S-1 | `.harness/design.md` 行 3（version header） | header 写"v0.2 及之前的章节移至文末 § 12 'Deprecated 设计（v1）'"，但实际无 § 12 标题，deprecated 内容原地保留于 §1-4 quote 块。描述与实现不符。 | 将 header 中"移至文末 § 12…保留"改为"v0.2 §1-4 就地加 Deprecated quote 块保留，新顶层节在 §1 之前插入"；或添加 `## 12. Deprecated 设计（v1）` 占位标题（内容保持原 §1-4）。后者改动较大，前者只需修一句描述。 |
| S-2 | `.harness/changes/platform-north-star-pivot-20260520/coding/coding_report_v1.md` 行 29 | `T-1` 任务映射说"6 条反边界"，实际 § 北极星 只有 4 条 `- 用户想要...` bullet。tasks.md T-1 description 也不要求"6 条"。 | 将 coding_report 中"6 条反边界"改为"4 条反边界"（事实更正）。 |
| S-3 | `.harness/changes/platform-north-star-pivot-20260520/coding/coding_report_v1.md` 行 17 | `design.md` 改动文件描述说"顶部插入 6 个新顶层节"，实际括号内列了 7 个（北极星/三层算子模型/stats-first/行级血缘/永不做清单/迁移路径/与业界的关系）。 | 将"6 个新顶层节"改为"7 个新顶层节"（与事实一致）。 |

### NICE TO HAVE

| # | 文件:行 | 问题 | 建议 |
|---|---|---|---|
| N-1 | `scripts/lint/check_design_north_star.sh` 行 61 | `awk -v sname="$subname"` 匹配的是 `^### <k>` 前缀而非精确匹配（如将来有 `### AdapterRegistry` 节则 `Adapter` 检查会误命中该节）。目前 design.md 无此问题。 | 收紧为 `$0 == "### " sname` 做精确等值匹配，或 `$0 ~ "^### "sname"( \|$)"` 要求后跟空格或行尾。 |
| N-2 | `scripts/lint/check_design_north_star.sh` 注释行 5 | 注释列出 6 个顶层节（含"迁移路径"但不含"与业界的关系"），与 SECTIONS 数组一致，但读者可能想知道"与业界的关系"为何不纳入 lint。 | 在注释末尾补一行：`# 注：§ 与业界的关系 不强制 lint（无 Protocol 草图验证需求）` |
| N-3 | `scripts/_self_check.sh` AC-1 行 1672 | `grep -qE 'LLM 训练数据.{0,5}工厂\|data prep'` 未显式声明 locale。在非标准环境（busybox grep）下 `.{0,5}` 计字节而非字符。 | 改为 `LC_ALL=C.UTF-8 grep -qE '...'` 或宽化正则为 `.{0,15}`。 |

---

## Verdict

**APPROVED**

所有 10 AC 全部 PASS，lint 脚本 exit 0，无业务代码改动，SHOULD FIX #3 R-6(c) 已在 rule 文件落地。发现 3 条 SHOULD FIX（均为文档描述不准确，不影响功能和流程正确性）和 3 条 NICE TO HAVE，不阻塞通过。

## 后续指引

1. S-1/S-2/S-3 建议在下次 change 触及 coding_report 或 design.md header 时一并修正（不需要专开 change）。
2. N-1 lint 精确匹配问题建议在 `operator-protocol-*` change 中修缮（届时 `### Adapter` 下可能出现更多子节）。
3. S-1 的 `§ 12` 不一致问题：如果后续要加任何 `## 12. ...` 标题，建议在 `api-snapshot-rename-*` 时一起处理。
4. 进入 stage 6 单测评审，结果同本文件所在目录。
