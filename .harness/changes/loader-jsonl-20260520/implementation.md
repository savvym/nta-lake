---
change_id: loader-jsonl-20260520
phase: implementation
status: done
authored_at: 2026-05-21T07:00:00Z
author: implementer-agent
model_used: sonnet
branch: change/loader-jsonl-20260520
---

# Implementation：JSONL loader (W3-6)

## 实施摘要

按 design.md SoT 端到端实现 `JsonlLoader`。采用与 W3-4 (HtmlMdLoader) 完全一致的 `asyncio.run(_run())` + stub BlobStore 模式。每行 JSON object → 1 个 SilverRow；坏行（坏 json / 非 dict / 缺 text_field）跳过并计入 error_count；空行静默跳过。stdlib `json` + `gzip` 实现 gz 透明解压，未引入任何新依赖。

## 改动文件清单

| 路径 | 类型 | 一句话说明 |
|---|---|---|
| `packages/core/src/dataplat_core/loaders/jsonl.py` | new | JsonlLoader 主实现 |
| `packages/core/src/dataplat_core/loaders/__init__.py` | edit | 注册 JsonlLoader + 加入 __all__ |
| `packages/core/tests/test_loader_jsonl.py` | new | 4 个 behavioral AC 测试 |

## 测试通过证据

### 新增测试（4 PASS）

```text
$ cd packages/core && uv run pytest tests/test_loader_jsonl.py -v
tests/test_loader_jsonl.py::test_jsonl_auto_registered    PASSED
tests/test_loader_jsonl.py::test_jsonl_load_plain_happy   PASSED
tests/test_loader_jsonl.py::test_jsonl_load_gz_happy      PASSED
tests/test_loader_jsonl.py::test_jsonl_requires_blob_store PASSED
4 passed in 0.11s
```

### 全套回归

```text
$ cd packages/core && uv run pytest -q
88 passed in 0.47s
（84 → +4 = 88，无回归）
```

## DEVIATIONS

**D-1：line_count 语义澄清（design AC-2 隐含，实施时显式）**

design.md AC-2 期望 `notes` 含 `"line_count=3, error_count=2"`，输入为 3 行有效 + 1 空行 + 1 坏 json + 1 缺 text 字段。

design.md 决策 8 写"空行跳过不计 line_count / error_count"，但对 line_count 的精确语义未显式定义。若 line_count = 全部非空行数，则应为 5（3 有效 + 2 坏）；若 line_count = 有效行数，则为 3。

AC-2 期望值 3 与 `total_count=3` 一致，确认：**line_count = len(rows) = 有效行数**（= total_count）。

实施方案：`notes = f"line_count={len(rows)}, error_count={error_count}"`，不另设 line_count 变量，直接用 `len(rows)`，语义最清晰。

其他无偏离。

## 总结

W3-6 JsonlLoader 完整落地；4 AC 全部 PASS；全套 88 PASS；设计意图完整保留；line_count 语义在本文件 DEVIATIONS 段显式澄清。进入 Phase 3 等待 opus verify。
