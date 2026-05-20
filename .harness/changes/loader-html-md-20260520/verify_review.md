---
change_id: loader-html-md-20260520
phase: verify
status: approved
reviewer: opus
reviewed_at: 2026-05-20T12:42:13Z
verdict: APPROVED
---

# Verify Review：html/md loader (W3-4)

## 验证结果

| AC | kind | 结果 | 证据 |
|---|---|---|---|
| AC-1 | behavioral | PASS | `pytest tests/test_loader_html_md.py::test_html_md_auto_registered` → 1 passed |
| AC-2 | behavioral | PASS | `pytest tests/test_loader_html_md.py::test_html_md_load_markdown_happy` → 1 passed |
| AC-3 | behavioral | PASS | `pytest tests/test_loader_html_md.py::test_html_md_load_html_happy` → 1 passed |
| AC-4 | behavioral | PASS | `pytest tests/test_loader_html_md.py::test_html_md_requires_blob_store` → 1 passed |

## 全套测试

`packages/core/tests` 78 passed in 0.29s（74 旧 + 4 新，预期吻合）

## Diff 扫描

- 修改文件：
  - `.harness/changes/loader-html-md-20260520/{design,design_review,implementation,summary,verify_review}.md`
  - `packages/core/src/dataplat_core/loaders/html_md.py` (新)
  - `packages/core/src/dataplat_core/loaders/__init__.py` (改)
  - `packages/core/tests/test_loader_html_md.py` (新)
- scope 内：YES（未触 apps/api/web、W1-* / W2-* / W3-1..3 产物、loaders/registry.py、protocols、adapters）
- 永不做清单 grep：clean（命中均为 design/summary 元文本"不做 manifest"声明，非真实产物）
- pyproject.toml 变化：none（决策 4：stdlib only，未引入 markdown-it-py / bs4）

## 不变量校验

- name="html-md" / version="0.1" / input_subtype="html-md" / output_schema_id="silver-text-v1"：OK
- ctx.blob_store 缺失早抛 ValueError，消息含 "ctx.blob_store"：OK
- format 选择顺序：config["format"] → path 后缀（.html/.htm/.md/.markdown）→ 默认 "md"：OK
- md 正则：`re.findall(r"^#{1,6}\s+.+$", re.MULTILINE)` + `r"!\[[^\]]*\]\([^)]+\)"`：OK
- html 解析：`html.parser.HTMLParser` 子类，handle_starttag + handle_startendtag 双覆盖 h1-h6 + img：OK
- decode utf-8 + errors="replace"：OK
- SilverRow stats 4 字段（format / heading_count / char_count / image_ref_count）：OK
- asyncio.run 包 async 内层（与 W1-4 PdfMineruLoader 同模式）：OK
- loaders/__init__.py：try/except ValueError + register + `__all__` 含 "HtmlMdLoader"：OK
- 测试用 `"html-md" in LoaderRegistry.list_names()`（W2-4 教训，未用 == N）：OK

## 既有产物回归

- W3-1 adapter-raw-upload + W3-2 adapter-folder-md-assets + W3-3 adapter-jsonl-import + LoaderRegistry 单测：13/13 PASS

## Verdict

APPROVED

design.md 4 个 behavioral AC 100% 兑现；实现严格落在 design.md 决策框内（stdlib only、单 row、stats 4 字段、asyncio.run 模板）；未引入依赖、未触 scope 外文件、未踩永不做清单；测试断言遵循 W2-4 反脆弱模式。可直接 merge to main + close change。连续 0-issue verdict 计数 +1（目标 11，本次达成）。

## NICE TO HAVE / Deferred

- 已在 design.md / summary.md Deferred 列出 5 个 follow-up（apps/api routes / XSS 净化 / frontmatter / async Protocol / 图片抓取），无需额外补登。
