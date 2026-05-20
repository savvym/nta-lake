---
change_id: loader-docx-pptx-20260520
phase: implementation
status: done
authored_at: 2026-05-20T00:00:00Z
author: sonnet-phase2-implementer
model_used: sonnet
branch: change/loader-docx-pptx-20260520
base_commit: bf27a90
head_commit: (回填于 commit 后)
pr_url: n/a
---

# Implementation：DocxLoader + PptxLoader (W3-5)

## 改动文件清单

| 路径 | 类型 | 一句话说明 |
|---|---|---|
| `packages/core/pyproject.toml` | edit | +python-docx>=1.1,<2; +python-pptx>=0.6,<2 |
| `packages/core/src/dataplat_core/loaders/docx.py` | new | DocxLoader（~80 行）：段落文本 + 图片真抓写 blob_store |
| `packages/core/src/dataplat_core/loaders/pptx.py` | new | PptxLoader（~90 行）：slide 文本 + 图片真抓写 blob_store |
| `packages/core/src/dataplat_core/loaders/__init__.py` | edit | +DocxLoader/PptxLoader import+register+__all__ |
| `packages/core/tests/test_loader_docx.py` | new | 3 behavioral tests |
| `packages/core/tests/test_loader_pptx.py` | new | 3 behavioral tests |

## 实现要点

- **DocxLoader**：`Document(BytesIO(data))` → `doc.paragraphs` 拼文本；`doc.part.related_parts` 过滤 `content_type.startswith("image/")` → `blob_store.put(BytesIO(part.blob))` 写图；stats: format/paragraph_count/image_count/char_count
- **PptxLoader**：`Presentation(BytesIO(data))` → 遍历 slides/shapes，`shape.has_text_frame` 拼文本（`\n\n[slide N]\n\n` 分隔）；`shape.shape_type == 13`（PICTURE）抓 `shape.image.blob` → `blob_store.put` 写图；stats: format/slide_count/image_count/char_count
- 图片 dict 含 `{filename, blob_sha, content_type}`；与 design.md AC 一致
- `asyncio.run(_run())` 同 W3-4 HtmlMdLoader 模式；流式 get() 有 chunk 拼接兜底
- auto-register：for 循环 + try/except ValueError；保持 html-md 已有注册不破裂
- 测试 fixture：运行时 python-docx / python-pptx 构造二进制；_PNG_1x1_B64 内嵌 base64，无外部文件

## 测试通过证据

```text
$ uv run pytest packages/core/tests/test_loader_docx.py packages/core/tests/test_loader_pptx.py -x -q
......
6 passed in 0.55s

$ uv run pytest packages/core/tests/ -x -q
84 passed in 0.78s
```

## AC 覆盖

| AC | 结果 |
|---|---|
| AC-1 LoaderRegistry 含 "docx"+"pptx" | PASS |
| AC-2 DocxLoader happy（text+images+stats） | PASS |
| AC-3 PptxLoader happy（text+images+stats.slide_count==1） | PASS |
| AC-4 blob_store 缺失 → ValueError("ctx.blob_store") | PASS × 2 |

## 偏离 design.md

なし（无偏离）。

## 下一步

进入 Phase 3：Application Owner spawn opus reviewer 对照 design.md 验 PR。
