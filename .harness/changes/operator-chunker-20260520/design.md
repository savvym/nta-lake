---
change_id: operator-chunker-20260520
phase: design
status: approved
authored_at: 2026-05-20T22:05:00Z
author: application-owner-agent
model_used: opus
ac_kind_lint: enforce
---

# Design：ChunkerOperator 1→N 切分语义 (W2-2，v3 mini-design)

> v3 mini-design：application-owner 自写；不 spawn Phase 1 reviewer（D-13）。

## 一句话目标

落 `ChunkerOperator`，按 `max_chars` 把 1 个 SilverRow 切成 N 个新 row（演示 1→N 语义），与 W2-1 filter/dedup/score 一同构成 Operator suite 基础。

## 背景

W1-2 Operator Protocol 明确 `run() -> list[SilverRow]` 覆盖 1→0 / 1→1 / 1→N 三种语义。W2-1 已落 filter (1→0/1→1) + dedup (1→0/1→1) + score (1→1)，**1→N 切分**作为 silver 层另一核心模式（PDF→markdown 长文本拆 chunk 训 LLM 必备）单独落地。

切分策略 v1 采用最简的 **按字符数硬切**（不做句子边界 / token 边界 / overlap 重叠）；更精细策略（句末切 / token-aware / overlap window）留 follow-up change。每个切片继承原 row 的 `source_ref` / `stats` / `images`（共享，因切片仍指向同一 bronze blob），并各自追加 lineage_ops（含切片 index）。

## 范围

In scope：

- `packages/core/src/dataplat_core/operators/chunker.py`（新）：`ChunkerOperator`：
  - 属性：`name = "chunker"`、`version = "1.0"`、`spec.config_schema = {"type": "object", "properties": {"max_chars": {"type": "integer", "minimum": 1}}, "required": ["max_chars"], "additionalProperties": False}`
  - `run(row, config, ctx) -> list[SilverRow]`：
    - `max_chars = config["max_chars"]`（必填；缺失或 < 1 应被 jsonschema 兜底，但 v1 直接 KeyError；后续 W2-5 加 schema 校验层）
    - `text = row.text`
    - 若 `text == ""` → 返 `[]`（drop empty；空 text 无意义切片）
    - 否则按 `[text[i:i+max_chars] for i in range(0, len(text), max_chars)]` 切片
    - 对每个 chunk_i 生成 `new_row = row.model_copy(update={...})`：
      - `text = chunk_str`
      - `stats = {**row.stats, "chunk_index": i, "chunk_total": N, "text_chars": len(chunk_str)}`（覆盖 text_chars 若原有，加 chunk_index / chunk_total）
      - `lineage_ops = [*row.lineage_ops, {"op": "chunker", "version": "1.0", "max_chars": max_chars, "chunk_index": i, "chunk_total": N}]`
      - 其他字段（images / source_ref）保留（不 mutate 原 row）
    - 返 `[new_row_0, new_row_1, ..., new_row_{N-1}]`
- `packages/core/src/dataplat_core/operators/__init__.py`：加 `ChunkerOperator` import + export + auto-register（沿用 W2-1 try/except ValueError 容错模式）
- `packages/core/tests/test_chunker.py`（新）：3 个 behavioral 用例

Out of scope：

- **不**做句子边界切分（"。""!""?"）/ token 边界切分 / overlap window：留 follow-up `operator-chunker-smart-*`
- **不**支持 unicode grapheme-aware 计数（max_chars 是 Python str len，即 Unicode codepoint 计数；emoji 多 codepoint 算多 chars 是已知行为）
- **不**改 W2-1 三个 Operator
- **不**接 worker 调度（recipe v2 W2-5）
- **不**改 W1-* 任何东西

## 验收标准

| ID | kind | 描述 | 验证方式 | 期望 |
|---|---|---|---|---|
| AC-1 | behavioral | text 长度 25 + max_chars=10 → 切 3 个 (10/10/5)；每个 row.text 长度正确 + stats.chunk_index/chunk_total/text_chars 正确 + lineage_ops 追加正确 + 原 row 未 mutate | `cd packages/core && uv run pytest tests/test_chunker.py::test_chunker_basic_split -x -q` | 1 passed |
| AC-2 | behavioral | text="" → 返 `[]`（drop empty） | `cd packages/core && uv run pytest tests/test_chunker.py::test_chunker_empty_returns_empty -x -q` | 1 passed |
| AC-3 | behavioral | text 长度恰好 == max_chars → 返 1 row，chunk_index=0, chunk_total=1（边界情况） | `cd packages/core && uv run pytest tests/test_chunker.py::test_chunker_exact_boundary -x -q` | 1 passed |
| AC-4 | behavioral | OperatorRegistry.list_names() import 后含 "chunker" | `cd packages/core && uv run pytest tests/test_chunker.py::test_chunker_registered -x -q` | 1 passed |

## 决策

1. **v1 简单按 char 硬切，不做句子/token/overlap**：切分策略未来扩展 follow-up；本 change 是 1→N 标杆而非 production-grade chunker。
2. **空 text 返 []**（drop empty）：避免下游 row 为空噪音；与 filter (1→0) 模式呼应。
3. **chunk_total 全在 stats 里**：行级元信息进 stats；不引入新 SilverRow 字段（保 schema 稳定）。
4. **共享 source_ref / images**：每个切片仍指向同一 bronze blob；source_ref 不变；images 不切（多模态切片是 W2-3 image-to-text suite 的事）。
5. **stats.text_chars 覆盖**：原 row 可能有 text_chars (W1-4 PdfMineruLoader 写入)，切片后 text_chars 必须反映 chunk 长度；显式覆盖避免误用原 row 的总长。
6. **max_chars 必填**：jsonschema `required: ["max_chars"]`；v1 不给默认值，强制 caller 显式选择切片粒度。

## 风险

| 风险 | 缓解 |
|---|---|
| 切分 lineage_ops 元素新增字段 (chunk_index/chunk_total) 与 lineage 数据契约偏离 | W1-2 设计明确"`{"op": <name>, "version": <ver>, ...optional config keys}`"——切片 index 属合理 optional key 扩展；W2-5 lineage spec 才会强 typed |
| chunk_index 大且 ctx 是 SimpleNamespace 时 stats 共享 dict 误用 | sonnet 用 `{**row.stats, ...}` 显式新 dict（与 ScoreOperator 同模式）；测试 AC-1 校验原 row 未 mutate |
| max_chars 缺失行为不明 | jsonschema `required` 在本 change 不实际校验（W2-5 才有）；v1 直接 KeyError——这是 expected behavior，不写 unit test |

## 交叉引用清单（reviewer 必查）

- 引用但不修改：
  - `packages/core/src/dataplat_core/operators/identity.py`（模板）
  - `packages/core/src/dataplat_core/operators/score.py`（W2-1，stats 写入模板）
  - `packages/core/src/dataplat_core/protocols/operator.py`（W1-2）
  - `packages/core/src/dataplat_core/protocols/loader.py`（SilverRow）
- 应当不动：
  - W2-1 三个 Operator (filter/dedup/score)
  - `packages/core/src/dataplat_core/operators/__init__.py` 现有 4 个注册（只追加 chunker）
  - `apps/*` / loaders/* / schemas/*
- 引用的其他 change：W1-2（Operator Protocol）、W2-1（auto-register 模式 + try/except 容错）

## 关联 follow-up

- `operator-chunker-smart-*`：句子/token 边界切分 + overlap window
- W2-5 recipe v2 时把 chunker 接进 silver 算子链跑 PDF→chunks 端到端
