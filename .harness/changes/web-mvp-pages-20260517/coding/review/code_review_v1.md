---
change_id: <feature-slug>-<yyyymmdd>
target: coding/<branch>
target_head: <head sha>
review_version: 1
reviewer: self-attest (template 占位符未填; 早期 change 部分 review 文件未填字段; 详见 harness-reviewer-agent-separation-20260518 §背景)
reviewed_at: <YYYY-MM-DDTHH:MM:SSZ>
verdict: REVISION REQUIRED
---

# Code Review v1

## 范围与作者声明对照

- coding_report 声明的改动文件：N 个
- `git diff --name-only main...HEAD` 实际：N 个
- 差异：_无 / 列出_

> 不一致 → MUST FIX。

## 正确性 / 安全 / 架构问题

### MUST FIX

| # | 文件:行 | 问题 | 建议 |
|---|---|---|---|
| 1 | _apps/api/dataplat_api/routers/repos.py:42_ | _未校验 owner == current_user_ | _在 service 层加权限检查_ |

### SHOULD FIX

| # | 文件:行 | 问题 | 建议 |
|---|---|---|---|

### NICE TO HAVE

| # | 文件:行 | 问题 | 建议 |
|---|---|---|---|

## 风格 / 性能 / 可观测性

> 引用 `.harness/rules/coding-style.md` 章节。

- _e.g. apps/api/.../service.py:88 — 异步函数里 sync IO，违反 §1.4_

## 跨改动观察

- _e.g. 多处使用相同 magic 字符串 "bronze"，建议提到 enum_（SHOULD FIX）

## Deferred SHOULD FIX

> 若 verdict = APPROVED 仍有未关闭 SHOULD FIX，必须在 summary.md 中列入 Deferred 表并标跟进位置。

## Verdict

REVISION REQUIRED / APPROVED

## 复检指引

作者修完后：

1. `uv run mypy apps/api/dataplat_api` → 0 errors
2. `uv run pytest apps/api -q` → all passed
3. `git diff main...HEAD -- apps/api/dataplat_api/routers/repos.py` 中 owner 权限检查已加入
4. 提交 v2 后开 `code_review_v2.md`，本文件保留作历史。
