---
change_id: loader-refactor-pdf-mineru-20260520
phase: implementation
status: done
authored_at: 2026-05-20T22:00:00Z
author: sonnet-phase2-implementer
model_used: sonnet
branch: change/loader-refactor-pdf-mineru-20260520
base_commit: 0e4bf66
head_commit: daf820a
pr_url: n/a (gh PAT 缺 pr:write)
---

# Implementation

## 做了什么

按 design.md W1-4 落地 `LoaderRegistry`（packages/core）+ `PdfMineruLoader`（apps/api），严格复用 `_mineru_client.py` + `_wait_terminal` + `PdfMineruSpec`，不动老 `PdfMineruProcessor`。从 bronze blob sha 读 PDF bytes，调 MinerU submit→poll→fetch_full_result，图片 put 进 blob_store，产出单个 `SilverRow`（text/images/source_ref/stats/lineage_ops 字段齐全）。

## 改动文件清单

| 路径 | 类型 | 一句话说明 |
|---|---|---|
| `packages/core/src/dataplat_core/loaders/__init__.py` | new | export LoaderRegistry |
| `packages/core/src/dataplat_core/loaders/registry.py` | new | LoaderRegistry 模块单例，严格对齐 OperatorRegistry 结构 |
| `apps/api/dataplat_api/loaders/__init__.py` | new | import PdfMineruLoader + 自动注册到 LoaderRegistry |
| `apps/api/dataplat_api/loaders/pdf_mineru.py` | new | PdfMineruLoader 实现 Loader Protocol |
| `packages/core/tests/test_loader_registry.py` | new | AC-1：register/get/list_names/重复ValueError/缺失KeyError |
| `apps/api/tests/test_pdf_mineru_loader.py` | new | AC-2+AC-3：mock MinerUClient 全链路 + 缺 env raise |

## 测试通过证据

### AC-1（LoaderRegistry）

```
$ cd packages/core && uv run pytest tests/test_loader_registry.py -x -q
.                                                                        [100%]
1 passed in 0.01s
```

### AC-2 + AC-3（PdfMineruLoader）

```
$ cd apps/api && uv run pytest tests/test_pdf_mineru_loader.py -x -q
..                                                                       [100%]
2 passed in 0.64s
```

### 全套 packages/core（38 passed）

```
$ cd packages/core && uv run pytest -q
......................................                                   [100%]
38 passed in 0.24s
```

### pyright 0 errors

```
$ cd packages/core && uv run pyright src/ tests/test_loader_registry.py 2>&1 | tail -3
0 errors, 0 warnings, 0 informations

$ cd apps/api && uv run pyright dataplat_api/loaders/ tests/test_pdf_mineru_loader.py 2>&1 | tail -3
0 errors, 0 warnings, 0 informations
```

### 老测试回归

```
$ cd apps/api && uv run pytest tests/test_pdf_mineru.py -q
.........                                                                [100%]
9 passed in 0.65s

$ cd apps/api && uv run pytest tests/test_pipeline_e2e.py -q
1 skipped in 0.82s
```

老 `PdfMineruProcessor`（9 tests）全 pass，pipeline e2e 1 skipped（pre-existing，非本 change 引入）。

## 偏离 design.md

无偏离。

## 下一步

进入 Phase 3：Application Owner spawn opus reviewer 对照 design.md 验 AC。
