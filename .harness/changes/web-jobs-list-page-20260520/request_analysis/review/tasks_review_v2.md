---
change_id: web-jobs-list-page-20260520
target: tasks.md
target_version: 2
review_version: 2
reviewer: claude-agent:web-jobs-list-page-20260520-stage2-reviewer-v2
reviewed_at: 2026-05-20T14:00:00Z
verdict: APPROVED
---

# Tasks Review v2

## v1 MUST FIX 复检

| # | v1 issue | 状态 | 证据 |
|---|---|---|---|
| MUST FIX-1 | T-3 写 `@router.get("")` 但 spec AC-3 grep 只匹配 `"/"` | **RESOLVED** | tasks v2 T-3 description 明确选定 `@router.get("", response_model=JobListResponse)`；spec v2 AC-3 grep 同步改为空字符串匹配；两者一致 |

## v1 SHOULD FIX 复检

| # | v1 issue | 状态 | 证据 |
|---|---|---|---|
| SHOULD FIX-1 | T-4 "400 非法 status" 被标"可选"，未能保证守门 | **RESOLVED** | tasks v2 T-4 用例 (e) 已改为必选，说明"≥ 5 全部必须"，400 白名单检查纳入必测范围 |
| SHOULD FIX-2 | T-2 签名缺少 `str \| None` 注解，编码 agent 可能实现为必填 | **NOT RESOLVED** | tasks v2 T-2 description 仍写 `list_jobs(session, status, job_type, limit, offset) -> tuple[items, total]`，无 `str \| None` 类型标注；与 SHOULD FIX-2 建议一致的修法未落地 |
| SHOULD FIX-3 | T-5 description 未注明 TS 层自定义接口（避免 agent 误以为需 codegen） | **NOT RESOLVED** | tasks v2 T-5 description 无对应说明；但因 v1 tasks_review 仅记录为 SHOULD FIX（非阻塞），不升为本轮 MUST FIX |

## 检查清单结论

| 条目 | 状态 | 说明 |
|---|---|---|
| 每个任务粒度合理（1-3 小时） | PASS | T-1~T-10 均单一职责，估时合理 |
| depends_on 形成 DAG，没有循环 | PASS | DAG 图无环，T-1→T-2→T-3→T-4；T-1→T-5→T-6→T-7/T-8；汇于 T-9→T-10 |
| 评审 / 单测 / CI 阶段对应任务都存在 | PASS | process_tasks 含 P-spec-review / P-code-review / P-test-review / P-push / P-ci / P-deploy / P-user-confirm |
| 没有"做完整个系统"类目标性任务 | PASS | T-10 为机械化验收 gate task |
| 验收覆盖映射完整 | PASS | AC-1~AC-10 全部有对应任务，AC 覆盖表完整 |

## 问题列表

### MUST FIX

无。

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| SHOULD FIX-1 | tasks.md T-2 description | v1 SHOULD FIX-2 未关闭：`list_jobs` 签名缺 `status: str \| None`、`job_type: str \| None` 类型标注，编码 agent 按 tasks 实现时可能把两者当必填参数，导致 router 层传 `None` 时服务层 TypeCheck 报错。 | 将签名改为 `list_jobs(session, status: str \| None, job_type: str \| None, limit: int, offset: int) -> tuple[list[JobORM], int]` |
| SHOULD FIX-2 | tasks.md T-5 description（v1 SHOULD FIX-3 延续） | T-5 定义 `JobsListResponse { items, total, limit, offset }` 为 TS 前端类型，但描述未说明"TS 层自定义接口，字段与后端 `JobListResponse` 对齐，无需 codegen"，编码 agent 可能误触发后端 schema 导出流程。 | 在 T-5 description 末尾加一句："`JobsListResponse` 为前端 TS 接口，手写与后端 `JobListResponse` 字段对齐；不依赖 codegen" |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| NTH-1 | tasks.md T-9 description（v1 NTH-1 未处理） | T-9 未列 AC-7 / AC-8 命令骨架引用，编码 agent 实现 self_check block 时易漏 JSON reporter 解析逻辑。 | 在 T-9 description 加"AC-7 / AC-8 完整命令见 spec AC-7/AC-8 节，直接引入 `run_web_jobs_list_page` block" |
| NTH-2 | tasks.md DAG 注释（v1 NTH-2 未处理） | 并行注解缺"T-2/T-3/T-4（后端链）与 T-5/T-6/T-7/T-8（前端链）可并行，汇于 T-9"，排期不直观。 | 在 DAG 注释行追加并行说明 |

## Verdict

**APPROVED**

v1 唯一 MUST FIX（T-3 路由 path 不一致）已正确修复，T-3 与 spec v2 AC-3 保持一致。

v1 SHOULD FIX-1（T-4 400 测试可选→必选）已修复。v1 SHOULD FIX-2（T-2 类型标注）和 SHOULD FIX-3（T-5 TS 接口说明）未关闭，延续为本轮 SHOULD FIX（非阻塞）。

tasks 整体结构清晰，DAG 无环，AC 覆盖完整，无新引入 MUST FIX，可进入下一阶段。

**注意**：spec v2 仍有 MUST FIX（AC-8 count ≥4 vs T-4 要求 ≥5 不一致），spec 须修为 v3 再确认后方可进入 coding 阶段。

## 后续指引

tasks APPROVED，但须等 spec v3 评审通过后方可联合推进 coding：

1. 若 Generator 修 tasks v3 处理 SHOULD FIX：
   - T-2 description 补全类型标注
   - T-5 description 末尾加 TS 接口说明

2. 自查命令：
   ```bash
   # 确认 T-2 签名含 str | None
   grep -A6 "id: T-2" .harness/changes/web-jobs-list-page-20260520/request_analysis/tasks.md | grep "str"
   # 确认 T-3 路由 path 与 spec AC-3 一致
   grep -A3 "id: T-3" .harness/changes/web-jobs-list-page-20260520/request_analysis/tasks.md | grep 'router.get'
   grep "AC-3" .harness/changes/web-jobs-list-page-20260520/request_analysis/spec.md | grep "grep"
   ```
