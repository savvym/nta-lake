---
change_id: processor-pdf-mineru-20260519
target: spec.md
target_version: 2
review_version: 2
reviewer: claude-agent:processor-pdf-mineru-20260519-stage2-reviewer-v2
reviewed_at: 2026-05-19T11:30:00Z
verdict: APPROVED
---

# Spec Review v2

## §1 v1 MUST FIX 复检

| # | v1 摘要 | v2 修法 | 验证证据 | 结论 |
|---|---|---|---|---|
| MUST FIX-1 | AC-8 grep ERE `\|` 字面化错误，`with_suffix\|\[:-4\]` 永不命中合法代码 | 完全重写 AC-8 命令：`grep -F -q ".md" ... && grep -q "with_suffix" ...`；同时把 scope 收窄为"只允许 with_suffix 路径"，彻底移除 `[:-4]` 备用路径，消除交替语义需求 | `grep -n 'AC-8' spec.md` 确认无 `\|` ERE 模式；实测 `echo 'Path(x).with_suffix(".md")' \| grep -q "with_suffix"` → exit 0；实测 `echo 'file.md' \| grep -F -q ".md"` → exit 0；`grep -n '\[:-4\]' spec.md` 无输出（`[:-4]` 已从 spec 移除） | **RESOLVED** |
| MUST FIX-2 | `config_schema` 属性未在 spec AC-1 命令和 T-2 描述中声明，Python 3.11 runtime_checkable isinstance 会 False | spec.md §范围 AC-1 及 AC 表命令补入 `config_schema`；AC-1 验证命令末尾增加 `and isinstance(p.config_schema, dict)` | AC-1 命令全文：`... assert isinstance(p, Processor) and isinstance(p.config_schema, dict)`；scope 行：`含 name / version / config_schema / accepts / produces 五项必备数据属性` | **RESOLVED** |
| MUST FIX-3 | AC-10 表格 `验证方式` 列内 `$()` 中写 `2>&1 \|`，管道被转义为字面字符串，整列命令报错退出 | AC-10 表格 `验证方式` 列改为 `见 AC 表下方 bash fenced block`；fenced block 中使用未转义 `2>&1 \| grep`（纯字面竖线已移除） | AC-10 表格行：`\| 见 AC 表下方 \`bash\` fenced block \|`；fenced block 第 1 行：`[ "$(... 2>&1 | grep -cE '...')" -ge 6 ]`（无 `\|`）；实测该语法（含 `# 2) 全部 PASS` 注释跟在 `&& \` 后）：bash 执行正常返 0 | **RESOLVED** |

v1 SHOULD FIX-1（AC-5 引用 AC-9 描述不准）：scope 行改为 `端到端体现在 AC-10 行为测试 test_run_env_missing_url 用例`，与 AC-9 实际覆盖（poll status=failed）解耦。已修，逻辑正确。

---

## 检查清单结论（plan 模式 spec.md v2）

| 项 | 结论 | 说明 |
|---|---|---|
| 背景写明了为什么现在做 | PASS | §背景 陈述业务诉求 + 已有 Processor 缺口 + MinerU 选型原因 |
| 问题陈述与目标可被外部读者理解 | PASS | §问题陈述 5 个缺失点，外部可独立阅读 |
| 范围 / 非范围都有 | PASS | §范围 与 §非范围 完整，6 个 follow-up 显式排除 |
| 验收标准每条可演示且可机械化 | PASS | 所有 v1 MUST FIX 已关闭；AC-8 / AC-10 命令实测可运行 |
| 风险有缓解措施或显式 accept | PASS | 9 条风险均有缓解说明 |
| 没有把已有架构当新提案重复 | PASS | 引用 design.md §2.3 §4.2，无架构重定义 |
| AC 表含 `kind` 列 | PASS | awk + grep -qE 验证命中 `kind` 表头 |
| 至少 1 行 AC kind=behavioral（锚定 regex） | PASS | AC-9 / AC-10 / AC-12 三行命中锚定 regex |
| behavioral AC 真跑代码并断言行为 | PASS | 三条 behavioral 均调 `uv run pytest`，使用 FakeAsyncClient monkeypatch |

---

## §2 v2 新增 / 调整内容审查

### 2.1 AC-8 修法与检查力度

v2 将 AC-8 命令从 ERE 交替换成两个独立 grep：
- `grep -F -q ".md" ...`（固定字符串，`.` 是字面点，不匹配 `file_md`）
- `grep -q "with_suffix" ...`（BRE，`with_suffix` 无正则特殊字符，可靠）

同时 spec §范围 与 T-2 描述均要求"输出 path 用 `Path(path).with_suffix('.md')`"，明确排除 `[:-4]` 写法。两个 grep 联合可确认文件中同时存在 `.md` 字符串和 `with_suffix` 调用，满足 static AC 要求。

**风险备注**（NICE TO HAVE）：`grep -F -q ".md"` 可被注释、文档字符串、import 语句中的 `.md` 误命中，但单独 `grep -q "with_suffix"` 已足够锚定路径变换方式，故组合检查不弱化保护。可接受。

### 2.2 AC-1 命令中的 `isinstance(p.config_schema, dict)` 数据属性校验

v2 AC-1 增加了 `isinstance(p.config_schema, dict)`，与 runtime_checkable Protocol 检查相符。T-2 描述提供了完整 JSON Schema 常量（inline dict），而非调用 `model_json_schema()`——两种实现均满足 `isinstance(..., dict)` 断言，命令不绑定特定实现细节，合理。

### 2.3 AC-10 fenced block 语法

Fenced block：
```
[ "$(... 2>&1 | grep -cE '...')" -ge 6 ] && \
# 2) 全部 PASS
(cd apps/api && uv run pytest -q --tb=no tests/test_pdf_mineru.py)
```
注释行 `# 2) 全部 PASS` 跟在 `&& \` 之后：已实测 bash 可正常解析（注释在行续符后等价于空行，不破坏 `&&` 链）。命令有效。

### 2.4 AC-5 scope 文字与 AC 表描述一致性

scope 行：`端到端体现在 AC-10 行为测试 test_run_env_missing_url 用例`  
AC-5 表行 `kind=static`，描述侧重 grep 命令；env 缺失行为验证确实在 AC-10 / T-4 `test_run_env_missing_url` 覆盖。两处一致。

### 2.5 跨链路自审 8 条（新增行 §跨链路一致性自审）

spec 末尾已列 8 条，均标 ✅，无可见遗漏。

### 2.6 revision_notes 与实际修改对齐

revision_notes 声明修了 MUST FIX-1/2/3 + SHOULD FIX-1，实际 diff 对应内容可验证，无虚假声明。

---

## §3 v2 verdict 与问题列表

### MUST FIX

（无）

### SHOULD FIX

（无）

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| NICE-1 | spec.md §验收标准 AC-8 | `grep -F -q ".md"` 的检查价值较弱（注释、docstring 均可命中）；实际有意义的锚是 `grep -q "with_suffix"`。若未来 coding agent 用 `with_suffix('.md')` 字面量，两条 grep 仍 PASS，所以不影响正确性。可考虑直接写 `grep -q "with_suffix(\".md\")"` 精确锚定，消除歧义。 | 可选：将 `grep -F -q ".md"` 替换为 `grep -q 'with_suffix(".md")'`，精确校验字面量，同时去掉前半段 redundant grep。不阻塞通过。 |
| NICE-2 | summary.md §Deferred 项 | v1 NICE-1 标注的模板占位符残留（`_e.g. 加更细的并发测试_` / `_follow-up change <id> 或 task <id>_`）在 v2 中未清理。不触发 self_check 硬检，但降低可读性。 | 若无 deferred 项，改写为"暂无 deferred 项"。 |

---

## Verdict

**APPROVED**

v1 三条 MUST FIX 全部 RESOLVED：
- MUST FIX-1（AC-8 ERE `\|` 字面化）：命令完全重写，去除交替语义，新命令实测有效。
- MUST FIX-2（`config_schema` 缺失）：AC-1 命令补 `isinstance(p.config_schema, dict)`；spec §范围 与 AC 表描述均明确 `config_schema` 必备属性。
- MUST FIX-3（AC-10 `\|` 破管）：表格改为引用 fenced block，fenced block 使用未转义 `|`，bash 语法实测正确。

v2 无新 MUST FIX。spec 可进入 stage 3 编码阶段。

---

## 复检指引（供 Generator 自查）

```bash
# 确认 AC-8 命令无旧 ERE \| 模式
grep "AC-8" .harness/changes/processor-pdf-mineru-20260519/request_analysis/spec.md | grep -v 'with_suffix\\|' && echo "PASS" || echo "FAIL"

# 确认 AC-1 命令含 config_schema 断言
grep "AC-1" .harness/changes/processor-pdf-mineru-20260519/request_analysis/spec.md | grep -q "config_schema" && echo "PASS" || echo "FAIL"

# 确认 AC-10 fenced block 无 \| 破管
sed -n '/^### AC-10 完整验证命令/,/^```$/p' .harness/changes/processor-pdf-mineru-20260519/request_analysis/spec.md | grep "2>&1" | grep -qv '2>&1 \\|' && echo "PIPE OK" || echo "BROKEN"

# kind 列存在
awk '/^## 验收标准/{p=1;next} p && /^## /{exit} p' .harness/changes/processor-pdf-mineru-20260519/request_analysis/spec.md \
  | grep -qE '^\|[^|]*\|[[:space:]]*kind[[:space:]]*\|' && echo "kind col PASS" || echo "FAIL"

# behavioral AC 锚定 regex
awk '/^## 验收标准/{p=1;next} p && /^## /{exit} p' .harness/changes/processor-pdf-mineru-20260519/request_analysis/spec.md \
  | grep -qE '^\|[[:space:]]*AC-[0-9]+[a-z]?[[:space:]]*\|[[:space:]]*(\*\*)?behavioral(\*\*)?[[:space:]]*\|' && echo "behavioral AC PASS" || echo "FAIL"
```
