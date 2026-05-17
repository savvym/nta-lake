---
change_id: processor-framework-20260517
version: 1
authored_at: 2026-05-17T18:50:00Z
status: waiting_review
---

# Test Report v1

## 验收项 ↔ 测试映射

| AC ID | 测试文件 | 测试函数 |
|---|---|---|
| AC-1 | apps/api/tests/test_processor.py | test_c_db_repo_view_open_roundtrip |
| AC-2 | apps/api/tests/test_processor.py | test_a_registry_register_get_list |
| AC-3 | apps/api/tests/test_processor.py | test_f_end_to_end_process_succeeded（间接：调 await ProcessorRunner.run） |
| AC-4 | apps/api/tests/test_processor.py | test_b_markdown_normalize_unit |
| AC-5 | apps/api/tests/test_processor.py | test_d_admin_process_returns_queued（间接：422 验证 extra=forbid） |
| AC-6 | apps/api/tests/test_processor.py | test_d_admin_process_returns_queued / test_e_user_process_returns_403 |
| AC-7 | apps/api/tests/test_processor.py | test_f_end_to_end_process_succeeded（间接：run_process_job 被 dequeue 跑） |
| AC-8 | apps/api/tests/test_processor.py | test_d_admin_process_returns_queued（间接：dispatch 后 job 进 RQ） |
| AC-9 | apps/api/tests/test_processor.py | test_c_db_repo_view_open_roundtrip（间接：StandardRunContext.blob_store 注入） |
| AC-10 | apps/api/tests/test_processor.py | 全部 8 个（满足 ≥ 8） |
| AC-11 | n/a | static check（ruff/mypy 在 self_check AC-11 跑） |
| AC-12 | n/a | static check（grep openapi.json 在 self_check AC-12 跑） |
| AC-13 | scripts/_self_check.sh | run_processor_framework / AC-13 自递归 |

## 测试文件清单

| 文件 | 类型 | 用例数 |
|---|---|---|
| apps/api/tests/test_processor.py | 集成（PG + MinIO + Redis + RQ + asyncio.run + thread） | 8 |

## Mock 范围声明

- 允许 mock：无（本测试不 mock）
- 禁止 mock：RepoService / BlobStore / RefService / ProcessorRunner / DbRepoView（按 coding-style §1.7 数据访问层禁 mock）

**本轮 mock 了**：无。所有 8 测试都打真 PG + 真 MinIO + 真 Redis；test_f 额外用 thread + 直接 dequeue + import call 绕开 RQ Worker 的 signal handler 限制（沿用 rq-worker-skeleton 同 trick）。

## 本地运行结果

```text
$ cd apps/api && DATAPLAT_DATABASE_URL=... DATAPLAT_REDIS_URL=... DATAPLAT_MINIO_ENDPOINT=... \
    uv run pytest -q tests/test_processor.py
........                                                                 [100%]
8 passed in 5.43s
```

## 已知 flaky / 跳过

- 无 skip。
- test_h 命名为 `test_h_source_ref_missing_marks_failed` 实际覆盖的是 "ref 名在 DB 中找不到" 路径（不是 "ref 存在但 commit 缺失"）。后者在 ProcessorRunner 中也会走 mark_failed，但 MVP 不单独测；列入 follow-up `processor-test-ref-commit-missing-*` 候选。

## 覆盖率

未配置 coverage 工具；本变更新增 5 个核心模块（registry / runner / repo_view / processors/markdown_normalize / routers/process / schemas/process）的关键路径都有至少 1 个集成测试覆盖。

## 下一步

进入阶段 6 单测评审，写 `test_review_v1.md`。
