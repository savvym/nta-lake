---
change_id: <feature-slug>-<yyyymmdd>
target: unit_test/test_report_v1.md
target_version: 1
review_version: 1
reviewer: <name 或 agent id>
reviewed_at: <YYYY-MM-DDTHH:MM:SSZ>
verdict: REVISION REQUIRED
---

# Test Review v1

## 检查清单结论

> 引用 `.harness/skills/expert-reviewer/SKILL.md` artifact 模式。

- [ ] 每条 spec AC 在映射表中至少出现一次。
- [ ] 没有空跑断言（`assert True` / `assert 1 == 1` / `pytest.skip` 滥用）。
- [ ] mock 范围与 `coding-style.md` §1.7 一致（数据访问层禁 mock）。
- [ ] 测试名能反映场景与期望。
- [ ] flaky / skip 已显式说明。

## 问题列表

### MUST FIX

| # | 文件:行 | 问题 | 建议 |
|---|---|---|---|
| 1 | _apps/api/tests/api/test_repos.py:88_ | _AC-2 的断言只检查 status code，未验证 blob 去重_ | _追加 `select count(*) from blobs` 断言_ |

### SHOULD FIX

| # | 文件:行 | 问题 | 建议 |
|---|---|---|---|

### NICE TO HAVE

| # | 文件:行 | 问题 | 建议 |
|---|---|---|---|

## Verdict

REVISION REQUIRED / APPROVED

## 复检指引

作者修完后：

1. `grep -E "assert\s+True|assert\s+1\s*==\s*1" apps/api/tests/` → 空。
2. 映射表每行的测试函数都能被 `pytest <文件>::<函数>` 单独跑通。
3. 每条 AC 的所有关联测试至少有一条断言**直接对应** AC 描述的期望。
4. 提交 v2 后开 `test_review_v2.md`。
