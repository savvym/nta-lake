---
change_id: loader-docx-pptx-20260520
phase: design
status: approved
authored_at: 2026-05-21T05:50:00Z
author: application-owner-agent
model_used: opus
ac_kind_lint: enforce
---

# Design：DOCX/PPTX loader (W3-5，v3 mini-design)

> v3 mini-design：application-owner 自写；不 spawn Phase 1 reviewer（D-13）。

## 一句话目标

新增 `DocxLoader` + `PptxLoader` 到 `packages/core/src/dataplat_core/loaders/`：从 bronze blob 读 .docx / .pptx，输出 1 个 SilverRow；正文文本 + 内嵌图片提取到 blob_store 形成 `images` 列；stats 含 `format` / `paragraph_count` 或 `slide_count` / `image_count` / `char_count`。

## 背景

W3-4 已落 `HtmlMdLoader` 模板（packages/core/loaders/html_md.py）；W3-5 是第二个真正 packages/core loader，扩展到 OOXML 格式（docx / pptx）。

参考实现：W3-4 HtmlMdLoader 的 `asyncio.run` + `ctx.blob_store.get/put` + SilverRow 输出模式；W1-4 PdfMineruLoader 的图片写 blob_store 模式（每张图 `blob_store.put(BytesIO(bytes))` → 收集 `{"filename":..., "blob_sha":...}`）。

业务诉求（roadmap W3-5）：DOCX / PPTX → silver row，**图片提取到 images column**（不是占位）；这与 W3-4 html-md "图片占位" 决策不同——本 change 真抓 blob。

新依赖：

- `python-docx`：docx 解析（业界事实标准）
- `python-pptx`：pptx 解析（同作者群体；同 OOXML 处理风格）

两者 pure-Python，无 C 扩展，适合 packages/core；与现有 pydantic 依赖无冲突。

## 范围

In scope：

- `packages/core/src/dataplat_core/loaders/docx.py`（新）：
  - class `DocxLoader`：name="docx" / version="0.1" / input_subtype="docx" / output_schema_id="silver-text-v1"
  - `load(sha, config, ctx) -> LoadResult`：
    - 从 `ctx.blob_store.get(sha)` 读 bytes（缺失 → ValueError 含 "ctx.blob_store"）
    - python-docx `Document(BytesIO(bytes))` 解析
    - 正文：`"\n\n".join(p.text for p in doc.paragraphs if p.text.strip())`
    - 图片提取：遍历 `doc.part.related_parts.values()`，过滤 image content_type（startswith "image/"）；每张图 `await blob_store.put(BytesIO(image_bytes), declared_size=...)` → 收集 `{"filename": part.partname.split("/")[-1], "blob_sha": result.sha256, "content_type": part.content_type}`
    - SilverRow：text + images + source_ref={blob_sha, loader:"docx", loader_version:"0.1"} + stats={format:"docx", paragraph_count, image_count, char_count} + lineage_ops=[]
    - 返回 LoadResult(rows=[row], total_count=1, notes=f"docx paragraphs={N}, images={M}")
- `packages/core/src/dataplat_core/loaders/pptx.py`（新）：
  - class `PptxLoader`：name="pptx" / version="0.1" / input_subtype="pptx" / output_schema_id="silver-text-v1"
  - `load(sha, config, ctx) -> LoadResult`：
    - 同模式读 blob → python-pptx `Presentation(BytesIO(bytes))`
    - 正文：拼接每张 slide 内 shape.text_frame.text；slide 间用 `\n\n[slide N]\n\n` 分隔
    - 图片提取：遍历 `prs.slides[i].shapes`，对 `shape.shape_type == 13`（MSO_SHAPE_TYPE.PICTURE）的 shape 调 `shape.image.blob` → 写 blob_store
    - SilverRow：stats={format:"pptx", slide_count, image_count, char_count}
- `packages/core/src/dataplat_core/loaders/__init__.py`（改）：
  - import DocxLoader / PptxLoader
  - try/except ValueError 包裹两次 `LoaderRegistry.register(...)`
  - `__all__` 加 `"DocxLoader"`, `"PptxLoader"`
- `packages/core/pyproject.toml`（改）：
  - dependencies 加 `python-docx>=1.1,<2` 和 `python-pptx>=0.6,<2`
- `packages/core/tests/test_loader_docx.py`（新）：3 个 behavioral 用例（auto-register + happy + no blob_store）
- `packages/core/tests/test_loader_pptx.py`（新）：3 个 behavioral 用例（auto-register + happy + no blob_store）
- `packages/core/tests/conftest.py` 或 fixtures dir 不新增；docx/pptx 测试 fixture **运行时构造**（`Document().add_paragraph("Hello").add_picture(BytesIO(png_bytes))` + save 到 BytesIO）

Out of scope：

- **不**接 apps/api routes：留 follow-up `loader-docx-route-*` / `loader-pptx-route-*`
- **不**做 docx 表格 / footnote / track-changes 解析：MVP 只抓 paragraph + image；留 follow-up
- **不**做 pptx 备注页 / 动画 / 母版解析：MVP 只抓 shape text + image
- **不**做 OCR / 图片自动 caption：W2-3 image_caption operator 处理
- **不**抓嵌入式 video / audio：仅图片
- **不**做 .doc / .ppt 老 OLE 格式：python-docx / python-pptx 只支持 OOXML；老格式留 follow-up
- **不**改 Loader Protocol / LoaderRegistry / 其他 loader / adapter
- **不**做 dataset-card.yaml / manifest.yaml（D-1 永不做清单）

## 验收标准

| ID | kind | 描述 | 验证方式 | 期望 |
|---|---|---|---|---|
| AC-1 | behavioral | import dataplat_core.loaders 后 LoaderRegistry.list_names() 含 "docx" 和 "pptx" | `cd packages/core && uv run pytest tests/test_loader_docx.py::test_docx_auto_registered tests/test_loader_pptx.py::test_pptx_auto_registered -x -q` | 2 passed |
| AC-2 | behavioral | DocxLoader happy：测试运行时 python-docx 构造一个含 paragraph + image 的 .docx bytes → load → rows[0].text 含 paragraph 文本，images 列长度 ≥1，stats.format=="docx", stats.image_count >=1, paragraph_count >=1 | `cd packages/core && uv run pytest tests/test_loader_docx.py::test_docx_load_happy -x -q` | 1 passed |
| AC-3 | behavioral | PptxLoader happy：测试运行时 python-pptx 构造一个含 1 张幻灯片 + text + picture 的 .pptx bytes → load → rows[0].text 含 text，images 列长度 ≥1, stats.format=="pptx", stats.slide_count==1, stats.image_count >=1 | `cd packages/core && uv run pytest tests/test_loader_pptx.py::test_pptx_load_happy -x -q` | 1 passed |
| AC-4 | behavioral | DocxLoader/PptxLoader ctx.blob_store 缺失 → 各自 raise ValueError 含 "ctx.blob_store" | `cd packages/core && uv run pytest tests/test_loader_docx.py::test_docx_requires_blob_store tests/test_loader_pptx.py::test_pptx_requires_blob_store -x -q` | 2 passed |

## 决策

1. **DocxLoader 与 PptxLoader 分两个独立类 + 两个独立文件**：python-docx / python-pptx 是两个独立库，schema 不重叠；分文件清晰；与 W3-4 单文件 HtmlMdLoader 处理两种格式不同——HTML/MD 是文本相近格式，docx/pptx 是 OOXML 但 schema 完全不同。
2. **图片真抓不占位**：与 W3-4 image_ref_count 占位不同；roadmap W3-5 明确"图片提取到 images column"；docx/pptx 内嵌图片可直接拿 bytes，无需外部 HTTP。
3. **新依赖 python-docx + python-pptx**：业界标准；pure-Python；与 pydantic 无冲突；packages/core 接受小幅依赖增长（这是 Wave 3 第一次引入第三方依赖）。
4. **测试 fixture 运行时构造**：不引入 fixture 二进制文件（避免仓库膨胀 + 与不变量难校验）；用 python-docx / python-pptx 在测试里现场构造 .docx / .pptx bytes，再喂给 loader。
5. **图片写 blob_store 用 `await put`**：与 W1-4 PdfMineruLoader 同模式；asyncio.run 包整个 _run 协程。
6. **paragraph_count vs slide_count 不同字段名**：保持 stats 字段对各 format 有意义；caller 按 stats.format 分支解读（与 W3-4 同模式）。
7. **不做表格 / 嵌入式 OLE / video / audio**：MVP 只 text + image；高级特性留 follow-up；与 W2-3 image_strip + W2-2 chunker 链路对齐——loader 只产 raw text + image refs，结构化拆分由 operator 链做。
8. **content_type 写到 images 列元数据**：每张图 dict 含 `{"filename", "blob_sha", "content_type"}`；与 W1-4 PdfMineruLoader 仅 `{"filename", "blob_sha"}` 略增；caller 可按 content_type 分支处理（jpg vs png）。
9. **不做 dataset-card.yaml / manifest.yaml**：D-1 永不做清单；grep roadmap W3-5 段确认无 manifest 类 AC。

## 风险

| 风险 | 缓解 |
|---|---|
| python-docx 1.x 与 python-pptx 0.6.x 跨版本 API 不一致 | pin 范围 `>=1.1,<2` / `>=0.6,<2`；CI 锁版本；sonnet 用 doc.paragraphs / prs.slides 基础 API（跨版本稳定） |
| 测试运行时构造 .docx 需要先有 image bytes | 用 stdlib `base64` 解码一个 minimal 1×1 PNG 作为图片（10 行 base64 字符串）；不依赖文件系统 |
| docx 图片是 sharing image（被多个段落引用）会重复写 blob_store | blob_store CAS 同 sha 上传是 idempotent（BlobPutResult.deduplicated=True）；多次写不破裂；最多统计 image_count 多算（接受） |
| pptx slide_count 在空 ppt 为 0 触发 happy AC 失败 | 测试 fixture 至少加 1 张 slide + 1 个 shape；AC-3 显式断 slide_count==1 |
| 新依赖 python-docx / python-pptx 体积大 | python-docx ~1.5MB / python-pptx ~5MB；total <10MB；packages/core 仍是轻量 |
| pyproject.toml 改动可能引发其他 package install 失败 | 仅改 packages/core/pyproject.toml；apps/api / packages/api-types 等不受影响；sonnet 跑 `uv sync` + 全套 pytest 确认 |

## 交叉引用清单（reviewer 必查）

- 引用但不修改：
  - `packages/core/src/dataplat_core/protocols/loader.py`（Loader Protocol / SilverRow / LoadResult）
  - `packages/core/src/dataplat_core/protocols/runcontext.py`（RunContext）
  - `packages/core/src/dataplat_core/loaders/registry.py`（LoaderRegistry）
  - `packages/core/src/dataplat_core/loaders/html_md.py`（W3-4 模板参考，但不动）
  - `apps/api/dataplat_api/loaders/pdf_mineru.py`（图片写 blob_store 模板参考，但不动）
- 应当不动：
  - `apps/api/*`（全部不动）
  - W1-* / W2-* / W3-1..4 已 merge 产物
  - `packages/core/src/dataplat_core/loaders/registry.py` / `html_md.py`
- 引用的其他 change：W1-2（Loader Protocol）、W1-4（PdfMineruLoader image-extract 模板）、W3-4（loader-html-md 模板）

## 关联 follow-up

- `loader-docx-route-*` / `loader-pptx-route-*`：apps/api 加 POST 路由
- `loader-docx-pptx-tables-*`：docx 表格 / pptx 备注页解析
- `loader-doc-ppt-ole-*`：老 .doc / .ppt OLE 格式
- `loader-async-protocol-*`：Loader Protocol async 版（与 W1-2 / W3-4 关联）
- `loader-docx-pptx-track-changes-*`：track changes / revision history
