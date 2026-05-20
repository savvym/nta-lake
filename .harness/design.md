# LLM 训练数据管理平台架构设计

> 版本：v0.3（**北极星 pivot - 2026-05-20**：定位从"data 上加 git"转为"LLM 训练数据工厂"；引入三层算子 Adapter/Loader/Operator + stats-first + 行级血缘；§ 永不做清单写入硬约束。v0.2 及之前的章节移至文末 § 12 "Deprecated 设计（v1）"保留，结构上由新顶层节作权威定义）
> 范围：为预训练 (CPT) / SFT / 评测等场景提供端到端的数据工程能力。

---

## 北极星

**一句话定位**：一个开箱即用的 LLM 训练数据工厂 (data prep platform)：插 Adapter 把世界变成 bronze 文件，跑 Loader 把 bronze 变成 silver 表，串 Operator 把表精炼成 gold 表。每行自带 source_ref + stats + lineage_ops 可追溯。重 lineage、轻 versioning，重 schema、轻 git。

**对标系统**：data-juicer（算子库形态）+ The Stack / StarCoder（代码 corpus 行级形态）+ Dolma / FineWeb / RefinedWeb（web 数据行级形态）。**不**对标 lakeFS / Pachyderm（"data 上加 git"路线已被业界证伪）。

**4 条硬约束**（违反即流程失败，详见 § 永不做清单）：

- **Bronze = 文件树**：保留 CAS 去重 + 不可变 snapshot；不要求 manifest.yaml；不强 schema
- **Silver / Gold = 表**：强制 Parquet/JSONL + schema 注册 + 每行 `source_ref` + 每行 `stats` 字段必填
- **Lineage = 双层**：commit 级（snapshot 之间由谁跑出来的）+ 行级（每行 source_ref + lineage_ops）；**不**做 blob→blob 派生图
- **永不做 git 数据语义**：branch / merge / cherry-pick / rollback / row-level diff 永不实现；commit 在 API/UI 心智上是 snapshot（API rename 见 follow-up `api-snapshot-rename-*`）

**北极星的"反"边界**（用户想要 X 时往哪指）：

- 用户想要"分支不同数据子集" → 用新建 silver/gold repo + 不同 Operator config，**不**给 branch
- 用户想要"合并两个数据集" → 用 union Operator 或新建 repo 同时 Loader 多个 bronze，**不**给 merge
- 用户想要"回滚某次 commit" → 新建 commit 把内容退回到老 snapshot；**不**给 rollback / force-push
- 用户想要"知道某行 silver 出自哪个 bronze blob" → 看 row.source_ref + row.lineage_ops；**不**给 blob 派生图查询

> ⚠ 本节是后续所有 change 的判定基线。stage 2 reviewer 评审时必须确认 change 不违反 4 条硬约束 + 6 条反边界。约束源文件：`.harness/rules/data-not-code-pivot.md`。

---

## 三层算子模型

> ⚠ **本节为契约草图**。Protocol 签名仅在 design.md 中以代码块形式给出，**尚未落到 `packages/core/protocols.py`**。实现见 follow-up：`adapter-protocol-*`（已部分落地为 SourceAdapter）/ `loader-protocol-*` / `operator-protocol-*`。在此之前，请勿基于"protocol 已存在"假设写 change spec。

新模型把"数据从外部世界 → 训练就绪表"的过程拆为三层独立算子。每层有自己的 Protocol、输入输出契约、错误语义。

| 层 | 接口签名 | 输入 | 输出 | 跑在哪 | 例子 |
|---|---|---|---|---|---|
| **Adapter** | `(spec, workspace, ctx) -> IngestResult` | 外部世界（URL / 上传文件 / API） | 一棵 bronze 文件树（snapshot） | RQ worker / 容器 | firecrawl-adapter / raw-pdf-upload / arxiv-fetcher / github-clone |
| **Loader** | `(bronze_snapshot, config, ctx) -> Iterator[Row]` | 1 个 bronze snapshot + glob/filter | 一组 silver row（含 source_ref + 初始 stats） | RQ worker（可重 IO / GPU） | pdf-mineru-loader / html2md-loader / code-file-loader |
| **Operator** | `(rows, config, ctx) -> Iterator[Row]` | 一组 silver/gold row | 一组 row（变形 / 过滤 / 扩展 / 聚合） | RQ worker（多数轻量，dedup 类需全局视图） | lang-id-filter / perplexity-filter / minhash-dedup / llm-qa-gen / repo-packing |

### Adapter

```python
class SourceAdapter(Protocol):
    name: str                # 唯一标识，如 "firecrawl-url"
    version: str             # 语义版本
    input_schema: JSONSchema # 接受什么样的输入 spec
    output_subtype: str      # 产出的 bronze subtype

    def ingest(
        self,
        spec: dict,                # 符合 input_schema
        workspace: Path,           # 平台分配的临时工作区
        ctx: RunContext,           # 日志 / metrics / secrets / cancel
    ) -> IngestResult:
        """产出一棵符合 Bronze 规范的文件树。
        平台负责把工作区 commit 到目标 bronze repo。"""
```

例子（已实现）：
- `FirecrawlAdapter(spec={"urls": [...], "render_js": true})` → `assets/<id>/content.md + images/`
- `RawPDFUploadAdapter(spec={"file_id": "..."})` → `content/<filename>.pdf`

### Loader

```python
class Loader(Protocol):
    name: str
    version: str
    config_schema: JSONSchema
    accepts: list[BronzeSelector]    # 接受哪些 bronze subtype
    output_schema: SchemaRef          # 产出 row 的 schema（必含 source_ref + stats）

    def load(
        self,
        snapshot: BronzeSnapshotView, # 1 个 bronze snapshot 的只读视图
        config: dict,                 # 符合 config_schema
        ctx: RunContext,
    ) -> Iterator[Row]:
        """遍历 bronze 文件，产出 silver row 流。
        每行必须填 source_ref{repo,snapshot,path,blob_sha}。
        Loader 通常是重活：跑 OCR / 模型推理 / API 调用。"""
```

例子：
- `pdf-mineru-loader`（待重写：将 `apps/api/dataplat_api/processors/pdf_mineru.py` 拆为 Loader）：bronze PDF blob → silver `{id, source_ref, text, page_count, image_refs[], lang, stats: {...}}` 行
- `code-file-loader`：bronze 代码文件 → silver `{id, source_ref, repo_name, path, content, language, license, stats: {alphanum_fraction, max_line_length, ...}}`，对标 The Stack
- `html2md-loader`：bronze HTML → silver Document.v1 schema

### Operator

```python
class Operator(Protocol):
    name: str
    version: str
    config_schema: JSONSchema
    kind: Literal["mapper", "filter", "deduplicator", "selector", "expander"]
    reads_stats: list[str]     # 显式声明读哪些 stats
    writes_stats: list[str]    # 显式声明写哪些 stats
    accepts_schema: SchemaRef  # 接受的 row schema
    output_schema: SchemaRef   # 产出的 row schema（可与输入相同）

    def apply(
        self,
        rows: Iterator[Row],   # 流式输入
        config: dict,
        ctx: RunContext,
    ) -> Iterator[Row]:
        """逐行（或全局）变形 / 过滤 / 扩展。
        kind 决定语义：
          - mapper: 1 row → 1 row（原地变 text / 补 stats）
          - filter: 1 row → 0 or 1 row（按 stats 留/丢）
          - deduplicator: N rows → M rows（全局视图，N ≥ M）
          - selector: N rows → K rows（top-K / 分位）
          - expander: 1 row → N rows（如 llm-qa-gen 把 1 doc 扩成 N QA pair）"""
```

例子（参考 data-juicer 算子库）：
- Mapper：`markdown-normalize` / `whitespace-clean` / `pii-redact`
- Filter：`lang-id-filter(allow=[en,zh])` / `alphanum-fraction-filter(min=0.25)` / `perplexity-filter(model=kenlm, max=800)`
- Deduplicator：`minhash-dedup(threshold=0.85)` / `simhash-dedup`
- Selector：`topk-by-stat(stat=quality_score, k=10000)`
- Expander：`llm-qa-gen(model=claude-opus-4-7, records_per_doc=N)` / `repo-packing(max_tokens=8192)`

### Recipe（新形态）

老 Recipe：N 个 Processor 节点 DAG（repo → repo）。
**新 Recipe**：1 个 Loader + N 个 Operator 链（行流水线）。

```yaml
# recipes/code-cpt-v1.yaml
name: code-cpt-v1
loader:
  name: code-file-loader@0.1
  inputs: [bronze/anthropic/github-py-snapshot@main]
  config:
    include_ext: [.py, .pyi]
    exclude_paths: ["**/test_*"]

operators:
  - { name: lang-id-filter@0.1,            config: { allow: [en, zh], min_confidence: 0.9 } }
  - { name: license-filter@0.1,            config: { allow: [MIT, Apache-2.0, BSD-3-Clause] } }
  - { name: alphanum-fraction-filter@0.1,  config: { min: 0.25, max: 0.95 } }
  - { name: perplexity-filter@0.1,         config: { model: kenlm-py, max_perplexity: 800 } }
  - { name: minhash-dedup@0.1,             config: { threshold: 0.85, num_perm: 128 } }
  - { name: repo-packing@0.1,              config: { max_tokens: 8192, separator: "<|file|>" } }

output: gold/anthropic/code-cpt-v1@auto
```

每个 Operator 跑完留 `stats/op_<name>_stats.json`（保留 / 丢弃 / 中位某指标），UI 直接画漏斗图。Pipeline 整体可解释 —— 像 SQL query plan。

---

## stats-first 设计

灵感来自 data-juicer：**每行的 `stats` 字段是一等公民**。每个 Operator 要么**算 stat**（perplexity / lang / token_count / alphanum_fraction），要么**按 stat 过滤**。这让 pipeline 整体可解释、可单元测试、可逐步调试。

### Row Schema（silver/gold 强制部分）

```python
class Row(BaseModel):
    # 行级血缘（强制，详见 § 行级血缘）
    id: str                              # row 唯一 id
    source_ref: SourceRef                # 指回 bronze blob
    lineage_ops: list[OpRef]             # 经过的 operator 链

    # stats（强制 dict 存在，但 keys 由 Operator 动态写）
    stats: dict[str, float | int | str | bool]

    # 业务字段（subtype-specific）
    # text, prompt, response, repo_name, ...
```

### Operator stats 契约

```python
class LangIdFilter(Operator):
    name = "lang-id-filter"
    kind = "filter"
    reads_stats = []           # 自己算 lang_id，不依赖前面
    writes_stats = ["lang_id", "lang_confidence"]
    # apply(): 算出 lang_id 写入 stats，再按 allow list 留/丢

class PerplexityFilter(Operator):
    name = "perplexity-filter"
    kind = "filter"
    reads_stats = []
    writes_stats = ["perplexity"]

class MinhashDedup(Operator):
    name = "minhash-dedup"
    kind = "deduplicator"
    reads_stats = []           # 自己算 minhash
    writes_stats = ["minhash_signature", "is_duplicate"]
```

### 编译期校验

Pipeline 加载时静态校验：

- 如果 `OperatorB.reads_stats = ["perplexity"]` 但前面没有任何 Operator 在 `writes_stats` 里写过 `perplexity`，**编译失败**（fail-fast，不要等运行时）
- 输出 `output_schema` 与下一个 Operator 的 `accepts_schema` 必须兼容

### 与 SQL/Iceberg 的关系

silver/gold 的"表"在物理上就是 Parquet 分区，stats 字段是 Parquet 列。可以直接用 DuckDB / Spark 跑 SQL：

```sql
SELECT lang_id, COUNT(*), AVG(perplexity)
FROM silver_normalized_text
WHERE quality_score > 0.7
GROUP BY lang_id;
```

这是 design.md v0.2 完全没做的可能性 —— v0.2 silver 是文件树，没法这么查。

---

## 行级血缘

每行 silver/gold row 必含两个字段，组合起来回答"这行从哪来 + 经过谁的处理"：

### source_ref（指回源头）

```python
class SourceRef(BaseModel):
    repo: str          # e.g. "bronze/anthropic/github-py"
    snapshot: str      # commit/snapshot hash
    path: str          # bronze 文件树中的相对路径
    blob_sha: str      # CAS blob sha256
    span: Span | None = None  # 可选：行/字节范围（如 PDF 第 N 页）
```

- **每个 Loader 产出每个 row 时必须填 source_ref**（不可缺）
- 一行只能有 1 个 source_ref；如需多源（e.g. dedup 后合并）走 `lineage_ops[].input_refs` 留痕
- Bronze 行**没有** source_ref（它们就是源头）

### lineage_ops（经过的算子链）

```python
class OpRef(BaseModel):
    name: str          # e.g. "lang-id-filter"
    version: str       # e.g. "0.1"
    config_hash: str   # sha256(canonical_json(config))
    snapshot: str      # 输出 snapshot hash（用于 join 回 commit 级 lineage）
    ts: datetime
```

- Loader 写 row 时填 1 个 OpRef（loader 自己）
- 每个 Operator 在 apply 末尾追加 1 个 OpRef
- expander 算子（如 llm-qa-gen）产出的 N 行**共享父 row 的 lineage_ops 前缀**，区别只在最后一项（含 expander 自己 + 同一个 row_id 的不同子 id）

### 查询接口（API 草图）

```
GET  /lineage/row/{repo}/{snapshot}/{row_id}
     → { source_ref, lineage_ops[], commit_level_lineage }

GET  /lineage/reverse?bronze_blob_sha={sha}
     → [ {silver_repo, snapshot, row_id}, ... ]  # 哪些 silver row 引用了这个 blob

GET  /lineage/operator-stats?op_name={n}&op_version={v}
     → { rows_in: N, rows_out: M, ratio: ..., distribution: {...} }
     # operator 漏斗统计；UI 用
```

### 与 commit 级 lineage 的关系

两层 lineage **共存不冲突**：

- **commit 级**（保留 design.md §4.4 的 `lineage` 字段）：snapshot → snapshot 由什么 recipe 跑出来的。粗粒度，回答"哪个 recipe 版本生成了 silver/x@abc123"。
- **行级**（本节）：每行自带 source_ref + lineage_ops。细粒度，回答"silver/x@abc123 的第 7 行 row 来自 bronze/y@def456 的 paper.pdf 第 3 页"。

行级 lineage 是 commit 级的"细节"，查询时可 join。

---

## 永不做清单

这些功能在新北极星下**永不实现**。每条附"为什么不"+"用户想要 X 时往哪指"。

- **不做 branch**：训练数据没有"实验分支"语义；用新建 repo 或 fork 表达"另一份数据"。
  - 用户想要：用 `POST /repos` 新建 silver/x-experiment 跑不同 Operator config
- **不做 merge**：数据不需要合并冲突解决；用 union Operator 或 Loader 多 input。
  - 用户想要：写一个 Recipe 让 Loader 接 N 个 bronze input + union Operator 拼起来
- **不做 cherry-pick**：snapshot 是原子写入产物，不存在"挑某几个改动"。
  - 用户想要：跑一个 Operator filter 把想要的 row 选出来，写新 snapshot
- **不做 rollback / force-push**：snapshot 不可改；已被训练用过的 snapshot 永不可删。
  - 用户想要：新建 commit 把内容退到老 snapshot（前向 commit）
- **不做 row-level diff**：行没有"修改前/修改后"语义；每次 Operator 输出是新行。
  - 用户想要：跑 join + filter 做"两个 snapshot 的 set diff"
- **不做 blob → blob 派生图**：每行的 source_ref 已经存了源 blob 引用，blob 级派生图查询走 `/lineage/reverse?bronze_blob_sha=...` 即可，**不**额外建 BlobDerivation 表。
  - 用户想要："这个 PDF 派生了哪些 silver row" → `GET /lineage/reverse?bronze_blob_sha={pdf_sha}`
- **不做 Asset 抽象 / manifest.yaml 强制**：bronze 用文件树就够；`manifest.yaml` 是 design.md v0.2 的失败遗产。
  - 用户想要"按逻辑包整组处理" → Loader 的 config 接 `include_paths` glob
- **不做"silver 是文件树"**：silver/gold 强制表形态；不允许往 silver/gold repo 直接写 .md / .txt 文件树。
  - 用户想要预览：silver Parquet → 平台自动生成 sample.jsonl 给 UI
- **不做单测覆盖率 / 强 schema 在 bronze**：bronze 只要文件树 + dataset-card.yaml；schema 在 silver/gold 强制。
  - 用户想要 schema：升 silver 用 Loader 转

**违反任何一条 → reviewer 在 stage 2 必须 MUST FIX 打回**。约束源文件：`.harness/rules/data-not-code-pivot.md`。

---

## 迁移路径

到 2026-05-20，已有 5 个 first-generation Processor / Adapter（在新模型下重分类）：

| 现有名 | 当前形态 | 新分类 | 何时重写 |
|---|---|---|---|
| `apps/api/dataplat_api/adapters/firecrawl.py` | SourceAdapter（已对齐） | Adapter（无需重写） | n/a，沿用 |
| `apps/api/dataplat_api/processors/pdf_mineru.py` (name=`pdf-mineru`) | Processor（repo→repo, 写 .md 文件树） | **Loader**（bronze PDF → silver Document 行） | `loader-refactor-pdf-mineru-*` |
| `apps/api/dataplat_api/processors/markdown_normalize.py` (name=`markdown-normalize`) | Processor（repo→repo, 改 .md 内容） | **Operator (Mapper)**（行级 text clean） | `loader-refactor-pdf-mineru-*` 之后 `operator-suite-mvp-*` 一起重写 |
| `apps/api/dataplat_api/processors/llm_summarize.py` (name=`llm-summarize`) | Processor（repo→repo, 调 LLM） | **Operator (Mapper)** | `operator-suite-mvp-*` |
| `apps/api/dataplat_api/processors/llm_qa_gen.py` (name=`llm-qa-gen`) | Processor（repo→repo, 1 doc → N QA） | **Operator (Expander)** | `operator-suite-mvp-*` |

**迁移策略**：

- **不**强制立刻重写。Processor 抽象在 follow-up `operator-protocol-*` 落地之前保留 work
- 新的 PDF→MD / 其他数据加工需求**仍可**走老 Processor 接口（标注"first-gen Processor"，不阻塞）
- `loader-refactor-pdf-mineru-*` 完成后，pdf-mineru 退役老路径
- 5 个 Processor 全部重写完后，老 `Processor` Protocol 进 `.harness/rules/data-not-code-pivot.md` 的 deprecated 清单 → 后续不允许新增 first-gen Processor

**21 个已闭环 change 处理策略**：**不回写**。它们的 spec / coding_report / summary 永远保留旧术语（Processor / commit DAG / Asset 等）。新 change 评审时 reviewer 必须用 v2 词汇引用本 design.md。

---

## 与业界的关系

| 系统 | 借鉴什么 | 划清什么 |
|---|---|---|
| **data-juicer** | 算子库三类（Mapper/Filter/Deduplicator）+ stats-first + YAML pipeline | 不直接依赖其代码（会粘上其实现细节）；自己实现 Protocol；长远兼容其 YAML config |
| **The Stack / StarCoder data** | 代码 corpus 行级形态（1 row = 1 file 含 hexsha/path/repo_name/license）+ repo-packing 训练样本 | 我们覆盖更广（多模态、PDF、网页），不只是代码 |
| **Dolma / FineWeb / RefinedWeb** | row-embedded provenance（每行带 source URL/timestamp/script_version）+ 漏斗式 filter pipeline | 同上，更通用 |
| **lakeFS / Pachyderm** | （**不借鉴**）数据 git 路线 | 这俩商业上证伪了；客户不要 data-git，要 lakehouse + lineage |
| **Apache Iceberg / Delta Lake** | snapshot 线性版本 + immutable data file + schema evolution 思路 | 不上 Iceberg/Delta 后端（PB 级才需要，现在不必） |
| **DataHub / OpenLineage** | job-level lineage 概念（commit 级 lineage 就是这一类） | 我们 lineage 同时含 commit 级 + 行级，DataHub 只到 table 级 |
| **HuggingFace Datasets** | dataset card / schema 注册 / 分发体验 | 我们不做分发市场（至少 Phase 1）|

**为什么不直接用 data-juicer 做后端**：data-juicer 不管行级血缘 / source_ref / Loader 这层 / 不管 snapshot 版本控制。我们的范围更宽，借鉴抽象但自己实现，保持架构主权。

---

## 1. 目标与设计原则

> ⚠ **Deprecated 设计（v1）** —— 本节 § 1.2 "以 Asset 而非文件为最小语义单位"已被北极星 pivot 弃用。v2 权威定义见 [§ 北极星](#北极星) 与 [§ 三层算子模型](#三层算子模型)。本节内容保留以防止老 change 引用 404。

### 1.1 目标
- 统一管理面向 LLM 训练的多源、多格式、多阶段数据。
- 提供 **Bronze → Silver → Gold** 三层的数据加工流水线。
- 把 **"数据集 (Repository)"** 做成像 HuggingFace 一样的一等公民：有 Card、有 Files、有 Versions、有可分享的 ID。
- **可插拔**：任何新的数据源、新的处理逻辑（含 LLM / Agentic）都能以插件形式接入，而不需要改主干。
- **可追溯**：任何一条 Gold 数据都能反查回它的 Silver / Bronze 来源、所用处理器、所用配置。

### 1.2 设计原则
1. **以"资产 (Asset)" 而非"文件"为最小语义单位**。一个资产可以是 1 个 PDF，也可以是 1 本书的 30 个 md，也可以是 1 个网页的 md+images。
2. **三层共用同一套 Repository 模型**，差异只在 `layer` 属性、schema 约束和血缘位置。
3. **获取器和处理器是同构的**——都是 `(inputs, config) → new_version`，只是 inputs 来源不同。
4. **版本和血缘是内置的**，不可选、不可绕过。
5. **存算分离**：元数据在数据库，内容在对象存储；版本控制走 CAS（内容寻址）。
6. **从 Day 1 起就提供 SDK / CLI / API / UI 四种入口**，但 UI 可以最后做。

### 1.3 非目标
- 不做训练框架本身（Megatron、TRL 之类不在范围内）。
- 不做实验追踪（W&B 之类）。但要能被它们引用。
- 不做实时数据流（Kafka 之类）。本平台是 batch / pipeline 思维。

---

## 2. 核心概念与领域模型

> ⚠ **Deprecated 设计（v1）** —— 本节 § 2.2 概念表中的 `Asset` / `manifest.yaml` 已弃用（bronze 不要求 manifest）。`Processor` 抽象拆为 Loader + Operator（v2 见 [§ 三层算子模型](#三层算子模型)）。v2 权威概念定义见 [§ 北极星](#北极星)。本节保留以防止老 change 引用 404。

### 2.1 领域模型一图概览

```
┌─────────────────────────────────────────────────────────────────┐
│                         Repository                              │
│  (Bronze / Silver / Gold 三层共用此抽象)                        │
│                                                                 │
│   id, owner, name, layer, subtype, visibility, card             │
│                                                                 │
│   ├── refs (main, dev, tag/v1.0, ...)                           │
│   │     └── points to Commit                                    │
│   │                                                             │
│   ├── Commits (有向链，类 Git)                                  │
│   │     └── parents[], tree, author, time, lineage_info         │
│   │                                                             │
│   └── Tree → Files (logical path → blob hash)                   │
│         └── Blobs 存储在对象存储, 按 sha256 寻址                │
└─────────────────────────────────────────────────────────────────┘

                ▲                                  ▲
                │  produces                        │  consumes
                │                                  │
        ┌───────┴────────┐                ┌───────┴────────┐
        │ Source Adapter │                │   Processor    │
        │   (Fetcher)    │                │ (含 LLM/Agent) │
        └────────────────┘                └────────────────┘
```

### 2.2 概念定义

| 概念 | 说明 |
|---|---|
| **Repository** | 数据集，HF 风格的库。是版本、ACL、Card、血缘的归属单位。 |
| **Layer** | Repository 所属层：`bronze` / `silver` / `gold`。 |
| **Subtype** | 二级类型。Bronze: `pdf` / `webpage` / `book` / `image-set` / ...；Silver: `text-corpus` / `qa-records` / ...；Gold: `cpt` / `sft` / `dpo` / `eval`。 |
| **Asset** | Bronze 层中的逻辑资产。一个 Repository 通常承载一个或多个 Asset。Asset 是带类型的、含 1～N 个文件的逻辑包。 |
| **File** | Repository tree 中的一个文件条目（path + blob hash + size + type）。 |
| **Blob** | 实际字节内容。按 sha256 内容寻址，存储在对象存储。 |
| **Commit** | Repository 的一次原子变更。指向一个 Tree、一组 parents、附带 lineage 元信息。 |
| **Ref** | 指向 Commit 的可变指针。如 `main`、`v1.0`、`pr-7`。 |
| **Source Adapter (Fetcher)** | 把"外部世界"（URL / 上传的文件 / S3 路径 / API）变成 Bronze Repository 的一个 Commit。可插拔。 |
| **Processor** | 把"上游 Repository@version"变成"下游 Repository@new_version"的函数。可插拔。涵盖普通 Python 函数、LLM 调用、Agent loop。 |
| **Pipeline / Recipe** | 一组 Processor 按 DAG 组合，可声明式地生成下游数据集。 |
| **Lineage** | Commit 级别的有向图：每个派生 commit 记录它的输入 commits + processor + config 哈希。 |
| **Schema** | Silver/Gold 层 Repository 必须声明的数据结构定义（Pydantic / JSON Schema）。 |
| **Card** | Repo 根目录的 `README.md` + `dataset-card.yaml`，描述用途、字段、license、统计等。 |

### 2.3 一个具体例子（贯穿全文）

> 团队想做一份"中文古典文学 SFT 数据集"。

- **Bronze**：
  - Repo A `cn-lit/honglou-shulianzhai-v1` (subtype=`book`)，含 120 个 md 章节文件。来源：用 `BookArchiveAdapter` 解压上传的 zip。
  - Repo B `cn-lit/jinyong-wuxia-pdfs` (subtype=`pdf-collection`)，含 14 个 PDF。来源：上传。
  - Repo C `cn-lit/baidu-baike-cn-literature` (subtype=`webpage-collection`)，含 8k 个 `<entry_id>/content.md + images/` 子目录。来源：`FirecrawlAdapter` 抓取。

- **Silver**：
  - Repo D `cn-lit/normalized-text-v1` (subtype=`text-corpus`)。Schema 是统一的 `Document` 记录（id, source_ref, title, sections[], meta）。由 Processor `pdf2text + html2md + chunk + dedupe` 从 A、B、C 三个 Bronze 派生。
  - 血缘：D@commit_xyz 的 parents = [A@main, B@main, C@main]，processor = `cn-lit-normalize@v0.3`。

- **Gold**：
  - Repo E `cn-lit/sft-styleimitate-v1` (subtype=`sft`)。Schema = `{prompt, response, meta}`。由 `LLMQAGenerator`（一个 Processor，内部跑 Claude / GPT）从 D 生成。
  - Repo F `cn-lit/eval-classical-cn-v1` (subtype=`eval`)。由人工 + LLM 联合 Processor 从 D 生成。

数据流：
```
A,B,C  ──(normalize pipeline)──▶  D  ──(qa-gen pipeline)──▶  E
                                  │
                                  └──(eval-gen pipeline)──▶  F
```

---

## 3. 数据分层规范

> ⚠ **Deprecated 设计（v1）** —— § 3.1 中 `manifest.yaml` 是 **可选** 不再强制；§ 3.2/3.3 中 Silver/Gold "推荐 Parquet" 升为 **强制 Parquet/JSONL + schema 注册 + 每行 source_ref + 每行 stats**（v2 见 [§ 行级血缘](#行级血缘) 与 [§ stats-first 设计](#stats-first-设计)）。本节保留以防止老 change 引用 404。

### 3.1 Bronze 层

**定位**：原始资产层。**忠实保留来源形态**，最小化处理（最多做格式无损归一化，如 PDF 元数据抽取、URL 抓取后输出 md+images）。

**Repository 结构示例**：

```
bronze/cn-lit/honglou-shulianzhai-v1/
├── README.md                 # Card
├── dataset-card.yaml         # 结构化元数据
├── manifest.yaml             # 资产清单（asset_id → files）
├── content/
│   ├── ch01.md
│   ├── ch02.md
│   └── ...
└── _source/                  # 原始来源备份（可选）
    └── original.zip
```

```
bronze/cn-lit/baidu-baike-cn-literature/
├── README.md
├── dataset-card.yaml
├── manifest.yaml
└── assets/
    ├── 0001/
    │   ├── content.md
    │   ├── meta.json
    │   └── images/img_001.png
    ├── 0002/
    │   └── ...
    └── ...
```

**关键约束**：
- 每个 Bronze repo 在 `dataset-card.yaml` 中声明 `subtype` 和 `source_spec`（URL 列表、原始文件 hash、爬取时间等）。
- 一个 Repo 可以单资产 (1 个 asset)，也可以多资产 (N 个 asset)。`manifest.yaml` 是 Asset 的索引。
- 不允许在 Bronze 层做"语义清洗"（如去广告、改写）。那是 Silver 的工作。允许做的是"格式归一化"（PDF→PDF/A、HTML→MD 之类）。

### 3.2 Silver 层

**定位**：**标准化的中间层**。所有 Silver Repository 必须遵循已注册的 Schema。这是为了让 Gold 层的 Processor 可以无差别地处理来自不同 Bronze 来源的数据。

**典型 Schema (示例 `document.v1`)**：

```python
class Section(BaseModel):
    heading: str | None
    text: str
    lang: str | None = None

class Document(BaseModel):
    id: str                           # 在 silver repo 内唯一
    source: SourceRef                 # 指回 Bronze repo@commit/path
    title: str | None
    sections: list[Section]
    lang: str
    quality_score: float | None = None
    meta: dict = {}
```

**Repository 结构示例**：

```
silver/cn-lit/normalized-text-v1/
├── README.md
├── dataset-card.yaml         # 声明 schema = document.v1
├── schema/                   # Schema 副本（保证可独立解析）
│   └── document.v1.json
├── data/
│   ├── part-00000.parquet    # 推荐 parquet，便于 sampling
│   ├── part-00001.parquet
│   └── ...
├── samples/                  # 抽样的 jsonl 文件，UI 直接展示
│   └── sample.jsonl
└── stats/                    # 统计信息
    ├── stats.json            # 字段分布、token 数等
    └── quality_report.md
```

**关键约束**：
- 必须有 Schema 声明且 schema 文件随版本一起冻结。
- 必须有 `stats/` 目录，平台自动生成基础统计。
- 推荐 Parquet/Arrow 作为主要存储格式；保留小批量 JSONL 作 sampling 供 UI 预览。
- Silver 内部可以再分子类型 (text-corpus / dialog-corpus / image-text-pairs)，但 schema 都要预注册。

### 3.3 Gold 层

**定位**：**任务就绪 (task-ready)** 的数据。直接喂给训练 / 评测代码。

**Subtype 与 Schema**：

| Subtype | 典型 Schema | 用途 |
|---|---|---|
| `cpt` | `{text, source_ref, token_count}` | 继续预训练 |
| `sft` | `{prompt, response, system?, tools?, meta}` | SFT |
| `dpo` / `rlhf-pref` | `{prompt, chosen, rejected, meta}` | 偏好对齐 |
| `eval` | 多变，但要声明 `metric_protocol`：`{input, reference, scoring_spec}` | 评测 |

**Repository 结构同 Silver**（也是 schema-driven 的 parquet + stats + samples），仅 schema 不同。

**关键约束**：
- 每个 Gold repo 必须能直接被训练代码加载（提供官方的 `datasets`/`webdataset`/`hf-style` loader）。
- 必须冻结 schema，发版后不允许 in-place 修改。修改必须出新 commit / 新版本。
- Eval 数据集必须额外声明评测协议（如 exact-match、LLM-as-judge prompt、reference 字段等），这部分写在 card 中。

---

## 4. 关键抽象的接口设计

> ⚠ **Deprecated 设计（v1）** —— § 4.2 `Processor` 单一抽象拆为 Loader + Operator；§ 4.3 Recipe 的 nodes[]-of-Processor 形态升级为 Loader+Operators 链；§ 4.4 commit.parents `list[str]`（DAG）退化为 `parent: str | None`（线性 snapshot 单链），branch/merge/cherry-pick 进入 [§ 永不做清单](#永不做清单)。v2 权威接口见 [§ 三层算子模型](#三层算子模型)。本节保留以防止老 change 引用 404。

### 4.1 Source Adapter (Fetcher) 接口

```python
class SourceAdapter(Protocol):
    name: str                # 唯一标识，如 "firecrawl-url"
    version: str             # 语义版本
    input_schema: JSONSchema # 接受什么样的输入 spec
    output_subtype: str      # 产出的 bronze subtype
    
    def ingest(
        self,
        spec: dict,                # 符合 input_schema 的具体输入
        workspace: Path,           # 平台分配的临时工作区
        ctx: RunContext,           # 日志、metrics、secrets、cancel 信号
    ) -> IngestResult:
        """产出一棵符合 Bronze 规范的文件树 + manifest.yaml。
        平台负责把工作区 commit 到目标 Repository。"""
```

**举例**：
- `FirecrawlAdapter(spec={"urls": [...], "render_js": true})` → 输出 `assets/<id>/content.md` + `images/`
- `RawPDFUploadAdapter(spec={"file_id": "..."})` → 输出 `content/<filename>.pdf`
- `BookArchiveAdapter(spec={"archive_id": "...", "layout": "chapter-per-md"})` → 输出 `content/ch*.md`
- `ArxivAdapter(spec={"arxiv_id": "2401.xxxxx"})` → 输出 pdf + 抽取后的 md

**插件机制**：
- Adapter 以 Python 包形式安装到平台 worker 镜像，或以独立容器形式注册（通过 manifest 声明镜像 + 入口）。
- 平台维护一个 **Adapter Registry**（数据库表 + UI），登记 name、version、input_schema、output_subtype、依赖等。
- 用户在登记 Bronze 资产时，先选 Adapter，平台用 input_schema 渲染表单。

### 4.2 Processor 接口

```python
class Processor(Protocol):
    name: str
    version: str
    config_schema: JSONSchema
    
    # 输入约束：可以指定接受的上游 layer/subtype/schema
    accepts: list[RepoSelector]
    # 输出约束：声明输出 layer/subtype/schema
    produces: RepoSpec
    
    def run(
        self,
        inputs: list[RepoView],    # 每个上游 repo@commit 的只读视图
        config: dict,              # 符合 config_schema
        workspace: Path,
        ctx: RunContext,
    ) -> ProcessResult:
        ...
```

**几类典型 Processor**：

| 类别 | 例子 | 实现要点 |
|---|---|---|
| 纯函数式 | `pdf-to-text`, `markdown-normalizer`, `dedup-minhash`, `lang-detect` | Python 函数；平台并行调度 |
| 结构化抽取 | `parquet-builder`, `chunker`, `schema-mapper` | 平台提供高阶工具：map-over-records、流式 parquet 写入 |
| LLM 式 | `llm-qa-gen`, `llm-rewrite`, `llm-quality-score` | 见 4.5 |
| Agentic | `agent-eval-synth`（多轮工具调用合成评测题）| 见 4.5 |
| 人在回路 | `human-label`, `human-review` | 平台提供标注 UI 钩子，处理器异步等待 |

**统一调用契约**：
- 上游 inputs 是只读的 RepoView（路径 + iter_records API）。
- workspace 是空目录，processor 往里写文件，平台 commit。
- 所有 processor 必须是**确定性可重放**的（同样的 inputs + config → 同样的 output content hash）。LLM 这类不确定 processor，须在 config 中固定 seed/temperature/model，并把模型版本写入 lineage。

### 4.3 Pipeline / Recipe

Pipeline 是 Processor 的 DAG，用声明式 YAML 描述：

```yaml
# recipes/cn-lit-sft-v1.yaml
name: cn-lit-sft-v1
nodes:
  - id: normalize_pdfs
    processor: pdf-to-document@v0.2
    inputs: [bronze/cn-lit/jinyong-wuxia-pdfs@main]
    config: { ocr: false, lang_hint: zh }
    output: silver/cn-lit/jinyong-normalized@auto

  - id: normalize_web
    processor: html-to-document@v0.4
    inputs: [bronze/cn-lit/baidu-baike-cn-literature@main]
    output: silver/cn-lit/baike-normalized@auto

  - id: merge
    processor: corpus-merge@v0.1
    inputs: [@normalize_pdfs, @normalize_web]
    output: silver/cn-lit/normalized-text-v1@auto

  - id: qa_gen
    processor: llm-qa-gen@v0.5
    inputs: [@merge]
    config:
      model: claude-opus-4-7
      prompt_template: prompts/cn-style-qa.j2
      samples_per_doc: 3
    output: gold/cn-lit/sft-styleimitate-v1@auto
```

**特性**：
- 节点引用上游可以是某个 `@version`（固定）或 `@auto`（让平台用同一次 run 的产物）。
- 平台基于 input commit hash + processor version + config hash 做**结果缓存**，只重跑变更的节点。
- Pipeline 也作为 artifact 被版本化（pipeline 本身在一个特殊 repo 里）。

### 4.4 版本管理：类 Git 的 CAS 模型

**对象类型**（参考 Git）：
- `Blob`：文件内容，按 sha256 寻址。
- `Tree`：目录条目列表，每条 `(name, mode, type, hash)`，sha256(序列化后) 作 hash。
- `Commit`：`{tree, parents, author, time, message, lineage}`。
- `Ref`：指针，可变，`(repo_id, ref_name) → commit_hash`。

**lineage 字段**（commit 内嵌）：
```json
{
  "produced_by": {
    "kind": "processor",          // 或 "adapter" 或 "manual"
    "name": "llm-qa-gen",
    "version": "0.5",
    "config_hash": "sha256:..."
  },
  "inputs": [
    {"repo": "silver/cn-lit/normalized-text-v1", "commit": "abc123..."}
  ],
  "run_id": "uuid",
  "env": {"python": "3.11", "model": "claude-opus-4-7@2026-05-01"}
}
```

**好处**：
- Blob 级去重：相同 PDF 上传两次只存一份。
- Diff & 回滚：任意两个 commit 之间能 diff，能 checkout 旧版本。
- 血缘 = commit lineage 字段的 DAG，全平台无缝可视化。

**API 草图**：
```
GET  /repos/{owner}/{name}                              # repo 元信息
GET  /repos/{owner}/{name}/tree/{ref}/{path}            # 列目录 / 看文件
GET  /repos/{owner}/{name}/blob/{ref}/{path}            # 下载
POST /repos/{owner}/{name}/commits                      # 创建 commit (需事先 PUT blobs)
GET  /repos/{owner}/{name}/commits/{hash}/lineage       # 单 commit 血缘
GET  /lineage/graph?root={repo@commit}&depth=...        # 全局血缘子图
```

### 4.5 LLM / Agentic Processor 的特殊处理

LLM 类处理器是 Processor 的一类，但平台对它们提供额外能力：

1. **统一 LLM 网关**：平台内置 LLM 客户端抽象，processor 通过 `ctx.llm.call(...)` 调用，避免每个 processor 自带 SDK。网关负责：
   - 多 provider（Anthropic、OpenAI、本地 vLLM）
   - rate limit、retry、并发
   - cost 记账（每次调用入 metrics）
   - prompt / response 全量审计日志（可关闭，敏感场景）
   - 缓存（同样的 prompt + 同样的 sampling params → 命中缓存）

2. **Agentic Processor**：基于 LLM 网关 + tools 接口实现 agent loop。tools 可以是平台提供的（如查询某个 silver repo、调本地代码沙箱），也可以由 processor 自带。Agentic processor 必须把 trace（每步 thought / tool call / observation）写入 `_trace/` 目录便于审计。

3. **确定性策略**：LLM 不确定性是天然的。约定：
   - 必须设 `seed`（如 provider 支持）。
   - `model_id` 必须显式声明，且会写入 lineage。
   - 重跑出现内容不一致是允许的，但平台会标记 `non-deterministic=true` 并提供"diff 上次 run"的视图。

4. **预算与限流**：每个 pipeline run 可以声明 cost 预算上限；超限自动暂停等待人审批。

---

## 5. 存储与系统架构

### 5.1 组件总览

```
                ┌──────────────────────────────────────┐
                │            Web UI (HF-like)          │
                └──────────────────────────────────────┘
                                  │
                ┌──────────────────────────────────────┐
                │   API Gateway  (REST / gRPC, AuthN)  │
                └──────────────────────────────────────┘
                  │              │              │
        ┌─────────▼──┐    ┌──────▼──────┐   ┌───▼─────────┐
        │ Catalog &  │    │ Orchestrator│   │  Lineage    │
        │ Repo API   │    │ (pipelines) │   │  Service    │
        └─────┬──────┘    └──────┬──────┘   └───┬─────────┘
              │                  │              │
              │                  ▼              │
              │           ┌─────────────┐       │
              │           │ Job Runner  │       │
              │           │ (k8s / Ray) │       │
              │           └──────┬──────┘       │
              │                  │              │
              │           ┌──────▼──────┐       │
              │           │ Plugin host │       │
              │           │ (adapters / │       │
              │           │ processors) │       │
              │           └──────┬──────┘       │
              │                  │              │
              ▼                  ▼              ▼
      ┌──────────────┐   ┌───────────────┐  ┌────────────┐
      │  PostgreSQL  │   │ Object Store  │  │  Lineage   │
      │ (metadata)   │   │ (S3 / MinIO)  │  │ Graph DB   │
      │ repos, refs, │   │ blobs (CAS)   │  │ (可选,初期 │
      │ commits...   │   │               │  │  用 PG)    │
      └──────────────┘   └───────────────┘  └────────────┘

                ┌──────────────────────────────────────┐
                │           LLM Gateway                │
                │  Anthropic / OpenAI / vLLM / 缓存    │
                └──────────────────────────────────────┘
```

### 5.2 存储分工

| 类别 | 存储 | 备注 |
|---|---|---|
| 元数据（repos、refs、commits、users、ACL、pipeline runs） | Postgres | 主库 |
| 文件 blob（CAS） | S3 / MinIO，key = `blobs/{sha256[0:2]}/{sha256}` | |
| 大数据 parquet | 同上对象存储，作为 blob 存 | 一个 parquet = 1 个 blob |
| 血缘图 | 初期：Postgres（commit 表 + edges 表）。后期：Neo4j / Nebula | 关键 query：N 跳上游/下游 |
| 搜索（repo 名、card 全文） | 初期 PG 全文索引；规模上来后 OpenSearch | |
| 任务/队列 | Redis + **RQ**（MVP）；后续可演进到 Dagster 接管 | RQ 简单可靠，对 MVP 够用 |
| 缓存（LLM 响应、processor 结果） | Redis + 对象存储 | |

### 5.3 处理执行模型

- **Job Runner**：把 pipeline 节点拆成 job，由 worker 进程从 RQ 队列消费。
  - **MVP (Phase 1)**：worker 以 **subprocess** 方式启动 plugin。Plugin 是 pip 安装的独立 Python 包，通过 entry_points 注册到平台；worker 用 `python -m <plugin_pkg>` 拉起，给到独立工作目录、注入限制过的环境变量、设超时（必要时叠 Linux cgroups 做内存/CPU 软限制）。优点：实现简单、调试方便、零容器运维。代价：plugin 间共享 worker 机器内核，不适合不可信代码（内部团队场景可接受）。
  - **Phase 2+**：把 subprocess 替换为容器（k8s Job / podman），inputs/workspace 走 volume 挂载。Plugin manifest 不变（向前兼容）。
  - 每个 job 的执行流程：
    1. 算 `cache_key = hash(inputs_commits, processor_version, config)`，命中直接复用上次 commit。
    2. 拉取上游 RepoView 到本地工作区。
    3. 跑 `adapter.ingest()` 或 `processor.run()`（subprocess）。
    4. 把 workspace 内容做 commit，写 lineage 记录。
- **并行**：对于 map 型 processor（每条 record 独立处理），平台提供 `IterativeProcessor` 基类，框架自动分片到多 worker。
- **Checkpoint**：长流水线支持 checkpoint：单条记录处理完即 flush 到中间 parquet 分片，失败重启从最新分片继续。

---

## 6. 扩展性设计

### 6.1 插件的三种集成深度

| 深度 | 形式 | 适用 |
|---|---|---|
| L1：内置 | 直接进主代码库 | 团队官方处理器（normalize、dedup、tokenizer 等） |
| L2：包插件 | `pip install` 的 Python 包，注册 entrypoint | 团队内部增量贡献 |
| L3：容器插件 | 独立 Docker 镜像 + manifest YAML，注册到平台 | 第三方、异构语言、需特殊依赖（如 CUDA、Java） |

L1 和 L2 用同一套 Python 接口；L3 走标准的 stdin/stdout + 文件挂载契约。

**MVP 范围（Phase 1）：只支持 L1 + L2**，全部走 subprocess 启动，依赖 worker 镜像/虚拟环境里已安装的 Python 包。**L3（容器插件）推迟到 Phase 2+**，届时把 worker 的 subprocess 拉起逻辑替换成容器拉起即可，plugin manifest 设计已向前兼容。

### 6.2 插件 Manifest 示例（L3）

```yaml
kind: processor
name: my-special-cleaner
version: 0.1.0
image: registry.internal/plugins/my-cleaner:0.1.0
entrypoint: ["/app/run.sh"]
config_schema:
  type: object
  properties:
    min_len: { type: integer, default: 50 }
accepts:
  - { layer: silver, subtype: text-corpus }
produces:
  layer: silver
  subtype: text-corpus
resources:
  cpu: 4
  memory: 8Gi
  gpu: 0
```

### 6.3 Schema 注册中心

- Silver/Gold 的所有 schema 在平台 Schema Registry 注册（带版本）。
- Processor 的 `accepts` / `produces` 引用 schema id + version。
- 新 schema 版本必须声明与旧版本的兼容性（compatible / breaking）。
- Repository 在 commit 时校验 records 符合声明的 schema，否则拒绝。

---

## 7. UI / SDK / CLI

### 7.1 Web UI（参考 HF）

每个 Repository 页面：
- **Top**：owner/name、layer 徽章（bronze/silver/gold 不同颜色）、subtype、stars、license。
- **Tabs**：
  - `Dataset Card`：渲染 README.md + dataset-card.yaml。
  - `Files and versions`：树状文件浏览，支持 commit 切换、diff。
  - `Lineage`：血缘 DAG 可视化，节点是 repo@commit，可点击跳转。
  - `Samples`：随机抽取 N 条记录（来自 samples/）。
  - `Stats`：字段分布、token 数、quality score 等图表。
  - `Pipelines`：本 repo 作为输入/输出参与过的 pipeline。
  - `Discussions`：评论/issue（后期）。

全局页面：
- 数据集列表（按 layer / subtype / tag 过滤）。
- Pipeline 列表 + run 历史。
- Plugin registry。
- Schema registry。

### 7.2 Python SDK

```python
from dataplat import Client

c = Client("https://platform.internal", token=...)

# 拉取
ds = c.dataset("silver/cn-lit/normalized-text-v1", ref="v1.0")
for record in ds.iter_records():
    print(record)

# 推送
repo = c.create_repo(
    "bronze/my-team/my-pdfs",
    layer="bronze", subtype="pdf-collection",
)
repo.upload_files({"content/a.pdf": open("a.pdf","rb")})
repo.commit(message="initial", lineage_manual=True)

# 跑 pipeline
run = c.run_pipeline("recipes/cn-lit-sft-v1.yaml")
run.wait()
```

### 7.3 CLI

```
dataplat repo create bronze/my/foo --subtype pdf-collection
dataplat upload bronze/my/foo content/a.pdf ./local/a.pdf
dataplat commit bronze/my/foo -m "init"
dataplat pipeline run recipes/cn-lit-sft-v1.yaml
dataplat lineage show gold/cn-lit/sft-styleimitate-v1@main --upstream 3
```

---

## 8. 关键决策与权衡

| 决策 | 选项 | 我倾向 | 理由 |
|---|---|---|---|
| 三层是否共用 Repository 模型 | (a) 共用 (b) 各自独立 | **a** | 避免三套存储 / API / UI 的重复；layer 只是属性 |
| 版本控制 | (a) 自研类 Git CAS (b) 直接用 lakeFS / DVC | **a (但参考 lakeFS 概念)** | 自研可控 + 跟血缘紧耦合；lakeFS 加进来运维成本不小 |
| 大文件存储 | (a) blob 全量 (b) Git LFS 风格 pointer | **a，对象存储天然适合** | 简化 |
| 处理引擎 | (a) k8s Job 自研编排 (b) Dagster / Prefect (c) Airflow | **(a) for MVP，后接 (b)** | MVP 不依赖外部编排器；后期接 Dagster 性价比最高 |
| 元数据库 | Postgres / MySQL | **Postgres** | JSONB、全文索引、PG vector 后续都有用 |
| 血缘图 | (a) PG 表 (b) Neo4j (c) OpenLineage | **(a) 起步，留接口出 OpenLineage 事件** | 起步简化；OpenLineage 是接其他生态的好桥 |
| LLM 调用 | (a) 每个 processor 自带 (b) 平台 LLM 网关 | **b** | 集中管 cost / cache / 审计 |
| Schema | (a) JSON Schema (b) Pydantic (c) Protobuf | **JSON Schema + Pydantic 生成** | JSON Schema 是 lingua franca；Pydantic 写起来爽 |
| 流水线 DSL | (a) YAML 声明 (b) Python imperative | **YAML + Python 两种入口** | YAML 适合发版固化；Python 适合 ad-hoc |
| 任务队列 (MVP) | (a) RQ (b) Celery | **a** | 简单太多；MVP 功能够用 |
| Plugin 执行隔离 (MVP) | (a) subprocess (b) container | **a** | 简化 MVP；plugin manifest 设计向 b 兼容，迁移成本低 |
| Turbo 缓存 | (a) 本地 (b) 自托管 remote (c) Vercel | **a** | 团队规模未上来前没必要；以后再评估自托管 |
| 认证 (MVP) | (a) username + JWT (b) OIDC/SSO | **a** | 内部工具，先内置账户体系；预留 AuthProvider 抽象 |

---

## 9. 实施路线图

### Phase 1 — MVP (8 周)
- Repository / Commit / Blob 模型 + Postgres + S3。
- Bronze 录入：手动上传 + 2 个 Adapter（`RawFileUpload`、`FirecrawlURL`）。
- Silver / Gold：schema 注册 + 1 个端到端流水线（PDF → text-corpus → SFT）。
- 1 个 LLM Processor + LLM 网关基础版。
- **Worker：RQ + subprocess 启动 plugin（L1/L2）**。
- **认证：username/password + JWT（httpOnly cookie），扁平角色（admin/user）**。
- 最小 UI：登录页 + repo 列表 / Card / Files / 版本列表 / samples 预览。
- Python SDK + CLI 基本命令。

### Phase 2 — 生产化 (再 8 周)
- 完整 lineage 图查询 + UI 可视化。
- 流水线编排：缓存、增量、checkpoint。
- **容器插件 (L3) 支持**：把 worker 的 subprocess 启动逻辑替换为容器启动；plugin manifest 已兼容。
- 完整 Schema Registry + 兼容性校验。
- Eval 子类型 + LLM-as-judge 协议。
- **Repository 级 ACL + 团队/组织模型**；预留 OIDC/SSO 接入点。

### Phase 3 — 规模化
- Dagster/Ray 替换内部编排，支持上亿 records 流式 parquet。
- 血缘图迁移到图数据库。
- 全文/语义搜索。
- 人在回路标注 UI。
- 与 W&B / 训练框架的双向集成（push gold dataset id 到训练 run 的 metadata）。

---

## 10. 待讨论的开放问题

1. **粒度问题**：8k 个网页是放一个 Repo (multi-asset) 还是 8k 个 Repo？建议默认 **multi-asset 单 Repo**，但对超大 (>10w 资产) 用 sharded repo（multi-asset 单 repo + 内部分片）。需要确认。
2. **PII / 合规**：是否需要内置 PII 检测、license 兼容性检查？建议作为标准 processor 提供。
3. **删除与遗忘权**：CAS 模型下"彻底删除"是难点（blob 可能被多个 commit 引用）。需要设计 retention / purge 流程。
4. **多模态**：当前抽象对图文混合 OK，对视频/音频需扩展 blob 类型和 schema。优先级？
5. **训练框架对接的契约**：Gold repo 想做到"训练代码一行 import 即用"，可能需要约定一个 manifest（指明 split、loader 类型）。要不要做成另一个 schema？
6. **Pipeline 调度的 fairness / quota**：多团队共用时如何排队、限额？

---

## 11. 工程实现：技术栈、仓库结构与开发环境

### 11.1 前端选型：Vite（不选 Next.js）

**结论：Vite + React 18 + TanStack Router + TanStack Query + shadcn/ui + Tailwind**

| 维度 | Next.js | Vite | 本项目结论 |
|---|---|---|---|
| SEO / SSR | 强 | 弱 | 内部工具，不需要 |
| 后端语言 | TS 时收益大（RSC、Server Actions） | 与后端解耦 | 后端是 Python，Next.js 服务端能力全部废弃 |
| 数据密集 UI 体验 | OK | 更快的 HMR / 启动 | Vite 占优 |
| shadcn 支持 | 一等公民 | 一等公民 | 平手 |
| 心智复杂度 | App Router 较重 | SPA 简单 | Vite 占优 |

参考标杆：Grafana、Sentry、Argo Workflows UI、lakeFS UI、Airbyte UI 全部是 SPA 架构。

**前端技术栈细节：**

| 用途 | 选型 |
|---|---|
| 路由 | **TanStack Router**（类型安全，比 React Router 现代） |
| 数据获取 / 缓存 | **TanStack Query**（缓存、重试、乐观更新、轮询一把梭） |
| 表单 | React Hook Form + Zod |
| 表格 | TanStack Table（虚拟滚动；用于文件列表 / 记录预览） |
| 图表 | Recharts（统计） |
| 血缘 DAG | React Flow |
| Diff 视图 | diff2html / monaco-editor |
| 代码高亮 | Shiki |
| API 客户端 | 从后端 OpenAPI 用 `openapi-typescript` 生成 TS 类型，配合 fetch wrapper 或 `@hey-api/openapi-ts` |

### 11.2 后端技术栈

| 组件 | 选型 | 理由 |
|---|---|---|
| Web 框架 | FastAPI | async、自动 OpenAPI、与 Pydantic 一体 |
| ORM | SQLAlchemy 2.0 (async) + Alembic | 异步从 Day 1 |
| 数据校验 | Pydantic v2 | 与 schema-driven 设计天然契合 |
| 任务队列 (MVP) | **RQ**（Redis backend） | 比 Celery 简单太多，对 MVP 功能充分；后续如需可演进 |
| 任务编排 (Phase 2+) | Dagster | 跨语言、有血缘原生概念 |
| 认证 (MVP) | argon2-cffi 哈希 + JWT (httpOnly cookie) | 见 §11.6 |
| 包管理 | **uv** | 比 poetry 快 10x+，2025 已是事实标准；原生支持 workspace |
| 代码质量 | ruff + mypy + pytest | |
| S3 客户端 | boto3（兼容 MinIO） | |

### 11.3 Monorepo 结构

```
dataplat/
├── apps/
│   ├── web/                      # Vite + React + shadcn 前端
│   │   ├── src/
│   │   │   ├── components/
│   │   │   │   └── ui/           # shadcn 拷贝下来的组件
│   │   │   ├── routes/           # TanStack Router 路由
│   │   │   ├── lib/api/          # 用 packages/api-types 包装的 client
│   │   │   └── main.tsx
│   │   ├── components.json       # shadcn 配置
│   │   ├── tailwind.config.ts
│   │   ├── vite.config.ts
│   │   └── package.json
│   └── api/                      # FastAPI 后端
│       ├── dataplat_api/
│       │   ├── routers/
│       │   ├── models/           # SQLAlchemy
│       │   ├── schemas/          # Pydantic
│       │   ├── services/         # repo / commit / lineage / pipeline
│       │   ├── storage/          # blob CAS 抽象
│       │   ├── llm/              # LLM 网关
│       │   └── main.py
│       ├── alembic/
│       ├── tests/
│       └── pyproject.toml
│
├── packages/
│   ├── api-types/                # 由 OpenAPI 生成的 TS 类型（前端依赖此包）
│   │   ├── openapi.json
│   │   ├── src/generated.ts
│   │   └── package.json
│   ├── core/                     # 后端 / SDK / worker 共用的 Pydantic 模型与接口
│   │   └── pyproject.toml
│   └── sdk-py/                   # Python SDK（用户侧）
│       └── pyproject.toml
│
├── plugins/                      # 可插拔 adapters / processors（独立发布单元）
│   ├── adapter-raw-upload/
│   ├── adapter-firecrawl/
│   ├── processor-pdf-to-text/
│   ├── processor-html-to-md/
│   ├── processor-dedup-minhash/
│   ├── processor-llm-qa-gen/
│   └── README.md                 # 插件开发指南
│
├── worker/                       # Job runner（拉取并执行 plugin）
│   ├── dataplat_worker/
│   └── pyproject.toml
│
├── recipes/                      # 流水线 YAML 示例（同时也是版本化产物）
│   └── examples/
│
├── docker/
│   ├── docker-compose.dev.yml    # postgres / minio / redis（本地开发依赖）
│   ├── docker-compose.test.yml
│   └── images/
│       ├── api.Dockerfile
│       ├── worker.Dockerfile
│       └── web.Dockerfile
│
├── scripts/                      # codegen / migrate / seed / openapi 导出
├── docs/                         # 设计文档、ADR、API 规范
│
├── pnpm-workspace.yaml           # JS workspace 声明
├── turbo.json                    # 跨语言任务编排
├── pyproject.toml                # uv workspace 根
├── uv.lock
├── package.json                  # 根，含 turbo + 共用 dev deps
├── Makefile                      # 一键命令入口
└── README.md
```

**几个工程层面的关键约定：**

1. **不用 Nx，用 Turborepo**。Nx 太重且偏 JS-only；Turbo 把任意 shell 命令（包括 `uv run`、`pytest`）纳入任务图，对多语言 monorepo 更友好。
2. **pnpm workspace 和 uv workspace 各自独立、各管各的 lockfile**。不要试图统一，这是 2025 年多语言 monorepo 的最佳实践。
3. **shadcn 不是 npm 包，是把组件源码拷进自己仓库**。直接在 `apps/web/src/components/ui/` 维护，**不要**为了"共享"抽到 `packages/ui` 再做包发布——增加复杂度且没收益（除非以后真有第二个前端 app）。
4. **plugins 必须独立成目录、独立打镜像**。Plugin 的发布节奏远快于平台本体，混在 api / worker 里会拖死核心 release。
5. **api-types 是单向生成产物，永远不要手写**。前端任何对后端类型的引用都从 `@dataplat/api-types` 拿。

### 11.4 本地开发环境

**原则：依赖中间件用 Docker 跑，业务代码本地原生跑**（HMR/重启体验最好）。

`docker/docker-compose.dev.yml` 起的服务：
- `postgres:16`（5432，volume 持久化）
- `minio`（9000 + 9001 console）+ `minio-init`（启动时建 bucket）
- `redis:7`（6379）
- `mailpit`（如需邮件通知，开发用假 SMTP）

业务代码本地运行：
- `apps/api`：`uv run uvicorn dataplat_api.main:app --reload --port 8080`
- `apps/web`：`pnpm --filter web dev`（默认 5173）
- `worker`：`uv run dataplat-worker`

**Makefile 入口（关键命令）：**

```makefile
.PHONY: up down api web worker codegen migrate seed test

up:
	docker compose -f docker/docker-compose.dev.yml up -d

down:
	docker compose -f docker/docker-compose.dev.yml down

api:
	cd apps/api && uv run uvicorn dataplat_api.main:app --reload --port 8080

web:
	pnpm --filter web dev

worker:
	cd worker && uv run dataplat-worker

migrate:
	cd apps/api && uv run alembic upgrade head

# 后端 OpenAPI -> 前端 TS 类型（CI 中强制 git diff --exit-code）
codegen:
	cd apps/api && uv run python -m dataplat_api.export_openapi \
	  > ../../packages/api-types/openapi.json
	pnpm --filter @dataplat/api-types run generate

seed:
	cd apps/api && uv run python -m dataplat_api.seed

test:
	cd apps/api && uv run pytest
	pnpm --filter web test
```

**新成员 onboarding 流程（目标：30 分钟内首次 commit 跑通）：**

```bash
# 1. 装语言工具
curl -LsSf https://astral.sh/uv/install.sh | sh
curl -fsSL https://get.pnpm.io/install.sh | sh

# 2. 装依赖
git clone <repo> && cd dataplat
uv sync       # Python 所有子项目统一安装
pnpm install  # JS workspace

# 3. 起中间件
make up
make migrate seed

# 4. 三个终端各起一个进程
make api
make worker
make web

# 浏览器打开 http://localhost:5173
```

### 11.5 CI 与发布

- **CI**：GitHub Actions。Turbo 本地缓存就够用（不引入远程缓存）；团队规模扩大后再评估自托管 `turbo-remote-cache`。
- **强契约**：CI 必须跑 `make codegen` 然后 `git diff --exit-code`，否则 PR 不让合（防止 API/前端类型失同步）。
- **镜像构建**：api、worker、web、每个 plugin 各自 Dockerfile，CI 中 build & push。
- **发布拓扑**：
  - Phase 1：单 VM + docker-compose（生产配置）足以验证。
  - Phase 2+：上 k8s，api/web 跑 Deployment，worker 跑 KEDA scaled job，plugins 跑 Job。

### 11.6 认证与授权

MVP 阶段采用最简方案：**username/password + JWT (httpOnly cookie)**。要点如下。

**后端 (FastAPI)：**

- **用户表**：`users(id, username, email, password_hash, role, is_active, external_id, created_at, updated_at)`。预留 `external_id` 是为 Phase 2+ 接 SSO 时不破坏现有数据。
- **密码哈希**：`argon2-cffi`。不用 bcrypt（argon2 是当前事实标准，抗 GPU 暴破能力更强）。
- **JWT 双 token**：
  - access token 短 TTL（15 min），放 `Authorization` 不实际，**改放 httpOnly + Secure + SameSite=Lax 的 cookie**，前端拿不到 token、XSS 偷不走。
  - refresh token 长 TTL（7 d），同样 cookie 投递，到期前由前端在 401 拦截器里静默换新。
- **依赖注入**：写一个 `get_current_user` 依赖，所有受保护路由 `Depends(get_current_user)`。不用 `fastapi-users` 等大而全的库，自己写 80 行更可控。
- **授权**：MVP 用扁平 role（`admin` / `user`）。Repository 级 ACL 留到 Phase 2，那时引入 `repo_acl(repo_id, principal_id, principal_type, permission)` 表。
- **抽象预留**：把"如何识别用户"封装成 `AuthProvider` 接口：
  - `LocalAuthProvider`（MVP，校验 password_hash）
  - 后续可加 `OIDCAuthProvider` / `SAMLAuthProvider` 实现同一接口
  业务代码只依赖接口，切换 provider 不改路由。

**前端 (Vite + React)：**

- 登录页：`/login`，表单 → `POST /auth/login` → 后端 `Set-Cookie` → 前端 router.navigate("/")。
- 所有 fetch 必须带 `credentials: "include"`；Vite dev server 配 proxy 把 `/api` 转到 `http://localhost:8080`，避免跨域 cookie 问题。
- API client 全局拦截：401 → 先尝试 `POST /auth/refresh`，成功重试原请求，失败跳 `/login`。
- 不用 Redux / Zustand 存"是否登录"。直接用 TanStack Query 缓存 `GET /auth/me` 的结果作为 single source of truth，登录/登出后 `queryClient.invalidateQueries(["me"])` 即可。

**MVP 明确不做的：**

- 注册流程（admin 在后台或种子脚本里建账号）。
- 密码重置邮件流程（admin 直接重置）。
- MFA、OAuth login、社交登录。
- Repository 级别精细 ACL（先用 `visibility = private | internal`）。

**路由清单（最小集）：**

```
POST   /auth/login           # username, password -> Set-Cookie
POST   /auth/logout          # 清 cookie
POST   /auth/refresh         # 用 refresh cookie 换新 access cookie
GET    /auth/me              # 当前用户信息
POST   /admin/users          # admin: 创建用户
PATCH  /admin/users/{id}     # admin: 改 role / 重置密码 / 停用
```

### 11.7 几个一定会遇到的坑

1. **SQLAlchemy 必须从一开始就用 async session**。同步模式在 IO 密集场景（频繁查 commit / 拉 blob）一上量就崩，迁移成本极高。
2. **不要把 LLM 调用散落在各个 processor**。统一走 `apps/api/dataplat_api/llm/` 网关；processor 通过 `ctx.llm.call()` 调用。否则 cost 监控、缓存、retry 策略各处不一致。
3. **OpenAPI codegen 一定在 CI 强制**。本地忘了跑是常态，必须靠 CI 兜底。
4. **dataset card 渲染要支持 frontmatter (YAML) + markdown**，参考 HF 的做法。前端直接用 `react-markdown` + `remark-gfm` + `gray-matter`。
5. **文件树 / records 预览要做虚拟滚动**。一个 silver repo 几万条 records 是常态，不虚拟化浏览器会卡死。TanStack Table + `@tanstack/react-virtual`。
6. **Tailwind 配置要把所有用到 className 的目录都加入 `content`**，包括 `packages/` 里的（如果以后真有共享组件）。漏配置 = 生产构建样式丢失，是经典坑。

---

*v0.2 修订：在 §5.3 / §6.1 / §8 / §9 / §11.2 / §11.5 落实 MVP 工程取舍（RQ、subprocess 隔离、本地 Turbo 缓存）；新增 §11.6 认证与授权章节，原 §11.6 顺延为 §11.7。下一步建议先就核心抽象（Repository / Asset / Adapter / Processor / Lineage）以及 §11.6 的 AuthProvider 接口形态达成共识，再细化到 API 字段级别。*

