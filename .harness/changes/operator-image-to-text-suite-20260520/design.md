---
change_id: operator-image-to-text-suite-20260520
phase: design
status: approved
authored_at: 2026-05-20T23:40:00Z
author: application-owner-agent
model_used: opus
ac_kind_lint: enforce
---

# Design：image-to-text Operator suite (W2-3，v3 mini-design)

> v3 mini-design：application-owner 自写；不 spawn Phase 1 reviewer（D-13）。

## 一句话目标

落 2 个多模态 Operator（image_strip / image_caption_stub），建立 `SilverRow.images` → 文本注入的算子模式（1→1），与 W2-1/W2-2 一同构成 silver 层完整算子套件。

## 背景

W1-2 Operator Protocol + W2-1 三个 Operator + W2-2 ChunkerOperator 覆盖了纯文本变换（filter/dedup/score/chunker）；`SilverRow.images` 自 W1-3/W1-4 起即承载附属图片（pdf-mineru 抽出的图片以 `{"filename": str, "blob_sha": str}` 入列）。北极星 §image-to-text 指明 OCR / caption / VQA 是 LLM 训练数据的核心多模态变换；W2-3 先把"images 字段消费 + 文本注入"的 Operator 模式标杆落地。

**LLM 调用刻意留作 follow-up**：本 change 仅落 2 个**确定性**算子（image_strip 清空 images；image_caption_stub 用 filename/blob_sha 拼占位符），与 W2-1 ScoreOperator 用 text_chars/alpha_ratio 不调 LLM 同模式。真正 LLM caption / OCR 留 `operator-image-caption-llm-*` / `operator-image-ocr-*`（依赖 LLM Gateway 形式化）。

## 范围

In scope：

- `packages/core/src/dataplat_core/operators/image_strip.py`（新）：`ImageStripOperator`
  - 属性：`name = "image_strip"`、`version = "1.0"`、`spec.config_schema = {"type": "object", "additionalProperties": False}`（无 config）
  - `run(row, config, ctx) -> list[SilverRow]`：
    - 用 `row.model_copy(update={...})` 产新 row：
      - `images = []`
      - `stats = {**row.stats, "image_count": 0}`（覆盖原 image_count；若原 row 无该 key 仍写入 0）
      - `lineage_ops = [*row.lineage_ops, {"op": "image_strip", "version": "1.0"}]`
    - 返 `[new_row]`（始终 1→1，即使原 images 已为空）
- `packages/core/src/dataplat_core/operators/image_caption_stub.py`（新）：`ImageCaptionStubOperator`
  - 属性：`name = "image_caption_stub"`、`version = "1.0"`、`spec.config_schema = {"type": "object", "properties": {"template": {"type": "string"}, "separator": {"type": "string"}}, "additionalProperties": False}`
  - `run(row, config, ctx) -> list[SilverRow]`：
    - `template = config.get("template", "[image: {filename} ({blob_sha_short})]")`
    - `separator = config.get("separator", "\n\n")`
    - 若 `row.images == []` → 仍返 `[new_row]`（1→1 no-op，仅追加 lineage_ops；不改 text）
    - 否则：
      - 对每个 image dict（断言含 `filename` + `blob_sha`，缺失 → KeyError 即可，v1 不兜底）：
        - 拼 `template.format(filename=img["filename"], blob_sha_short=img["blob_sha"][:8], blob_sha=img["blob_sha"])`
      - 用 separator 连接所有 caption marker
      - 新 `text = row.text + separator + captions_joined`（即使原 text 为空也加 separator；保 deterministic 行为）
      - `stats = {**row.stats, "image_captions_added": len(row.images)}`
      - `lineage_ops = [*row.lineage_ops, {"op": "image_caption_stub", "version": "1.0", "image_count": len(row.images)}]`
      - images **不动**（保留原列表；strip 是另一个 Operator 的事）
    - 返 `[new_row]`
- `packages/core/src/dataplat_core/operators/__init__.py`：加 `ImageStripOperator` + `ImageCaptionStubOperator` import + export + auto-register（沿用 W2-1/W2-2 try/except ValueError 模式，注册总数从 5 升到 6+1=7…实际是 5 + 2 = 7）
  - 等等：W2-2 后是 5 个 operator（identity + filter + dedup + score + chunker）。本 change 加 2 个 → 总 7 个。
- `packages/core/tests/test_image_to_text_suite.py`（新）：4 个 behavioral 用例

Out of scope：

- **不**做真 LLM caption / OCR / VQA：留 `operator-image-caption-llm-*` / `operator-image-ocr-*`（依赖 LLM Gateway 形式化）
- **不**实际读图片 blob 内容（caption_stub 只用 filename + blob_sha 元数据；blob 字节读出与解码留 LLM caption follow-up）
- **不**改 W2-1 / W2-2 Operator
- **不**新增 SilverRow 字段（images 字段 schema 仍是 W1-4 的 `{"filename": str, "blob_sha": str}`）
- **不**改 PdfMineruLoader / W1-* 任何东西
- **不**接 worker 调度（recipe v2 W2-5）

## 验收标准

| ID | kind | 描述 | 验证方式 | 期望 |
|---|---|---|---|---|
| AC-1 | behavioral | ImageStripOperator：喂 row 带 2 images → 返 1 row，images=[]，stats.image_count=0，lineage_ops 追加正确，原 row 未 mutate | `cd packages/core && uv run pytest tests/test_image_to_text_suite.py::test_image_strip_clears_images -x -q` | 1 passed |
| AC-2 | behavioral | ImageCaptionStubOperator：喂 row text="hello" + 2 images → 返 1 row，text 含原文本 + 2 个 caption marker，stats.image_captions_added=2，images 保留原值 | `cd packages/core && uv run pytest tests/test_image_to_text_suite.py::test_image_caption_stub_appends_markers -x -q` | 1 passed |
| AC-3 | behavioral | ImageCaptionStubOperator no-op：喂 row images=[] → 返 1 row，text 不变，lineage_ops 仍追加 | `cd packages/core && uv run pytest tests/test_image_to_text_suite.py::test_image_caption_stub_no_images_noop -x -q` | 1 passed |
| AC-4 | behavioral | OperatorRegistry import 后 list_names() 含 "image_strip" 和 "image_caption_stub"，且总数 == 7 | `cd packages/core && uv run pytest tests/test_image_to_text_suite.py::test_image_operators_registered -x -q` | 1 passed |

## 决策

1. **2 个 Operator 一并落地**（不拆 change）：与 W2-1 三合一同模式；scope 与 cost 都小。
2. **LLM 调用全留 follow-up**：与 W2-1 ScoreOperator（text_chars / alpha_ratio 不调 LLM）一致；LLM Gateway 形式化是更大范围工作。
3. **image_caption_stub 用 filename + blob_sha 占位符**：演示"image metadata → text"模式；real captioner 改 template + 真调 LLM 即可平滑升级。
4. **image_strip 与 image_caption_stub 解耦**：strip 清空 / caption 保留 — 两种正交意图；caller 可串 caption→strip 做"先抽 caption 再丢图"。
5. **caption_stub 在 images=[] 时仍追加 lineage_ops**：保 lineage 完整性（"我跑过你"），与 IdentityOperator 1→1 模式一致。
6. **不读图片字节**：blob_store IO 在 v1 stub 不必要；真 caption / OCR 才需要读图。

## 风险

| 风险 | 缓解 |
|---|---|
| image dict 缺 filename / blob_sha 字段时 KeyError | v1 不做兜底；W1-4 已定型 schema；caller 保证 invariant；测试 AC-2 喂合规 dict |
| 占位符 template 注入风险（用户传 `{filename}` 之外的 key 触发 KeyError） | template.format 用命名参数；用户传错 key Python 抛 KeyError 是 expected；不静默 |
| 总注册 operator 数 7 影响 W1-2 test_operator_protocol.py | W1-2 测试用唯一 key "identity_test_ac2" 与正式 "identity" 不冲突；list_names 测试只断言 contains，不断言总数（W2-1 测试同理） |
| caption_stub 改 text 后下游 chunker 拿到的 text 含 caption marker | 这是 expected behavior — caller 在 recipe 中决定算子顺序；不属于本 change 的契约问题 |

## 交叉引用清单（reviewer 必查）

- 引用但不修改：
  - `packages/core/src/dataplat_core/operators/identity.py`（模板）
  - `packages/core/src/dataplat_core/operators/score.py`（W2-1，stats 写入模板）
  - `packages/core/src/dataplat_core/operators/chunker.py`（W2-2，row.model_copy 模板）
  - `packages/core/src/dataplat_core/protocols/operator.py`（W1-2）
  - `packages/core/src/dataplat_core/protocols/loader.py`（SilverRow + images schema）
  - `apps/api/dataplat_api/loaders/pdf_mineru.py`（参考 images dict shape：`{"filename": ..., "blob_sha": ...}`）
- 应当不动：
  - W2-1 三个 Operator (filter/dedup/score)
  - W2-2 ChunkerOperator
  - `packages/core/src/dataplat_core/operators/identity.py`
  - `apps/*` / loaders/* / schemas/*
- 引用的其他 change：W1-2（Operator Protocol）、W1-4（images schema 来源）、W2-1 / W2-2（auto-register + lineage 模式）

## 关联 follow-up

- `operator-image-caption-llm-*`：用 ctx.llm 调真 captioner（依赖 LLM Gateway 形式化）
- `operator-image-ocr-*`：OCR Operator（可能集成 mineru / paddle-ocr）
- `operator-image-vqa-*`：VQA Operator（visual question answering）
- W2-5 recipe v2 把 image 算子接进 silver 链
