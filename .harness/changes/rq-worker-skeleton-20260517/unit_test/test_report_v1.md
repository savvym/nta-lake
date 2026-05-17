---
change_id: rq-worker-skeleton-20260517
version: 1
authored_at: 2026-05-17T14:50:00Z
status: waiting_review
---

# Test Report v1

## AC ↔ 测试映射

| AC | 测试 |
|---|---|
| AC-1~5 | self_check AC-1~5 |
| AC-6 | self_check AC-6 + tests 隐式（JobIngestRequest 提交） |
| AC-7~9 | self_check AC-7~9 |
| AC-10 | self_check AC-10（worker/main.py grep） |
| AC-11 | self_check AC-11 + `test_jobs.py` 10 测试（含 g 端到端 succeeded、h parent 链、i 异常 failed、j 幂等 dedup） |
| AC-12 | self_check AC-12（ruff + mypy） |
| AC-13 | self_check AC-13 |

## 测试清单

| 文件 | 用例数 |
|---|---|
| `apps/api/tests/test_jobs.py` | 10（a~j）|
| `scripts/_self_check.sh` rq-worker-skeleton | 13 |

**总：10 + 13 = 23 断言**

## Mock 范围

- **无 mock**：直连 PG + MinIO + Redis
- 唯一变形：测试用 thread + 直接 dequeue 取代 SimpleWorker（绕开 signal handler 限制）；本质仍调真 task 函数
- `app.dependency_overrides[get_blob_store]` 注入 per-test bucket；同时 monkeypatch worker 端 singleton + env 让两者指向同 bucket

## 本地运行结果

```text
pytest -q apps/api/tests/test_jobs.py → 10 passed in 6.83s
pytest -q apps/api/tests/ → 74 passed in ~30s（无回归）
ruff/mypy → clean
self_check rq-worker-skeleton → 13/13 PASS
self_check 全仓 → 134/134 PASS（10 个 block）
```

## 已知 flaky

- 无 flaky；Redis 队列在 fixture 中 `queue.empty()` 清空避免跨测试污染

## reviewer 重点

1. (g) 端到端 succeeded 是否真断言 commit_hash 存在 + len(64) ？
2. (h) parent 链 C2.parents=[C1.hash] 真断言 ？
3. (i) 用 unknown adapter 触发 worker 异常 → status=failed 真覆盖
4. (j) 两次 enqueue → result.deduplicated 第二次 true 真覆盖（commit-api-mvp 幂等链路）
