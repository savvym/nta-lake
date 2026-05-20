---
change_id: web-jobs-list-page-20260520
target: tasks.md
target_version: 1
review_version: 1
reviewer: claude-agent:web-jobs-list-page-20260520-stage2-reviewer-v1
reviewed_at: 2026-05-20T05:00:00Z
verdict: REVISION REQUIRED
---

# Tasks Review v1

## 检查清单结论

| 条目 | 状态 | 说明 |
|---|---|---|
| 每个任务粒度合理（1-3 小时） | PASS | T-1~T-10 均单一职责，可在 1-3h 内完成 |
| depends_on 形成 DAG，没有循环 | PASS | DAG 图附在文末，无环，已验证 |
| 评审 / 单测 / CI 阶段对应任务都存在 | PASS | P-spec-review / P-code-review / P-test-review / P-ci / P-deploy / P-user-confirm 均在 process_tasks |
| 没有"做完整个系统"类目标性任务 | PASS | T-10 是验收性 gate task，但描述为"全跑一遍命令"，仍属机械化可执行范畴 |
| 验收覆盖映射完整 | PASS | AC-1~AC-10 全部映射 |

## 问题列表

### MUST FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| MUST FIX-1 | tasks.md T-3 description | **T-3 写 `@router.get("")`，但 spec AC-3 grep 只匹配 `@router.get("/")`**（含斜杠）。这是 spec MUST FIX-1 的直接对偶：task 与 spec 不一致，同样必须在 tasks v2 修正（与 spec v2 同步），否则编码 agent 可能选错实现。 | 与 spec 统一后，T-3 description 写明最终选定的 path 字符串（`""` 或 `"/"`）。 |

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| SHOULD FIX-1 | tasks.md T-4 description | T-4 用例列表写"可选：400 / type 过滤"，但 spec AC-8 明确要求 4 个子项 (a) admin list (b) user 403 (c) status 过滤 (d) limit/offset 分页。type 过滤 (可选) 与 spec AC-8 子项(d)描述一致，但 "400 bad request" 是 spec 风险缓解的关键行为，却被标 "可选"——实际若未测，400 逻辑完全可以不写。 | 将 "400 非法 status" 测试从"可选"升为"建议"；或在 spec AC-8 显式加"(e) invalid status → 400"子项，使 T-4 须 ≥5 用例。 |
| SHOULD FIX-2 | tasks.md T-2 description | T-2 签名写 `list_jobs(session, status, job_type, limit, offset)`，所有参数无 None 默认标注。实现时 `status: str | None = None` 和 `job_type: str | None = None` 是可选参数，建议 task 描述显式注明，避免编码 agent 实现为必填参数。 | 改为 `list_jobs(session, status: str | None, job_type: str | None, limit: int, offset: int)` |
| SHOULD FIX-3 | tasks.md T-5 depends_on | T-5 depends_on=[T-1]（正确），但 T-5 接口 `JobsListResponse { items, total, limit, offset }` 是在前端 TS 层定义的类型，不直接依赖后端 T-1 Python schema。依赖关系在逻辑上没错（后端 schema 先定），但建议在 T-5 description 加注"TS 层自定义接口，与后端 JobListResponse 字段对齐"，避免 agent 误以为需 codegen。 | 在 T-5 description 末尾加一句说明。 |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| NTH-1 | tasks.md T-9 description | T-9 只说"在 run_web_blob_md_image_resolver 后插入"，未说明 10 AC 的 grep 表达式骨架。编码 agent 实现时可能漏掉某些 AC（尤其 AC-7/AC-8 的 JSON reporter 解析逻辑）。 | 在 T-9 description 中列出 AC-7 / AC-8 命令摘要（已在 spec 有，引用即可）。 |
| NTH-2 | tasks.md DAG 图 | 注释"T-5 与 T-2/T-3/T-4 后端链可并行"——这是正确的，但 T-5 的 depends_on=[T-1]（而非 []），如果并发多 agent 执行，前端链 T-5→T-6→T-7/T-8 可以在 T-2/T-3/T-4 进行时同步跑。DAG 图可补一条并行注解使排期更清晰。 | 在 DAG 注释中加"T-2/T-3/T-4（后端链）与 T-5/T-6/T-7/T-8（前端链）可并行，汇于 T-9"。 |

## Verdict

**REVISION REQUIRED**

存在 1 个未关闭 MUST FIX：T-3 路由 path 与 spec AC-3 不一致（是 spec MUST FIX-1 的直接映射）。须与 spec v2 同步修正后重提评审。

tasks 整体结构清晰，DAG 无环，覆盖完整，非 MUST FIX 问题均为增强项。

## 后续指引

Generator 修 tasks v2 时：

1. MUST FIX-1：T-3 description 的路由 path 与 spec v2 AC-3 保持一致（统一选 `""` 或 `"/"`）
2. 建议同步处理 SHOULD FIX-1（T-4 "可选" → "建议"，或 spec AC-8 加 e 子项）
3. 修完后人工确认：
   ```bash
   # T-3 与 AC-3 的 path 字符串一致
   grep -A5 "id: T-3" .harness/changes/web-jobs-list-page-20260520/request_analysis/tasks.md
   grep "AC-3" .harness/changes/web-jobs-list-page-20260520/request_analysis/spec.md | grep "grep"
   ```
