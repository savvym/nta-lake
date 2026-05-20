---
change_id: operator-suite-mvp-20260520
phase: verify
reviewer: claude-agent:opus-phase3-reviewer
model_used: opus
authored_at: 2026-05-20T10:42:39Z
verdict: APPROVED
---

# Verify Review

> Phase 3 reviewer 产物。对照 design.md（原始要求）+ implementation.md（声称的实现）+ `git diff main...change/operator-suite-mvp-20260520` 验 PR。

## 输入

- **Design**：`.harness/changes/operator-suite-mvp-20260520/design.md`（reviewer 必读）✅ 已读
- **Implementation**：`.harness/changes/operator-suite-mvp-20260520/implementation.md`（reviewer 必读）✅ 已读
- **Git diff**：`git diff main...change/operator-suite-mvp-20260520`（606 行新增，9 文件）
- **PR**：branch `change/operator-suite-mvp-20260520`，head `a4e5779`（实现）+ `d53d548`（impl.md）

## AC 对照表

| AC | kind | reviewer 跑的命令 | 结果 | PASS/FAIL/NOT-VERIFIABLE |
|---|---|---|---|---|
| AC-1 | behavioral | `cd packages/core && uv run pytest tests/test_operator_suite_mvp.py::test_filter_operator_drop_and_keep -x -q` | `1 passed in 0.10s` | PASS |
| AC-2 | behavioral | `cd packages/core && uv run pytest tests/test_operator_suite_mvp.py::test_dedup_operator_text_key -x -q` | `1 passed in 0.10s` | PASS |
| AC-3 | behavioral | `cd packages/core && uv run pytest tests/test_operator_suite_mvp.py::test_score_operator_text_chars -x -q` | `1 passed in 0.10s` | PASS |
| AC-4 | behavioral | `cd packages/core && uv run pytest tests/test_operator_suite_mvp.py::test_all_four_operators_registered -x -q` | `1 passed in 0.10s` | PASS |

## 机械化检查日志

```text
$ cd packages/core && uv run pytest tests/test_operator_suite_mvp.py::test_filter_operator_drop_and_keep -x -q
.                                                                        [100%]
1 passed in 0.10s

$ cd packages/core && uv run pytest tests/test_operator_suite_mvp.py::test_dedup_operator_text_key -x -q
.                                                                        [100%]
1 passed in 0.10s

$ cd packages/core && uv run pytest tests/test_operator_suite_mvp.py::test_score_operator_text_chars -x -q
.                                                                        [100%]
1 passed in 0.10s

$ cd packages/core && uv run pytest tests/test_operator_suite_mvp.py::test_all_four_operators_registered -x -q
.                                                                        [100%]
1 passed in 0.10s

# W1-2 兼容性回归
$ cd packages/core && uv run pytest tests/test_operator_protocol.py -q
...                                                                      [100%]
3 passed in 0.09s

# 全套
$ cd packages/core && uv run pytest tests/ -q
..........................................                               [100%]
42 passed in 0.23s

$ git diff --stat main...change/operator-suite-mvp-20260520
 .../changes/operator-suite-mvp-20260520/design.md  | 107 +++++++++++++++++++++
 .../operator-suite-mvp-20260520/implementation.md  |  71 ++++++++++++++
 .../changes/operator-suite-mvp-20260520/summary.md |  49 ++++++++++
 .../operator-suite-mvp-20260520/verify_review.md   |  81 ++++++++++++++++
 .../core/src/dataplat_core/operators/__init__.py   |  21 ++++
 packages/core/src/dataplat_core/operators/dedup.py |  66 +++++++++++++
 .../core/src/dataplat_core/operators/filter.py     |  52 ++++++++++
 packages/core/src/dataplat_core/operators/score.py |  66 +++++++++++++
 packages/core/tests/test_operator_suite_mvp.py     |  93 ++++++++++++++++++
 9 files changed, 606 insertions(+)

$ git log main..HEAD --oneline
d53d548 docs(change): fill implementation.md for operator-suite-mvp-20260520 (W2-1)
a4e5779 feat(core): filter/dedup/score Operator MVP + auto-register 4 operators (W2-1)
614ce13 docs(harness): operator-suite-mvp mini-design (W2-1, v3)
```

## 隐式偏离审计

> reviewer 对照 design.md vs implementation.md vs git diff，列出 implementation.md § 偏离 没声明但实际发生的偏离。

对照 design.md § In scope 与 git diff 全部源文件逐项核对：

- **5 个改动文件齐**（design 期望 1 改 + 4 新）：
  - `operators/filter.py` (new, 52L) — FilterOperator ✅
  - `operators/dedup.py` (new, 66L) — DedupOperator ✅
  - `operators/score.py` (new, 66L) — ScoreOperator ✅
  - `operators/__init__.py` (edit, +21L) — auto-register 4 ✅
  - `tests/test_operator_suite_mvp.py` (new, 93L) — 4 AC tests ✅
- **3 个 Operator 4 属性齐**：`name` / `version` / `spec` (含 `config_schema` JSON Schema) 全对，与 design 表述字符对字符一致（含 `additionalProperties: False`）。
- **filter.run() 行为**：`len(row.text) < min_chars` 返 `[]`；否则 `model_copy(update={"lineage_ops": [*row.lineage_ops, {"op": "filter", "version": "1.0", "min_chars": min_chars}]})` 后返 `[new_row]`。完全匹配 design。
- **dedup.run() 行为**：`ctx._dedup_seen` 用 `getattr / setattr` 兜底（与 design 第 2 决策 "ctx attribute hack" 一致）；`text` → `hashlib.sha256(text.encode("utf-8")).hexdigest()`；`source_blob` → `row.source_ref["blob_sha"]`；命中返 `[]`；否则 `seen.add(hash_key)` + 追加 lineage_ops。完全匹配。
- **score.run() 行为**：`text_chars` → `len(row.text)`；`alpha_ratio` → `round(sum(...) / max(len(row.text), 1), 4)`（分母防 0，design 文本写的也是 `max(len(row.text), 1)`）；新 stats 用 `{**row.stats, f"score_{metric}": score}` 不 mutate；追加 lineage_ops。完全匹配。
- **__init__.py auto-register**：`for (name, cls) in [("identity", ...), ("filter", ...), ("dedup", ...), ("score", ...)]` + `try/except ValueError` 兜底，与 design 第 4 决策 + risk 表第 1 行缓解策略一致。
- **不 mutate 输入行**：3 个 Operator 全部用 `row.model_copy(update={...})` + list/dict literal，输入 `row.lineage_ops` / `row.stats` 在 test 中显式断言未变（test_filter 第 42 行、test_score 第 81-82 行）。
- **未触碰应当不动的文件**：`git diff --name-only` 仅列出 5 个 code + 4 个 doc 文件；`identity.py` / `registry.py` / `protocols/*` / `loaders/*` / `schemas/*` / `apps/*` 全部 0 改动 ✅。
- **测试**：4 个测试函数名 / 期望断言与 design 表 AC-1..AC-4 一致；额外加了"输入未 mutate"的断言（增强而非偏离）。

**结论：无隐式偏离。** implementation.md § 偏离声明 "无偏离" 属实。

## 问题列表

### MUST FIX

- 无。

### SHOULD FIX

- 无。

### NICE TO HAVE

- (可选 / follow-up) DedupOperator 当前在 `source_blob` 分支直接 `row.source_ref["blob_sha"]`，若上游 row 缺该 key 会 `KeyError`。design 默认 SilverRow 必有此字段（W1-3 schema 已约束），但加一个显式异常分支或 `dict.get` + 抛 ValueError 会更友好。可挂 follow-up，不阻塞本 change。
- (可选) ScoreOperator 的 `alpha_ratio` 用 `c.isalpha()` 对 unicode 字母全 True（包括中文 / 西里尔等），与单词命名 "alpha" 的英语直觉不完全一致；design 未约束语义，不算偏离。后续 W4-8 LLM 评分演化时可定义更精确的 metric 语义。

## Verdict

**APPROVED**

- PR 严格兑现 design.md § In scope 全部条目；
- 4 个 AC 全 PASS；
- W1-2 `test_operator_protocol.py` 3 个用例 + 全套 42 个用例 0 fail（W1-2 用 `"identity_test_ac2"` 唯一 key，与新自动注册的 `"identity"` 不冲突，与 design risk 表第 4 行预言一致）；
- 隐式偏离审计：无；
- 决策合规：D-1（不涉 DB）/ D-11（实现 + impl.md 拆 2 commit，与 W1-2/3/4 一致）/ D-13（v3 mini-design 无 Phase 1 reviewer）/ 永不做清单（不违反）全部 OK；
- 无 MUST / SHOULD FIX。

## 后续指引

1. Application Owner merge `change/operator-suite-mvp-20260520` → `main`（fast-forward 或 merge commit 任一均可，本仓库历史以 merge commit 为主）。
2. close W2-1 change：将本 change 目录 status 视为 done（无需移动；harness changes 按 frontmatter status 标识）。
3. 推进 W2-2 chunker：可在 W2-1 落地的 FilterOperator/DedupOperator/ScoreOperator 模板上继续；注意 chunker 是首个 1→N 语义算子。
4. 已记录 NICE TO HAVE 2 项；可于 W2-5 recipe v2 + RunContext Protocol 形式化时一并处理（与 design § 关联 follow-up 第 1 条对齐）。
