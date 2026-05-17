---
change_id: adapter-framework-20260517
target: tasks.md
target_version: 1
review_version: 1
reviewer: claude-stage2-reviewer
reviewed_at: 2026-05-17T11:10:00Z
verdict: REVISION REQUIRED
---

# Tasks Review v1

## 检查清单结论

> 引用 `.harness/skills/expert-reviewer/SKILL.md` §1 tasks 部分。

- [x] 每个任务粒度合理（T-1~T-9 均 1-3 小时；最重的 T-8 拆成 12 测试，每条独立约 15 分钟）。
- [x] depends_on 无环（DAG 在 line 113-120 显式画出：T-1/T-2/T-3 并行 → T-4 / T-5 → T-6 → T-7 → T-8 → T-9）。
- [ ] 包含评审 / 单测 / CI 阶段对应任务——**未显式列出 process_tasks**（stage-2 spec review / stage-4 code review / stage-6 test review / stage-7 CI / stage-9 deploy / stage-10 user-confirm）；详见 MUST FIX #1。
- [x] 没有 "做完整个系统" 类目标任务（T-1~T-9 每个都钉死具体文件 / 函数）。
- [ ] 每条 AC 都有非 process_tasks 任务覆盖——AC-12（ruff + mypy）**没有任何 T-* 任务挂钩**；详见 MUST FIX #2。

## 问题列表

### MUST FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | tasks.md 全文 line 1-120（缺章节） | **process_tasks 完整性不达标**。SKILL `expert-reviewer` §1 tasks 部分要求"评审 / 单测 / CI 阶段对应任务都存在"，但 tasks.md 只列 T-1~T-9 的实现任务，**缺**：(a) stage-2 spec review 任务（虽然 review 文件已存在，但作为流程节点需挂任务以便 summary.md 串联）；(b) stage-4 coding review 任务；(c) stage-6 unit-test review 任务；(d) stage-7 CI 验证任务（T-9 是 self_check 不是 CI gate）；(e) stage-9 deploy-verify 任务（即便部署是 noop 也要显式 task）；(f) stage-10 user-confirm 任务。复现命令：`grep -cE "estimated_stage: stage-(2\|4\|6\|7\|9\|10)" .harness/changes/adapter-framework-20260517/request_analysis/tasks.md` 命中 0 行。对比已 closed 的 `commit-api-mvp-20260517/request_analysis/tasks.md` 看是否也缺；若也缺则属系统性遗漏，需在本变更补齐**并**反哺 SKILL | 在 T-9 之后追加 T-10~T-15：T-10 spec-review（estimated_stage: stage-2, depends_on: T-1~T-9 出 v1）；T-11 code-review（estimated_stage: stage-4, depends_on: T-7）；T-12 test-review（estimated_stage: stage-6, depends_on: T-8）；T-13 CI（estimated_stage: stage-7, depends_on: T-12）；T-14 deploy-verify（estimated_stage: stage-9, depends_on: T-13）；T-15 user-confirm（estimated_stage: stage-10, depends_on: T-14）。同时在依赖图末尾延展该串行段 |
| 2 | tasks.md line 1-120（AC-12 无主） | **AC-12（`uv run ruff check` + `uv run mypy` 全 PASS）没有任何 T-* 任务声明 AC 覆盖**。`grep "AC-12" tasks.md` 实测命中 0 行。后果：coding agent 实现完 T-1~T-7 后若 mypy fail，由谁修复 / 在哪个 task 内修复无契约约束——会被推到 stage-4 review 才发现，回退成本高 | 任选其一：(a) 在 T-7（OpenAPI codegen）合并加 "运行 ruff + mypy 全仓库通过"，AC 覆盖加 AC-12；或 (b) 新增 T-7.5 / T-7b "lint + type 闭环"，独立列出。后者更清晰。同时检查 `grep -nE "^- AC 覆盖:" tasks.md` 把每条 AC 至少绑到一个 T-*，覆盖矩阵无孤儿 |

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | tasks.md line 64 (T-5 step 7) | 签名漂移：`返 (commit, dedup, result)（注：方法签名调整为 3-tuple 或把 dedup 嵌入 commit；选 3-tuple 更显式）`——但 spec AC-4 line 70 写 `返 (commit, result)`（2-tuple）。**spec 与 tasks 在返回值元组上互相矛盾**，coding agent 拿不准实现。这是 commit-api-mvp 反哺 checklist 的"措辞一字不差"原则在 tasks vs spec 跨文档版本上的失效证据 | 选 3-tuple（与 CommitService `(CommitORM, bool)` 同构），把 spec AC-4 step 7 同步改为 `(commit, dedup, result)`；T-6 line 78 已隐式假设有 dedup 字段（构造 IngestResponse 时需要），所以 3-tuple 更连贯 |
| 2 | tasks.md line 14 (T-1) | T-1 描述加字段未提 `Field` import：`IngestResult.files: list[IngestFileRef] = Field(default_factory=list)`。当前 `packages/core/src/dataplat_core/protocols/adapter.py` 只 import `BaseModel, ConfigDict`，未 import `Field`——coding agent 漏 import 会报 NameError | 在 T-1 第 1 个 bullet 后加："同时在 `from pydantic import ...` 行追加 `Field`" |
| 3 | tasks.md line 75 (T-6 schemas/__init__.py 导出) | T-6 说 "更新 `schemas/__init__.py` export 3 个新类型"，但**没有同步要求**在 `packages/core/.../protocols/__init__.py` 导出 `IngestFileRef`（spec AC-1 line 54 暗示由 `from dataplat_core.protocols.adapter import ... IngestFileRef` 直接 import，但 spec line 14 of T-1 已说"更新 protocols/__init__.py 导出 IngestFileRef"）。**重复声明位于 T-1 而非 T-6 是对的，但 spec 风险 #1 又只提"既有字段保留"未提"导出表新增"**——读者要在 3 处对照才能拼齐 | 把 T-1 line 14 的"更新 protocols/__init__.py" 改为子 bullet 明确："新增 `IngestFileRef` 到 `__all__` 数组"，同时 T-6 加一条交叉检查："验证 `from dataplat_core.protocols import IngestFileRef` 不报错" |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | tasks.md line 117 (依赖图) | 依赖图 ASCII 把 T-1 画了两次（一次进 T-4，一次进 T-5），可读性略差；T-5 也依赖 T-2 / T-3，图中只画 T-1 → T-5 漏了 | 用单一根节点 fanout：`T-1, T-2, T-3 ──┬──→ T-4 ──┐` ` ──┴──→ T-5 ──→ T-6 ...`；或改用 mermaid graph |
| 2 | tasks.md line 96 (T-8 探针) | 测试 fixture 抄自 `test_commits.py` 但没明确列出**复用具体函数 / class** 名（`_override_blob_store`、`admin_user` 等）。coding agent 可能在 conftest 重复实现 | T-8 第 2 bullet 加："优先 import 自 `apps/api/tests/conftest.py` 已有 fixtures（`admin_user_client`, `normal_user_client`, `override_blob_store`），未提供的再本地新增" |

## Verdict

REVISION REQUIRED（MUST FIX = 2）

## 复检指引

作者修完 tasks_v2.md 后**自查**：

1. **MUST FIX #1 闭合**：
   - `grep -cE "estimated_stage: stage-(2|4|6|7|9|10)" tasks.md` 命中 ≥ 6
   - 依赖图末段含 T-10 → T-11 → ... → T-15 串行链
   - 每个 process_tasks 任务 owner 字段或 description 标明 "由 reviewer / CI agent / human 完成"
2. **MUST FIX #2 闭合**：
   - `grep "AC 覆盖:.*AC-12" tasks.md` 命中 ≥ 1
   - 覆盖矩阵自查：列出 AC-1~AC-13 每条对应的 T-* 编号，无孤儿
3. **SHOULD FIX #1 联动**：spec_v2.md AC-4 step 7 与 tasks_v2.md T-5 step 7 互相 grep 验证返回值元组一致（2-tuple vs 3-tuple 二选一统一）
4. **DAG 校验**：人工沿依赖箭头跑一遍无环；任意单条任务删除后剩余图仍可拓扑排序
5. **SKILL 反哺**：MUST FIX #1 揭示"process_tasks 完整性"在 commit-api-mvp 是否同问题。**reviewer 已注意此模式可能系统性遗漏**——建议提交 v2 前快速 `grep -L "estimated_stage: stage-(2|4|6|7|9|10)" .harness/changes/*/request_analysis/tasks.md` 全仓查证；若同模式遍布，则反哺 `request-analysis/SKILL.md` § 步骤 5 加一条 "process_tasks 6 条必填" 强约束

提交 tasks_v2.md 后开 `tasks_review_v2.md`。

## 评审实跑证据

- `grep -cE "estimated_stage: stage-(2|4|6|7|9|10)" .harness/changes/adapter-framework-20260517/request_analysis/tasks.md` → 0（确认 MUST FIX #1）
- `grep "AC-12" .harness/changes/adapter-framework-20260517/request_analysis/tasks.md` → 0 命中（确认 MUST FIX #2）
- `grep -nE "tuple|return" .harness/changes/adapter-framework-20260517/request_analysis/tasks.md` line 56 `tuple[CommitORM, IngestResult]` vs line 64 `(commit, dedup, result)` 与 spec.md line 63 `tuple[CommitORM, IngestResult]` 三处签名不一致（SHOULD FIX #1 证据）
- DAG 手工拓扑排序：`T-1, T-2, T-3 → T-4 → T-5 → T-6 → T-7 → T-8 → T-9` 无环
