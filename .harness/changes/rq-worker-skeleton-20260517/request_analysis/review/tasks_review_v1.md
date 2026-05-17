---
change_id: rq-worker-skeleton-20260517
target: tasks.md
target_version: 1
review_version: 1
reviewer: claude-stage2-reviewer
reviewed_at: 2026-05-17T14:10:00Z
verdict: APPROVED
---

# Tasks Review v1

## 检查清单结论

> 引用 `.harness/skills/expert-reviewer/SKILL.md` §1（plan/tasks）+ SKILL `.harness/skills/request-analysis/SKILL.md` §跨 AC 一致性自审清单第 7 条。

- [x] 每个任务粒度合理（1-3 小时）。T-1~T-10 实现任务各自单一职责（ORM / deps / redis_client / service / tasks.py / schemas+router / worker main / tests / self_check / lint），无 "做完整个系统" 类条目。
- [x] depends_on 形成 DAG，无循环。reviewer 手画依赖图核对：
  - T-1, T-2 独立根节点
  - T-3 ← T-2；T-4 ← T-1, T-3；T-5 ← T-1, T-3, T-4；T-7 ← T-2
  - T-6 ← T-4, T-5；T-8 ← T-1~T-7；T-9 ← T-1~T-8；T-10 ← T-9
  - T-11~T-16 process 链顺序串接
  - 无回边。
- [x] 评审 / 单测 / CI / 部署阶段对应任务都存在（T-11 stage-2 / T-12 stage-4 / T-13 stage-6 / T-14 stage-7 / T-15 stage-9 / T-16 stage-10）。
- [x] 没有 "做完整个系统" 类目标任务。
- [x] 每条 AC 都有非 process_tasks 任务覆盖（AC 覆盖矩阵 L150-L165 列全 13 条，与 reviewer 复核一致）。

机械化复核：

```text
grep -cE "estimated_stage: stage-(2|4|6|7|9|10)" tasks.md → 6
# SKILL 第 7 条 process_tasks 6 条必填 PASS
```

AC ↔ Task 覆盖逐条核对（reviewer 实跑）：

| AC | tasks.md 声明 | 实际任务体确认 |
|---|---|---|
| AC-1 | T-1 | T-1 L11-L13 含 JobORM + alembic 0003 |
| AC-2 | T-1 | T-1 L13 显式列 `alembic/versions/0003_jobs_table.py` |
| AC-3 | T-2, T-3 | T-2 加 rq/redis 依赖；T-3 redis_client 单例 + queue helper |
| AC-4 | T-4 | T-4 列 5 个 JobsService 方法 + DELETE-on-enqueue-fail |
| AC-5 | T-5 | T-5 列 run_ingest_job + asyncio.run + 7 步内部流程 |
| AC-6 | T-6 | T-6 L60-L62 列 JobIngestRequest + JobRead extra=forbid |
| AC-7 | T-6 | T-6 L63-L66 列 router 2 路由 + admin + require login + 404 |
| AC-8 | T-6 | T-6 L67 列 main.py include + make codegen |
| AC-9 | T-6 | T-6 L65 显式 "_resolve_repo" 复用 RepoService.get_by_owner_name |
| AC-10 | T-7 | T-7 列 worker/main.py + Worker(['default']).work() |
| AC-11 | T-8 | T-8 列 10 测试 (a)~(j) 全对应 |
| AC-12 | T-2, T-10 | T-2 sync 安装 + T-10 ruff/mypy gate |
| AC-13 | T-9 | T-9 self_check 13 AC block + filter |

无孤立 AC，无目标性任务。

## 问题列表

### MUST FIX

无。

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | tasks.md L42-L55（T-5）步骤 1 | 写 "新建独立 async engine + session（不依赖 FastAPI lifecycle）"，但**没说明禁止 `from dataplat_api.db import engine`**。RQ 默认 Worker fork 模式下，全局 engine 的 asyncpg 连接池跨进程共享会导致 stale conn / event-loop closed。SimpleWorker 同进程测试无法暴露。 | T-5 步骤 1 追加："禁止 import `dataplat_api.db.engine` / `AsyncSessionLocal` 全局对象；改为 `from dataplat_api.db import _database_url` + 局部 `create_async_engine(url, poolclass=NullPool)` 自建。Phase 2 follow-up `worker-fork-safety-*` 引入 RQ before_fork hook 时再统一回收。" 同步 spec.md 风险 #1 缓解段（spec review SHOULD FIX-5）。 |
| 2 | tasks.md L78-L90（T-8） | 测试 (a)~(j) 描述了行为，但**没声明 Redis 测试 db 隔离 fixture**。AC-11 跑在 `DATAPLAT_REDIS_URL=redis://localhost:6379/0` 默认值时，与 conftest 其他 fixture / 生产 worker 共用 db 0 → 队列残留 + key 冲突。 | T-8 fixture 段追加："`@pytest.fixture(scope='session', autouse=True)` 设 `os.environ['DATAPLAT_REDIS_URL'] = 'redis://localhost:6379/15'` 并在 teardown 调 `r.flushdb()`；或用 unique queue 前缀（`Queue(f'test-{uuid.uuid4()}', ...)`）。" |
| 3 | tasks.md L97-L100（T-10 lint+mypy gate） | T-10 depends_on T-9，但 lint 应在 T-1~T-7 实现任意阶段就能跑（不需要等 self_check）。当前依赖链强制开发者写完 self_check 才能跑 lint，反馈环偏长。 | 把 T-10 depends_on 改为 `T-1~T-8`（不依赖 T-9），让 lint 与 self_check 可以并行。覆盖矩阵不变。 |
| 4 | tasks.md L102-L106（T-11 stage-2 review） | depends_on 写 "T-1~T-10 v1 完"——但 stage-2 review 评审的是 spec.md + tasks.md，**不依赖任何实现任务**。当前写法把 stage-2 review 拖到所有代码写完之后，与十阶段流程定义 "stage-2 在 stage-3 之前" 矛盾。 | T-11 depends_on 改为空数组（或仅依赖 spec/tasks v1 完成的状态标记）。实测：reviewer 本人正在 stage-2 评审，此时 T-1~T-10 未实施。 |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | tasks.md L93-L95（T-9 self_check） | "Redis 探针 helper（_redis_reachable）" 一句话带过——没说明探针 fallback 行为（unreachable → SKIP 还是 FAIL）。 | T-9 追加："`_redis_reachable` 复用 `_pg_reachable` 形态：socket connect timeout=1，失败 → SKIP（不 FAIL）。三探针组合 AC：PG ∧ MinIO ∧ Redis 任一不可达整组 SKIP。" |
| 2 | tasks.md L140-L146（任务依赖图 ASCII） | 文本图有错位：T-7 后面是注释空格 + 接 T-6，视觉上像悬挂。 | 用 Mermaid graph LR 或重画 ASCII：把 T-7 和 T-5 都画到 T-6 入边。或干脆删掉图依靠覆盖矩阵 + depends_on 字段已经足够。 |
| 3 | tasks.md L107-L111（T-12 stage-4 coding review） | depends_on `T-1~T-10` 但应在实现 PR 写好之后（实际是 stage-3 输出 working-tree diff），现在的 depends_on 没区分 "实现产物" 与 "实现任务" 状态。 | 改为 `depends_on: T-10`（lint+mypy 通过即 stage-3 出口条件），表达上更清晰。 |

## Verdict

APPROVED（MUST FIX 数 = 0）

SHOULD FIX 4 条均不阻塞 stage-3 进入，但作者**应在 spec_v2 / tasks_v2 一并处理**（SHOULD FIX-1/-2 与 spec review SHOULD FIX-4/-5 耦合）。流程 process_tasks 完整、AC 覆盖完整、依赖 DAG 无环——核心质量门禁达成。

特别说明：本评审与 spec 评审是**并列**关系（同 stage-2 同时给出），spec_review_v1 verdict = REVISION REQUIRED 因此整个 stage-2 仍需作者修 spec_v2 → 重 stage-2 评审；本 tasks_review APPROVED 意味着 tasks.md **本身**可不动，但作者应顺手把上述 4 条 SHOULD FIX 在 tasks_v2 一并优化（与 spec 联动）。

## 复检指引

作者修完 tasks_v2.md 后：

1. **依赖 DAG 校验**：
   ```bash
   # 提取所有 depends_on 行做拓扑排序，无环即 PASS
   grep -E "^- depends_on:" tasks.md
   ```

2. **process_tasks 6 条必填**：
   ```bash
   grep -cE "estimated_stage: stage-(2|4|6|7|9|10)" tasks.md
   # 期望 6
   ```

3. **AC 覆盖矩阵**：
   ```bash
   # 每条 AC-N 至少一处 task 引用
   for n in $(seq 1 13); do
     echo -n "AC-$n: "
     grep -c "AC-$n\b" tasks.md
   done
   # 期望全部 ≥ 1
   ```

4. **SHOULD FIX-3 / -4 依赖修复后**：T-10 depends_on 不再包含 T-9；T-11 depends_on 不再包含 T-1~T-10。重画 / 删除依赖图 ASCII。

5. **SHOULD FIX-1 / -2 修复后**：grep 自查：
   ```bash
   grep -nE "_database_url|NullPool" tasks.md       # 期望 T-5 步骤 1 命中
   grep -nE "redis://localhost:6379/15|flushdb|test-\{uuid" tasks.md  # 期望 T-8 fixture 命中
   ```

提交 v2 后开 `tasks_review_v2.md`，target_version=2 / review_version=1。
