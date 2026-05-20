---
change_id: adapter-jsonl-import-20260520
phase: verify
status: approved
reviewer: opus
reviewed_at: 2026-05-21T04:45:00Z
verdict: APPROVED
---

# Verify Review：jsonl import adapter (W3-3)

## 验证结果

| AC | kind | 结果 | 证据 |
|---|---|---|---|
| AC-1 | behavioral | PASS | `uv run pytest tests/test_adapter_jsonl_import.py::test_jsonl_import_auto_registered -x -q` → `1 passed in 0.10s` |
| AC-2 | behavioral | PASS | `uv run pytest tests/test_adapter_jsonl_import.py::test_jsonl_import_ingest_happy -x -q` → `1 passed in 0.10s` |
| AC-3 | behavioral | PASS | `uv run pytest tests/test_adapter_jsonl_import.py::test_jsonl_import_rejects_non_jsonl -x -q` → `1 passed in 0.10s` |
| AC-4 | behavioral | PASS | `uv run pytest tests/test_adapter_jsonl_import.py::test_jsonl_import_rejects_multi_files -x -q` → `1 passed in 0.10s` |

## 全套测试

`cd packages/core && uv run pytest tests/ -x -q` → `74 passed in 0.30s`（70 旧 + 4 新，符合预期）。

## Diff 扫描

修改文件（`git diff main..HEAD --name-only`）：

- `.harness/changes/adapter-jsonl-import-20260520/design.md`（新）
- `.harness/changes/adapter-jsonl-import-20260520/design_review.md`（模板占位，未生效；v3 无 Phase 1 reviewer）
- `.harness/changes/adapter-jsonl-import-20260520/implementation.md`（新）
- `.harness/changes/adapter-jsonl-import-20260520/summary.md`（新）
- `.harness/changes/adapter-jsonl-import-20260520/verify_review.md`（本文件）
- `packages/core/src/dataplat_core/adapters/__init__.py`（改：+import JsonlImportAdapter、+try/except register、+`__all__`）
- `packages/core/src/dataplat_core/adapters/jsonl_import.py`（新，109 行）
- `packages/core/tests/test_adapter_jsonl_import.py`（新，47 行 / 4 用例）

scope 内：YES（apps/api / apps/web / W1-* / W2-* / W3-1 raw_upload.py / W3-2 folder_md_assets.py / registry.py / protocols/ 全部未动）。

永不做清单 grep：clean（仅命中 design.md / summary.md 元文本声明"不做 manifest.yaml"，符合 D-1 期望）。

## 不变量校验

- **ingest 顺序**（pydantic → len assert → 后缀 → 返回）：OK — `jsonl_import.py` L80-L109 严格按序
- **path 后缀 case-insensitive**：OK — `path.lower().endswith((".jsonl", ".jsonl.gz"))`（L95）
- **pydantic schema minItems=1 + maxItems=1**：OK — `_INPUT_SCHEMA["properties"]["files"]` L40-L41
- **line_count None → notes None；非 None → notes "line_count=N"**：OK — L100-L102
- **测试用 `name in names`**：OK — `test_jsonl_import_auto_registered` L11 `assert "jsonl-import" in get_default().list_names()`
- **W3-1/W3-2 回归**：8/8 PASS（`uv run pytest tests/test_adapter_raw_upload.py tests/test_adapter_folder_md_assets.py -x -q` → `8 passed in 0.11s`）

## Verdict

APPROVED

- 4 个 behavioral AC 全 PASS
- 模板复用三连击成功（W3-1 / W3-2 / W3-3）
- 实现严格匹配 design § 决策 1-8（含 D-1 不做 manifest 声明、决策 5 line_count 透传到 notes）
- 无 scope creep / 无永不做清单 hit / 无不变量破裂

## NICE TO HAVE / Deferred

- design 已声明 3 个 follow-up：`adapter-jsonl-import-route-*` / `-ndjson-alias-*` / `-magic-byte-*`；按 design 节奏推
- 上游 W3-6 `loader-jsonl-20260520` 将消费本 adapter 的 `notes="line_count=N"`；loader 实现时建议 `parts = notes.split("=")` + `int(parts[1])`，与决策 5 字段约定保持一致
