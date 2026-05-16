# 领域术语表

> 仓库内的唯一术语权威。代码命名、文档措辞、UI 文案都以此为准。**新增术语必须经过 ADR 或评审通过**。

## 核心抽象

### Repository

数据集容器，HuggingFace 风格的"库"。版本、ACL、Card、血缘归属于 Repository。一个 Repository 属于唯一 `layer`（bronze/silver/gold）且声明 `subtype`。

- 不缩写为 "repo" 在文档中；代码 / URL 中可以。
- 多语种统一用 Repository，不用"仓库"/"数据集"混用——除了对外宣传文案。

### Layer

Repository 所属层：`bronze` / `silver` / `gold`。

| Layer | 角色 | Schema 强制 |
|---|---|---|
| bronze | 原始资产层，忠实保留来源形态 | 不强制 |
| silver | 标准化中间层，统一 schema | **强制** |
| gold | 任务就绪层（CPT / SFT / DPO / eval） | **强制** |

### Subtype

Layer 内的二级分类。

- bronze：`pdf` / `pdf-collection` / `webpage` / `webpage-collection` / `book` / `image-set` / ...
- silver：`text-corpus` / `qa-records` / `dialog-corpus` / `image-text-pairs` / ...
- gold：`cpt` / `sft` / `dpo` / `rlhf-pref` / `eval`

新增 subtype 必须同步注册到 Schema Registry（Phase 2+）。

### Asset

Bronze 层中的逻辑资产单元。一个 Repository 含一个或多个 Asset。Asset 是带类型的、含 1 ~ N 个文件的逻辑包（如"一本书的 30 个 md"是一个 Asset）。

`bronze/.../manifest.yaml` 是 Asset 的索引。

### File

Repository tree 中的一个文件条目：`path` + `blob hash` + `size` + `type`。物理内容在 Blob。

### Blob

实际字节内容。按 sha256 内容寻址，存储在对象存储下 `blobs/{sha256[0:2]}/{sha256}`。

- 跨 Repository 共享：相同 sha256 全平台只存一份。
- 不允许直接由 plugin 写入路径——必须走 `packages/core` 的 storage 抽象。

### Commit

Repository 的一次原子变更，指向一棵 Tree、一组 parent commits、附带 lineage 元信息。语义同 Git Commit。

### Ref

指向 Commit 的可变指针。`main` / `v1.0` / `pr-7` 都是 Ref。

### Tree

目录条目列表（`(name, mode, type, hash)`）的有序序列化，sha256 寻址。

## 流程与插件

### Source Adapter（Fetcher）

把"外部世界"（URL / 上传文件 / S3 路径 / API）变成 Bronze Repository 的一个 Commit 的插件。接口 `SourceAdapter`（见 design.md §4.1）。

**别名禁用**：不要说 "ingester"、"connector"——统一 Source Adapter（或 Adapter）。

### Processor

把"上游 Repository@version"变成"下游 Repository@new_version"的插件。涵盖纯函数、LLM 调用、Agentic loop。接口 `Processor`（见 design.md §4.2）。

### Pipeline / Recipe

Processors 的 DAG，用 YAML 声明。Pipeline 自身也是版本化 artifact。

- 文档用 "Pipeline"；YAML 文件统一叫 "recipe"。

### RunContext

平台注入到 adapter / processor 运行环境的对象，提供日志、metrics、secrets、LLM 网关、cancel 信号。

### Workspace

平台分配给 adapter / processor 的临时工作目录。plugin 往里写文件，结束后由平台 commit 到目标 Repository。

## 血缘与版本

### Lineage

跨 Repository 的有向图：每个派生 commit 记录它的输入 commits + 处理器 + config 哈希。lineage 信息内嵌在 commit 的 `lineage` 字段。

### Config Hash

processor / adapter 的运行参数（config）的 sha256，写入 lineage 用于结果缓存与可重放。

### Cache Key

`hash(inputs_commits, processor_version, config_hash)`。命中即复用上次的输出 commit。

## Schema & Card

### Schema

Silver / Gold 层 Repository 必须声明的数据结构（Pydantic / JSON Schema）。

- Schema 注册到 Schema Registry，带版本。
- Repository commit 时校验 records 符合声明的 schema。

### Schema Compatibility

新 schema 版本必须声明与旧版本的兼容性：`compatible`（向后兼容）或 `breaking`。

### Dataset Card

Repository 根目录的 `README.md` + `dataset-card.yaml`。描述用途、字段、license、统计等。前端 UI 直接渲染。

## LLM 相关

### LLM Gateway

平台内置的 LLM 客户端抽象，所有 LLM 调用必经的入口。负责多 provider、限流、重试、cost 记账、prompt/response audit、缓存。

### LLM Cache

LLM Gateway 的请求/响应缓存。key = `(model, normalized_prompt, sampling_params)`。

### Audit Log

LLM 调用的全量 prompt / response 持久化记录。可关闭（敏感场景）。

### Agentic Processor

基于 LLM Gateway + tools 的 agent loop 实现的 Processor。必须把每步 thought / tool call / observation 写入 `_trace/` 目录。

## 阶段与角色术语（Harness 自身）

### Generator

执行实现 / 编写产物的 Agent 角色（编码、写 spec、写测试都属 Generator）。

### Reviewer

独立评判 Generator 产物的 Agent 角色。**不能与 Generator 共享上下文**。

### Change

一次完整的"需求→实现→验证"档案，目录在 `.harness/changes/<feature-slug>-<yyyymmdd>/`。

### Quality Gate

阶段过关的机械化条件。必须可程序化验证。

### Rollback Route

阶段失败时回退到的上一阶段。在 `.harness/rules/development-process.md` 中固化。

### Skill

可复用 SOP，定义在 `.harness/skills/<name>/SKILL.md`。按阶段加载，不全量。

### Rule

必须遵守的约束，定义在 `.harness/rules/*.md`。

### ADR

Architecture Decision Record。在 `wiki/adr/` 中。

## 不要混用的术语

| 推荐 | 禁用 / 易混 | 说明 |
|---|---|---|
| Repository | 数据集 / dataset（除非外宣文案） | "dataset" 在 HF 语义里 ≈ Repository，但在我们这里多义易混 |
| Source Adapter | Ingester / Connector | |
| Commit | 版本 / 快照 | "version" 留给 Repository 级别 tag |
| Blob | 文件 / file | File 是 tree 条目；Blob 是字节内容，两者不同 |
| Pipeline | Workflow / DAG（口语化时允许） | 文档统一 Pipeline |
| Run | Execution / Job（口语化允许） | run 表示一次 Pipeline 实例化 |
| Cache | 缓存 / Memo | 文档英文用 Cache |
