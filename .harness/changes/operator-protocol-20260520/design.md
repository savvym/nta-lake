---
change_id: operator-protocol-20260520
phase: design
status: approved
authored_at: 2026-05-20T19:00:00Z
author: application-owner-agent
model_used: opus
ac_kind_lint: enforce
---

# Design：Operator Protocol + Registry + identity Operator (W1-2，v3 mini-design)

> v3 mini-design：application-owner 自写；不 spawn Phase 1 reviewer（D-13）。Phase 2 sonnet 按本文件落地，Phase 3 opus 跑 pytest 验收。

## 一句话目标

落 Operator Protocol（row→row）+ OperatorRegistry + identity 标杆 Operator；Loader Protocol（bronze→silver row）一并落地占位。

## 背景

`.harness/design.md` § 北极星 + `data-not-code-pivot.md` 把"Processor (repo→repo)" 拆为"Loader (bronze→silver row) + Operator (row→row)" 两层。当前 `packages/core/src/dataplat_core/protocols/` 只有 adapter / processor 两个老抽象（first-gen Processor 过渡保留），新模型缺三件套：(1) Loader Protocol，(2) Operator Protocol + Registry，(3) 至少 1 个 identity Operator 作为基准。本 change 只落 Protocol + Registry 骨架，**不**写真正过滤/去重/评分（留给 W2-1 `operator-suite-mvp`）。Processor 老类保留不撤。

## 范围

In scope：

- `packages/core/src/dataplat_core/protocols/loader.py`（新）：`Loader` Protocol + `LoadResult` Pydantic + `SilverRow` Pydantic（必含 `source_ref: dict` + `stats: dict` + `lineage_ops: list` + `text: str` + `images: list[dict]`）
- `packages/core/src/dataplat_core/protocols/operator.py`（新）：`Operator` Protocol（`run(row: SilverRow, config: dict, ctx: RunContext) -> list[SilverRow]`，返 list 支持 1→0/1→1/1→N 三种语义）+ `OperatorSpec` 元数据
- `packages/core/src/dataplat_core/operators/__init__.py` + `registry.py`（新）：`OperatorRegistry` 单例（`register(name, cls)` / `get(name)` / `list_names()`），dict 即可
- `packages/core/src/dataplat_core/operators/identity.py`（新）：`IdentityOperator` 实现 Operator Protocol；`run()` 把 `lineage_ops` 追加一条 `{"op": "identity", "version": "1.0"}` 后返 `[row]`（必须返新 row，不能 in-place mutate 输入）
- `packages/core/src/dataplat_core/protocols/__init__.py`：export Loader / Operator / SilverRow / LoadResult / OperatorSpec
- `packages/core/tests/test_operator_protocol.py`（新）：3 个 behavioral 用例，跑通即满足 AC

Out of scope：

- **不**改 `protocols/processor.py` / `protocols/adapter.py`（first-gen 保留）
- **不**实现真正 Loader（pdf-mineru loader 是 W1-4）
- **不**实现其他 Operator（filter/dedup/score 是 W2-1，chunker 是 W2-2）
- **不**改 worker runner / API recipe 调度（recipe v2 是 W2-5）
- **不**动 plugins/ 目录（当前为空）
- **不**改 silver_row schema 强校验（是 W1-3 的事；本 change 仅定 Pydantic）

## 验收标准

| ID | kind | 描述 | 验证方式 | 期望 |
|---|---|---|---|---|
| AC-1 | behavioral | 三 Protocol + Registry + identity 全套 import + 类型正确 | `cd packages/core && uv run pytest tests/test_operator_protocol.py::test_protocol_import_set -x -q` | 1 passed |
| AC-2 | behavioral | Registry 注册 + 查找：`register("identity", IdentityOperator); assert get("identity") is IdentityOperator; assert "identity" in list_names()` | `cd packages/core && uv run pytest tests/test_operator_protocol.py::test_registry_register_and_lookup -x -q` | 1 passed |
| AC-3 | behavioral | identity Operator 跑一次 row→[row]：输入含 `lineage_ops: []` 的 SilverRow，输出 `len(result) == 1` 且 `result[0].lineage_ops == [{"op": "identity", "version": "1.0"}]`，输入 row 不被 mutate | `cd packages/core && uv run pytest tests/test_operator_protocol.py::test_identity_operator_passthrough -x -q` | 1 passed |

## 决策

1. **Loader 一起落地**：roadmap W1-2 目标本来只提 Operator，但 SilverRow schema 是 Loader / Operator 共用前置；先在本 change 把 `SilverRow` 定型，W1-3 silver-schema-enforce 直接复用；W1-4 loader-refactor-pdf-mineru 实现首个 Loader。本 change 仅落 Protocol，不写真正 Loader 实现。
2. **Operator.run 返 `list[SilverRow]`**：覆盖 1→0（过滤）/ 1→1（变换）/ 1→N（切分）；返空 list 等同 drop。比"返 row | None"更通用。
3. **不引入 OperatorContext / Pipeline 抽象**：单 Operator + RunContext 已够 W1-2；recipe / chain 留给 W2-5。
4. **identity Operator 必须返新 row**（不 in-place mutate）：AC-3 强制；后续 Operator 跟随这个模式，避免行级 lineage_ops 在并发场景被覆盖。
