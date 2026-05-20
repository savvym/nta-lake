---
change_id: platform-north-star-pivot-20260520
version: 1
authored_at: 2026-05-20T16:00:00Z
status: waiting_review
---

# Test Report v1

> 纯文档 / 治理 change，无业务代码，无 pytest / vitest 单测。"测试" = 跑 self_check AC block + 跑 lint 脚本，全 PASS = 文档结构正确。

## 验收项 ↔ 测试映射

| AC ID | kind | 测试方式 |
|---|---|---|
| AC-1 北极星节 | static | `bash scripts/_self_check.sh platform-north-star-pivot` → AC-1 PASS |
| AC-2 三层算子三子节 | static | 同上 AC-2 |
| AC-3 永不做清单 ≥ 7 条 | static | 同上 AC-3 |
| AC-4 stats-first reads/writes_stats | static | 同上 AC-4 |
| AC-5 行级血缘 source_ref/lineage_ops | static | 同上 AC-5 |
| AC-6 迁移路径 5 个 processor | static | 同上 AC-6 |
| AC-7 data-not-code-pivot.md | static | 同上 AC-7 |
| AC-8 CLAUDE.md 指针 | static | 同上 AC-8 |
| AC-9 lint 脚本 exit 0 | **behavioral** | `bash scripts/lint/check_design_north_star.sh` → exit 0 + "OK: design.md north-star structure complete" |
| AC-10 self_check 自递归 | static | 同上 AC-10 |

## 测试结果

```text
$ bash scripts/_self_check.sh platform-north-star-pivot
=== platform-north-star-pivot-20260520 :: 10 AC ===
PASS  AC-1   design.md 含 § 北极星 + 一句话定位 + ≥ 4 条硬约束 bullet
PASS  AC-2   design.md 三层算子节含 Adapter / Loader / Operator 三个子节 + Protocol 草图
PASS  AC-3   design.md § 永不做清单 ≥ 7 条粗体 bullet
PASS  AC-4   design.md § stats-first 含 reads_stats + writes_stats
PASS  AC-5   design.md § 行级血缘 含 source_ref + lineage_ops
PASS  AC-6   design.md § 迁移路径 涵盖 5 个 processor
PASS  AC-7   .harness/rules/data-not-code-pivot.md 存在 + 含 永不做 + 引用 design.md
PASS  AC-8   CLAUDE.md 含 北极星 + data-not-code-pivot
PASS  AC-9   lint 脚本 exit 0 + OK 字样
PASS  AC-10  self_check 含 run_platform_north_star_pivot ≥ 3 次

PASS: 10 / FAIL: 0 / SKIP: 0
全部通过

$ bash scripts/lint/check_design_north_star.sh
OK: design.md north-star structure complete
$ echo $?
0
```

## awk 边界情况防回归说明

stage 2 reviewer v1 抓到的 awk `/start/,/end/` 闭区间陷阱（start 行自身满足 end pattern 导致区间立即关闭），本 change 所有 awk 都改用 flag-based pattern：

```awk
# 不要：awk '/^## X/,/^## /' （X 行自身满足 /^## / 立即终止）
# 要：awk 'found && /^## /{exit} /^## X/{found=1} found' （X 行先设 flag 再检查）
```

边界情况已验证（fixture 在 reviewer v2 复审时测过 4 种）：
- X 是文件末尾的节
- X 含 `### ` 子级标题
- X 含 `#### ` 子子级标题
- X 是 `### Operator`（三级标题最后一个）

## 与上游 / 兄弟 change 的回归

- 不动业务代码：apps/api / apps/web / worker/src / packages/core 全部零改动
- 不动 21 个已闭环 change 的 spec.md / coding_report.md / summary.md（per spec § 范围 + § 非范围）
- self_check full 链应当无回归（其余 block 不变）

## 下一步

进入 stage 6 单测评审 + stage 4 编码评审：合并 spawn 一个 sonnet reviewer，写两份 review。
