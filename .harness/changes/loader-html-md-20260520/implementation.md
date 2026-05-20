---
change_id: loader-html-md-20260520
phase: implementation
status: done
authored_at: 2026-05-20T00:00:00Z
author: sonnet-phase2-implementer
model_used: sonnet
branch: change/loader-html-md-20260520
base_commit: 7e46c9a
head_commit: (回填于 commit 后)
pr_url: n/a
---

# Implementation：html/md loader (W3-4)

## 落地文件

| 路径 | 类型 | 一句话说明 |
|---|---|---|
| `packages/core/src/dataplat_core/loaders/html_md.py` | new | HtmlMdLoader 实现（~110 行） |
| `packages/core/src/dataplat_core/loaders/__init__.py` | edit | +import/register/\_\_all\_\_ |
| `packages/core/tests/test_loader_html_md.py` | new | 4 behavioral tests |

## 实现要点

- stdlib `re` 处理 MD：`^#{1,6}\s+.+$` 多行匹配标题；`!\[...\](...)` 匹配图片引用
- stdlib `html.parser.HTMLParser` 子类 `_HtmlStatsParser`：`handle_starttag` + `handle_startendtag` 统计 h1..h6 / img
- format 优先级：`config['format']` > `config['path']` 后缀推断 > 默认 `"md"`
- 异步 `blob_store.get()` 用 `asyncio.run(_run())` 包装（与 PdfMineruLoader 同模式）
- 流式响应兜底：get() 非 bytes 时逐 chunk 拼接
- `images=[]` 占位，不抓图片 blob
- auto-register 在 `loaders/__init__.py` import 时触发；try/except ValueError 防重复注册

## 测试通过证据

```text
$ cd packages/core && uv run pytest tests/test_loader_html_md.py -x -q
....
4 passed in 0.10s

$ uv run pytest tests/ -x -q
78 passed in 0.29s
```

- AC-1 PASS（html-md in LoaderRegistry；get("html-md") is HtmlMdLoader）
- AC-2 PASS（md happy path：heading_count=2 / image_ref_count=1 / char_count / source_ref / images=[]）
- AC-3 PASS（html happy path：heading_count=2 / image_ref_count=1 / images=[]）
- AC-4 PASS（ctx.blob_store=None → ValueError match "ctx.blob_store"）
- 全套：74 旧 + 4 新 = 78/78 PASS

## 偏离 design.md

无。
