---
change_id: processor-pdf-mineru-20260519
target: spec.md
target_version: 1
review_version: 1
reviewer: claude-agent:processor-pdf-mineru-20260519-stage2-reviewer-v1
reviewed_at: 2026-05-19T10:30:00Z
verdict: REVISION REQUIRED
---

# Spec Review v1

## v0 MUST FIX 复检

不适用（本次为 v1 首次评审）。

---

## 检查清单结论（plan 模式 spec.md）

| 项 | 结论 | 说明 |
|---|---|---|
| 背景写明了为什么现在做 | PASS | §背景 明确说明缺失 Processor + 业务诉求 |
| 问题陈述与目标可被外部读者理解 | PASS | §问题陈述 列出 5 个缺失点，可独立阅读 |
| 范围 / 非范围都有 | PASS | §范围 与 §非范围 均完整，非范围有 6 个 follow-up 显式排除 |
| 验收标准每条可演示且可机械化 | **FAIL** | AC-8 regex 存在 bug（见 MUST FIX-1）；AC-10 命令有 `\|` 破管问题（见 MUST FIX-3）；`config_schema` 缺失影响 AC-1 可达性（见 MUST FIX-2） |
| 风险有缓解措施或显式 accept | PASS | 9 条风险均有缓解或 accept，含 env 缺失 / poll 超时 / httpx mock / worker import / live API 字段名漂移 |
| 没有把已有架构当新提案重复 | PASS | 引用 design.md §2.3 §4.2，未重新定义架构 |
| AC 表含 `kind` 列 | PASS | `awk` + `grep -qE '^\|[^|]*\|[[:space:]]*kind[[:space:]]*\|'` 验证命中 |
| 至少 1 行 AC kind=behavioral（锚定 regex） | PASS | AC-9 / AC-10 / AC-12 均为 behavioral，锚定 awk+regex 验证命中 |
| behavioral AC 真跑代码并断言行为 | PASS | 三条 behavioral AC 均调用 `uv run pytest`，测试文件使用 FakeAsyncClient monkeypatch |

---

## 问题列表

### MUST FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| MUST FIX-1 | spec.md §验收标准 AC-8 验证方式列 | **AC-8 grep -E 正则 bug**：`grep -qE "with_suffix\|\[:-4\]"` 中 `\|` 在 ERE 模式下是**字面竖线**（不是交替分隔符），整个 pattern 匹配 `with_suffix|[:-4]` 这个字面字符串——在任何正常 Python 代码中永远不会出现。执行测试：`echo 'Path(x).with_suffix(".md")' \| /bin/grep -qE "with_suffix\|\[:-4\]"` 返回 1（不匹配）。| 改为不转义的 `|`：`grep -qE "with_suffix|\[:-4\]"`（ERE 中 `|` 是交替算符；`\[:-4\]` 匹配字面 `[:-4]`）。可验证：`echo 'Path(x).with_suffix(".md")' \| /bin/grep -qE "with_suffix|\[:-4\]"` 命中。注意在 Markdown 表格中需写成 `with_suffix\|\[:-4\]` 以显示正确，但 spec 的说明注释需指出 shell 实际用 `with_suffix|\[:-4\]`（不转义 `|`）。 |
| MUST FIX-2 | spec.md §范围 AC-1 / §问题陈述 / tasks.md T-2 | **`config_schema` 属性缺失于 spec 和 T-2 描述**：`dataplat_core.protocols.processor.Processor` 是 `@runtime_checkable` Protocol，含 `config_schema: dict[str, Any]` 属性；`isinstance(PdfMineruProcessor(), Processor)` 在 Python 3.11 下**会检查此属性**（已实测）。spec.md AC-1 的 isinstance 验证命令 + T-2 实现描述均未提及 `config_schema`，导致 coding agent 极可能遗漏，AC-1 的 dry-import 在 stage 2 review 后会运行失败。| spec.md §范围 AC-1 描述中补充"须含 `config_schema: dict[str, Any] = PdfMineruSpec.model_json_schema()` 或等效常量"；T-2 description 在 PdfMineruProcessor 属性列表中加 `config_schema = PdfMineruSpec.model_json_schema()`（参考 `llm_qa_gen.py` 第 105 行）。 |
| MUST FIX-3 | spec.md §验收标准 AC-10 验证方式列 | **AC-10 验证命令中 `\|` 破管**：命令为 `[ "$(cd apps/api && uv run pytest --collect-only -q tests/test_pdf_mineru.py 2>&1 \| grep -cE 'test_pdf_mineru\.py::')" -ge 6 ]`。在 bash 中，`$()` 内的 `\|` **不是管道符**，`\` 被作为字面字符处理，`\| grep` 不产生管道，整个 `$()` 捕获的是 pytest 输出与 ` | grep -cE...` 拼接的字符串（如 `"3 tests collected\n... | grep -cE..."`），`[ ... -ge 6 ]` 因整数解析失败直接报错退出。已实测：`result=$(echo "foo" 2>&1 \| grep -c "foo")` → `result="foo | grep -c foo"`（非整数）。spec 说明命令应"可在 `scripts/_self_check.sh` 直接跑"，此命令不满足。| 验证方式列改用与 `llm-qa-gen-20260518` spec AC-10 一致的写法（在代码块而非表格 `\|` 形式）：`[ "$(cd apps/api && uv run pytest --collect-only -q tests/test_pdf_mineru.py 2>&1 | grep -cE 'test_pdf_mineru\.py::')" -ge 6 ] && (cd apps/api && uv run pytest -q --tb=no tests/test_pdf_mineru.py)`；或在表格备注中注明"shell 使用 `|`（不转义）"。 |

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| SHOULD FIX-1 | spec.md §范围 AC-5 条目 | **AC-5 "失败分支" 描述引用 AC-9 不准确**：条目写 "空/缺失 → ValueError，端到端体现在 AC-9 失败分支"，但 AC-9 的验证命令只跑 `test_run_success` 和 `test_run_poll_failed_raises`——"AC-9 失败分支" 指 poll 返回 `status=failed`，而非 env URL 缺失。env URL 缺失的行为测试（`test_run_env_missing_url`）实际由 AC-10（≥6 全 PASS）覆盖，不在 AC-9 的命名测试范围内。此描述会误导 coding 阶段认为 AC-9 已覆盖 env 缺失断言，从而在 AC-9 命令中漏写 `test_run_env_missing_url`。 | 将 "端到端体现在 AC-9 失败分支" 改为 "行为测试由 `test_run_env_missing_url` 承载（包含于 AC-10 全套测试）"；或直接在 AC-9 的验证命令中加入 `tests/test_pdf_mineru.py::test_run_env_missing_url`。 |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| NICE-1 | summary.md §Deferred 项 | 模板示例文字残留：`_e.g. 加更细的并发测试_` 和 `_follow-up change <id> 或 task <id>_` 仍在 Deferred 表格中。不触发 `_self_check.sh` 硬检（检查模式为 `<feature-slug>` 等特定占位符），但降低文档可读性。 | 若当前无 Deferred 项，清空该表格行或改写为 "暂无 deferred 项"。 |

---

## Verdict

**REVISION REQUIRED**

存在 3 条 MUST FIX：

- MUST FIX-1：AC-8 grep ERE 正则 bug，`\|` 作字面竖线，验证命令永不命中合法代码，stage 3 coding 中 AC-8 验证将始终失败。
- MUST FIX-2：`config_schema` 属性未在 spec 和 T-2 中声明，`isinstance(PdfMineruProcessor(), Processor)` 在 Python 3.11 会返回 False，AC-1 将失败。
- MUST FIX-3：AC-10 验证命令中 `$()` 内 `\|` 不产生管道，命令报错退出，无法机械化。

3 条均阻塞 stage 3 进入，须修后重提 spec_review_v2。

---

## 复检指引

Generator 修完 spec_v2 + tasks_v2 后，reviewer 复检命令：

```bash
# 复检 MUST FIX-1：AC-8 regex 应命中 with_suffix 代码
echo 'path = Path(orig).with_suffix(".md")' | /bin/grep -qE 'with_suffix|\[:-4\]' && echo "PASS" || echo "FAIL"
echo 'path = orig[:-4] + ".md"' | /bin/grep -qE 'with_suffix|\[:-4\]' && echo "PASS" || echo "FAIL"

# 复检 MUST FIX-2：T-2 描述含 config_schema
grep "config_schema" .harness/changes/processor-pdf-mineru-20260519/request_analysis/tasks.md && echo "FOUND" || echo "MISSING"

# 复检 MUST FIX-3：AC-10 command 无 \| 破管（验证 pipe 可用）
# 在 spec.md 找到 AC-10 行，确认 '2>&1 |' 不含反斜线
grep "AC-10" .harness/changes/processor-pdf-mineru-20260519/request_analysis/spec.md | grep -qv '2>&1 \\|' && echo "PIPE OK" || echo "STILL BROKEN"

# 复检 AC kind 列仍存在
awk '/^## 验收标准/{p=1;next} p && /^## /{exit} p' .harness/changes/processor-pdf-mineru-20260519/request_analysis/spec.md \
  | /bin/grep -qE '^\|[^|]*\|[[:space:]]*kind[[:space:]]*\|' && echo "kind col PASS" || echo "FAIL"

# 复检 behavioral AC 锚定 regex
awk '/^## 验收标准/{p=1;next} p && /^## /{exit} p' .harness/changes/processor-pdf-mineru-20260519/request_analysis/spec.md \
  | /bin/grep -qE '^\|[[:space:]]*AC-[0-9]+[a-z]?[[:space:]]*\|[[:space:]]*(\*\*)?behavioral(\*\*)?[[:space:]]*\|' && echo "behavioral AC PASS" || echo "FAIL"
```
