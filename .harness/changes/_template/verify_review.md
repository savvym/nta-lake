---
change_id: <feature-slug>-<yyyymmdd>
phase: verify
reviewer: claude-agent:opus-phase3-reviewer
model_used: opus
authored_at: <YYYY-MM-DDTHH:MM:SSZ>
verdict: <APPROVED | MINOR FIX | MAJOR ISSUE>
---

# Verify Review

> Phase 3 reviewer 产物。对照 design.md（原始要求）+ implementation.md（声称的实现）+ `git diff main...change/<id>` 验 PR。

## 输入

- **Design**：`.harness/changes/<id>/design.md`（reviewer 必读）
- **Implementation**：`.harness/changes/<id>/implementation.md`（reviewer 必读）
- **Git diff**：`git diff main...change/<id>`
- **PR**：<pr url 或 branch ref>

## AC 对照表

每条 AC 真去跑命令验证：

| AC | kind | reviewer 跑的命令 | 结果 | PASS/FAIL/NOT-VERIFIABLE |
|---|---|---|---|---|
| AC-1 | static | `grep -q "..." apps/api/...` | 0 / exit 0 | PASS |
| AC-2 | behavioral | `uv run pytest tests/test_x.py` | 2 passed | PASS |
| AC-N | ... | ... | ... | ... |

## 机械化检查日志

```text
$ bash scripts/_self_check.sh <change-id>
=== <change-id> :: N AC ===
... (粘 reviewer 自己跑的输出)

$ git diff --stat main...change/<change-id>
... 

$ curl <new-endpoint>（如适用）
... 
```

## 隐式偏离审计

> reviewer 对照 design.md vs implementation.md vs git diff，列出 implementation.md § 偏离 没声明但实际发生的偏离。**隐式偏离 = MUST FIX**。

- <无 / 列出>

## 问题列表

### MUST FIX

> Phase 3 reviewer 给 MAJOR ISSUE 时必含 MUST FIX；MINOR FIX 时一般不应有 MUST FIX，最多 SHOULD FIX；APPROVED 时为空。

- <无 / 列出>

### SHOULD FIX

> 建议合入前修但不阻塞 merge。MINOR FIX verdict 下的"待 sonnet 一轮修"内容写在这里。

- <无 / 列出>

### NICE TO HAVE

> 完全可选。可记入 follow-up change。

- <无 / 列出>

## Verdict

<APPROVED | MINOR FIX | MAJOR ISSUE>

- **APPROVED**：PR 兑现 design + 所有 AC PASS + 无隐式偏离 → merge to main + close change
- **MINOR FIX**：1-3 个小问题 → spawn sonnet 一轮修 → 直接 merge，**不再 spawn Phase 3 reviewer**
- **MAJOR ISSUE**：多个 AC 没兑现 / 实现与 design 严重偏离 / 引入回归 → 回 Phase 2 重做

## 后续指引

<具体下一步>
