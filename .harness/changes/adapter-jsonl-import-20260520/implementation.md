---
change_id: adapter-jsonl-import-20260520
phase: implementation
status: done
model_used: sonnet
implemented_at: 2026-05-21T04:30:00Z
---

# Implementation：jsonl import adapter (W3-3)

## 落地文件

- `packages/core/src/dataplat_core/adapters/jsonl_import.py`（新，~90 行）
- `packages/core/src/dataplat_core/adapters/__init__.py`（改，+8 行）
- `packages/core/tests/test_adapter_jsonl_import.py`（新，~48 行 / 4 用例）

## 实现要点

- 按 W3-1 / W3-2 refs-only adapter 模板：pydantic spec model + class + ingest 方法
- `_JsonlImportFile` / `_JsonlImportSpec`（extra="forbid"）校验 spec；try/except 包成 "JsonlImport spec 非法"
- 防御性 assert `len(files) == 1`（schema 已限 maxItems，代码再校验防 schema 漂移）
- path 后缀校验：`.lower().endswith((".jsonl", ".jsonl.gz"))`；违规抛含 ".jsonl 或 .jsonl.gz" 的 ValueError
- `line_count` 若非 None → notes=`"line_count={N}"`；否则 notes=None
- `__init__.py` 加 import + try/except register + `__all__` 更新

## 验证

- AC-1 PASS: "jsonl-import" in get_default().list_names() — auto-register 正常
- AC-2 PASS: happy path spec with line_count=1000 → file_count==1, asset_count==0, notes=="line_count=1000"
- AC-3 PASS: "data.csv" → ValueError 含 ".jsonl 或 .jsonl.gz"
- AC-4 PASS: files=[] → ValueError 含 "JsonlImport spec 非法"；files=[f1,f2] → 同
- 全套：`packages/core/tests` 74 passed（4 新 + 70 旧，W3-1/W3-2 不受影响）
