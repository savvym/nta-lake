---
change_id: operator-snapshot-mixer-20260520
phase: design
status: approved
authored_at: 2026-05-21T00:05:00Z
author: application-owner-agent
model_used: opus
ac_kind_lint: enforce
---

# Design：snapshot-mixer Operator suite (W2-4，v3 mini-design)

> v3 mini-design：application-owner 自写；不 spawn Phase 1 reviewer（D-13）。

## 一句话目标

落 2 个 row 级 Operator（snapshot_tag / snapshot_sample），为 W2-5 recipe v2 的"跨 snapshot row 级 union / weighted-mix"提供基础原语。

## 背景

W1-2 Operator Protocol 是 row 级 (`run(row, config, ctx) -> list[SilverRow]`)，单流变换。北极星 W2-4 roadmap 要求"跨 snapshot 的 row 级 union / filter Operator，支持从 5 个 silver snapshot 各取符合条件的 row 拼成 gold snapshot"。

**多流 union 本身是 recipe v2 的编排职责**（W2-5 会让 recipe 串多个 `loader → operator_chain` 然后 concat 行流）；本 change 落两个**支持 recipe v2 mixing 的行级 Operator 原语**：

- `snapshot_tag`：给行打上 `source_snapshot` 标签（recipe v2 串接前后下游可识别来源）
- `snapshot_sample`：基于 row 内容确定性哈希做"按权重抽样"——典型用法：snapshot A 配 weight=0.7，snapshot B 配 weight=0.3，两者 union 后比例稳定（与 GPT-3/Gopher data-mixing 同模式）

这两个 Operator 都是 1→0/1→1，**完全契合现有 Operator Protocol**，**无需扩展协议**。真正的多流 union 由 recipe v2 在编排层串两个 loader-operator-chain 实现。

## 范围

In scope：

- `packages/core/src/dataplat_core/operators/snapshot_tag.py`（新）：`SnapshotTagOperator`
  - 属性：`name = "snapshot_tag"`、`version = "1.0"`、`spec.config_schema`：
    ```json
    {"type": "object", "properties": {"snapshot_name": {"type": "string"}, "snapshot_weight": {"type": "number", "minimum": 0, "maximum": 1}}, "required": ["snapshot_name"], "additionalProperties": False}
    ```
  - `run(row, config, ctx) -> list[SilverRow]`：1→1
    - `name = config["snapshot_name"]`（必填；缺失 → KeyError v1 expected）
    - `weight = config.get("snapshot_weight")`（可选）
    - 新 `stats = {**row.stats, "source_snapshot": name}`；若 weight 给了则加 `"source_snapshot_weight": weight`
    - `lineage_ops = [*row.lineage_ops, {"op": "snapshot_tag", "version": "1.0", "snapshot_name": name, **({"snapshot_weight": weight} if weight is not None else {})}]`
    - 返 `[new_row]`
- `packages/core/src/dataplat_core/operators/snapshot_sample.py`（新）：`SnapshotSampleOperator`
  - 属性：`name = "snapshot_sample"`、`version = "1.0"`、`spec.config_schema`：
    ```json
    {"type": "object", "properties": {"weight": {"type": "number", "minimum": 0.0, "maximum": 1.0}, "seed": {"type": "string"}}, "required": ["weight"], "additionalProperties": False}
    ```
  - `run(row, config, ctx) -> list[SilverRow]`：1→0/1→1，确定性
    - `weight = config["weight"]`（必填，0.0 ≤ w ≤ 1.0；v1 不做校验，期望 caller / jsonschema 保证）
    - `seed = config.get("seed", "")`
    - 计算 `u = int(sha256((seed + row.text).encode("utf-8")).hexdigest()[:16], 16) / (1 << 64)`（uniform [0, 1) 确定性）
    - 若 `u >= weight` → `return []`（drop）
    - 否则 lineage_ops 追加 `{"op": "snapshot_sample", "version": "1.0", "weight": weight, "seed": seed}` 后返 `[new_row]`
    - **确定性**：同一 (text, seed) 永远同 decision；测试可断言；recipe v2 跑两次结果一致
- `packages/core/src/dataplat_core/operators/__init__.py`：加 2 个新 import + export + auto-register（沿用 W2-1..W2-3 try/except ValueError 模式；注册总数 7 → 9）
- `packages/core/tests/test_snapshot_mixer.py`（新）：4 个 behavioral 用例

Out of scope：

- **不**实现跨 snapshot 多流 union：留 W2-5 recipe v2 在编排层做（不动 Operator Protocol）
- **不**实现 row-merge / row-dedup-across-snapshots：DedupOperator (W2-1) 已覆盖单流去重；跨流去重也是 recipe v2 编排职责
- **不**扩展 Operator Protocol 让 Operator 看到多个 row：违反 row-level Protocol；本 change 用 ctx 也不做 cross-row state
- **不**改 W1-* / W2-1 / W2-2 / W2-3 Operator
- **不**接 worker 调度（recipe v2 W2-5）
- **不**做随机数（W2-1 dedup 同模式，本 change 用 sha256 确定性哈希做"伪随机"）

## 验收标准

| ID | kind | 描述 | 验证方式 | 期望 |
|---|---|---|---|---|
| AC-1 | behavioral | SnapshotTagOperator：喂 row + config={"snapshot_name": "alpaca", "snapshot_weight": 0.7} → 返 1 row，stats.source_snapshot=="alpaca"，stats.source_snapshot_weight==0.7，lineage_ops 追加正确，原 row 未 mutate | `cd packages/core && uv run pytest tests/test_snapshot_mixer.py::test_snapshot_tag_basic -x -q` | 1 passed |
| AC-2 | behavioral | SnapshotSampleOperator weight=1.0：喂任意 row → 必返 [new_row]（永不 drop）；lineage_ops 追加 | `cd packages/core && uv run pytest tests/test_snapshot_mixer.py::test_snapshot_sample_weight_one_keeps_all -x -q` | 1 passed |
| AC-3 | behavioral | SnapshotSampleOperator weight=0.0：喂任意 row → 必返 [] (永远 drop)；同样 row 跑两次结果一致 (deterministic) | `cd packages/core && uv run pytest tests/test_snapshot_mixer.py::test_snapshot_sample_weight_zero_drops_all -x -q` | 1 passed |
| AC-4 | behavioral | OperatorRegistry import 后 list_names() 含 "snapshot_tag" 和 "snapshot_sample"；总数 == 9 | `cd packages/core && uv run pytest tests/test_snapshot_mixer.py::test_snapshot_operators_registered -x -q` | 1 passed |

## 决策

1. **2 个 Operator 一并落地，不拆 change**：与 W2-1 / W2-3 同模式；scope 与 cost 都小。
2. **多流 union 留 recipe v2**：不扩展 Operator Protocol；保持 row-level 单流抽象简单一致；recipe v2 在编排层串多个 loader-chain 然后 concat 行流。
3. **snapshot_sample 用 sha256 确定性哈希，不用 random**：训练数据 reproducibility 关键；同样 (text, seed) 永远同 decision；与 W2-1 DedupOperator 用 sha256 哈希 text key 同模式。
4. **snapshot_sample seed 默认 ""**：caller 可显式选；测试用空 seed 也可确定性断言。
5. **snapshot_tag 不强制 weight 必填**：weight 是 mixing 阶段才有用的元信息；可选；snapshot_tag 即使只打 name 也合法。
6. **uniform [0, 1) 取 sha256 前 16 hex (uint64 / 2^64)**：标准做法；偏差极小；够用。
7. **不在 v1 加 statistical AC (1000 rows ~50%)**：测试非确定性风险高；边界值 weight=0 / weight=1 已覆盖确定性 + 边界行为；mid-weight 行为靠下游 recipe v2 集成测验证。

## 风险

| 风险 | 缓解 |
|---|---|
| weight 越界 (< 0 或 > 1) 不被校验 → behavior 异常 | jsonschema minimum/maximum 在本 change 不实际校验（W2-5 才有 schema 校验层）；v1 期望 caller 守约；测试只跑合规范围 |
| sha256 hash 截位偏差导致 weight 不准确 | 取前 16 hex (uint64) / 2^64 偏差 < 2^-64，远小于训练数据 epsilon；够用 |
| snapshot_name 重复 / 冲突 | caller / recipe v2 责任；本 Operator 不维护全局 name 命名空间 |
| seed 空串导致跨 caller 抽样结果一致 | 这是 feature 不是 bug — caller 显式选 seed 才能解相关；与 dedup ctx._dedup_seen 用 caller 自行管理同模式 |
| snapshot_tag 与 snapshot_sample 顺序问题 | recipe v2 责任；典型顺序是 tag → sample；本 change 不限制 |

## 交叉引用清单（reviewer 必查）

- 引用但不修改：
  - `packages/core/src/dataplat_core/operators/identity.py`（模板）
  - `packages/core/src/dataplat_core/operators/dedup.py`（W2-1 sha256 哈希模式参考）
  - `packages/core/src/dataplat_core/operators/score.py`（W2-1 stats 写入模板）
  - `packages/core/src/dataplat_core/operators/filter.py`（W2-1 1→0/1→1 drop 模式参考）
  - `packages/core/src/dataplat_core/protocols/operator.py`（W1-2）
  - `packages/core/src/dataplat_core/protocols/loader.py`（SilverRow）
- 应当不动：
  - W2-1/W2-2/W2-3 所有 Operator (filter/dedup/score/chunker/image_strip/image_caption_stub/identity)
  - `packages/core/src/dataplat_core/protocols/*`
  - `apps/*` / loaders/* / schemas/*
- 引用的其他 change：W1-2（Protocol）、W2-1（sha256 哈希 + 1→0/1→1 drop + stats 写入模式）

## 关联 follow-up

- W2-5 recipe v2：编排多个 loader-chain 然后 concat 行流；snapshot_tag / snapshot_sample 是其前置原语
- `operator-snapshot-dedup-cross-stream-*`：跨流去重（W2-1 dedup 是单流；跨流需要 recipe v2 编排时持久 seen-set）
