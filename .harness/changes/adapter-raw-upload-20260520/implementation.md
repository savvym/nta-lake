---
change_id: adapter-raw-upload-20260520
phase: implementation
status: done
authored_at: 2026-05-20T04:00:00Z
author: sonnet-phase2-implementer
model_used: sonnet
branch: change/adapter-raw-upload-20260520
base_commit: e57f1e0
head_commit: 1332034
pr_url: n/a (gh PAT 缺 pr:write)
---

# Implementation

> Phase 2 sonnet 端到端产物。一次 sonnet 调用内完成：编码 + 单元测试 + 端到端验证 + commit。

## 改动文件清单

| 路径 | 类型 | 一句话说明 | 关联 task |
|---|---|---|---|
| `packages/core/src/dataplat_core/adapters/registry.py` | new | AdapterRegistry 实例存储 + module-level singleton + get_default() | W3-1 |
| `packages/core/src/dataplat_core/adapters/raw_upload.py` | new | RawFileUploadAdapter port（从 apps/api 副本，import 路径不变均已是 dataplat_core） | W3-1 |
| `packages/core/src/dataplat_core/adapters/__init__.py` | new | 自动注册 raw-file-upload，idempotent try/except ValueError | W3-1 |
| `packages/core/tests/test_adapter_raw_upload.py` | new | AC-1..AC-4 行为测试 | W3-1 |
| `.harness/changes/adapter-raw-upload-20260520/implementation.md` | edit | 本文件（Phase 2 产物） | W3-1 |

## 任务完成情况

| Task | 状态 | 备注 |
|---|---|---|
| AdapterRegistry（register/get/list_names/duplicate ValueError/singleton） | done | 严格按 design.md 范围落地 |
| RawFileUploadAdapter port to packages/core | done | 与 apps/api 副本完全一致；import 路径不变（已是 dataplat_core） |
| adapters/__init__.py 自动注册 | done | idempotent try/except ValueError；与 operators/__init__.py 同模式 |
| test_adapter_raw_upload.py（AC-1..AC-4） | done | 4/4 PASS |

## 测试通过证据

### AC 单测（4 个，全部独立跑）

```text
$ cd packages/core && uv run pytest tests/test_adapter_raw_upload.py -x -q
....
4 passed in 0.10s
```

### 全量 pytest

```text
$ cd packages/core && uv run pytest -x -q
66 passed in 0.29s
```

（基线 62 + 本 change 新增 4 = 66；无回归）

### Pyright

```text
$ cd packages/core && uv run pyright src/dataplat_core/adapters/ tests/test_adapter_raw_upload.py 2>&1 | tail -10
0 errors, 0 warnings, 0 informations
```

## 偏离 design.md（如有）

无偏离。严格按 design.md In scope 落地。

apps/api 副本 import 路径本已是 dataplat_core（非 dataplat_api），所以 raw_upload.py port 几乎无需改动——与 design.md 决策 1 描述一致。

## 跨 change / 上游回归

- 全量 pytest packages/core：66/66 PASS（W1-2..W2-6 + 本 change 4 全部无回归）
- pyright adapters/ + test_adapter_raw_upload.py：0/0/0
- apps/api 0 改动（design.md Out of scope 明确）

## 风险确认

| 风险 | 确认 |
|---|---|
| apps/api 私有 RawFileUploadAdapter 与 packages/core 副本漂移 | 显式接受；follow-up adapter-raw-upload-api-bridge-* 桥接 |
| AdapterRegistry 与 apps/api/runner/registry.py 命名冲突 | 模块路径不同，import 不冲突，PASS |
| pytest 全套回归 | 66/66 PASS，无 regression |
| stub adapter AC-1 命名碰撞 production | stub name "test-adapter-w3-1" 唯一，与 raw-file-upload 不冲突，PASS |

## 下一步

进入 Phase 3：Application Owner spawn opus reviewer 对照 design.md 验 AC-1..AC-4。
