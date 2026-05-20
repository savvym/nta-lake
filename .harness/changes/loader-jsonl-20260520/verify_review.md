---
change_id: loader-jsonl-20260520
phase: verify
status: approved
verdict: APPROVED
reviewed_at: 2026-05-20T13:11:18Z
reviewer: verify-reviewer-agent
model_used: opus
ac_kind_lint: enforce
---

# Verify Review：JSONL loader (W3-6)

## Verdict

**APPROVED — 0 issues**。设计意图完整落地；4 个 behavioral AC 全 PASS；88 全量回归 PASS；diff scope 严格匹配设计；永不做清单 clean；跨 change 回归 30 PASS；不变量逐项符合 design SoT。

## 1. 4 个 behavioral AC 执行

```text
$ cd packages/core && uv run pytest tests/test_loader_jsonl.py -v
tests/test_loader_jsonl.py::test_jsonl_auto_registered    PASSED [ 25%]
tests/test_loader_jsonl.py::test_jsonl_load_plain_happy   PASSED [ 50%]
tests/test_loader_jsonl.py::test_jsonl_load_gz_happy      PASSED [ 75%]
tests/test_loader_jsonl.py::test_jsonl_requires_blob_store PASSED [100%]
4 passed in 0.10s
```

| AC | 状态 | 备注 |
|---|---|---|
| AC-1 auto-register | PASS | `"jsonl" in LoaderRegistry.list_names()` + `get("jsonl") is JsonlLoader` |
| AC-2 plain happy | PASS | rows=[hello,world,third]、line_nos=[1,3,6]、`line_count=3, error_count=2`、stats.format="jsonl" |
| AC-3 gz happy | PASS | `format=jsonl.gz` 命中解压；2 rows；stats.format="jsonl.gz" |
| AC-4 no blob_store | PASS | `pytest.raises(ValueError, match="ctx.blob_store")` |

## 2. 全量回归

```text
$ cd packages/core && uv run pytest -q
88 passed in 0.47s
```

84 → +4 = 88，无回归。

## 3. Diff scope

```text
$ git diff main..change/loader-jsonl-20260520 --stat
 .harness/changes/loader-jsonl-20260520/design.md          | 130 +++
 .harness/changes/loader-jsonl-20260520/implementation.md  |  62 ++
 .harness/changes/loader-jsonl-20260520/summary.md         |  64 ++
 packages/core/src/dataplat_core/loaders/__init__.py       |   9 +-
 packages/core/src/dataplat_core/loaders/jsonl.py          | 116 +++
 packages/core/tests/test_loader_jsonl.py                  | 128 +++
 6 files changed, 508 insertions(+), 1 deletion(-)
```

```text
$ git diff main..change/loader-jsonl-20260520 --name-only
.harness/changes/loader-jsonl-20260520/design.md
.harness/changes/loader-jsonl-20260520/implementation.md
.harness/changes/loader-jsonl-20260520/summary.md
packages/core/src/dataplat_core/loaders/__init__.py
packages/core/src/dataplat_core/loaders/jsonl.py
packages/core/tests/test_loader_jsonl.py
```

严格匹配设计允许范围。**未出现**：
- apps/api/* — clean
- packages/core 其他源码 / 测试 — clean
- pyproject.toml / uv.lock — clean
- W1-* / W2-* / W3-1..5 产物 — clean

`__init__.py` 仅在现有 for 循环 tuple 加 `("jsonl", JsonlLoader)`、加 import、加 `__all__`，与设计 § 范围 In scope 第 2 条一致。

## 4. 永不做清单 grep

```text
$ grep -RInE "manifest\.yaml|dataset-card\.yaml|row.?diff|cherry.?pick|rollback" \
    packages/core/src/dataplat_core/loaders/jsonl.py \
    packages/core/tests/test_loader_jsonl.py
clean
```

无违反 D-1 `data-not-code-pivot.md` 永不做清单。

## 5. 不变量检查清单（逐项 ✅）

| 不变量 | 源码位置 | 状态 |
|---|---|---|
| `name="jsonl"` / `version="0.1"` / `input_subtype="jsonl"` / `output_schema_id="silver-text-v1"` | jsonl.py:27-30 | ✅ |
| `asyncio.run(_run())` 包 async → sync `load(...)` | jsonl.py:116 | ✅ |
| `ctx.blob_store` 缺失 → `ValueError` 含 `"ctx.blob_store"` 子串 | jsonl.py:38-42 | ✅ |
| 仅用 stdlib（`json` + `gzip` + `asyncio`），未引入新依赖 | jsonl.py:14-17 + pyproject 无变化 | ✅ |
| gz 判定：`format == "jsonl.gz"` OR path hint `.jsonl.gz` 后缀 | jsonl.py:59-61 | ✅ |
| `text_field` 默认 `"text"`；`cfg.get("text_field") or "text"`（空串/None 都走默认） | jsonl.py:48 | ✅ |
| 空行跳过（不计 error、不计 line_count） | jsonl.py:75-76 | ✅ |
| 坏 json / 非 dict / 非 str text_field → `error_count += 1` 跳过 | jsonl.py:80-92 | ✅ |
| `SilverRow.source_ref` 含 `{blob_sha, loader, loader_version, line_no(1-based)}` | jsonl.py:98-103 | ✅ |
| per-row `stats = {"format", "char_count"}` | jsonl.py:104-107 | ✅ |
| `LoadResult.notes` 含 `"line_count=N"` 和 `"error_count=N"`（line_count = len(rows)） | jsonl.py:113 | ✅ |
| text 解码 `utf-8 errors="replace"` | jsonl.py:68 | ✅ |
| auto-register：在现有 for 循环 tuple 加 `("jsonl", JsonlLoader)` + try/except ValueError 包裹（idempotent） | __init__.py:9-18 | ✅ |
| `images=[]` + `lineage_ops=[]` | jsonl.py:97, 108 | ✅ |

## 6. 跨 change 回归

```text
$ cd packages/core && uv run pytest \
    tests/test_loader_html_md.py tests/test_loader_docx.py tests/test_loader_pptx.py \
    tests/test_loader_registry.py \
    tests/test_adapter_raw_upload.py tests/test_adapter_folder_md_assets.py tests/test_adapter_jsonl_import.py \
    tests/test_operator_protocol.py tests/test_operator_suite_mvp.py -q
30 passed in 0.35s
```

W3-1..W3-5 + W2-1 + W1-2 全套 PASS，无 regression。auto-register idempotent 工作正常（W3-5 引入的 try/except 在本 change 再次验证）。

## 7. DEVIATIONS 评估

**D-1（sonnet 报告）：line_count 语义澄清 = len(rows)（有效行数）**

- 上下文：design.md AC-2 期望 `notes` 含 `"line_count=3, error_count=2"`，输入 = 3 有效 + 1 空行 + 1 坏 json + 1 缺 text 字段。design.md 决策 8 写"空行跳过不计 line_count / error_count"，但 line_count 在"全部非空行（5）"和"有效行（3）"之间存在歧义。
- 隐含语义：AC-2 期望值 `line_count=3` 与 `total_count=3 = len(rows)` 一致；design 自身已隐含 `line_count = len(rows)`。
- 实施方案：`notes = f"line_count={len(rows)}, error_count={error_count}"`，不另设 line_count 变量。
- **裁定：ACCEPT**。设计 AC-2 期望值已唯一确定该语义；sonnet 仅做显式澄清，未引入新行为；语义可直接从单一变量 `len(rows)` 读出，最清晰。

无其他 DEVIATIONS。

## 8. NICE TO HAVE

无。本 change 范围克制、实现简洁、与 W3-4/W3-5 模板高度对齐，无可有可无的小优化建议；流式读取 / 嵌套字段 / prompt-completion 模式 / 行内嵌图片等均已在 design § Out of scope + § 关联 follow-up 显式 deferred，符合 v3 mini-design 精神。

## 总结

W3-6 JsonlLoader Phase 3 verify **APPROVED**。可进入 merge 流程。
