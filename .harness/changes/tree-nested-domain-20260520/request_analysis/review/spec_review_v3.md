---
change_id: tree-nested-domain-20260520
target: spec.md
target_version: 3
review_version: 3
reviewer: claude-agent:tree-nested-domain-20260520-stage2-reviewer-v3
reviewed_at: 2026-05-19T17:00:00Z
verdict: APPROVED
---

# Spec Review v3

## v2 MUST FIX 复检

| # | v2 MUST FIX 摘要 | v3 修法 | 状态 | 证据 |
|---|---|---|---|---|
| MUST FIX-1 | AC-6 验收表行"描述"列仍为"算法不变（grep 函数签名锚定）"，与 §范围已修正文本不一致 | v3 frontmatter revision_notes 明确"v3 同步表行"；AC-6 表行描述改为"_canonical_tree_bytes / _tree_hash 代码实现不改，entry_type 可为 'tree' 故 hash 输入空间扩大；dedup 仅 per-repo（TreeORM PK=(hash, repo_id)）" | **RESOLVED** | 命令 `grep "AC-6" spec.md | grep -v "算法不变"` 返回非空；验收表 AC-6 行（第 106 行）与 §范围 AC-6（第 72-73 行）措辞一致，"算法不变"字样已消除 |

---

## 检查清单结论

| 条目 | 状态 | 备注 |
|---|---|---|
| 背景写明了为什么现在做 | PASS | 痛点列表完整（3 类实测问题 + 起源 change 引用） |
| 问题陈述与目标可被外部读者理解 | PASS | 问题陈述精确到文件路径 + 函数 |
| 范围 / 非范围都有 | PASS | 14 条 AC 对应范围；非范围显式列出 9 条 |
| 验收标准每条都可演示且可机械化 | PASS | AC-6 表行已修正；所有 AC 均有可执行命令或 pytest 断言 |
| 风险有缓解措施或显式 accept | PASS | 风险表 8 行，每行有缓解或 accept 说明 |
| 没有把已有架构当新提案重复 | PASS | domain tree.py 现有支持有明确引用 |
| AC kind 列存在 | PASS | 验收表表头含 `kind` 列 |
| 至少 1 行 kind=behavioral | PASS | AC-9 / AC-10 / AC-11 / AC-13 共 4 条 behavioral |
| spec frontmatter ac_kind_lint: exempt | N/A | 未声明 exempt |

---

## 问题列表

### MUST FIX

无。

### SHOULD FIX（继承自 v2，未关闭）

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| SHOULD FIX-1 | spec.md 验收表 AC-5 验证命令（第 105 行） | `src.count('TreeORM(') >= 1` 只验证至少 1 次实例化，无法区分单 tree upsert（旧路径）与多 tree 循环 upsert（新路径） | 改断言为 `src.count('TreeORM(') >= 2` 或加 `assert 'all_trees' in src`；或将 AC-5 改为 behavioral（AC-11 的 test_dedup 用例可覆盖） |
| SHOULD FIX-2 | spec.md 验收表 AC-3 验证命令（第 103 行） | 验证命令仅 grep 函数名，不验证 7 类校验规则中任意一条是否被实现 | 改为 dry-import 运行时检查，至少测 `name=''` 和 `name='a/'` 两个边界 raise ValueError |
| SHOULD FIX-3 | spec.md 验收表 AC-14 描述列（第 114 行） | "AC-14 自递归"措辞无意义（v1/v2 SHOULD FIX 未关闭） | 改为"scripts/_self_check.sh 已注册 run_tree_nested_domain block（含本 change 14 条 AC 的 grep/pytest 命令）；self_check current 可独立运行" |

### NICE TO HAVE（继承自 v2，未关闭）

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| NTH-1 | spec.md §验收标准 AC-11 (f) | 路径校验测试用例 (f) 未列"trailing `/`、空白 segment" case（v2 新增但 AC-11 描述未同步） | AC-11 (f) 补"trailing `/`、空白 segment" case |
| NTH-2 | spec.md §风险 第 127 行 | 风险缓解写"reviewer 复核"——reviewer 无法在 spec review 阶段复核运行时行为 | 删除或改为"AC-9 behavioral test 覆盖" |

---

## Verdict

**APPROVED**

v2 唯一 MUST FIX（AC-6 表行描述与 §范围文本不一致）已在 v3 中完整修复：验收表 AC-6 行"描述"列从"算法不变（grep 函数签名锚定）"改为"代码实现不改，entry_type 可为 'tree' 故 hash 输入空间扩大；dedup 仅 per-repo（TreeORM PK=(hash, repo_id)）"，与 §范围 AC-6 文本语义一致，"算法不变"字样已消除。

遗留 SHOULD FIX 3 条 + NICE TO HAVE 2 条不阻塞通过，建议 generator 在 coding 阶段或 tasks 中一并处理 SHOULD FIX-1/2（AC-5/AC-3 验证命令偏弱），或在 summary.md 声明 deferred。

---

## 后续指引

APPROVED → 进入 stage 3（coding）：
1. generator 可开始实现 `schemas/tree.py` / `services/commit.py` / `routers/commits.py`
2. 建议在编码阶段同步处理 SHOULD FIX-1（AC-5 断言）与 SHOULD FIX-2（AC-3 边界验证命令）
3. stage 4 code review 时 SHOULD FIX-1/2/3 可作为复检项
