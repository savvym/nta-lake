---
change_id: operator-protocol-20260520
phase: implementation
status: done
authored_at: 2026-05-20T20:00:00Z
author: sonnet-phase2-implementer
model_used: claude-sonnet-4-6
branch: change/operator-protocol-20260520
base_commit: 53fbce2
head_commit: <push 后回填>
pr_url: n/a
---

# Implementation (W1-2)

## 做了什么（≤ 30 字）

新增 Loader / Operator 两个 Protocol、OperatorRegistry 单例、IdentityOperator 标杆实现。

## 改动文件清单

```
 packages/core/src/dataplat_core/protocols/__init__.py         |  7 ++++++
 packages/core/src/dataplat_core/protocols/loader.py           | 新建，56 行
 packages/core/src/dataplat_core/protocols/operator.py         | 新建，49 行
 packages/core/src/dataplat_core/operators/__init__.py         | 新建，15 行
 packages/core/src/dataplat_core/operators/registry.py         | 新建，47 行
 packages/core/src/dataplat_core/operators/identity.py         | 新建，44 行
 packages/core/tests/test_operator_protocol.py                 | 新建，60 行
 .harness/changes/operator-protocol-20260520/implementation.md | 本文件
 7 files changed
```

## 测试通过证据

### 单元测试（对应 AC-1/AC-2/AC-3）

```text
$ cd packages/core && uv run pytest tests/test_operator_protocol.py -x -q
...                                                                      [100%]
3 passed in 0.09s
```

### 全量回归

```text
$ cd packages/core && uv run pytest tests/ -q
....................................                                     [100%]
36 passed in 0.22s
```

### pyright 类型检查

```text
$ cd packages/core && uv run pyright src/ tests/test_operator_protocol.py 2>&1 | head -30
0 errors, 0 warnings, 0 informations
```

## 偏离 design.md

**1 处微小偏离（不影响行为）**：

设计文档测试模板中 `ctx = SimpleNamespace()  # type: ignore[assignment]`，但 pyright 在 `op.run(row, config={}, ctx=ctx)` 调用处额外报 `reportArgumentType`（SimpleNamespace 不满足 RunContext Protocol 的 5 个属性）。已在调用行追加 `# type: ignore[arg-type]` 使 pyright 0 errors。此偏离属于 type-checking suppress，不改变运行时行为，原测试意图完整保留。

除此之外实现与 design.md § 范围完全对应，无其他偏离。

## 下一步

进入 Phase 3：Application Owner spawn opus reviewer 对照 design.md 验 AC-1/AC-2/AC-3。
