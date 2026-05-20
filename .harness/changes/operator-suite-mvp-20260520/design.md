---
change_id: operator-suite-mvp-20260520
phase: design
status: approved
authored_at: 2026-05-20T21:30:00Z
author: application-owner-agent
model_used: opus
ac_kind_lint: enforce
---

# Design：filter / dedup / score 三个 MVP Operator (W2-1，v3 mini-design)

> v3 mini-design：application-owner 自写；不 spawn Phase 1 reviewer（D-13）。Phase 2 sonnet 端到端；Phase 3 opus 跑 pytest 验收。

## 一句话目标

落 3 个 MVP Operator（filter / dedup / score），实现 Operator Protocol，注册进 OperatorRegistry，作为 Operator 层第一批实用算子。

## 背景

W1-2 落定了 Operator Protocol + Registry + IdentityOperator 标杆（`packages/core/src/dataplat_core/operators/identity.py`）。`data-not-code-pivot.md` § 北极星明确 Operator 是 silver 行级变换的核心抽象（1→0/1→1/1→N）。Wave 2 第一步是把 filter / dedup / score 三类最常见的过滤/去重/打分能力先落地，作为 W2-2（chunker）/ W2-3（image-to-text）/ W2-5（recipe v2）的依赖前置。

设计原则：
- **3 个 Operator 类，互相独立**，复用 IdentityOperator 同款属性 + run() 形态
- **每个 Operator 都演示 list[SilverRow] 返回的不同语义**：filter 演示 1→0/1→1；dedup 演示 1→0/1→1（基于 ctx state）；score 演示 1→1（变换）
- **dedup 的去重 state 暂用 ctx 上挂 attribute**（与 W1-4 ctx.blob_store 同模式）；正式 RunContext 扩展是 W2-5 的事

## 范围

In scope：

- `packages/core/src/dataplat_core/operators/filter.py`（新）：`FilterOperator`：
  - 属性：`name = "filter"`、`version = "1.0"`、`spec.config_schema = {"type": "object", "properties": {"min_chars": {"type": "integer", "minimum": 0}}, "additionalProperties": False}`
  - `run(row, config, ctx) -> list[SilverRow]`：若 `len(row.text) < config.get("min_chars", 0)` → `return []`（drop）；否则追加 lineage_ops `{"op": "filter", "version": "1.0", "min_chars": <n>}` 后返 `[new_row]`
- `packages/core/src/dataplat_core/operators/dedup.py`（新）：`DedupOperator`：
  - 属性：`name = "dedup"`、`version = "1.0"`、`spec.config_schema = {"type": "object", "properties": {"key": {"type": "string", "enum": ["text", "source_blob"]}}, "additionalProperties": False}`
  - `run(row, config, ctx) -> list[SilverRow]`：从 `ctx._dedup_seen` (set) 读已见 key；按 config.key (默认 "text") 取 row 的 hash key（"text" → sha256(text) 16 进制；"source_blob" → row.source_ref["blob_sha"]）；命中 → `return []`；否则加入 seen + 追加 lineage_ops 后返 `[new_row]`
  - `ctx._dedup_seen` 不存在 → `setattr(ctx, "_dedup_seen", set())` 自动初始化（不抛错；caller 一次调用链共享同一 ctx 即可去重）
- `packages/core/src/dataplat_core/operators/score.py`（新）：`ScoreOperator`：
  - 属性：`name = "score"`、`version = "1.0"`、`spec.config_schema = {"type": "object", "properties": {"metric": {"type": "string", "enum": ["text_chars", "alpha_ratio"]}}, "additionalProperties": False}`
  - `run(row, config, ctx) -> list[SilverRow]`：按 config.metric (默认 "text_chars") 算分：
    - `text_chars` → `score = len(row.text)`
    - `alpha_ratio` → `score = round((sum(1 for c in row.text if c.isalpha()) / max(len(row.text), 1)), 4)`
  - 写入新 stats dict `{**row.stats, f"score_{metric}": score}`（不 mutate 原 dict），追加 lineage_ops 后返 `[new_row]`
- `packages/core/src/dataplat_core/operators/__init__.py`：
  - export 三个新类 + 保留现有 IdentityOperator/OperatorRegistry export
  - 模块 import 时自动调 `OperatorRegistry.register("identity", IdentityOperator)` + `"filter"` + `"dedup"` + `"score"` 四次注册（identity 现在未自动注册，本 change 一并加上；W1-2 测试用唯一 key "identity_test_ac2" 不冲突，参考 `test_operator_protocol.py:test_registry_register_and_lookup`）
  - 与 loaders/__init__.py 自动注册模式对齐
- `packages/core/tests/test_operator_suite_mvp.py`（新）：4 个 behavioral 用例
  - `test_filter_operator_drop_and_keep`：min_chars=10，喂两个 row（text 长度 5 / 20），前者返 []，后者返 [new_row] + lineage_ops 追加正确
  - `test_dedup_operator_text_key`：连喂两个 text 相同的 row（共享 ctx），第一个返 [new_row]，第二个返 []；ctx._dedup_seen 长度 == 1
  - `test_score_operator_text_chars`：喂 text="hello world" (11 chars) → 返 1 row + row.stats["score_text_chars"] == 11 + lineage_ops 追加正确
  - `test_all_four_operators_registered`：`import dataplat_core.operators` 后 `OperatorRegistry.list_names()` 含 4 个 {"identity", "filter", "dedup", "score"}

Out of scope：

- **不**改 IdentityOperator（W1-2 落定）
- **不**实现 chunker（W2-2）/ image-to-text suite（W2-3）/ snapshot-mixer（W2-4）/ recipe v2（W2-5）
- **不**接入 worker 调度（recipe v2 才接 Operator）
- **不**正式扩 RunContext Protocol（dedup 的 ctx._dedup_seen 暂用 attribute hack；W2-5 形式化）
- **不**做 LLM 评分（score 仅本地确定性算法；LLM 评分是 W4-8 operator-eval-gen）
- **不**新增 packages/core 之外的文件（api/web/sdk 都不动）

## 验收标准

| ID | kind | 描述 | 验证方式 | 期望 |
|---|---|---|---|---|
| AC-1 | behavioral | FilterOperator drop + keep + lineage_ops 追加 | `cd packages/core && uv run pytest tests/test_operator_suite_mvp.py::test_filter_operator_drop_and_keep -x -q` | 1 passed |
| AC-2 | behavioral | DedupOperator 基于 ctx._dedup_seen 跨调用去重；text-key 模式正确 | `cd packages/core && uv run pytest tests/test_operator_suite_mvp.py::test_dedup_operator_text_key -x -q` | 1 passed |
| AC-3 | behavioral | ScoreOperator text_chars metric 算分 + 写 row.stats + lineage_ops 追加 | `cd packages/core && uv run pytest tests/test_operator_suite_mvp.py::test_score_operator_text_chars -x -q` | 1 passed |
| AC-4 | behavioral | OperatorRegistry import packages.core 后 `list_names()` 含 "identity", "filter", "dedup", "score" | `cd packages/core && uv run pytest tests/test_operator_suite_mvp.py::test_all_four_operators_registered -x -q` | 1 passed |

## 决策

1. **3 个 Operator 一并落地**（不拆 3 个 change）：粒度等同 W1-3 一次落 SchemaRegistry + 2 builtin schema；都是同款属性 + run() 模板，scope 与 cost 都小。
2. **dedup state 暂用 ctx attribute hack**：RunContext Protocol 形式化扩展（如加 state dict）属 W2-5 范围；本 change 用 `getattr/setattr(ctx, "_dedup_seen", set())` 兜底，与 W1-4 ctx.blob_store 同模式。
3. **score 仅本地确定性算法**：LLM 打分（perplexity / classification）是 W4-8；本 change 用 text_chars / alpha_ratio 演示 stats 写入 + 行级血缘。
4. **automatic 注册到 Registry**：在 `operators/__init__.py` import 时 register；与 W1-4 loaders/__init__.py 自动注册模式对齐。
5. **不引入 BaseOperator 抽象基类**：复制属性模板比抽象 5 行 mixin 更明白；W2-* 加更多 Operator 后再考虑提炼。
6. **stats 写入用 `{**row.stats, ...}` 不 mutate 原 dict**：避免 Pydantic frozen=False 下的隐式 mutation；与 lineage_ops 追加同模式。

## 风险

| 风险 | 缓解 |
|---|---|
| operators/__init__.py 现有 identity 注册再加 3 个，注意不要重复 register（重复 ValueError） | sonnet 检查当前 __init__.py 状态；如 identity 已注册则在同一 import 路径加 3 个；如 identity 是惰性注册则保持 |
| dedup ctx 属性 hack 被 reviewer 当成偏离 | Decision 2 已显式声明；reviewer 比对 design.md 即可 |
| 隐式数据契约：lineage_ops 元素 schema | 沿用 W1-2 模式 `{"op": <name>, "version": <ver>, ...optional config keys}`；不强 typed schema（留给 W2-5 lineage spec） |
| 测试隔离：4 个 Operator 全局注册可能污染其他测试 | OperatorRegistry 是模块单例；W1-2 test_operator_protocol.py 已经在 identity 注册场景下跑过；新增 3 个不影响 identity 用例 |

## 交叉引用清单（reviewer 必查）

- 引用但不修改：
  - `packages/core/src/dataplat_core/protocols/operator.py`（W1-2 落定）
  - `packages/core/src/dataplat_core/protocols/loader.py`（SilverRow）
  - `packages/core/src/dataplat_core/operators/identity.py`（标杆模板）
  - `packages/core/src/dataplat_core/operators/registry.py`（W1-2）
- 应当不动：
  - `apps/api/*`（Operator suite 是 core 内部能力）
  - `packages/core/src/dataplat_core/loaders/*`（W1-4 落定）
  - `packages/core/src/dataplat_core/schemas/*`（W1-3 落定）
- 引用的其他 change：W1-2（Operator Protocol）、W1-4（auto-register 模式参考）

## 关联 follow-up（如有）

- W2-5 recipe v2 时把 dedup 的 ctx._dedup_seen 形式化进 RunContext Protocol（替换 attribute hack）
- W4-8 operator-eval-gen 时基于 ScoreOperator 模板加 LLM 打分变体
