---
change_id: loader-html-md-20260520
phase: design
status: approved
authored_at: 2026-05-21T05:00:00Z
author: application-owner-agent
model_used: opus
ac_kind_lint: enforce
---

# Design：HTML/MD loader (W3-4，v3 mini-design)

> v3 mini-design：application-owner 自写；不 spawn Phase 1 reviewer（D-13）。

## 一句话目标

新增 `HtmlMdLoader` 到 `packages/core/src/dataplat_core/loaders/html_md.py`：从 bronze blob 读取 .md / .html 文件，输出 1 个 `SilverRow`，stats 含 `format` / `heading_count` / `char_count` / `image_ref_count`；图片仅占位（不抓取真实 blob）。

## 背景

W3-1..W3-3 已落 3 个 adapter（refs → IngestResult）；W3-4 是 Wave 3 第一个 **Loader**，把 bronze blob → silver rows。

参考实现：`apps/api/dataplat_api/loaders/pdf_mineru.py`（W1-4 PdfMineruLoader，Loader Protocol 现成模式：`load(bronze_blob_sha, config, ctx)` → 通过 `ctx.blob_store.get(sha)` 读 bytes → 解析 → 返 `LoadResult(rows=[SilverRow], total_count=1)`）。

业务诉求（roadmap W3-4）：HTML / MD → silver row；保留 heading 结构进 `stats.heading_count`；图片占位。

`packages/core/src/dataplat_core/loaders/` 当前**只有 LoaderRegistry 骨架**——本 change 是 packages/core 内首个真正的 Loader 落地，为 W3-5（docx/pptx）/ W3-6（jsonl）建立 packages/core loader 模板。

## 范围

In scope：

- `packages/core/src/dataplat_core/loaders/html_md.py`（新）：
  - class `HtmlMdLoader`：
    - `name: str = "html-md"`
    - `version: str = "0.1"`
    - `input_subtype: str = "html-md"`
    - `output_schema_id: str = "silver-text-v1"`
    - `load(bronze_blob_sha, config, ctx) -> LoadResult`：
      - 从 `ctx.blob_store.get(bronze_blob_sha)` 读 bytes（与 W1-4 PdfMineruLoader 同模式；blob_store 缺失 → ValueError 含 "ctx.blob_store"）
      - 处理 bytes → str（`decode("utf-8", errors="replace")`）
      - 根据 `config.get("format")` 二选一解析：
        - format == "md" 或 path 后缀 .md / .markdown → markdown 解析
        - format == "html" 或 path 后缀 .html / .htm → html 解析
        - format 缺失且无 path hint → 默认 md（与 roadmap "md 文件 loader 输出 1+ row" AC 对齐）
      - **stats** 字段：
        - `format`: "md" / "html"
        - `heading_count`: int（md: `re.findall(r'^#{1,6}\s+.+$', text, re.MULTILINE)` 计数；html: `html.parser` 提取 h1..h6 标签计数）
        - `char_count`: len(text)
        - `image_ref_count`: int（md: `re.findall(r'!\[[^\]]*\]\([^)]+\)', text)` 计数；html: `<img>` 标签计数）
      - **图片占位**：不抓取实际图片 bytes / 不写 blob_store；只统计 `image_ref_count`；`SilverRow.images = []`
      - 输出 1 个 SilverRow：
        - `text`: 原始 markdown / html 字符串（不做净化；下游 operator 处理）
        - `images`: `[]`（占位决策）
        - `source_ref`: `{"blob_sha": bronze_blob_sha, "loader": "html-md", "loader_version": "0.1"}`
        - `stats`: 上述 4 个字段
        - `lineage_ops`: `[]`
      - 返回 `LoadResult(rows=[row], total_count=1, notes=f"format={format}")`
- `packages/core/src/dataplat_core/loaders/__init__.py`（改）：
  - import `HtmlMdLoader`
  - `LoaderRegistry.register("html-md", HtmlMdLoader)` 用 try/except ValueError 包裹（idempotent，避免反复 pytest 加载破裂）
  - `__all__` 加 `"HtmlMdLoader"`
- `packages/core/tests/test_loader_html_md.py`（新）：4 个 behavioral 用例 + 内联 `_StubBlobStore` 与 W2-6 同模式

Out of scope：

- **不**接入 apps/api routes / worker：留 follow-up `loader-html-md-route-*`
- **不**做 HTML 净化（XSS / 脚本剥离）：留 follow-up `loader-html-md-sanitize-*`
- **不**做 frontmatter 解析（如 jekyll YAML front matter）：留 follow-up
- **不**抓取实际图片到 blob_store：本 change 仅 image_ref_count；真图片处理留 W2-3 image_strip / W3-5 docx-pptx 同模式 follow-up
- **不**做 markdown 高级特性（table / footnote / math）：仅 heading + image ref count 满足 AC
- **不**改 Loader Protocol / LoaderRegistry / W1-* / W2-* / W3-1..3 产物
- **不**改 apps/api PdfMineruLoader

## 验收标准

| ID | kind | 描述 | 验证方式 | 期望 |
|---|---|---|---|---|
| AC-1 | behavioral | import dataplat_core.loaders 后 LoaderRegistry.list_names() 含 "html-md"；LoaderRegistry.get("html-md") is HtmlMdLoader | `cd packages/core && uv run pytest tests/test_loader_html_md.py::test_html_md_auto_registered -x -q` | 1 passed |
| AC-2 | behavioral | md happy path：blob_store 含 `# Title\n\n## Sub\n\ntext ![alt](img.png)` → load 返 LoadResult(total_count=1, rows[0].stats={"format":"md", "heading_count":2, "char_count": N, "image_ref_count":1}, source_ref["blob_sha"]==sha) | `cd packages/core && uv run pytest tests/test_loader_html_md.py::test_html_md_load_markdown_happy -x -q` | 1 passed |
| AC-3 | behavioral | html happy path：blob_store 含 `<h1>X</h1><h2>Y</h2><img src=a.png>` + config={"format":"html"} → rows[0].stats={"format":"html","heading_count":2,"image_ref_count":1, ...} | `cd packages/core && uv run pytest tests/test_loader_html_md.py::test_html_md_load_html_happy -x -q` | 1 passed |
| AC-4 | behavioral | ctx.blob_store 缺失 → raise ValueError 含 "ctx.blob_store" 子串 | `cd packages/core && uv run pytest tests/test_loader_html_md.py::test_html_md_requires_blob_store -x -q` | 1 passed |

## 决策

1. **packages/core 内落 loader**：与 W3-1..W3-3 同节奏（核心落 core）；apps/api 接入留 follow-up。这是 packages/core 内首个真正 Loader，为 W3-5 / W3-6 立模板。
2. **单文件 → 单 row（不按 heading 拆分）**：行级拆分是 chunker operator（W2-2）职责；loader 保持 "1 blob → 1+ row"，本场景 1 blob → 1 row 最简。
3. **format 优先看 config，再看 path hint，最后默认 md**：caller 用 config["format"] 显式覆盖；不存在 path 元数据时（仅 bronze_blob_sha）默认 md。
4. **stdlib 解析，不引入新依赖**：md heading 用 `re.MULTILINE` 正则；html 用 `html.parser`（stdlib）。markdown-it-py / beautifulsoup 留 future（packages/core 当前只依赖 pydantic）。
5. **图片占位（image_ref_count + images=[]）**：不抓取实际图片 blob；与 W2-3 image_strip 操作语义对齐（loader 不做强算子语义；图片走 operator 链）。
6. **decode utf-8 errors=replace**：bronze blob 可能含非 UTF-8 字节（legacy html）；replace 比 strict 友好；下游 operator 可基于 stats 判断是否需 cleanup。
7. **stub BlobStore 内联在测试文件**（与 W2-6 同模式）：实现 `async def get(sha) -> bytes`；不复用 W2-6 测试 stub 跨文件 import（保持测试文件独立）。
8. **asyncio.run 内嵌实现**（与 W1-4 PdfMineruLoader 同模式）：blob_store.get 是 async；loader.load 同步签名；内部 `asyncio.run(_run())` 把 async 包到 sync 接口。
9. **不做 manifest.yaml / dataset-card.yaml**：D-1 永不做清单；grep roadmap W3-4 段确认无 manifest 类 AC。

## 风险

| 风险 | 缓解 |
|---|---|
| markdown 正则简陋（如 `# Title` 在代码块内也被算 heading）| 决策 4：MVP 用简单正则；后续 follow-up 引入 markdown-it-py 做精确解析；当前 stats.heading_count 是"近似"——足够 AC 表达 |
| html.parser 对损坏 html 容错弱 | stdlib html.parser 默认容错；malformed input 解析时不抛；上游 adapter 已校验文件格式 |
| asyncio.run 嵌套在调用方已有 event loop 会抛 RuntimeError | 与 W1-4 PdfMineruLoader 同模式（同样问题）；caller 用 async loader 抽象留 follow-up `loader-async-protocol-*`（与 W1-2 关联） |
| blob_store stub 测试与生产 store 行为漂移 | stub 仅实现 get + put 最小子集；与 W2-6 dataset_export 测试同模式；生产 store 由 W1-4 BlobStore Protocol 已定义 |
| LoaderRegistry 注册 idempotent 不破裂 | try/except ValueError 包裹（与 OperatorRegistry / AdapterRegistry W3-1 同模式） |
| heading 正则在文件首行无换行时不匹配 | `re.MULTILINE` 模式 `^` 匹配行首；文件首行 `# Title` 也命中；已验证 |

## 交叉引用清单（reviewer 必查）

- 引用但不修改：
  - `packages/core/src/dataplat_core/protocols/loader.py`（Loader Protocol / SilverRow / LoadResult）
  - `packages/core/src/dataplat_core/protocols/runcontext.py`（RunContext）
  - `packages/core/src/dataplat_core/loaders/registry.py`（LoaderRegistry）
  - `apps/api/dataplat_api/loaders/pdf_mineru.py`（**实现模板参考**，但不动）
- 应当不动：
  - `apps/api/*`（全部不动）
  - W1-* / W2-* / W3-1..3 所有产物
  - `packages/core/src/dataplat_core/loaders/registry.py`（W1-4 已稳）
- 引用的其他 change：W1-2（Loader Protocol）、W1-4（PdfMineruLoader 实现模板）、W3-1（auto-register 模式）

## 关联 follow-up

- `loader-html-md-route-*`：apps/api 加 POST 触发 html-md loader
- `loader-html-md-sanitize-*`：HTML XSS 净化
- `loader-html-md-frontmatter-*`：jekyll / hugo YAML frontmatter 解析
- `loader-async-protocol-*`：Loader Protocol 加 async 版本（与 W1-2 关联）
- `loader-html-md-image-fetch-*`：抓取相对/绝对图片 URL 入 blob_store
