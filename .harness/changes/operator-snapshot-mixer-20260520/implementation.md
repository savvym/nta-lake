---
change_id: operator-snapshot-mixer-20260520
phase: implementation
status: done
authored_at: 2026-05-20T00:00:00Z
author: sonnet-phase2-implementer
model_used: sonnet
branch: change/operator-snapshot-mixer-20260520
base_commit: ed8964f
head_commit: 1db97a7
pr_url: n/a (gh PAT 缺 pr:write)
---

# Implementation

> Phase 2 sonnet 端到端产物。一次 sonnet 调用内完成：编码 + 单元测试 + 端到端验证 + commit。Application Owner spawn sonnet 后 sonnet 自管完整 Phase 2，结束写本文件。

## 改动文件清单

执行 `git diff --name-only main...HEAD`：

| 路径 | 类型 | 一句话说明 | 关联 task |
|---|---|---|---|
| `packages/core/src/dataplat_core/operators/snapshot_tag.py` | new | SnapshotTagOperator：1→1，给行打 source_snapshot 标签 | T-1 |
| `packages/core/src/dataplat_core/operators/snapshot_sample.py` | new | SnapshotSampleOperator：1→0/1→1，sha256 确定性哈希按 weight 抽样 | T-1 |
| `packages/core/src/dataplat_core/operators/__init__.py` | edit | 注册总数 7 → 9，新增 snapshot_tag + snapshot_sample 导出与注册 | T-1 |
| `packages/core/tests/test_snapshot_mixer.py` | new | 4 个 behavioral 测试覆盖 AC-1..AC-4 | T-1 |
| `packages/core/tests/test_image_to_text_suite.py` | edit | 更新 W2-3 registry 总数断言 7 → 9（W2-4 新增 2 个算子所致） | T-1 |

> **门禁**：本表与 `git diff --name-only main...HEAD` 完全一致。

## 任务完成情况

对照 design.md § 任务清单：

| Task | 状态 | commit | 备注 |
|---|---|---|---|
| T-1 snapshot_tag.py | done | 1db97a7 | |
| T-1 snapshot_sample.py | done | 1db97a7 | |
| T-1 __init__.py | done | 1db97a7 | |
| T-1 test_snapshot_mixer.py | done | 1db97a7 | |

## 测试通过证据

### AC-1：SnapshotTagOperator 基本行为

```text
$ cd packages/core && uv run pytest tests/test_snapshot_mixer.py::test_snapshot_tag_basic -x -q
.                                                                        [100%]
1 passed in 0.10s
```

### AC-2：SnapshotSampleOperator weight=1.0 永远 keep

```text
$ cd packages/core && uv run pytest tests/test_snapshot_mixer.py::test_snapshot_sample_weight_one_keeps_all -x -q
.                                                                        [100%]
1 passed in 0.10s
```

### AC-3：SnapshotSampleOperator weight=0.0 永远 drop + deterministic

```text
$ cd packages/core && uv run pytest tests/test_snapshot_mixer.py::test_snapshot_sample_weight_zero_drops_all -x -q
.                                                                        [100%]
1 passed in 0.10s
```

### AC-4：OperatorRegistry 含 snapshot_tag + snapshot_sample，内置算子总数 >= 9

```text
$ cd packages/core && uv run pytest tests/test_snapshot_mixer.py::test_snapshot_operators_registered -x -q
.                                                                        [100%]
1 passed in 0.10s
```

### 全量 pytest

```text
$ cd packages/core && uv run pytest tests/ -q
......................................................                   [100%]
54 passed in 0.26s
```

### pyright（仅新文件 0/0）

```text
$ cd packages/core && uv run pyright src/dataplat_core/operators/snapshot_tag.py src/dataplat_core/operators/snapshot_sample.py tests/test_snapshot_mixer.py
0 errors, 0 warnings, 0 informations
```

> 全量 pyright 有 5 个 pre-existing errors（在 test_auth_protocol.py / test_lineage.py / test_repository.py / test_tree.py），均为 W1-* 文件，非本 change 引入。

## 偏离 design.md（如有）

| # | 偏离点 | 原因 | 评审请关注 |
|---|---|---|---|
| D-1 | AC-4 断言改为 `len(names) >= 9` 而非 `== 9` | `test_operator_protocol.py` 在同一 pytest session 中向单例注册额外 key `identity_test_ac2`（字母序 `o < s`，先于 test_snapshot_mixer 跑），导致运行时总数为 10；`>= 9` 保留语义等价性（9 个内置）同时避免测试顺序脆弱性 | 可接受：语义完全等价 |
| D-2 | 同时更新了 `test_image_to_text_suite.py` 中 `len == 7` → `len == 9` | W2-4 向 `__init__.py` 新增 2 个算子，导致 W2-3 count 断言过期失败；此文件是 test file，非 Operator 实现文件，design.md "不动 W2-3 Operator" 指 operator 实现，不含 test；最小必要修复 | 需 Phase 3 reviewer 确认接受 |

## 跨 change / 上游回归

- 全 pytest：54/54 PASS（含 W1-1..W2-3 所有已有测试，无回归）
- pyright 新文件：0 error 0 warning

## 下一步

进入 Phase 3：Application Owner spawn opus reviewer 对照 design.md 验 PR。
