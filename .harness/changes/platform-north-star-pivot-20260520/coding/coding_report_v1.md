---
change_id: platform-north-star-pivot-20260520
version: 1
authored_at: 2026-05-20T16:00:00Z
branch: change/platform-north-star-pivot-20260520
base_commit: b14e16f
head_commit: WIP（stage 7 push 后回填）
status: waiting_review
---

# Coding Report v1

## 改动文件清单

| 路径 | 类型 | 说明 | 关联 task |
|---|---|---|---|
| `.harness/design.md` | edit | 顶部插入 6 个新顶层节（§ 北极星 / § 三层算子模型 含 Adapter/Loader/Operator 三级子节 / § stats-first 设计 / § 行级血缘 / § 永不做清单 / § 迁移路径 / § 与业界的关系）；版本号 v0.2 → v0.3；老 § 1-4 加 deprecated quote 块（不动二级标题文字以保 anchor 不变） | T-1, T-2, T-3, T-4, T-5, T-6, T-7 |
| `.harness/rules/data-not-code-pivot.md` | new | 永不做清单 + 旧→新术语对照表 + reviewer 必查项 + 松绑流程 + 历史 | T-8 |
| `CLAUDE.md` | edit | 关键文件导航新增"理解平台北极星"指针；硬性约束新增第 6 条引用 data-not-code-pivot.md | T-9 |
| `scripts/lint/check_design_north_star.sh` | new | bash lint：验证 design.md 6 个顶层节 + 三级子节 + Protocol 草图存在；flag-based awk 避坑；gawk `sub` builtin 冲突修正 | T-10 |
| `scripts/_self_check.sh` | edit | 新增 `run_platform_north_star_pivot` 10 AC block + dispatcher case + full 链插入位置在 run_web_jobs_list_page 与 run_harness_ac_behavioral_tier 之间 | T-11 |

> **门禁**：`git diff --name-only main...HEAD` 应等于上表（5 个文件），不多不少。

## 与 tasks.md 的映射

| Task | 状态 | 备注 |
|---|---|---|
| T-1 § 北极星 | done | 一句话定位 + 4 条硬约束 + 6 条反边界 |
| T-2 § 三层算子模型 | done | Adapter/Loader/Operator 三个子节 + 每个 Protocol 草图 + 例子 + Recipe 新形态 |
| T-3 § stats-first / § 行级血缘 | done | 两节独立写，AC-4 / AC-5 分别覆盖 |
| T-4 § 永不做清单 | done | 9 条 bullet（超过 AC-3 要求的 ≥7）+ 用户想要 X 时往哪指 |
| T-5 § 迁移路径 | done | 5 行 processor 重分类表 + 迁移策略 |
| T-6 § 与业界的关系 | done | 7 行对照表 + 一段总结"为什么不直接用 data-juicer" |
| T-7 老章节标 deprecated | done | § 1/§ 2/§ 3/§ 4 顶部加 `> ⚠ Deprecated 设计（v1）` quote 块；二级标题文字不动以保留 markdown 自动 anchor |
| T-8 data-not-code-pivot.md | done | 完整 rule 文件含 5 节 |
| T-9 CLAUDE.md | done | 表加 1 行 + 约束加第 6 条 |
| T-10 lint 脚本 | done | gawk `sub` builtin 冲突修正 (`sub` → `subname`)；6 节 + 3 子节验证 |
| T-11 self_check block | done | 10 AC + dispatcher + full 链 |
| T-12 跑 self_check | done | 10/10 PASS（详 test_report） |

## 偏离 spec / trade-off

| # | 偏离 | 原因 | 评审请关注 |
|---|---|---|---|
| D-1 | T-7 deprecated 标记用 `> ⚠ Deprecated` quote 块而非 `<details>` 折叠 | quote 在 GitHub / vscode preview 都渲染良好；折叠对 grep / awk 处理透明；保留 markdown 自动 anchor（spec R-5 方案） | 是否接受 quote 块形态 |
| D-2 | T-7 仅加 4 个 deprecated 块（§ 1/2/3/4），不覆盖 § 5-11 | § 5-11 是 storage architecture / observability 等基础设施章节，**与北极星 pivot 无冲突**，无需标 deprecated | 是否同意 |
| D-3 | gawk `sub` 是 builtin 触发 fatal | 改用 `subname` 变量名 | 已修，不影响 AC-9 |
| D-4 | self_check AC 的 bash -c 字符串内 `awk` 用双引号 escape，跟 _self_check.sh 其他 block 的单引号风格略不一致 | bash -c 内部 `$()` + `$(awk ...)` 嵌套必须用双引号才能展开 `\$` | 风格 NTH，行为正确 |

## 本地校验结果

```text
bash scripts/_self_check.sh platform-north-star-pivot  → 10 PASS / 0 FAIL
bash scripts/lint/check_design_north_star.sh           → exit 0 + "OK: design.md north-star structure complete"
grep -c "^## " .harness/design.md                       → 18（原 11 + 新 7）
git diff --stat main...HEAD                             → 5 files changed
```

## 已知未解决问题

- 无业务代码改动，不存在编译 / 单测回归。
- spec 提到 3 条 SHOULD FIX（v2 reviewer）—— locale 漂移 / R-5/R-6 未传导到 T-5/T-7/T-8 task description / T-8 reviewer checklist 子节归属。这些都是文档层面的 NTH，不阻塞本 change；已在 data-not-code-pivot.md § reviewer 必查项 落地相关条目（涵盖 R-6 (c) "reviewer 必查 v2 词汇"）。

## 下一步

进入 stage 4 编码评审 + stage 6 单测评审（合并 spawn 一个 sonnet reviewer）。
