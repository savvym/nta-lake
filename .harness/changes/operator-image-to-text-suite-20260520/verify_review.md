---
change_id: operator-image-to-text-suite-20260520
phase: verify
reviewer: claude-agent:opus-phase3-reviewer
model_used: opus
authored_at: 2026-05-20T23:58:00Z
verdict: APPROVED
---

# Verify Review

> Phase 3 reviewer 产物。对照 design.md（原始要求）+ implementation.md（声称的实现）+ `git diff main...change/<id>` 验 PR。

## 输入

- **Design**：`.harness/changes/operator-image-to-text-suite-20260520/design.md`（113 行，符合 D-13 mini-design ≤120 行约束）
- **Implementation**：`.harness/changes/operator-image-to-text-suite-20260520/implementation.md`（sonnet Phase 2 端到端产物，声明 0 偏离）
- **Git diff**：`git diff main...change/operator-image-to-text-suite-20260520`
- **Branch**：`change/operator-image-to-text-suite-20260520`
- **Commits**：
  - `d865090` docs(harness): operator-image-to-text-suite mini-design (W2-3, v3)
  - `3429f35` feat(core): ImageStrip + ImageCaptionStub Operators + auto-register (W2-3)
  - `2e59f3d` chore(harness): 回填 head_commit 到 implementation.md (W2-3)
- **PR**：n/a（branch-only，无 PR）

## AC 对照表

每条 AC 真去跑命令验证：

| AC | kind | reviewer 跑的命令 | 结果 | PASS/FAIL/NOT-VERIFIABLE |
|---|---|---|---|---|
| AC-1 | behavioral | `cd packages/core && uv run pytest tests/test_image_to_text_suite.py::test_image_strip_clears_images -x -q` | `1 passed in 0.10s` | PASS |
| AC-2 | behavioral | `cd packages/core && uv run pytest tests/test_image_to_text_suite.py::test_image_caption_stub_appends_markers -x -q` | `1 passed in 0.10s` | PASS |
| AC-3 | behavioral | `cd packages/core && uv run pytest tests/test_image_to_text_suite.py::test_image_caption_stub_no_images_noop -x -q` | `1 passed in 0.10s` | PASS |
| AC-4 | behavioral | `cd packages/core && uv run pytest tests/test_image_to_text_suite.py::test_image_operators_registered -x -q` | `1 passed in 0.10s` | PASS |

## 机械化检查日志

```text
$ cd packages/core && uv run pytest tests/test_image_to_text_suite.py::test_image_strip_clears_images -x -q
.                                                                        [100%]
1 passed in 0.10s

$ cd packages/core && uv run pytest tests/test_image_to_text_suite.py::test_image_caption_stub_appends_markers -x -q
.                                                                        [100%]
1 passed in 0.10s

$ cd packages/core && uv run pytest tests/test_image_to_text_suite.py::test_image_caption_stub_no_images_noop -x -q
.                                                                        [100%]
1 passed in 0.10s

$ cd packages/core && uv run pytest tests/test_image_to_text_suite.py::test_image_operators_registered -x -q
.                                                                        [100%]
1 passed in 0.10s

$ cd packages/core && uv run pytest tests/ -q
..................................................                       [100%]
50 passed in 0.24s

$ cd packages/core && uv run pyright src/dataplat_core/operators/image_strip.py src/dataplat_core/operators/image_caption_stub.py src/dataplat_core/operators/__init__.py tests/test_image_to_text_suite.py
0 errors, 0 warnings, 0 informations

$ git diff main...HEAD --stat
 .../design.md                                      | 113 ++++++++++++++
 .../design_review.md                               |  58 +++++++
 .../implementation.md                              | 127 ++++++++++++++++
 .../summary.md                                     |  52 +++++++
 .../verify_review.md                               |  81 ++++++++++
 .../core/src/dataplat_core/operators/__init__.py   |  22 ++-
 .../dataplat_core/operators/image_caption_stub.py  |  99 ++++++++++++
 .../src/dataplat_core/operators/image_strip.py     |  47 ++++++
 packages/core/tests/test_image_to_text_suite.py    | 168 +++++++++++++++++++++
 9 files changed, 760 insertions(+), 7 deletions(-)

$ git diff main...HEAD --name-only
.harness/changes/operator-image-to-text-suite-20260520/design.md
.harness/changes/operator-image-to-text-suite-20260520/design_review.md
.harness/changes/operator-image-to-text-suite-20260520/implementation.md
.harness/changes/operator-image-to-text-suite-20260520/summary.md
.harness/changes/operator-image-to-text-suite-20260520/verify_review.md
packages/core/src/dataplat_core/operators/__init__.py
packages/core/src/dataplat_core/operators/image_caption_stub.py
packages/core/src/dataplat_core/operators/image_strip.py
packages/core/tests/test_image_to_text_suite.py

# W2-1 三个 Operator (filter/dedup/score) 0 改动
$ git diff main...HEAD -- packages/core/src/dataplat_core/operators/filter.py \
      packages/core/src/dataplat_core/operators/dedup.py \
      packages/core/src/dataplat_core/operators/score.py
(empty)

# W2-2 chunker.py + identity.py 0 改动
$ git diff main...HEAD -- packages/core/src/dataplat_core/operators/chunker.py \
      packages/core/src/dataplat_core/operators/identity.py
(empty)

# SilverRow schema + Operator Protocol 0 改动
$ git diff main...HEAD -- packages/core/src/dataplat_core/protocols/loader.py \
      packages/core/src/dataplat_core/protocols/operator.py
(empty)

# apps/* / loaders/* / schemas/* 0 改动
$ git diff main...HEAD -- apps/ packages/core/src/dataplat_core/loaders/ \
      packages/core/src/dataplat_core/schemas/
(empty)
```

## 隐式偏离审计

> reviewer 对照 design.md vs implementation.md vs git diff，列出 implementation.md § 偏离 没声明但实际发生的偏离。**隐式偏离 = MUST FIX**。

逐项对照 design.md In scope 与 git diff --name-only：

| design.md In scope | git diff 实际 | 状态 |
|---|---|---|
| `packages/core/src/dataplat_core/operators/image_strip.py`（新） | new file 47 行 | OK |
| `packages/core/src/dataplat_core/operators/image_caption_stub.py`（新） | new file 99 行 | OK |
| `packages/core/src/dataplat_core/operators/__init__.py`（edit：加 2 import + register） | edit +15/-3 行 | OK |
| `packages/core/tests/test_image_to_text_suite.py`（新，4 个 AC 测试） | new file 168 行，4 测试函数 | OK |
| harness docs（design / design_review / implementation / summary / verify_review） | 5 个文档 | OK（流程产物，非代码变更） |

**0 隐式偏离**。implementation.md 声明的 4 个代码文件与 git diff 完全匹配；harness 文档变更属流程产物，不计入代码偏离范围。

## 关键 invariant 检查

| 检查项 | 期望 | 实际 | 状态 |
|---|---|---|---|
| W2-1 filter/dedup/score 0 改动 | empty diff | empty | OK |
| W2-2 chunker.py 0 改动 | empty diff | empty | OK |
| identity.py 0 改动 | empty diff | empty | OK |
| SilverRow schema 不变 (protocols/loader.py) | empty diff | empty | OK |
| Operator Protocol 不变 (protocols/operator.py) | empty diff | empty | OK |
| apps/* / loaders/* / schemas/* 不动 | empty diff | empty | OK |
| permanent-not-do list (data-not-code-pivot) 0 触碰 | 无 branch/merge/cherry-pick/rollback/row-diff/blob 图/Asset/manifest 强制/silver 文件树/bronze 强 schema | 全 0 | OK |
| auto-register try/except ValueError 容错 | 沿用 W2-1/W2-2 模式 | `__init__.py:44-47` 用 try/except ValueError | OK |
| lineage_ops 不 mutate（用 `[*row.lineage_ops, ...]`） | 不 mutate 原 list | image_strip.py:41-44 / image_caption_stub.py:64-67 + 88-95 均用 spread literal | OK |
| stats 不 mutate（用 `{**row.stats, ...}`） | 不 mutate 原 dict | image_strip.py:40 / image_caption_stub.py:87 均用 spread literal | OK |
| 新 row 用 model_copy(update=...) | 不直接 mutate row | image_strip.py:37 / image_caption_stub.py:62 + 84 均用 model_copy | OK |
| caption_stub no-op 仍追加 lineage_ops | image_count=0 | image_caption_stub.py:62-69 追加 `{"op": "image_caption_stub", "version": "1.0", "image_count": 0}` | OK |
| caption_stub 不改 images | 保留原列表 | image_caption_stub.py:96 注释明示，update dict 不含 images key | OK |
| template 默认值 | `"[image: {filename} ({blob_sha_short})]"` | image_caption_stub.py:18 一致 | OK |
| separator 默认值 | `"\n\n"` | image_caption_stub.py:19 一致 | OK |
| blob_sha_short = blob_sha[:8] | 前 8 位 | image_caption_stub.py:76 `img["blob_sha"][:8]` | OK |
| 注册总数 7 | identity + filter + dedup + score + chunker + image_strip + image_caption_stub | __init__.py:36-43 注册 7 个；AC-4 断言 `len(names) == 7` PASS | OK |
| 不新增 SilverRow 字段 | images dict schema 仍 W1-4 的 `{"filename": str, "blob_sha": str}` | 测试 fixture _IMAGES_2 用同 shape；protocols/loader.py 0 diff | OK |
| design.md ≤120 行（D-13） | ≤120 | 113 行 | OK |

## 问题列表

### MUST FIX

- 无

### SHOULD FIX

- 无

### NICE TO HAVE

- `image_caption_stub.py:82` `new_text = row.text + separator + captions_joined`：即使原 text 为空也会前置 separator（如 text="" + "\n\n" + "marker"）。design.md §决策 §3 + §In scope 第 47 行明示这是**有意设计**（保 deterministic 行为），不属于问题；若未来 caller 反馈空 text 前置分隔符不雅观，可在 follow-up change 加 `if row.text else ""` 条件，但本 change 内不需处理。
- 未来 follow-up 若加 `operator-image-caption-llm-*` / `operator-image-ocr-*`，建议复用 ImageCaptionStubOperator 的 template/separator config 形式，保持 image-to-text 算子族一致体验。

## Verdict

**APPROVED**

- PR 兑现 design.md 全部 In scope 条目
- 4/4 AC PASS（实际 reviewer 跑通）
- 全量回归 50/50 PASS（W1-* / W2-1 / W2-2 / W2-3 全绿，0 回归）
- pyright W2-3 文件 0/0/0
- 隐式偏离审计 0 项
- 关键 invariant 检查 全 OK（W2-1/W2-2 不改、protocols 不动、apps/loaders/schemas 不动、permanent-not-do list 0 触碰）
- 实现质量遵循 W2-1/W2-2 既有模式（model_copy + spread literal 不 mutate + try/except ValueError auto-register）
- design.md mini-design 113 行符合 D-13 ≤120 行约束

## 后续指引

1. **application-owner**：在 main 分支合入 `change/operator-image-to-text-suite-20260520`（fast-forward 或 squash merge 均可，参考 W2-2 历史风格）
2. 合入后 close W2-3 task #26（TaskUpdate status=completed）
3. 启动 W2-4：language-detection-or-pii Operator change（建议沿用 v3 mini-design 模式）
4. 不需要 follow-up change：image-to-text Operator 的真 LLM 升级路径已在 design.md §关联 follow-up 登记（operator-image-caption-llm-* / operator-image-ocr-* / operator-image-vqa-*）
