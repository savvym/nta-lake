---
change_id: loader-docx-pptx-20260520
phase: verify
status: approved
verdict: APPROVED
reviewed_at: 2026-05-21T06:30:00Z
reviewer: verify-reviewer-agent
model_used: opus
ac_kind_lint: enforce
---

# Verify Review：DOCX/PPTX Loader (W3-5)

## Verdict

**APPROVED**：6 个新 behavioral AC 全 PASS / packages/core 全量 84 passed / 跨 change 回归 23 passed clean / diff 范围严格在 design 允许内 / 不变量逐项符合 / 永不做清单 grep clean。**0 个 MUST FIX / 0 个 SHOULD FIX**。

## 输入

- Design：`.harness/changes/loader-docx-pptx-20260520/design.md`（4 个 behavioral AC）
- Implementation：`.harness/changes/loader-docx-pptx-20260520/implementation.md`（sonnet 报告 DEVIATIONS 无）
- Git diff：`git diff main..change/loader-docx-pptx-20260520`
- 分支：`change/loader-docx-pptx-20260520`
- Impl commits：`91b215f`（DocxLoader + PptxLoader）+ `c0cb178`（implementation.md backfill）

## AC 对照表

| AC | kind | reviewer 跑的命令 | 实际输出 | PASS/FAIL |
|---|---|---|---|---|
| AC-1 | behavioral | `uv run pytest tests/test_loader_docx.py::test_docx_auto_registered tests/test_loader_pptx.py::test_pptx_auto_registered -v` | 2 passed | **PASS** |
| AC-2 | behavioral | `uv run pytest tests/test_loader_docx.py::test_docx_load_happy -v` | 1 passed（text 含 "Hello docx" / stats.format=="docx" / paragraph_count>=1 / image_count>=1 / images[0] 含 blob_sha + content_type 起始 "image/"） | **PASS** |
| AC-3 | behavioral | `uv run pytest tests/test_loader_pptx.py::test_pptx_load_happy -v` | 1 passed（text 含 "Hello pptx" / stats.format=="pptx" / slide_count==1 / image_count>=1 / images[0] 含 blob_sha + content_type 起始 "image/"） | **PASS** |
| AC-4 | behavioral | `uv run pytest tests/test_loader_docx.py::test_docx_requires_blob_store tests/test_loader_pptx.py::test_pptx_requires_blob_store -v` | 2 passed（两个 loader 均 raise ValueError 含 "ctx.blob_store" 子串） | **PASS** |

合计：**6 / 6 behavioral PASS**。

## 机械化检查日志

### 6 个新测试单跑

```text
$ uv run pytest tests/test_loader_docx.py tests/test_loader_pptx.py -v
tests/test_loader_docx.py::test_docx_auto_registered PASSED              [ 16%]
tests/test_loader_docx.py::test_docx_load_happy PASSED                   [ 33%]
tests/test_loader_docx.py::test_docx_requires_blob_store PASSED          [ 50%]
tests/test_loader_pptx.py::test_pptx_auto_registered PASSED              [ 66%]
tests/test_loader_pptx.py::test_pptx_load_happy PASSED                   [ 83%]
tests/test_loader_pptx.py::test_pptx_requires_blob_store PASSED          [100%]
============================== 6 passed in 0.30s ===============================
```

### packages/core 全量回归

```text
$ uv run pytest -q
............................................................................ [ 85%]
............                                                                  [100%]
84 passed in 0.48s
```

W3-4 基线 78 → W3-5 落地 84，新增 6 个测试，**0 个回归**。

### 跨 change 回归（W3-1/W3-2/W3-3/W3-4 + W2-*）

```text
$ uv run pytest tests/test_loader_html_md.py tests/test_adapter_*.py tests/test_operator_*.py -q
.......................                                                  [100%]
23 passed in 0.14s
```

### diff 范围扫描

```text
$ git diff main..change/loader-docx-pptx-20260520 --name-only
.harness/changes/loader-docx-pptx-20260520/design.md
.harness/changes/loader-docx-pptx-20260520/design_review.md
.harness/changes/loader-docx-pptx-20260520/implementation.md
.harness/changes/loader-docx-pptx-20260520/summary.md
.harness/changes/loader-docx-pptx-20260520/verify_review.md
packages/core/pyproject.toml
packages/core/src/dataplat_core/loaders/__init__.py
packages/core/src/dataplat_core/loaders/docx.py
packages/core/src/dataplat_core/loaders/pptx.py
packages/core/tests/test_loader_docx.py
packages/core/tests/test_loader_pptx.py
uv.lock

$ git diff main..change/loader-docx-pptx-20260520 --stat
 .harness/changes/loader-docx-pptx-20260520/design.md           | 127 +++
 .harness/changes/loader-docx-pptx-20260520/design_review.md    |  58 +
 .harness/changes/loader-docx-pptx-20260520/implementation.md   |  62 +
 .harness/changes/loader-docx-pptx-20260520/summary.md          |  62 +
 .harness/changes/loader-docx-pptx-20260520/verify_review.md    |  ~~
 packages/core/pyproject.toml                                   |   2 +
 packages/core/src/dataplat_core/loaders/__init__.py            |  13 +-
 packages/core/src/dataplat_core/loaders/docx.py                |  95 +
 packages/core/src/dataplat_core/loaders/pptx.py                | 118 +
 packages/core/tests/test_loader_docx.py                        |  97 +
 packages/core/tests/test_loader_pptx.py                        |  98 +
 uv.lock                                                        | 234 +
```

确认改动范围 ⊆ design 允许：

- `packages/core/src/dataplat_core/loaders/docx.py` 新（design § In scope 第 1 项）
- `packages/core/src/dataplat_core/loaders/pptx.py` 新（design § In scope 第 2 项）
- `packages/core/src/dataplat_core/loaders/__init__.py` 改（auto-register 新增 docx + pptx，design § In scope 第 3 项）
- `packages/core/pyproject.toml` 改（python-docx>=1.1,<2 + python-pptx>=0.6,<2，design § 决策 3 允许）
- `packages/core/tests/test_loader_docx.py` 新（design § In scope）
- `packages/core/tests/test_loader_pptx.py` 新（design § In scope）
- `.harness/changes/loader-docx-pptx-20260520/*` 五文档（design / design_review / implementation / summary / verify_review，design_review 为模板占位）
- `uv.lock` 因新依赖变化（design § 决策 3 隐含允许）

**不出现**禁区改动：`apps/api/*` / `packages/core/src/dataplat_core/loaders/html_md.py` / `packages/core/src/dataplat_core/loaders/registry.py` / 任何 W1-* / W2-* / W3-1..3 产物，**全部未触碰**。

### 永不做清单 grep

```text
$ grep -RInE "manifest\.yaml|dataset-card\.yaml|row.?diff|cherry.?pick|rollback" \
    packages/core/src/dataplat_core/loaders/docx.py \
    packages/core/src/dataplat_core/loaders/pptx.py \
    packages/core/tests/test_loader_docx.py \
    packages/core/tests/test_loader_pptx.py
# (no output) exit=1 → clean
```

**clean**：未引入任何禁词。

## 不变量检查（直读源码逐项）

### DocxLoader (`packages/core/src/dataplat_core/loaders/docx.py`)

| 不变量 | 实际 | ✅/❌ |
|---|---|---|
| name="docx" | line 24 `name: str = "docx"` | ✅ |
| version="0.1" | line 25 `version: str = "0.1"` | ✅ |
| input_subtype="docx" | line 26 | ✅ |
| output_schema_id="silver-text-v1" | line 27 | ✅ |
| `asyncio.run(_run())` 包 async 到 sync `load(...)` | line 95 + `_run` line 42 | ✅ |
| ctx.blob_store 缺失 → ValueError 含 "ctx.blob_store" | line 36-40 | ✅ |
| 图片 dict = `{filename, blob_sha, content_type}` | line 66-70 | ✅ |
| 图片 bytes 写 `await blob_store.put(BytesIO(image_bytes), declared_size=...)` | line 62-64 | ✅ |
| SilverRow 字段 text + images + source_ref + stats + lineage_ops=[] | line 72-87 | ✅ |
| stats 含 format="docx" / paragraph_count / image_count / char_count | line 80-85 | ✅ |
| source_ref 含 `{blob_sha, loader, loader_version}` | line 75-79 | ✅ |
| bytes / 流双兼容（chunk 拼接兜底） | line 46-50 | ✅ |

### PptxLoader (`packages/core/src/dataplat_core/loaders/pptx.py`)

| 不变量 | 实际 | ✅/❌ |
|---|---|---|
| name="pptx" | line 26 | ✅ |
| version="0.1" | line 27 | ✅ |
| input_subtype="pptx" | line 28 | ✅ |
| output_schema_id="silver-text-v1" | line 29 | ✅ |
| `asyncio.run(_run())` 包 async 到 sync `load(...)` | line 118 + `_run` line 44 | ✅ |
| ctx.blob_store 缺失 → ValueError 含 "ctx.blob_store" | line 38-42 | ✅ |
| 图片 dict = `{filename, blob_sha, content_type}` | line 80-84 | ✅ |
| 图片 bytes 写 `await blob_store.put(BytesIO(image_bytes), declared_size=...)` | line 77-79 | ✅ |
| SilverRow 字段 text + images + source_ref + stats + lineage_ops=[] | line 95-110 | ✅ |
| stats 含 format="pptx" / slide_count / image_count / char_count | line 103-108 | ✅ |
| source_ref 含 `{blob_sha, loader, loader_version}` | line 98-102 | ✅ |
| MSO_SHAPE_TYPE.PICTURE 用整数常量 `_MSO_PICTURE = 13` 而非动态 import | line 22 + line 67 | ✅（更鲁棒，避免 enum import 跨版本问题） |

### Tests fixture 运行时构造（design § 决策 4）

- `tests/test_loader_docx.py` line 51-61：`Document().add_paragraph(...).add_picture(BytesIO(_PNG_BYTES))` → `save(BytesIO())` ✅
- `tests/test_loader_pptx.py` line 50-62：`Presentation().slides.add_slide(...).shapes.add_picture(...)` → `save(BytesIO())` ✅
- `_PNG_1x1_B64` base64 内嵌 minimal 1×1 PNG（10 行字符串），无外部二进制资源 ✅

### `loaders/__init__.py` 注册逻辑

```python
for _name, _cls in (("html-md", HtmlMdLoader), ("docx", DocxLoader), ("pptx", PptxLoader)):
    try:
        LoaderRegistry.register(_name, _cls)
    except ValueError:
        pass
```

- DocxLoader / PptxLoader import + register ✅
- `__all__` 加 `"DocxLoader"`, `"PptxLoader"` ✅
- 保留 W3-4 html-md 注册不破裂 ✅
- 与 W3-4 单独 try/except 模式略变（合并为 for 循环），但语义等价且更紧凑 — design § 决策未禁止此重构 ✅

## 隐式偏离审计

对照 design.md vs implementation.md vs git diff，逐行扫描：

- implementation.md § "偏离 design.md" 声明 "なし（无偏离）"
- 实际 diff 与 design § In scope 一致；__init__.py 注册逻辑从两个独立 try/except 合并为 for + try/except，**这是局部重构使代码更紧凑**，等价语义；design 未明确要求保持单独 try/except 形式，不视为隐式偏离
- PptxLoader 文件名兜底 `f"slide-{slide_idx}-pic-{pic_idx}.{img.ext}"` 在 `img.filename` 缺失时使用 — design § In scope 未明文细化此 fallback，但与 design § 决策 8（content_type 写到 images 列）方向一致，**实现细节**不构成偏离
- 其余字段、依赖、stats key、注册路径完全符合 design

**结论**：无隐式偏离。

## 问题列表

### MUST FIX

无。

### SHOULD FIX

无。

### NICE TO HAVE（非阻塞，可留 follow-up）

1. **`design_review.md` 模板占位文件残留**：v3 mini-design 流程（design.md frontmatter `process_variant: v3-mini-design`）明确"不 spawn Phase 1 reviewer"，但 `harness_new_change.sh` 创建 change 时 copy 了 `_template/design_review.md`，导致 git 里多出一份占位文档。建议在 follow-up `harness-template-v3-cleanup-*` 里：（a）让脚本按 `process_variant` 选择性 copy 模板；或（b）在 v3 流程下直接 `git rm design_review.md`。**本 change 不修**——属于 harness 框架细节，不阻塞 W3-5 merge。
2. **PptxLoader fallback filename 含 slide 索引**：`f"slide-{slide_idx}-pic-{pic_idx}.{img.ext}"` 当前用 0-based slide_idx，可考虑与 stats / text 中 `[slide N]` 的 1-based 对齐，便于人类追踪。**纯文案级**，不阻塞。

## 后续指引

- **可以 merge 到 main**：4 AC PASS / 84 total PASS / 跨 change clean / diff 范围合规 / 不变量全 ✅ / 永不做清单 grep clean / 无隐式偏离
- merge 后 application-owner 回填：
  - `summary.md` frontmatter `status` → `merged`
  - `summary.md` 阶段进度表 Phase 1/2/3 commit 列回填
  - `implementation.md` frontmatter `head_commit` 与 `pr_url`（若有）
- NICE TO HAVE 项可在收尾时统一开一个 harness meta change 处理
