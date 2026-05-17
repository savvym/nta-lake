---
change_id: processor-framework-20260517
version: 1
env: dev
deployed_at: 2026-05-17T19:05:00Z
image_tag: working-tree（未打 image，dev 本地 uv run）
commit_sha: (will-be-filled-at-commit)
verifier: application-owner-agent
verdict: PASS
---

# Deploy Verification v1

> Dev 环境用 `uv run` 直接跑（无 Docker image）。验证通过 self_check + pytest 端到端 + API + worker 进程检查。

## 验证矩阵

| ID | 验收项 | 验证方式 | 期望 | 实际 | 备注 |
|---|---|---|---|---|---|
| AC-6 | POST /process 路由可达 | OpenAPI 含 /process | path 存在 | 存在 | self_check AC-6 PASS |
| AC-10 | 8 集成测试全 PASS（含端到端） | pytest test_processor.py | 8 passed | 8 passed in 5.43s | — |
| DEP-1 | API import 不报错 | `uv run python -c "from dataplat_api.main import app"` | 退出 0 | 退出 0 | — |
| DEP-2 | DB 迁移落地 | `alembic current` | head 0003_jobs | head 0003_jobs | rq-worker-skeleton 阶段已迁移 |
| DEP-3 | worker import 不报错（含 processors 自注册） | `uv run python -c "from dataplat_worker.main import main; import dataplat_api.processors"` | 退出 0 | 退出 0 | — |
| DEP-4 | ProcessorRegistry 在 worker 进程中可见 | self_check AC-2 | markdown-normalize 注册 | 注册 | — |
| DEP-5 | end-to-end 任务真跑 | test_f_end_to_end_process_succeeded | target ref 指向新 commit | 指向 | — |
| DEP-6 | 全仓 self_check 无回归 | self_check 全跑 | 173/173 PASS | 173/173 PASS | — |

## 证据

### DEP-1 / DEP-3

```text
$ cd apps/api && uv run python -c "from dataplat_api.main import app; print(len(app.routes))"
（无输出错误，正常退出）

$ uv run python -c "from dataplat_worker.main import main; import dataplat_api.processors; print('ok')"
ok
```

### DEP-5 端到端

```text
$ cd apps/api && DATAPLAT_DATABASE_URL=... DATAPLAT_REDIS_URL=... DATAPLAT_MINIO_ENDPOINT=... \
    uv run pytest -q tests/test_processor.py::test_f_end_to_end_process_succeeded -v
test_f_end_to_end_process_succeeded PASSED
1 passed
```

### DEP-6 self_check

```text
PASS: 173
FAIL: 0
SKIP: 0
全部通过（FAIL=0；SKIP 不阻塞）。
```

## 风险评估

- [ ] schema 不兼容？**否**。新增 ProcessRequest / ProcessResponse、StandardRunContext 加可选字段 blob_store（向后兼容；老 callers 不传也行——但本仓没老 callers）。
- [ ] 不可回滚操作？**否**。无 DB 迁移、无数据销毁、无外部副作用。
- [ ] 需要 follow-up？**是**。已在 coding_report / code_review 列出：worker-engine-pool / processor-cycle-detection / processor-iter-records / processor-parallel-map / processor-subprocess-isolation / processor-test-content-assert。

## Verdict

PASS。

## 处理动作

PASS → 进入阶段 10 用户确认 → close。
