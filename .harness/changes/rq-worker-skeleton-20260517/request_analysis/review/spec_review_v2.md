---
change_id: rq-worker-skeleton-20260517
target: spec.md
target_version: 2
review_version: 2
reviewer: claude-stage2-reviewer-v2
reviewed_at: 2026-05-17T14:25:00Z
verdict: APPROVED
---

# Spec Review v2

## v1 MUST FIX 闭合复核

| # | v1 问题 | v2 修复定位 | 复核结论 |
|---|---|---|---|
| 1 | AC-4 验证命令 `for m in [...]: assert ...` Python 复合语句不可在 `python -c` 单语句解析（SyntaxError） | spec.md L61 已改为 generator expression：`assert all(hasattr(JobsService, m) for m in ['enqueue','get_by_id','mark_running','mark_succeeded','mark_failed'])`；frontmatter `revisions` 段第一条明示该消化 | **CLOSED** |

reviewer 实跑机械化验证（命令复制自 spec v2 L61，原样不动）：

```bash
$ cd apps/api && uv run python -c "from dataplat_api.jobs.service import JobsService; \
    assert all(hasattr(JobsService, m) for m in ['enqueue','get_by_id','mark_running','mark_succeeded','mark_failed'])"
Traceback (most recent call last):
  File "<string>", line 1, in <module>
ModuleNotFoundError: No module named 'dataplat_api.jobs'
exit=1
```

预期结果：**`ModuleNotFoundError`**（模块未实现 — stage-3 实施前必然如此）；**SyntaxError 不再出现**。命令语法合法 → MUST FIX-1 闭合。

## 其他 AC `python -c` 命令 dry-parse 全量复核（v1 review 复检指引第 4 条）

reviewer 抽 spec v2 全部 `python -c` 命令，用 `compile(..., '<ac>', 'exec')` 做 dry-parse；语法非法即新增 MUST FIX。结果：

| AC | 命令位置 | dry-parse 结论 | 注 |
|---|---|---|---|
| AC-1 | L52 | PASS（exit=0） | set comprehension + 子集断言 + `assert ..., msg` 形态合法 |
| AC-3 | L58 | PASS（exit=0） | `callable(...) and callable(...)` 单行表达式合法 |
| AC-4 | L61 | PASS（exit=0） | **v1 修复确认**：generator expression 替代 for-loop |
| AC-5 | L64 | PASS（exit=0） | `import inspect; sig=...; assert ...` 三条简单语句 `;` 串接合法 |
| AC-6 | L69 | PASS（exit=0） | `model_config.get('extra')` 链式访问合法 |
| AC-7 | L72 | PASS（exit=0） | set comprehension `{r.path for r in router.routes}` 合法 |
| AC-8 | L75 | PASS（exit=0） | `app.openapi()` 调用 + dict 索引合法 |

实跑命令：

```bash
python3 -c "compile(<spec 中提取的 python -c payload>, '<ac>', 'exec')"
# 7/7 全部 exit=0
```

**结论**：spec v2 无残留 SyntaxError 类问题。SKILL 第 8 条 dry-parse 自审在本变更已自洽闭环。

## SKILL 第 8 条反哺生效复核

`.harness/skills/request-analysis/SKILL.md` 检查：

- **L135** 新增第 8 条标题：`8. **AC 验证命令必须真跑过 dry-parse**（rq-worker-skeleton stage 2 反哺...）`，明示典型陷阱（Python 复合语句嵌 `;`）、修复手段（generator expression / 真换行 / exec）、自查命令（`python -c "compile(...)"` 或 `bash -n`）
- **L161** 配套 grep 自查脚本块新增第 8 段：抽取所有 `python -c "..."` payload 用 `compile(...)` dry-parse，命中 SyntaxError 即 MUST FIX
- **L169** checklist 总结段补充："第 8 条来自 rq-worker-skeleton v1 stage 2 反哺（AC-4 Python 复合语句 SyntaxError）——形态合法 ≠ 语法合法，generator 必须真跑 dry-parse"

三处反哺一致，**SKILL 第 8 条生效**。

## SKILL 7 条 + 第 8 条 checklist 完整回归

| # | 检查项 | v2 状态 | 备注 |
|---|---|---|---|
| 1 | 四链路（hash / schema / idempotency / fixture）一致 | N/A | 本变更不引入新 hash |
| 2 | 事务边界声明 AC + 风险 + tasks 三处一致 | PASS | "独立 async engine + session" 措辞统一 |
| 3 | AC 验证命令一行式可执行（形态） | PASS | 14 条 `uv run python -c` / `test -f` / `bash` 全一行 |
| 4 | 风险 ↔ AC 测试号映射 | PARTIAL | 与 v1 review SHOULD FIX-1 同状态，未列为 MUST FIX |
| 5 | commit 历史链连续性 | PASS | 无裸 `parents=[]` |
| 6 | 反向 grep 配 `test -f` + 不吞 stderr | PASS | AC-9 L78 模板严格 |
| 7 | process_tasks 6 条（stage-2/4/6/7/9/10） | PASS | tasks v1 grep -cE 计数 = 6（v1 review 已确认） |
| 8 | **AC 验证命令 dry-parse**（**本变更新增**） | **PASS** | 7/7 `python -c` 命令 compile 全 exit=0 |

机械化复跑 spec v2 自审 grep（spec.md L131-L138 自审命令块）：

```text
grep -nE "事务前|事务内|事务外" spec.md     → L132 仅自审注释行
grep -nE "parents=\[\]" spec.md            → L115 + L133 仅自审注释行（无裸代码）
grep -nE "! *grep" spec.md                 → L78 AC-9 1 处（配 test -f）+ L134 自审注释
grep -nE "2>/dev/null" spec.md             → L135 仅自审注释行
grep -cE "estimated_stage: stage-(2|4|6|7|9|10)" tasks.md → 6（tasks v1 未改）
grep -cE "test -f|cd apps/api|grep -q|uv run python" spec.md → ≥ 12
```

全部满足期望（reviewer 实跑确认）。

## 问题列表

### MUST FIX

无。

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | spec v1 review SHOULD FIX-1~-5 | v2 frontmatter `revisions` 段只声明消化了 MUST FIX-1 与 SKILL 第 8 条反哺，未对 v1 5 条 SHOULD FIX 做"## v2 evaluation against v1 review" 处理记录（v1 review 复检指引第 3 条期望此区块） | spec v2 末追加一段，逐条标 accept / defer / reject + 理由；不阻塞 stage-3 进入，但下游 reviewer 检阅链路完整度受影响 |

### NICE TO HAVE

无新增。

## Verdict

**APPROVED**（残留 MUST FIX 数 = 0）

- v1 唯一 MUST FIX（AC-4 SyntaxError）→ 已闭合（generator expression + 实跑确认）
- SKILL 第 8 条 dry-parse 自审已反哺到 `request-analysis/SKILL.md`（L135 / L161 / L169 三处）
- 全部 7 条 `python -c` AC 验证命令 dry-parse 通过，第 8 条已自洽生效
- SHOULD FIX-1（v1 SHOULD FIX 处理记录缺失）不阻塞通过；建议 stage-3 进入前作者补一段处理记录

可进入 stage 3（coding）。
