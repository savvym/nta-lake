---
change_id: operator-protocol-20260520
phase: verify
reviewer: claude-agent:opus-phase3-reviewer
model_used: opus
authored_at: 2026-05-20T21:00:00Z
verdict: APPROVED
---

# Verify Review

> Phase 3 reviewer 产物。对照 design.md（v3 mini-design）+ implementation.md（sonnet 报告）+ `git diff main...HEAD` 验 PR。
> 本 change 走 D-13 v3 mini-design 流程：无 Phase 1 reviewer；本 review 仅核对行为 AC + 范围 + 关键设计点。

## 输入

- **Design**：`.harness/changes/operator-protocol-20260520/design.md`（≤56 行 v3 mini-design）
- **Implementation**：`.harness/changes/operator-protocol-20260520/implementation.md`（sonnet 报告）
- **Git diff**：`git diff main...change/operator-protocol-20260520` (a51a126..e261b79)
- **Branch**：`change/operator-protocol-20260520`，2 commit 在 main 之上：
  - `607d03c` feat(core): Loader + Operator protocols + OperatorRegistry + IdentityOperator (W1-2)
  - `e261b79` chore(core): operator.py 删未用 TYPE_CHECKING import (W1-2)

## AC 对照表

reviewer 真去跑 3 条 behavioral AC：

| AC | kind | reviewer 跑的命令 | 结果 | PASS/FAIL/NOT-VERIFIABLE |
|---|---|---|---|---|
| AC-1 | behavioral | `cd packages/core && uv run pytest tests/test_operator_protocol.py::test_protocol_import_set -x -q` | `1 passed in 0.09s` | PASS |
| AC-2 | behavioral | `cd packages/core && uv run pytest tests/test_operator_protocol.py::test_registry_register_and_lookup -x -q` | `1 passed in 0.09s` | PASS |
| AC-3 | behavioral | `cd packages/core && uv run pytest tests/test_operator_protocol.py::test_identity_operator_passthrough -x -q` | `1 passed in 0.09s` | PASS |

## 机械化检查日志

### AC-1：Protocol import set 全套类型正确

```text
$ cd packages/core && uv run pytest tests/test_operator_protocol.py::test_protocol_import_set -x -q
.                                                                        [100%]
1 passed in 0.09s
```

`Loader / LoadResult / SilverRow / Operator / OperatorSpec` 从 `dataplat_core.protocols` 可 import；`IdentityOperator / OperatorRegistry` 从 `dataplat_core.operators` 可 import；7 个 symbol 全部非 None。

### AC-2：Registry 注册 + 查找 + 异常路径

```text
$ cd packages/core && uv run pytest tests/test_operator_protocol.py::test_registry_register_and_lookup -x -q
.                                                                        [100%]
1 passed in 0.09s
```

测试用 `identity_test_ac2` 唯一前缀避免模块单例污染；覆盖 4 条断言：
- `register("identity_test_ac2", IdentityOperator)` 成功
- `get(name) is IdentityOperator`
- `name in list_names()`
- 重复 `register` 抛 `ValueError`
- 缺失 `get("does-not-exist-x")` 抛 `KeyError`

设计点（registry.py L30-31 / L41-42）100% 兑现。

### AC-3：IdentityOperator 不 mutate 输入 + 追加 lineage_ops

```text
$ cd packages/core && uv run pytest tests/test_operator_protocol.py::test_identity_operator_passthrough -x -q
.                                                                        [100%]
1 passed in 0.09s
```

测试断言：
- `len(out) == 1`（1→1 语义）
- `out[0].text / source_ref / stats` 与输入一致
- `out[0].lineage_ops == [{"op": "identity", "version": "1.0"}]`
- `row.lineage_ops == []`（输入 row 未被 mutate）

`identity.py` 第 35-39 行用 `row.model_copy(update={"lineage_ops": [*row.lineage_ops, {...}]})`，list literal 解构保证不共享原引用，行为正确。

### 零回归证明

```text
$ cd packages/core && uv run pytest tests/ -q
....................................                                     [100%]
36 passed in 0.22s
```

主分支 main (a51a126) 上 `tests/test_operator_protocol.py` 不存在；预存 33 个测试 + 新增 3 个 = 36 个全 PASS。reviewer 验证：

```text
$ cd packages/core && uv run pytest tests/ --ignore=tests/test_operator_protocol.py -q
.................................                                        [100%]
33 passed in 0.23s
```

→ 老的 33 个测试零回归。

### 范围审计：git diff --stat

```text
$ git diff main...HEAD --stat
 .../changes/operator-protocol-20260520/design.md                |  56 +++++++
 .../changes/operator-protocol-20260520/implementation.md        |  69 ++++++++
 .../changes/operator-protocol-20260520/summary.md               |  49 ++++++
 .../changes/operator-protocol-20260520/verify_review.md         |  81 ++++++++
 packages/core/src/dataplat_core/operators/__init__.py           |  14 ++++
 packages/core/src/dataplat_core/operators/identity.py           |  40 ++++++
 packages/core/src/dataplat_core/operators/registry.py           |  48 ++++++
 packages/core/src/dataplat_core/protocols/__init__.py           |   7 ++
 packages/core/src/dataplat_core/protocols/loader.py             |  67 ++++++++
 packages/core/src/dataplat_core/protocols/operator.py           |  54 ++++++
 packages/core/tests/test_operator_protocol.py                   |  62 ++++++++
 11 files changed, 547 insertions(+)
```

逐条核对 design.md § 范围：
- ✅ `protocols/loader.py`（新，67 行）
- ✅ `protocols/operator.py`（新，54 行）
- ✅ `protocols/__init__.py`（+7 行，export 新 symbol）
- ✅ `operators/__init__.py` + `registry.py` + `identity.py`（新 3 文件）
- ✅ `tests/test_operator_protocol.py`（新，62 行 / 3 用例）
- ✅ `protocols/processor.py` / `protocols/adapter.py` / `protocols/runcontext.py` 0 改动
- ✅ `apps/` / `plugins/` / worker / recipe 0 改动

完全符合 In scope + Out of scope。

### 关键设计点核查

| 设计点 | 来源 | 实际实现 | 结论 |
|---|---|---|---|
| `SilverRow` 5 字段 `text / images / source_ref / stats / lineage_ops` | design § 范围 | `loader.py:32-36` 5 字段全在 | ✅ |
| `SilverRow` 用 `ConfigDict(extra="forbid")` | data-not-code-pivot 一致性 | `loader.py:30` `model_config = ConfigDict(frozen=False, extra="forbid")` | ✅ |
| `Operator.run` 返 `list[SilverRow]` | design § 决策 2 | `operator.py:49-54` 签名 `-> list[SilverRow]` | ✅ |
| `OperatorRegistry.register` 重复抛 `ValueError` | reviewer instructions | `registry.py:30-31` | ✅ |
| `OperatorRegistry.get` 缺失抛 `KeyError` | reviewer instructions | `registry.py:41-42` | ✅ |
| `IdentityOperator.run` 用 `model_copy(update=...)`，不 in-place mutate | design § 决策 4 | `identity.py:35-39` | ✅ |
| `Loader` + `Operator` Protocol 用 `@runtime_checkable` | reviewer instructions | `loader.py:49` / `operator.py:37` | ✅ |
| pyright `0 errors` | implementation.md 声称 | reviewer 复跑 `uv run pyright src/ tests/test_operator_protocol.py` → `0 errors, 0 warnings, 0 informations` | ✅ |

8/8 设计点全过。

## 隐式偏离审计

implementation.md § 偏离 声明 1 处微小偏离：测试调用 `op.run(row, config={}, ctx=ctx)` 行追加 `# type: ignore[arg-type]` 抑制 pyright `reportArgumentType`（`SimpleNamespace` 不满足 `RunContext` Protocol 五属性）。

reviewer 复核 `tests/test_operator_protocol.py:54`：

```python
out = op.run(row, config={}, ctx=ctx)  # type: ignore[arg-type]
```

属于 type-check 抑制，runtime 行为零变化，且已显式声明 → 非隐式偏离。

reviewer 通览 git diff 其余 10 个文件，未发现任何未声明偏离。

**结论**：无隐式偏离。

## 关于 IDE Pyright 噪音

会话期间 IDE Pyright 报了一批 `Import "dataplat_core.protocols.operator" could not be resolved` —— 这是 IDE 从 workspace root 跑、不识别 `packages/core` editable install 的已知配置问题（W1-1 同模式）。reviewer 在 `cd packages/core && uv run pyright src/ tests/test_operator_protocol.py` 跑出 `0 errors, 0 warnings, 0 informations`，runtime 由 pytest 36/36 PASS 证明。**不因 IDE 诊断 fail change**。

## 问题列表

### MUST FIX

- 无。

### SHOULD FIX

- 无。

### NICE TO HAVE

- `OperatorRegistry` 是模块级 dict 单例，跨测试存在污染风险（本次测试用唯一前缀绕开）。W2-1 `operator-suite-mvp` 落多 Operator 时可考虑加 fixture-scoped reset 或改 instance 接口。属架构演进点，本 change 无需修。
- `LoadResult.notes` 为 `str | None`，未来若要支持结构化警告列表（如 token-budget warning），可演进为 `list[dict]`。同样留待 W1-4 loader 落地时再议。

## Verdict

**APPROVED**

- 3 条 behavioral AC（AC-1/AC-2/AC-3）全 PASS。
- 全量回归 36/36 PASS（33 老 + 3 新），零回归。
- pyright `0 errors`。
- 范围审计：`git diff main...HEAD` 涉及 11 个文件，全部在 design.md § In scope 内，Out of scope 区域（processor.py / adapter.py / runcontext.py / apps/ / plugins/ / worker / recipe）0 改动。
- 8 个关键设计点（SilverRow 5 字段 / extra=forbid / `list[SilverRow]` / Registry ValueError + KeyError / model_copy 不 mutate / @runtime_checkable / pyright clean）全部兑现。
- 隐式偏离审计 = 0。implementation.md 声明的 1 处 `type: ignore[arg-type]` 偏离已记录、合理、不影响运行时。

## 后续指引

1. Application Owner 合并 `change/operator-protocol-20260520` 到 main（merge commit 或 squash）。
2. 在 `summary.md` 阶段进度表回填 Phase 3 verdict = APPROVED + verify commit。
3. 关闭 change：把 `summary.md` status 改为 `closed`，更新 last_updated，回填 merge_commit。
4. 启动下游 W1-3 `silver-schema-enforce-20260520`：依赖本 change 的 `SilverRow` Pydantic 定型；W1-4 `loader-refactor-pdf-mineru-20260520` 依赖本 change 的 `Loader` Protocol。
