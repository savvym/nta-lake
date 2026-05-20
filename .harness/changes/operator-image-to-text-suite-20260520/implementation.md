---
change_id: operator-image-to-text-suite-20260520
phase: implementation
status: done
authored_at: 2026-05-20T23:55:00Z
author: sonnet-phase2-implementer
model_used: sonnet
branch: change/operator-image-to-text-suite-20260520
base_commit: 5041e7a
head_commit: 3429f35
pr_url: n/a (gh PAT 缺 pr:write)
---

# Implementation

> Phase 2 sonnet 端到端产物。一次 sonnet 调用内完成：编码 + 单元测试 + 端到端验证 + commit。

## 改动文件清单

执行 `git diff --name-only main...HEAD`：

| 路径 | 类型 | 一句话说明 | 关联 task |
|---|---|---|---|
| `packages/core/src/dataplat_core/operators/image_strip.py` | new | ImageStripOperator：清空 images + stats.image_count=0（1→1） | W2-3 |
| `packages/core/src/dataplat_core/operators/image_caption_stub.py` | new | ImageCaptionStubOperator：images 元数据占位符注入 text（1→1） | W2-3 |
| `packages/core/src/dataplat_core/operators/__init__.py` | edit | 加 2 个新 operator import + export + auto-register；注释更新总数 5→7 | W2-3 |
| `packages/core/tests/test_image_to_text_suite.py` | new | 4 个 behavioral 测试，覆盖 AC-1..AC-4 | W2-3 |

## 任务完成情况

| Task | 状态 | commit | 备注 |
|---|---|---|---|
| ImageStripOperator 新建 | done | 3429f35 | 严格按 design.md 规格 |
| ImageCaptionStubOperator 新建 | done | 3429f35 | 严格按 design.md 规格 |
| __init__.py 加 2 import + register | done | 3429f35 | try/except ValueError 容错，沿用 W2-1/W2-2 模式 |
| test_image_to_text_suite.py 4 个 AC 测试 | done | 3429f35 | 4/4 passed |

## 测试通过证据

### AC-1 单测

```text
$ cd packages/core && uv run pytest tests/test_image_to_text_suite.py::test_image_strip_clears_images -x -q
1 passed in 0.08s
```

### AC-2 单测

```text
$ cd packages/core && uv run pytest tests/test_image_to_text_suite.py::test_image_caption_stub_appends_markers -x -q
1 passed in 0.08s
```

### AC-3 单测

```text
$ cd packages/core && uv run pytest tests/test_image_to_text_suite.py::test_image_caption_stub_no_images_noop -x -q
1 passed in 0.08s
```

### AC-4 单测

```text
$ cd packages/core && uv run pytest tests/test_image_to_text_suite.py::test_image_operators_registered -x -q
1 passed in 0.08s
```

### W2-3 全量（4 tests）

```text
$ cd packages/core && uv run pytest tests/test_image_to_text_suite.py -x -v
============================= test session starts ==============================
tests/test_image_to_text_suite.py::test_image_strip_clears_images PASSED [ 25%]
tests/test_image_to_text_suite.py::test_image_caption_stub_appends_markers PASSED [ 50%]
tests/test_image_to_text_suite.py::test_image_caption_stub_no_images_noop PASSED [ 75%]
tests/test_image_to_text_suite.py::test_image_operators_registered PASSED [100%]
============================== 4 passed in 0.16s ==============================
```

### 全量回归（50 tests，含 W1-2/W1-3/W1-4/W2-1/W2-2）

```text
$ cd packages/core && uv run pytest tests/ -q
..................................................
50 passed in 0.25s
```

### pyright（W2-3 新建/修改文件）

```text
$ cd packages/core && uv run pyright src/dataplat_core/operators/image_strip.py src/dataplat_core/operators/image_caption_stub.py src/dataplat_core/operators/__init__.py tests/test_image_to_text_suite.py
0 errors, 0 warnings, 0 informations
```

> 注：全量 `uv run pyright` 报 5 errors，全部来自 W1-x 预存测试文件（test_auth_protocol.py / test_lineage.py / test_repository.py / test_tree.py），本 change 未引入。

## 偏离 design.md（如有）

无偏离。所有实现严格按 design.md In scope 规格。

## 跨 change / 上游回归

- 全 pytest packages/core：50/50 PASS（16 files）
- W1-2 / W1-3 / W1-4 / W2-1 / W2-2 相关测试全部 PASS（无回归）
- pyright W2-3 文件：0/0/0

## PR 描述

```markdown
## Summary
- 新增 ImageStripOperator（清空 SilverRow.images + stats.image_count=0，1→1）
- 新增 ImageCaptionStubOperator（images 元数据 filename/blob_sha 占位符注入 text，1→1）
- __init__.py 自动注册，内置算子总数 5→7；4 个 AC 测试 4/4 PASS

## Test plan
- [x] AC-1: ImageStripOperator 清空 images + stats 写 image_count=0 + lineage_ops 追加
- [x] AC-2: ImageCaptionStubOperator 有 2 images → text 含 2 个 caption marker
- [x] AC-3: ImageCaptionStubOperator images=[] → no-op，text 不变，lineage_ops 仍追加
- [x] AC-4: OperatorRegistry 含 "image_strip" 和 "image_caption_stub"，总数 == 7
- [x] 全量回归 50/50 PASS

🤖 Generated with [Claude Code](https://claude.com/claude-code)
```

## 下一步

进入 Phase 3：Application Owner spawn opus reviewer 对照 design.md 验 AC-1..AC-4。
