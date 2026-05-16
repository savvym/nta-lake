---
change_id: core-domain-model-20260516
target: tasks.md
target_version: 1
review_version: 2
reviewer: claude-agent:core-domain-model-stage2-reviewer
reviewed_at: 2026-05-16T21:45:28Z
verdict: APPROVED
---

# Tasks Review v2

> 评审基准：用户在 v1 反馈中**就地修改** tasks.md（version 字段仍为 1，文件内容上无 diff——见 v1 关闭情况说明）。

## v1 MUST FIX 关闭情况

| v1 # | 状态 | 复检证据 |
|---|---|---|
| 1 T-1 Subtype 三方契约漂移 | ✅ CLOSED | T-1 description 文字"Subtype Literal 拆 Bronze/Silver/Gold"与 spec AC-2 v2 选择的"分层 Subtype Literal（BronzeSubtype/SilverSubtype/GoldSubtype）"用同一术语；联合阅读 T-1 + spec AC-2，实施者能清楚知道按 spec AC-2 落字面值；用户在反馈中显式承诺"T-1 description 已含 Subtype Literal 拆 Bronze/Silver/Gold，与 spec v2 一致即可"——契约可一致解读，可接受 |
| 2 AC-8 import 集合不全 | ✅ CLOSED | spec AC-8 命令补全为 8 个 import（SourceAdapter / IngestResult / Processor / ProcessResult / RepoView / RepoSelector / RepoSpec / RunContext）；`grep -oE "(SourceAdapter\|...)" spec.md tasks.md \| sort -u` 两侧集合完全一致 |

## SHOULD FIX / NICE TO HAVE 状态（v1 沿留）

> 用户在反馈中**仅承诺修复 MUST FIX**，未表态 SHOULD FIX；Reviewer 不强制阻塞，但记账提醒。

| v1 # | 类别 | 状态 |
|---|---|---|
| SHOULD FIX 1 | T-7 commits.lineage_json vs Pydantic `lineage` 字段命名分歧 | **未修**（tasks.md 未改），建议 stage 3 编码前在 T-7 description 显式 |
| SHOULD FIX 2 | T-9 index/FK 未列具体清单 | **未修**，建议在 stage 3 编码前补 description |
| SHOULD FIX 3 | T-6/T-8 alembic env.py 与 `models/__init__.py` re-export 关系未显式 | **未修**，stage 3 实施踩坑高风险 |
| SHOULD FIX 4 | P-spec-review / P-code-review / P-test-review 缺 reason 字段 | **未修**（process_tasks 仍 P-spec-review / P-code-review / P-test-review 三项无 reason），上一变更评审反馈未沉淀 |
| SHOULD FIX 5 | AC 覆盖矩阵 AC-13/15 关联任务不充分 | **未修** |
| SHOULD FIX 6 | T-11 测试隔离与并发清理策略未定 | **未修** |
| NICE TO HAVE 1-4 | 矩阵双列 / T-10 映射 / P-deploy summary / T-12 SKIP 语义 | **未修** |

## DAG 与覆盖矩阵实测

- 拓扑排序仍成功，无环（与 v1 同）。
- AC 覆盖矩阵每条 AC ≥ 1 个 T-*，名义 17/17。
- process_tasks 7 项覆盖 stage 2-10。

## 风险评估补充

- T-3 description 含 8 个类型（3 Protocol + 5 数据类），时间预估应 > 90 min；建议 stage 3 实施时拆 T-3a（adapter.py + IngestResult）/ T-3b（processor.py + ProcessResult + RepoView + RepoSelector + RepoSpec）/ T-3c（runcontext.py）三个子提交。
- 其余风险同 v1 review。

## Verdict

APPROVED（MUST FIX 数 = 0）

> 说明：tasks v2 MUST FIX 全部消化（T-1 与 spec AC-2 用词一致；AC-8 ↔ T-3 import 集合一致）。SHOULD FIX 用户未承诺修复——Reviewer 不阻塞 verdict，但**强烈建议**在 summary §Deferred 项显式登记 SHOULD FIX 1-6 的延后理由，否则 stage 3 编码评审会重新提出（特别是 SHOULD FIX 3 alembic env.py 与 `models/__init__.py` re-export 是高发踩坑点）。
>
> **本 verdict 不依赖 spec v2 的状态**——但需注意：spec v2 仍有 1 条 MUST FIX（AC-2 双 cd），见 `spec_review_v2.md`。stage 2 整体进入 stage 3 的判据是 **spec 与 tasks 两份 verdict 同时为 APPROVED**，按 `.harness/rules/development-process.md` 阶段间硬约束（CLAUDE.md §硬性约束 #3）spec 未 APPROVED 前**不得进入 stage 3**。

## 复检指引

无需 v3（tasks 已 APPROVED）。但 Generator 进入 stage 3 前建议：

1. 在 summary §Deferred 项追加 SHOULD FIX 1-6 的延后理由（或择优在 v3 一并修），保留追溯链。
2. SHOULD FIX 3（alembic env.py + models/__init__.py re-export）作为 T-6/T-8 编码 checklist 显式 carry，避免 stage 4 评审重提。
3. spec v3 落地后，本 tasks APPROVED 验定生效，进入 stage 3。
