---
rollout_id: north-star-rollout-20260520
owner: application-owner (opus, team-leader)
started_at: 2026-05-20T16:30:00Z
authority_basis: |
  用户在 2026-05-20 16:25Z 完整授权（"我只最后验收整个系统"+"也不用给我过目了"），
  agent team leader 模式，自主决定文档、节奏、change 拆分与 spawn 策略。
  约束：每个 change 仍走 harness v2 三阶段；不违反 data-not-code-pivot.md 永不做清单。
last_updated: 2026-05-20T16:30:00Z
---

# Roadmap：北极星 rollout（27 changes / 5 waves）

> 本文件是 27 个 follow-up changes 的"种子库"。每个 change 进 Phase 1 时，application-owner 直接把对应 § 的内容塞进 `bash scripts/harness_new_change.sh <id>` 之后的 design.md，**不重新思考**。

## 终态愿景（用户原话沉淀）

> 一个开箱即用的 LLM 训练数据工厂：
> - **入口**：多源（PDF / URL / DOCX / PPT / Excel / 带 assets 的文件夹 / JSONL）
> - **中间**：bronze 文件 → silver row（含 source_ref / stats / 图片占位）→ gold row（精炼后）
> - **出口**：版本化数据集（HF datasets 格式 / JSONL / Parquet）供 CPT / SFT / bench / DPO 训练
> - **可视化**：上传 → 预览 row → 拖拽 Operator chain → 导出 snapshot
> - **图片处理**：文档里的示例图在 Operator chain 阶段转成文字描述 / mermaid / unicode art

## 5 个 Wave 的策略

| Wave | 主题 | 数量 | 串/并 | 验收 checkpoint |
|---|---|---|---|---|
| 0 | 编排准备 | 0 changes | — | roadmap / dashboard / decisions 三文档落地 |
| 1 | 地基 | 4 | **串行** | end-to-end PDF→bronze→silver→gold demo 走通新模型 |
| 2 | 核心算子链 | 6 | 串行 for packages/core；UI 无关的可并 2 | 一个完整 recipe.yaml v2 跑通：upload→loader→6 个 operator→export |
| 3 | 源覆盖 + 训练对接 | 7 | 6 个 adapter/loader 可并 3；gold-hf-datasets 串 | 4 种格式（PDF/MD-folder/JSONL/HTML）跑通完整链路 + HF dataset 导出 |
| 4 | UI + 工程化 | 10 | UI 4 个串；可观测性/成本/集成测试并 2；DPO/eval/backup 串 | 用户在 UI 上完成一次完整流程：上传 → preview → 拖 Operator → export → 拿到训练用数据集 |

总计 **27 changes**。串行节点在 Wave 1 + Wave 2 packages/core 之间最密；UI / 数据源类可并行。

---

## Wave 1：地基（4 changes，串行）

> **为什么串行**：每个 change 都改 packages/core 的接口定义；并行会导致 schema 冲突。

### W1-1：`api-snapshot-rename-20260520`

- **一句话目标**：API / UI / SDK 词汇统一从 Commit → Snapshot；删 `parents: list[str]` 改 `parent: str | None`；删 `branches` 复数 API
- **范围**：apps/api routes / schemas、apps/web routes / hooks / components、packages/api-types、packages/sdk-py
- **非范围**：DB schema 不动（DB 内部仍可叫 commit）；老 change 文档不回写
- **核心 AC**：（behavioral）curl `/api/v1/repos/<id>/snapshots` 返回 200；旧 `/commits` 路径返回 308 → 新路径；ts/py types 含 `Snapshot` 不含 `Commit` (排除 deprecated 注释)
- **依赖**：无（Wave 1 起点）
- **永不做清单触发**：撤掉 `parents` 复数 = 撤 DAG，落实"无 branch / merge"

### W1-2：`operator-protocol-20260520`

- **一句话目标**：把 Adapter / Loader / Operator 三个 Protocol 类落到 `packages/core/protocols.py`；建 OperatorRegistry；落 1 个标杆 Operator（identity 透传，做 self-check 基准）
- **范围**：packages/core/protocols.py / registry.py，worker/src/runner.py 路由分发
- **非范围**：不写真正的过滤 / 去重 / 评分 Operator（留给 W2）；不动 plugins 老 Processor
- **核心 AC**：（behavioral）`uv run pytest packages/core/tests/test_protocols.py` PASS；OperatorRegistry 能注册 + 查找；identity Operator 能跑通一次 row→row
- **依赖**：W1-1（用 Snapshot 词汇）
- **永不做清单触发**：Protocol 强制 row→row，撤"repo→repo" 老 Processor 抽象

### W1-3：`silver-schema-enforce-20260520`

- **一句话目标**：silver / gold repo 创建时强制写 schema；每行必含 `source_ref: dict` + `stats: dict` + `lineage_ops: list`；Parquet/JSONL 二选一
- **范围**：packages/core/schemas/silver_row.py，apps/api repo 创建路由 schema 校验，schema registry 实现
- **非范围**：bronze 不动（仍是文件树）；老 silver repo 不强制迁移（标 deprecated）
- **核心 AC**：（behavioral）创建无 schema 的 silver repo 返回 422；含 schema 但缺 source_ref 列的返回 422；合法 schema 通过 + sqlalchemy 持久化
- **依赖**：W1-2（schema 校验用 Operator Protocol 的 row 定义）
- **永不做清单触发**：撤"silver 文件树" + "bronze 强 schema"

### W1-4：`loader-refactor-pdf-mineru-20260520`

- **一句话目标**：把现有 pdf-mineru processor 重写为 Loader；输出 silver row（含 source_ref / stats / 文本 + 图片占位 + images column）
- **范围**：plugins/loaders/pdf_mineru/，删 plugins/processors/pdf_mineru（或标 deprecated）
- **非范围**：图片→文字转换不在这做（留给 W2 image-to-text-suite）；UI 不改（UI 留给 W4）
- **核心 AC**：（behavioral）一份 sample PDF 跑通 Loader 输出 ≥ 1 行 parquet，每行 source_ref.blob_sha 可回查 bronze；image_count stats 字段非零
- **依赖**：W1-3（silver schema）
- **永不做清单触发**：撤 repo→repo Processor 单一抽象

**Wave 1 checkpoint**：手动跑一次 `upload sample.pdf → snapshot → loader → silver row 表` 验证。失败回到 W1-3 / W1-4 修。

---

## Wave 2：核心算子链（6 changes）

### W2-1：`operator-suite-mvp-20260520`

- **一句话目标**：一次加 3 个标杆 Operator：lang-id-filter / perplexity-score / minhash-dedup
- **范围**：plugins/operators/lang_id/, perplexity/, minhash_dedup/
- **核心 AC**：（behavioral）3 个 Operator 各自单测 PASS；recipe 中 lang-id 过滤掉非英文行；minhash 去重在 1k 重复行集合上召回 ≥ 95%
- **依赖**：W1-4

### W2-2：`operator-chunker-20260520`

- **一句话目标**：文档切分 Operator（按 token / 按 markdown heading / 按段落三模式）
- **范围**：plugins/operators/chunker/
- **核心 AC**：（behavioral）一行 ≥ 8k token 的 row 经切分输出 N 行；每行 lineage_ops 含 chunker；总 token 数守恒（± 5%）
- **依赖**：W2-1（共用 Operator 框架）

### W2-3：`operator-image-to-text-suite-20260520`

- **一句话目标**：图片→文字 Operator 三件套 + 1 个 triage 预过滤
  - `image-triage`：本地视觉 model 分类（装饰图 / 流程图 / 数据图 / 公式图 / 其他）→ 决定下游用哪种转换
  - `image-to-caption`：通用图片→自然语言描述（VLM 调用 LLM Gateway）
  - `image-to-mermaid`：流程图 / 架构图 → mermaid 代码
  - `image-to-unicode-art`：简单数据图 / 公式 → unicode art / latex
- **范围**：plugins/operators/image_triage, image_to_caption, image_to_mermaid, image_to_unicode_art
- **核心 AC**：（behavioral）sample row 含 3 张图（1 装饰 / 1 流程 / 1 数据），triage 路由正确；最终输出 row 的 text 字段图占位被替换为对应文字；lineage_ops 含 4 个算子链路
- **依赖**：W2-1，LLM Gateway 调用（已有）
- **风险点**：VLM 调用成本 → 必须先过 image-triage 过滤"装饰图直接丢"

### W2-4：`operator-snapshot-mixer-20260520`

- **一句话目标**：跨 snapshot 的 row 级 union / filter Operator；支持"从 5 个 silver snapshot 各取符合条件的 row 拼成 gold snapshot"
- **范围**：plugins/operators/snapshot_union, snapshot_filter
- **核心 AC**：（behavioral）从 2 个 silver snapshot 各按 lang=en+perplexity<50 过滤后 union，输出 gold snapshot 行数 = 两侧之和
- **依赖**：W2-1
- **永不做清单触发**：用 Operator union 实现"跨 repo 合数据"，撤 merge

### W2-5：`recipe-yaml-v2-20260520`

- **一句话目标**：Recipe YAML 新形态：`loader: ...; operators: [...]; output: ...`；解析器 + 执行器
- **范围**：packages/core/recipe.py 重写，apps/api recipe routes
- **核心 AC**：（behavioral）一份 yaml 含 1 loader + 5 operators 能 parse + 真跑通；老 v1 yaml 报"deprecated, use v2"
- **依赖**：W2-1..W2-4

### W2-6：`dataset-export-engine-20260520`

- **一句话目标**：gold snapshot → 版本化数据集导出（Parquet / JSONL）；含 manifest 记录 row 数 / 来源 snapshot / lineage 摘要
- **范围**：apps/api export route，packages/core/exporter.py
- **核心 AC**：（behavioral）从一个 gold snapshot 导出 parquet + manifest.json，manifest.json 含 row_count / source_snapshots[] / config_hash
- **依赖**：W2-5

**Wave 2 checkpoint**：一份 PDF 走完 upload → bronze → loader → 6 个 Operator → recipe v2 → export.parquet。

---

## Wave 3：源覆盖 + 训练对接（7 changes）

> Wave 3 内 adapter / loader 多数互不影响 packages/core，可并 3。

### W3-1：`adapter-raw-upload-20260520`

- **一句话目标**：通用文件上传 Adapter；接收 PDF / DOCX / PPT / XLSX / 任意 binary 入 bronze
- **范围**：plugins/adapters/raw_upload/, apps/api upload route, apps/web 上传组件
- **核心 AC**：（behavioral）上传 .docx 文件，bronze 路径含原文件名 + sha256，dataset-card.yaml 自动生成

### W3-2：`adapter-folder-md-assets-20260520`

- **一句话目标**：上传含 `*.md + ./assets/` 的 zip / 拖拽文件夹；保留相对路径
- **范围**：plugins/adapters/folder_md_assets/
- **核心 AC**：（behavioral）一个含 doc.md + assets/img1.png 的 zip 上传后 bronze 树结构保持；后续 loader 能识别 ![](assets/img1.png) 相对引用

### W3-3：`adapter-jsonl-import-20260520`

- **一句话目标**：JSONL 直接进 bronze（每行存为一个 blob 还是整文件存？决策：整文件存 bronze，loader 拆行）
- **范围**：plugins/adapters/jsonl_import/
- **核心 AC**：（behavioral）一份 1k 行 jsonl 上传，bronze 单 blob；后续 loader-jsonl 可读出 1k row

### W3-4：`loader-html-md-20260520`

- **一句话目标**：HTML / MD → silver row；保留 heading 结构进 stats.heading_count；图片占位
- **范围**：plugins/loaders/html_md/
- **核心 AC**：（behavioral）一份 md 文件 loader 输出 1+ row，stats.format=md / stats.heading_count > 0

### W3-5：`loader-docx-pptx-20260520`

- **一句话目标**：DOCX / PPTX → silver row（python-docx / python-pptx）；图片提取到 images column
- **范围**：plugins/loaders/docx/, plugins/loaders/pptx/
- **核心 AC**：（behavioral）一份 sample.docx loader 输出 row 含正文文本 + images 列非空

### W3-6：`loader-jsonl-20260520`

- **一句话目标**：bronze 的 jsonl 文件 → 每行展开成 silver row；可配置字段映射
- **范围**：plugins/loaders/jsonl/
- **核心 AC**：（behavioral）映射 `{prompt, response}` 字段后输出 row.text = prompt + "\n" + response

### W3-7：`gold-loader-hf-datasets-20260520`

- **一句话目标**：gold snapshot → HuggingFace `datasets` library 兼容格式（dataset_info.json + parquet shards）
- **范围**：packages/core/exporters/hf_datasets.py
- **核心 AC**：（behavioral）export 后用 `datasets.load_from_disk(path)` 能加载 + iterate；schema 含 text 列

**Wave 3 checkpoint**：4 种格式（PDF / MD-folder / JSONL / HTML）走完整链路 + HF 导出。

---

## Wave 4：UI + 工程化（10 changes）

### W4-1：`web-pdf-mineru-ui-v2-20260520`

- **一句话目标**：基于新 Loader/Operator 模型重做 PDF→MD UI；可预览 silver row 而非老的 markdown 渲染
- **范围**：apps/web/src/routes/repos/$repoId/pdf-mineru/
- **核心 AC**：（behavioral）上传 PDF 后页面可分页展示 silver row 表格；点击行展开 source_ref / stats / lineage_ops

### W4-2：`web-row-preview-20260520`

- **一句话目标**：通用 silver / gold row 预览界面（virtualized table + JSON 详情侧栏）
- **范围**：apps/web/src/routes/repos/$repoId/snapshots/$snapshotId/rows.tsx
- **核心 AC**：（behavioral）打开任意 snapshot rows 路由能展示 ≥ 100 行不卡顿；侧栏展示完整 row JSON

### W4-3：`web-operator-chain-builder-20260520`

- **一句话目标**：拖拽 UI 组装 Operator chain；保存为 recipe v2 yaml；预览每步输出
- **范围**：apps/web/src/routes/recipes/builder.tsx，react-flow 引入
- **核心 AC**：（behavioral）拖 3 个 Operator 节点连线后能保存 yaml + 实际跑通

### W4-4：`web-snapshot-export-ui-20260520`

- **一句话目标**：gold snapshot 导出 UI；选格式（parquet / jsonl / hf_datasets）+ 下载链接
- **范围**：apps/web/src/routes/repos/$repoId/snapshots/$snapshotId/export.tsx
- **核心 AC**：（behavioral）选择格式后点击导出，下载 .zip 含 manifest.json + 数据文件

### W4-5：`cost-budget-system-20260520`

- **一句话目标**：LLM Gateway 调用前预算检查；超额报 402；记 cost stats 到每行
- **范围**：packages/core/cost.py, apps/api/middleware/cost_check.py
- **核心 AC**：（behavioral）设置 repo 月预算 $1，连续调用 VLM 至累计 ≥ $1 后返回 402

### W4-6：`integration-test-framework-20260520`

- **一句话目标**：端到端测试框架；含 fixtures（sample.pdf / sample.docx / sample.jsonl）+ docker-compose 启动
- **范围**：tests/integration/, scripts/integration_test.sh
- **核心 AC**：（behavioral）`bash scripts/integration_test.sh` 跑完输出 PASS / 失败定位明确

### W4-7：`observability-mvp-20260520`

- **一句话目标**：Operator 执行时长 / row 处理量 / 失败率 metrics；简单 dashboard
- **范围**：packages/core/metrics.py, apps/web/src/routes/observability.tsx
- **核心 AC**：（behavioral）跑 1 个 recipe 后 dashboard 显示每个 Operator 处理 row 数 + 平均耗时

### W4-8：`operator-eval-gen-20260520`

- **一句话目标**：bench 数据生成 Operator；从 silver row 自动生成 multiple-choice eval items
- **范围**：plugins/operators/eval_gen/
- **核心 AC**：（behavioral）一份 silver row（文章）经 eval_gen 输出 ≥ 3 道 mc 题，含正确答案 + 干扰项

### W4-9：`operator-dpo-pair-gen-20260520`

- **一句话目标**：DPO 偏好对生成 Operator；从 SFT row 生成 (chosen, rejected) pair
- **范围**：plugins/operators/dpo_pair_gen/
- **核心 AC**：（behavioral）SFT row 输入，输出 row 含 chosen / rejected 双列

### W4-10：`backup-restore-20260520`

- **一句话目标**：bronze CAS 备份到 S3 / 本地外盘；snapshot metadata 备份；恢复脚本
- **范围**：scripts/backup.sh, scripts/restore.sh, apps/api/backup.py
- **核心 AC**：（behavioral）`bash scripts/backup.sh` 输出 backup_<ts>.tar.gz；`bash scripts/restore.sh <file>` 在空 db 上还原 + repo 列表一致

**Wave 4 checkpoint（系统终态验收）**：用户在 UI 上完成完整流程：
1. 上传 PDF + MD folder + JSONL 三种源
2. 在 web/row-preview 看 silver row
3. 在 web/operator-chain-builder 拖一条 6-step chain
4. 在 web/snapshot-export-ui 导出 hf_datasets 格式
5. 用 `datasets.load_from_disk()` 加载验证

---

## 横切硬约束（所有 27 changes 适用）

1. 每个 change 都走 harness v2 三阶段：Design (opus) → Implementation (sonnet 端到端) → Verify (opus)
2. 每个 change 至少 1 条 behavioral AC（ac_kind_lint 不允许 exempt，除非真的纯文档 / 治理）
3. 每个 change Phase 1 reviewer 必查 `.harness/rules/data-not-code-pivot.md` 永不做清单
4. 每个 change 一个 `change/<id>` 分支，Phase 2 一次 push，Phase 3 APPROVED 后 merge --no-ff
5. self_check 每个 change 加自己的 block；full 调用链 ≥ 3 次出现
6. 不允许跨 wave 抢跑（W2 不能在 W1-4 未完成时启动）
7. Wave 内串行节点见各 wave 表格备注

## 反 over-engineering 兜底

- Phase 1 reviewer SMALL REVISIONS 修一轮直接进 Phase 2
- Phase 3 reviewer MINOR FIX 修一轮直接 merge
- MAJOR ISSUE 回 Phase 2 重 spawn（最多 1 次；第 2 次仍 MAJOR → 升级到 application-owner 评估是否拆 change）
- 任何 change spec.md 超 500 行 → 信号"拆 change"，停下来评估

## 验收闭环

- Wave 1 / 2 / 3 / 4 各 checkpoint 在 dashboard.md 标 `wave_checkpoint: pending → in_progress → done`
- Wave 4 全 done 后，application-owner 自审一次完整 user journey，写 `final_verification.md`
- 提交给用户最终验收
