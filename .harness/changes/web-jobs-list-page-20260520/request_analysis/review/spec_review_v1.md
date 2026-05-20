---
change_id: web-jobs-list-page-20260520
target: spec.md
target_version: 1
review_version: 1
reviewer: claude-agent:web-jobs-list-page-20260520-stage2-reviewer-v1
reviewed_at: 2026-05-20T05:00:00Z
verdict: REVISION REQUIRED
---

# Spec Review v1

## 检查清单结论

| 条目 | 状态 | 说明 |
|---|---|---|
| 背景写明了为什么现在做 | PASS | 现状/用户痛点/用户选定 三段清晰 |
| 问题陈述与目标可被外部读者理解 | PASS | 5 个问题点逐条列出 |
| 范围 / 非范围都有 | PASS | 均有，非范围 5 条 |
| 验收标准每条都可演示且可机械化 | PARTIAL | AC-3 grep 表达式与 T-3 描述不一致（见 MUST FIX-1） |
| 风险有缓解措施或显式 accept | PASS | 风险表 7 行均有缓解 |
| 没有把已有架构当新提案重复 | PASS | 未重复 design.md |
| AC 表存在 `kind` 列 | PASS | 表头含 kind 列 |
| 至少 1 行 AC kind=behavioral（锚定 regex） | PASS | AC-7 / AC-8 均为 behavioral |
| ac_kind_lint 非 exempt | PASS | frontmatter 无 exempt |

## 问题列表

### MUST FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| MUST FIX-1 | spec.md AC-3 验证命令 + T-3 描述 | **AC 与 task 路由 path 不一致**：AC-3 grep `@router\.get\(\s*[\"\x27]/[\"\x27]\s*` 只能匹配 `@router.get("/")`（含斜杠），但 T-3 spec 描述写 `@router.get("")`（空字符串）。两者不能同时为真——实现时只能选其一，而 AC grep 是 `"/"` 、task 是 `""`，导致实现 `""` 时 self_check 必 FAIL，实现 `"/"` 时又产生尾斜杠路由 `/jobs/`（与 `/jobs` 不同）。必须统一：明确选择 `@router.get("")` 还是 `@router.get("/")`，并把 AC-3 grep 表达式与 T-3 描述同步。 | 建议选 `@router.get("")`（挂在 prefix="/jobs" 下等价 `GET /jobs`，无尾斜杠歧义）；相应把 AC-3 grep 改为 `grep -qE '@router\.get\(\s*[\"\x27][\"\x27]\s*'`（空引号匹配）。若选 `"/"` 则需在 spec 非范围或风险表明确尾斜杠行为。 |

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| SHOULD FIX-1 | spec.md §非范围 | 非范围未明确"不往 JobORM 加 owner_id 列/migration"。summary.md deferred 表有写，但 spec 非范围段只说"不加 alembic"。编码阶段 agent 看 spec 时可能误加列。 | 在非范围加一条：`不向 JobORM 加 owner_id/任何新列（schema 变更留 jobs-owner-acl-* follow-up）` |
| SHOULD FIX-2 | spec.md §风险 "status/type 值域无 enum" | 风险缓解写"router 层显式 validate；不在白名单 → 400"，但 AC-3 验证只 grep 函数存在 + require_admin，未校验 400 行为。这意味着 self_check 可能放过"validate 逻辑缺失"。 | 在 AC-3 或单独加一条 static AC，grep whitelist 逻辑存在（如 `grep -q "400"` 或 `grep -q "VALID_STATUS"` 在 routers/jobs.py），或将此校验升为 behavioral 测试（AC-8 d 子项"invalid status → 400"）。 |
| SHOULD FIX-3 | spec.md §跨链路自审 第 6 条 | 自审第 6 条写"✅ AC-3 grep 精确（含 @router.get 锚定 path '/'）"——这正是与 T-3 `""` 矛盾的来源；自审通过了一个不准确的结论。 | 修正自审第 6 条表述，与 MUST FIX-1 的统一结论一致。 |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| NTH-1 | spec.md AC-8 完整命令 | `[ "$(cd apps/api && uv run pytest --collect-only -q tests/test_jobs_list.py 2>&1 | grep -cE 'test_jobs_list\.py::')" -ge 4 ]` 用 `grep -cE` 统计行数；`grep -c` 找不到时返回非 0 使 `[ ... -ge 4 ]` 前的 subshell 先 exit 1，导致整条 AC-8 命令失败（即使测试全 PASS）。 | 加 `|| true` 在 grep 后：`grep -cE ... || true`；或改用 `--co -q | wc -l` 方案。 |
| NTH-2 | spec.md AC-5 描述 | "用时 (started→completed 差值)" 在 started_at 为 null（queued 状态）时无法计算。UI 应有 null guard，但 spec 未说明。 | 在 AC-5 中补"当 started_at 或 completed_at 为 null 时显示 —"。 |
| NTH-3 | spec.md §路由顺序（审阅重点 #3） | spec 未指定 `GET /jobs`（新）与 `GET /jobs/{job_id}`（已有）的定义顺序。FastAPI 按定义顺序匹配——若 `/{job_id}` 在前，不会错误吞 `GET /jobs?...`（因 path 有 `{job_id}` 参数），实际无 bug；但 spec 显式说明顺序（新端点在前）有助于编码 agent 避免误解。 | 在 AC-3 或受影响模块一节加注："GET /jobs（空 path）须定义在 GET /jobs/{job_id} 之前，或视 FastAPI 路由匹配规则确认无优先级冲突"。 |

## Verdict

**REVISION REQUIRED**

存在 1 个未关闭 MUST FIX：AC-3 grep 与 T-3 路由 path 不一致，会导致实现与 self_check 之间必有一个出错。必须在 spec v2 + tasks v2 同步修正后重提评审。

## 后续指引

Generator 修 spec v2 时：

1. 确定路由 path 为 `""` 或 `"/"`，同步修改：
   - spec.md AC-3 验证命令的 grep 表达式
   - spec.md §跨链路自审 第 6 条
   - tasks.md T-3 description
2. 建议运行自查：
   ```bash
   # 确认 AC-3 grep 与 T-3 一致（人工对比）
   grep "AC-3" .harness/changes/web-jobs-list-page-20260520/request_analysis/spec.md
   grep "T-3" .harness/changes/web-jobs-list-page-20260520/request_analysis/tasks.md
   # 确认 kind 列存在且有 behavioral
   awk '/^## 验收标准/{p=1;next} p && /^## /{exit} p' \
     .harness/changes/web-jobs-list-page-20260520/request_analysis/spec.md \
     | grep -E '^\|[[:space:]]*AC-[0-9]+[a-z]?[[:space:]]*\|[[:space:]]*(\*\*)?behavioral(\*\*)?[[:space:]]*\|'
   ```
3. SHOULD FIX-1 建议同步修（非阻塞但强烈建议）；NTH 项可在 v2 选择性处理。
