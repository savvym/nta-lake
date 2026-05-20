---
change_id: web-blob-md-image-resolver-20260520
target: request_analysis/tasks.md
target_version: 2
review_version: 2
reviewer: claude-agent:web-blob-md-image-resolver-20260520-stage2-reviewer-v2
reviewed_at: 2026-05-20T15:00:00Z
verdict: APPROVED
---

# Tasks Review v2

## v1 MUST FIX 复检

| # | v1 issue | 状态 | 证据 |
|---|---|---|---|
| MUST FIX-1 | T-4 粒度过大（三合一：ReactMarkdown 替换 + resolveRelative + CustomImage） | RESOLVED | v2 拆为 T-4a（ReactMarkdown 切换）→ T-4b（resolveRelative + 路径辅助函数）→ T-4c（CustomImage + hook 集成），串行 DAG；每段 covers_ac 独立；验收覆盖矩阵同步更新 |

## 检查清单结论

| 项 | 结论 | 备注 |
|---|---|---|
| 每个任务粒度合理（1-3 小时） | PASS | T-4a ≈ 30min，T-4b ≈ 45min，T-4c ≈ 90min，其余均单一职责 |
| depends_on 形成 DAG，没有循环 | PASS | T-1→T-2→T-3→T-4a→T-4b→T-4c→T-5→T-6→T-7 线性无环；DAG 小节亦声明 |
| 评审 / 单测 / CI 阶段对应任务都存在 | PASS | process_tasks 7 个 P-* 节点完整 |
| 没有"做完整个系统"类目标性任务 | PASS | 拆分后每 task 单一职责 |
| 验收覆盖矩阵完整 | PASS | AC-1~9 全有对应；AC-4→T-4a，AC-5→T-4b+T-4c，矩阵已更新 |

## 问题列表

### MUST FIX

无。

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| SHOULD FIX-1 | tasks.md T-4a description | "不动 renderMinimalMarkdown 函数定义（避免 typescript dead code 警告，标记 @deprecated 暂留供 follow-up 清；**或直删——选直删**）" 措辞自相矛盾：前半句说"不动"，后半句明确选择"直删"。coding agent 可能按"不动"实现导致 dead code 留存，也可能按"直删"实现，行为不确定 | 删除矛盾前半句，改为明确单一指令："直接删除 renderMinimalMarkdown 函数定义（和调用点），不保留 @deprecated 占位" |
| SHOULD FIX-2 | tasks.md T-4b depends_on: [T-4a] | T-4b 只实现 `isAbsoluteUrl` / `resolveRelative` / `resolveImagePath` / `splitDirAndBasename` 等纯辅助函数，与 T-4a（ReactMarkdown 替换）没有代码依赖；depends_on [T-4a] 是人工序列化，延长了可并行开发的关键路径。注：线性 DAG 保留有其简化管理的好处，但 description 未说明序列化原因 | 在 T-4b description 加注"depends_on T-4a 为简化 DAG 管理，实为纯函数无耦合；如并行开发可独立实现后 merge"；或将 depends_on 改为 `[]`（T-4c depends_on [T-4a, T-4b]），并在 DAG 节更新 |
| SHOULD FIX-3 | tasks.md T-5 description | v1 SHOULD FIX-2 指出 mock 结构描述过简（缺 TreeRead 格式示例），v2 仍未修复：T-5 仍只写"mock useSubtreeByPath 返 images/a.jpg entry"，没有 `{ hash, entries: [{ name, mode, entry_type, target_hash }] }` 格式示例。coding agent 可能 mock 成直接返 entry 对象而非 TreeRead，导致组件内 `.entries.find(...)` 抛 TypeError | 在 T-5 description 补充 mock 格式示例："useSubtreeByPath mock 返回值结构：`{ hash: 'aaaa...', entries: [{ name: 'a.jpg', mode: 33188, entry_type: 'blob', target_hash: '<64hex>' }] }`，与 queries.ts TreeRead 接口一致" |
| SHOULD FIX-4 | tasks.md T-5 description | v1 NICE-1 建议将"可选"的 d 用例（`md_nested_md_relative_path`，对应风险表"nested 目录路径错 → 高概率"）提升为 required，v2 未采纳且无 deferred 记录。该场景（papers/2026/a.md 引用 papers/2026/images/*.jpg）被 spec 风险表标为高概率。optional 用例在 AC-6 数量门禁（≥6）满足后极可能被 coding agent 跳过 | 将 d 用例从"可选"改为 required（AC-6 则相应可选升为 ≥7）；或在 tasks T-5 description 加注"d 为 recommended，跳过时在 coding_report 说明" |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| NICE-1 | tasks.md T-6 | T-6 description 仍未列出 9 条 AC 的具体 grep 命令（v1 NICE-2 未修）。generator 需手写 self_check AC block，容易与 spec.md 验收表不一致 | T-6 description 补充"AC 验证命令与 spec.md 验收标准表完全一致；逐条复制，避免自行改写" |
| NICE-2 | tasks.md T-4c description | 说明 hooks rules（无论分支都无条件调用）已正确，但没有提示 coding agent 如何通过 Vitest 验证 hook 不被条件调用（通常需要在测试里 spy / assert 调用次数）。该细节影响 T-5 的测试质量 | 可在 T-4c description 加注："测试中确认 useSubtreeByPath 始终被调用（不受 commit 缺 / entry-miss 条件绕过）" |

## Verdict

**APPROVED**

v1 唯一 MUST FIX（T-4 粒度过大）已核实关闭：T-4 正确拆为 T-4a/T-4b/T-4c 三段串行任务，职责独立，DAG 无环，验收覆盖矩阵同步更新。

v2 无新 MUST FIX。4 条 SHOULD FIX（其中 2 条来自 v1 SHOULD FIX/NICE 未追加）不阻塞进入 coding。建议 generator 在执行 T-4a 前修 SHOULD FIX-1（矛盾措辞），执行 T-5 前修 SHOULD FIX-3（mock 格式示例），否则风险落到 coding agent 自由发挥。

## 后续指引

APPROVED → 可配合 spec_review_v2 APPROVED，进入 stage 3 coding。建议 coding agent 在 coding_report 里对各 SHOULD FIX deferred 的条目注明 deferred 原因。
