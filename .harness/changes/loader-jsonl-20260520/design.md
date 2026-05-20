---
change_id: loader-jsonl-20260520
phase: design
status: approved
authored_at: 2026-05-21T06:35:00Z
author: application-owner-agent
model_used: opus
ac_kind_lint: enforce
---

# Design：JSONL loader (W3-6，v3 mini-design)

> v3 mini-design：application-owner 自写；不 spawn Phase 1 reviewer（D-13）。

## 一句话目标

新增 `JsonlLoader` 到 `packages/core/src/dataplat_core/loaders/jsonl.py`：从 bronze blob 读 .jsonl / .jsonl.gz，每行 JSON object → 1 个 `SilverRow`；stats 含 `format` / `line_count` / `error_count` / `char_count`；坏行跳过 + 计入 error_count 不抛。

## 背景

W3-3 已落 `JsonlImportAdapter`（refs → IngestResult，强制单文件 .jsonl(.gz) + 可选 line_count 透传到 notes）；W3-6 是上下游配对，从 bronze 拆行成 silver rows。

参考实现：W3-4 `HtmlMdLoader`（packages/core/loaders/html_md.py）— asyncio.run + ctx.blob_store.get + SilverRow 模式；W3-5 `DocxLoader/PptxLoader` 多 row 输出（pptx 每 slide 1 row 类似 jsonl 每行 1 row 但语义不同：jsonl 强制行级 1→1）。

业务诉求（roadmap W3-6）：jsonl 是 LLM 训练数据集最常见格式（HF datasets / OpenAI fine-tuning / SFT 等导出都是 jsonl）；典型 1 行 = 1 个训练样本；每行有 `text` 字段（或 `prompt`/`completion` 对，但首版只取单字段）。

`packages/core/loaders/` 已有 `html_md` / `docx` / `pptx`；本 change 是第 4 个真正 loader。stdlib `json` + `gzip` 足够，不引入新依赖。

## 范围

In scope：

- `packages/core/src/dataplat_core/loaders/jsonl.py`（新）：
  - class `JsonlLoader`：
    - `name: str = "jsonl"`
    - `version: str = "0.1"`
    - `input_subtype: str = "jsonl"`
    - `output_schema_id: str = "silver-text-v1"`
    - `load(bronze_blob_sha, config, ctx) -> LoadResult`：
      - 从 `ctx.blob_store.get(sha)` 读 bytes（缺失 → ValueError 含 "ctx.blob_store"）
      - 按 `config.get("format")` 或 path hint 判 gz：
        - format == "jsonl.gz" 或 path 以 `.jsonl.gz` 结尾 → `gzip.decompress(data)`
        - 否则当作明文 jsonl
      - `text = data.decode("utf-8", errors="replace")`
      - 按行拆（`splitlines()`）；跳过空行；非空行 `json.loads`：
        - 解析失败（`json.JSONDecodeError`）→ `error_count += 1`，跳过该行
        - 解析后非 dict（如 list / str / number）→ `error_count += 1`，跳过该行
        - 缺 `text_field` 字段或字段非 str → `error_count += 1`，跳过该行
      - 每条有效行 → 1 个 SilverRow：
        - `text`: 该行 JSON 对象的 `text_field` 字段值（默认 `"text"`，可由 `config.get("text_field")` 覆盖）
        - `images`: `[]`（jsonl 文本场景；图片留 follow-up）
        - `source_ref`: `{"blob_sha": bronze_blob_sha, "loader": "jsonl", "loader_version": "0.1", "line_no": <1-based 在原 jsonl 中的行号>}`
        - `stats`: `{}`（per-row stats 留空；全局 stats 见下）
        - `lineage_ops`: `[]`
      - 全局 stats（放在 LoadResult.notes 字符串里更省事，但 W3-4/W3-5 已确立 per-row stats，所以本 change 也把 stats 放到**每个 row** 的 `stats` dict —— 但 line_count / error_count 是全局量，写到 notes）：
        - 决策：per-row stats 仅 `{"format": "jsonl"/"jsonl.gz", "char_count": len(row_text)}`
        - 全局：`notes = f"line_count={N_total}, error_count={N_error}"`（caller / 测试 split + int 解析）
      - 返回 `LoadResult(rows=[...], total_count=len(rows), notes=...)`
- `packages/core/src/dataplat_core/loaders/__init__.py`（改）：
  - import `JsonlLoader`
  - 在现有 for 循环加 `("jsonl", JsonlLoader)`
  - `__all__` 加 `"JsonlLoader"`
- `packages/core/tests/test_loader_jsonl.py`（新）：4 个 behavioral 用例

Out of scope：

- **不**接 apps/api routes：留 follow-up `loader-jsonl-route-*`
- **不**做 prompt/completion 对模式（每行多字段映射）：MVP 只单字段；留 follow-up `loader-jsonl-prompt-completion-*`
- **不**抓取 jsonl 行内嵌图片 URL / base64：留 follow-up `loader-jsonl-image-extract-*`
- **不**做嵌套字段提取（如 `messages[0].content`）：留 follow-up
- **不**做流式读取（whole blob 加载到内存）：留 follow-up `loader-async-stream-protocol-*`
- **不**改 Loader Protocol / LoaderRegistry / 其他 loader / adapter
- **不**做 dataset-card.yaml / manifest.yaml（D-1 永不做清单）

## 验收标准

| ID | kind | 描述 | 验证方式 | 期望 |
|---|---|---|---|---|
| AC-1 | behavioral | import dataplat_core.loaders 后 LoaderRegistry.list_names() 含 "jsonl" | `cd packages/core && uv run pytest tests/test_loader_jsonl.py::test_jsonl_auto_registered -x -q` | 1 passed |
| AC-2 | behavioral | jsonl 明文 happy：blob 含 3 行有效 + 1 空行 + 1 坏 json + 1 缺 text 字段 → load 返 LoadResult(total_count=3, rows[i].text == 对应行 text 字段, notes 含 "line_count=3, error_count=2", rows[i].stats.format=="jsonl", source_ref.line_no 是 1-based 原行号) | `cd packages/core && uv run pytest tests/test_loader_jsonl.py::test_jsonl_load_plain_happy -x -q` | 1 passed |
| AC-3 | behavioral | jsonl.gz happy：gzip.compress(b'{"text":"a"}\n{"text":"b"}\n') → blob → load with config={"format":"jsonl.gz"} → total_count=2, stats.format=="jsonl.gz" | `cd packages/core && uv run pytest tests/test_loader_jsonl.py::test_jsonl_load_gz_happy -x -q` | 1 passed |
| AC-4 | behavioral | ctx.blob_store 缺失 → raise ValueError 含 "ctx.blob_store" 子串 | `cd packages/core && uv run pytest tests/test_loader_jsonl.py::test_jsonl_requires_blob_store -x -q` | 1 passed |

## 决策

1. **每行 1 row（行级 1→N）**：与 W3-4 html-md 单 row、W3-5 docx/pptx 单 row 不同；jsonl 天然每行 1 训练样本；rows 数量 = 有效行数。
2. **坏行不抛**：jsonl 训练数据集常含少量 malformed 行（爬虫日志 / 拼接错误）；loader 跳过 + error_count 计数比 fail-fast 更友好；caller 通过 `notes` 字段感知；error_count 大时下游 operator 可决定丢弃数据集。
3. **default text_field = "text"**：业界事实标准；可由 `config.text_field` 覆盖（OpenAI SFT 用 "prompt"/"completion"；HF SFTTrainer 默认 "text"）。
4. **stdlib json + gzip**：不引入新依赖；packages/core 当前仅依赖 pydantic + python-docx + python-pptx（W3-5 引入）。
5. **gz 透明解压**：format / path hint 任一命中 `.jsonl.gz` 则解压；与 W3-3 adapter 后缀决策对齐。
6. **per-row stats 极简**：仅 format + char_count；line_count / error_count 是全局量放 notes；避免 row stats 冗余。
7. **source_ref 加 line_no（1-based 原行号）**：与 W3-4 html-md / W3-5 docx/pptx 的 source_ref 仅 {blob_sha, loader, loader_version} 略增；jsonl 多 row 场景需要追溯到 bronze 原行（用于 caller 复现 / debug）。
8. **空行跳过不计 error**：jsonl 文件尾常有空行；空行非数据非错误；只跳过；不计入 line_count 或 error_count。
9. **缺 text_field 也计 error_count**：与 "坏 json" 同等待遇；caller 看到 error_count 高就该换 text_field 配置或换 adapter。
10. **不做 dataset-card.yaml / manifest.yaml**：D-1 永不做清单；grep roadmap W3-6 段确认无 manifest 类 AC。

## 风险

| 风险 | 缓解 |
|---|---|
| 大文件（GB 级 jsonl）一次性 load 到内存 OOM | 决策 4 + 风险接受：MVP 不做流式；packages/core blob_store get 当前也是 bytes 接口；流式留 follow-up `loader-async-stream-protocol-*`；caller 已通过 W3-3 adapter line_count 提示可预估大小 |
| `json.JSONDecodeError` 之外的 `TypeError`（如 line 是 bytes 而非 str）| 已用 `text.splitlines()`（str 来源）；json.loads(str) 是默认；不会触发 TypeError |
| jsonl 行内嵌 `\n`（json 字符串里的转义换行）| splitlines() 按物理行拆；json 转义 `\n` 在源 jsonl 文件里写作 `\\n`，splitlines 不会破裂；如有 caller 在生成 jsonl 时把字符串里的真换行没转义，那是 caller 的 bug，本 loader 不修 |
| 空 jsonl 文件（0 行）| total_count=0，notes="line_count=0, error_count=0"；返回 `LoadResult(rows=[])`；caller 自决（与 W3-4 / W3-5 不同：jsonl 允许 0 row 是合法语义） |
| `config.text_field` 为空字符串或 None | `text_field = config.get("text_field") or "text"`；空串/None 都走默认 |
| asyncio.run 嵌套在调用方已有 event loop 抛 RuntimeError | 与 W1-4 / W3-4 / W3-5 同模式；follow-up `loader-async-protocol-*` |
| LoaderRegistry 注册 idempotent | 现 for 循环已 try/except ValueError 包裹（W3-5 引入）；不破裂 |

## 交叉引用清单（reviewer 必查）

- 引用但不修改：
  - `packages/core/src/dataplat_core/protocols/loader.py`（Loader Protocol / SilverRow / LoadResult）
  - `packages/core/src/dataplat_core/protocols/runcontext.py`（RunContext）
  - `packages/core/src/dataplat_core/loaders/registry.py`（LoaderRegistry）
  - `packages/core/src/dataplat_core/loaders/html_md.py`（W3-4 模板参考）
  - `packages/core/src/dataplat_core/loaders/docx.py` / `pptx.py`（W3-5 模板参考）
  - `packages/core/src/dataplat_core/adapters/jsonl_import.py`（W3-3 上游 adapter）
- 应当不动：
  - `apps/api/*`（全部不动）
  - W1-* / W2-* / W3-1..5 已 merge 产物
  - 既有 `loaders/__init__.py` for 循环逻辑（只在 tuple 加一项）
- 引用的其他 change：W1-2（Loader Protocol）、W3-3（JsonlImportAdapter，上游）、W3-4（loader-html-md 模板）、W3-5（loader-docx-pptx 多 loader auto-register 模板）

## 关联 follow-up

- `loader-jsonl-route-*`：apps/api 加 POST 触发 jsonl loader
- `loader-jsonl-prompt-completion-*`：多字段映射模式（prompt/completion / messages）
- `loader-jsonl-image-extract-*`：jsonl 行内嵌 image URL / base64 抓取入 blob_store
- `loader-jsonl-nested-field-*`：嵌套字段提取（messages[0].content / data.text 等）
- `loader-async-stream-protocol-*`：流式 Loader Protocol（与 W1-2 / W3-4 关联）
