---
change_id: processor-framework-20260517
version: 1
authored_at: 2026-05-17T18:30:00Z
branch: main
base_commit: 02d21cc (repo-files-tab close)
head_commit: working-tree
status: waiting_review
---

# Coding Report v1

## 改动文件清单

| 路径 | 类型 | 说明 | 关联 task |
|---|---|---|---|
| `packages/core/src/dataplat_core/protocols/processor.py` | edit | 补 `RepoView` Protocol + `ProcessContext.blob_store / repo_view` 字段 | T-1 |
| `apps/api/dataplat_api/runner/processor_registry.py` | new | `ProcessorRegistry` + `get_processor_registry()` 单例（沿 AdapterRegistry 同构） | T-2 |
| `apps/api/dataplat_api/runner/processor_runner.py` | new | `ProcessorRunner.run` async：open source → process → CAS write → tree build → commit → update target ref | T-2 |
| `apps/api/dataplat_api/runner/repo_view.py` | new | `DbRepoView` 实现 RepoView Protocol（DB + BlobStore read-through） | T-2 |
| `apps/api/dataplat_api/runner/runcontext.py` | edit | `StandardRunContext` 加 `blob_store` 字段 | T-2 |
| `apps/api/dataplat_api/runner/__init__.py` | edit | export `ProcessorRegistry/ProcessorRunner/DbRepoView/get_processor_registry` | T-2 |
| `apps/api/dataplat_api/processors/__init__.py` | new | import 触发自注册 | T-3 |
| `apps/api/dataplat_api/processors/markdown_normalize.py` | new | `MarkdownNormalizeProcessor` id=markdown-normalize v=0.1；CRLF→LF + 行尾 trailing ws 去除 | T-3 |
| `apps/api/dataplat_api/schemas/process.py` | new | `ProcessRequest / ProcessResponse`（extra=forbid） | T-4 |
| `apps/api/dataplat_api/routers/process.py` | new | `POST /process`（admin only）→ `JobsService.enqueue(job_type="process", ...)` → 202 | T-4 |
| `apps/api/dataplat_api/main.py` | edit | include `process_router` | T-4 |
| `apps/api/dataplat_api/jobs/tasks.py` | edit | 新 `run_process_job(job_id)` sync-RQ 入口（asyncio.run + 独立 engine + ProcessorRunner.run + swallow → mark_failed） | T-5 |
| `apps/api/dataplat_api/jobs/service.py` | edit | `enqueue` 按 `job_type` dispatch（ingest → run_ingest_job；process → run_process_job） | T-5 |
| `apps/api/tests/test_processor.py` | new | 8 集成测试覆盖 registry / unit / repo_view / 路由权限 / 端到端 / 错误分支 | T-6 |
| `packages/api-types/openapi.json` | edit | codegen 同步（含 `/process` path） | T-7 |
| `packages/api-types/src/generated.ts` | edit | codegen 同步 | T-7 |
| `scripts/_self_check.sh` | edit | 追加 `run_processor_framework` 13 AC + filter + 总入口 | T-8 |

## 与 tasks.md 的映射

| Task | 状态 | 备注 |
|---|---|---|
| T-1 协议增 RepoView + ProcessContext | done | |
| T-2 runner 三件套 + runcontext blob_store | done | |
| T-3 markdown-normalize | done | |
| T-4 schema + router + main include | done | |
| T-5 jobs dispatch + run_process_job | done | |
| T-6 test_processor.py 8 测试 | done（全 PASS） | |
| T-7 codegen + lint + type | done（ruff fix 1 处 import 排序 + mypy 76 files 0 errors） | |
| T-8 self_check 注册 | done（13/13；全仓 173/173） | |

## 偏离 spec / trade-off

- **AC-1 自审补强**：spec 原始 AC-1 仅 `grep -q "class DbRepoView"`，无法区分"文件缺失"与"类缺失"。在 _self_check.sh 注册时主动补 `test -f apps/api/dataplat_api/runner/repo_view.py &&` 前置（reverse-grep checklist 第 6 条）。spec v1 不动，本次以 spec_review_v1.md SHOULD FIX 形式记录。
- **AC-8 用双正向 grep**：service.py 必须同时含 `run_process_job` 与 `run_ingest_job`（dispatch 必要条件），比单 grep 更强；spec 原命令是 `grep -qE "run_process_job|run_ingest_job"` 即"任一即可"，本实现是"两者皆需"，比 spec 更严格。
- **Test_h 命名**：`test_h_source_ref_missing_marks_failed` 实际验证的是 ref 名在 DB 中查不到（不是 ref 存在但 commit 缺失）；属 tasks_review NICE TO HAVE 的范围，已在 test_report 注明。

## 本地校验

```text
ruff: All checks passed!（自动 fix 1 处 test_processor.py I001 import 排序）
mypy: Success: no issues found in 76 source files
pytest test_processor.py: 8 PASS (5.43s)
self_check processor-framework: PASS=13 / FAIL=0 / SKIP=0
self_check 全仓: PASS=173 / FAIL=0 / SKIP=0
```

## 已知未解决问题

- **cycle detection**：source_ref == target_ref 时 ProcessorRunner 允许跑（CAS 保证内容不变 → commit hash 也不变 → 实际为空操作）。spec 显式 deferred 到 follow-up `processor-cycle-detection-*`。
- **iter_records / parallel map / subprocess 隔离**：均在 Out of scope；待 `processor-iter-records-*` / `processor-parallel-map-*` / `processor-subprocess-isolation-*` follow-up。

## 下一步

进入阶段 4 编码评审，写 `code_review_v1.md`。
