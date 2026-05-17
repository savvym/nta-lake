---
change_id: rq-worker-skeleton-20260517
target: spec.md
target_version: 1
review_version: 1
reviewer: claude-stage2-reviewer
reviewed_at: 2026-05-17T14:10:00Z
verdict: REVISION REQUIRED
---

# Spec Review v1

## 检查清单结论

> 引用 `.harness/skills/expert-reviewer/SKILL.md` §1（plan/spec）+ `.harness/skills/request-analysis/SKILL.md` §跨 AC 一致性自审清单。

- [x] 背景写明了为什么现在做（spec.md L10-L12 引 design.md §5.3 + §9 Phase 1 #5）。
- [x] 问题陈述对外部读者可理解（L14-L19，4 条同步阻塞痛点）。
- [x] 范围 / 非范围都有（L22-L40，in/out 列举清楚）。
- [ ] 每条验收标准可演示且可机械化（AC-4 一行式语法**不可执行**，详 MUST FIX-1）。
- [x] 风险有缓解或显式 accept（L99-L110，6 条风险全配缓解或 follow-up）。
- [x] 没有把已有架构当新提案（仅引 design.md §5.3 + §9 Phase 1 #5）。
- [x] 待澄清问题已清零（无遗留澄清项）。

### SKILL 7 条 checklist 第三次回归生效情况（commit-api-mvp + adapter-framework 反哺后）

| # | 检查项 | 状态 | 备注 |
|---|---|---|---|
| 1 | 四链路（hash / schema / idempotency / fixture）一致 | N/A | 本变更不引入新 hash 算法；payload→worker→AdapterRunner 直链复用 commit-api 既有 hash |
| 2 | 事务边界声明 AC + 风险 + tasks 三处一字不差 | PASS | spec 风险 #1 + 决策表 + tasks T-5 步骤均明示 "worker 内独立 async engine + session"，无矛盾 |
| 3 | AC 验证命令一行式可执行 | **FAIL** | AC-4 用 `for m in [...]: assert ...` 在 `python -c` 单语句不可解析（MUST FIX-1） |
| 4 | 风险 ↔ AC 测试号映射 | PARTIAL | 风险 #2 显式引 AC-11 (g)(h)(i)(j)；其余风险（#3/#4/#5）未点对应 AC 编号（SHOULD FIX-1） |
| 5 | commit 历史链连续性 | PASS | 风险 #6 + 决策表 + AC-11 (h) 复用 commit-api 的 ref 接链；无裸 `parents=[]` 写法 |
| 6 | 反向 grep 配 `test -f` + 不吞 stderr | PASS | AC-9（spec.md L73）配 `test -f` 两个前置 + 正向 grep + 反向 grep，未写 `2>/dev/null`；模板严格遵循 |
| 7 | process_tasks 6 条（stage-2/4/6/7/9/10） | PASS | tasks.md 列 T-11~T-16 各对应一阶段；grep 计数 = 6 |

机械化复跑结果（reviewer 实跑 spec.md L126-L133 自审 grep）：

```text
grep -nE "事务前|事务内|事务外" spec.md     → L127 仅自审说明行
grep -nE "parents=\[\]" spec.md            → L110 仅自审说明行（无裸代码示例）
grep -nE "! *grep" spec.md                 → L73 AC-9 1 处（配 test -f）
grep -nE "2>/dev/null" spec.md             → L130 仅自审说明行
grep -cE "estimated_stage: stage-(2|4|6|7|9|10)" tasks.md → 6
grep -cE "test -f|cd apps/api|grep -q|uv run python" spec.md → 13
```

reviewer 额外环境核验：

```text
cd apps/api && uv run alembic heads → "0002 (head)"
→ spec.md L101 "alembic 0003 down_revision=0002" 正确
```

## 问题列表

### MUST FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | spec.md L56（AC-4 验证命令） | `python -c "from ... import JobsService; for m in [...]: assert hasattr(JobsService, m), m"` 在 Python 中**语法非法**——`for ... :` 复合语句不可跟在 `;` 后作为单语句。reviewer 实跑 `uv run python -c "..."` 命中 `SyntaxError: invalid syntax`，AC-4 在 stage-7 self_check 跑时会直接 FAIL，**不是缺测试而是命令本身错的**。这是 SKILL §跨 AC 一致性自审清单第 3 条 "一行式可执行" 的直接违反。 | 改为生成器表达式：`python -c "from dataplat_api.jobs.service import JobsService; assert all(hasattr(JobsService, m) for m in ['enqueue','get_by_id','mark_running','mark_succeeded','mark_failed'])"`。reviewer 已验证该形态可执行（用 stub class 实测 PASS）。同时在 spec.md L132 "grep 期望 ≥ 12" 自审命令旁追加一项 "AC 验证命令真跑得过" 自查，避免下个变更重犯。 |

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | spec.md L101-L103（风险 #3 / #4 / #5） | 风险 #2 已显式引 AC 编号（AC-11 (g)(h)(i)(j)），但 #3 alembic / #4 Redis-auth / #5 payload-Pydantic-revalidate 三条缓解只描述了机制，未点对应 AC 或 follow-up id。违反 SKILL 跨 AC 第 4 条 "每条风险若声称有测试覆盖作为缓解，必须在 AC 测试列表里列出对应测试编号"。 | 风险 #3 末追加 "见 AC-2"；#5 末追加 "见 AC-11 (g)/(j) 路径"；#4 显式标 "follow-up `redis-auth-tls-*` accept，无 MVP 测试覆盖"。 |
| 2 | spec.md L52（AC-3 验证命令） | 仅检查 `callable(get_redis) and callable(get_queue)`——不会触碰 Redis 真实连通性。Redis 探针在 AC-13 自检里有，但 AC-3 本身仅 import 通过即过，无法暴露 "环境变量名拼错 / 默认 URL 拼错" 这类问题。 | 追加 `os.environ.pop('DATAPLAT_REDIS_URL', None); assert get_redis() is get_redis()`（单例语义）+ 一条对默认 URL 的断言。或在 AC-13 自检块明示 "AC-3 复用 redis 探针"。 |
| 3 | spec.md L66 + L120（AC-7 + 决策表 "Job 读权限：任何登录可读"） | MVP 把 GET /jobs/{job_id} 开放给任何登录用户，但 JobORM.payload 内含 IngestRequest（含 spec content + 文件 sha256 列表）+ result 含 commit_hash。这意味着**任意 logged-in user 可读 admin enqueue 的任意 repo 的 ingest 详情**——即便他对该 repo 无 visibility 权限。风险已被决策表显式标 "ACL 留 follow-up"，但 spec 没把这条信息暴露到风险清单与 out-of-scope，下游 reviewer / 实现者容易漏知 payload 反查问题。 | 风险段加 #7：「GET /jobs/{job_id} MVP 任何登录可读 payload+result——绕过 repo visibility；follow-up `job-acl-*` 明示」；out-of-scope 段加同名 follow-up。**或者** AC-7 收紧为 "admin only read" 等 follow-up 上线；二选一。reviewer 倾向前者，因为 MVP 内部用户场景可接受，但显式声明可避免后期补做的成本变高。 |
| 4 | spec.md L29 + AC-10 默认 Redis URL `redis://localhost:6379/0` | 测试与生产共用 db 0。MVP 没有生产 worker 拉起时不冲突，但 stage-7 self_check 跑测试时会把 SimpleWorker 提交的 job 写到与未来生产 worker 同一 namespace。AC-11 (j) "二次 enqueue" 测试若残留到 db 0，跨变更跑会污染。 | 在风险段补一条 "follow-up `worker-redis-isolation-*`：生产 worker 用 db 1 / queue name = `prod`；测试 fixture 用 db 15 + unique queue 前缀"。或 AC-11 fixture 段显式注 "测试覆盖 `DATAPLAT_REDIS_URL=redis://localhost:6379/15`，避免与默认值冲突"。spec 现在对此沉默。 |
| 5 | spec.md L99（风险 #1）+ tasks.md L47-L48 | "worker 在 task 内新建独立 async engine + session" 是缓解，但 RQ 默认 Worker 在 fork 模式下，**worker 父进程**若已 import 任何包含 `dataplat_api.db` 的模块（例如 RQ task 自动导入 `dataplat_api.jobs.tasks`，间接拉起 `dataplat_api.db`），fork 时全局 `engine` 对象的 asyncpg 连接会被共享 → 子进程跑 `asyncio.run` 时可能复用 stale connection。SimpleWorker 同进程不 fork 所以测试通过，但生产 Worker 跑时会潜伏。 | 风险 #1 缓解措施补充："任务函数内必须 `from dataplat_api.db import _database_url; create_async_engine(_database_url(), ...)` 自建 engine **而不是 import 全局 engine**；follow-up `worker-fork-safety-*` 在 Phase 2 落子进程级 engine 重建钩子（如 RQ Worker `setup_worker_signals` / `before_fork` callback）。" tasks.md T-5 步骤 1 已写 "新建独立 async engine"，但 spec 风险段没把"禁止 import 全局 engine" 这条规则点透。 |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | spec.md L76（AC-10 grep） | `grep -qE "Worker|work\("` 模式过宽——`Worker` 单字会被 `# rq Worker` 注释命中，`work(` 会被 `network(...)` / `homework(...)` 误匹配。无 MUST FIX 级风险因为 MVP main 文件简洁，但 grep 健壮性差。 | 改为 `grep -qE "rq\.Worker|Worker\s*\(\s*\[" worker/src/dataplat_worker/main.py`，强约束 RQ 命名空间或位置参数模式。 |
| 2 | spec.md L88（AC-11 (h)） | "二次 ingest 同 ref → 第二次 commit.parents=[第一次 commit_hash]" 但本变更 GET /jobs/{id} 只返 result.commit_hash，**不返 parents**——测试只能从 commit_hash 拉 commits API 二次断言。spec 没说明这条联动。 | AC-11 (h) 改为 "二次 ingest 同 ref → 取 job.result.commit_hash → `GET /repos/{o}/{n}/commits/{h}` 返 parents=[first_commit_hash]"，让测试路径清晰。 |
| 3 | spec.md L90（AC-11 (j) 幂等） | "二次 enqueue → 两个 job 各自跑 → 第二次 result.deduplicated=true" 这是 commit-level dedup 透传到 result，不是 job-level dedup。"幂等" 措辞会让人误以为 second enqueue 被去重。 | 改为 "commit 去重透传：二次 enqueue 跑出两个独立 job，但第二个 job result.deduplicated=true（commit_hash 与首个相同），证明 worker 复用了 adapter 既有 commit 路径"。 |
| 4 | spec.md L122-L123（决策表 "任务执行模型 in-process MVP"） | 决策表行 1 + 行 2 + 行 7 都隐含 in-process + asyncio.run + 独立 session，**且互相耦合**——但没有显式标注 "若任一改动，另两个需联动评估"。 | 决策表末加一条注解："1 / 2 / 7 三行耦合：subprocess 隔离 / sync worker / 共享 session 任一选项变更将影响另两行；follow-up `adapter-subprocess-isolation-*` 需同步评估。" |

## Verdict

REVISION REQUIRED（MUST FIX 数 = 1）

唯一 MUST FIX：AC-4 验证命令 Python `SyntaxError`。SHOULD FIX 5 条均不阻塞通过，但下一版应明示是否接受 / 修补。SKILL 7 条 checklist 6/7 通过，仅 #3（一行式可执行）因 AC-4 实测 FAIL。

## 复检指引

作者修完 spec_v2.md 后：

1. **机械化复跑 MUST FIX-1 修复**：
   ```bash
   # 修复后应 PASS（无输出表示 assert 通过）
   cd apps/api && uv run python -c "from dataplat_api.jobs.service import JobsService; assert all(hasattr(JobsService, m) for m in ['enqueue','get_by_id','mark_running','mark_succeeded','mark_failed'])"
   ```
   注：此命令需 T-4 实现完成；spec stage 阶段只验证**命令本身语法可解析**，建议作者额外跑：
   ```bash
   python -c "class X: pass; assert all(hasattr(X, m) for m in ['__class__'])"
   # 上行应输出空 / 无 SyntaxError
   ```

2. **SKILL 7 条 checklist 自审第三次重跑（spec.md 末尾）全部应保持 PASS**：
   ```bash
   cd .harness/changes/rq-worker-skeleton-20260517/request_analysis
   grep -nE "事务前|事务内|事务外" spec.md          # 期望仅自审注释行
   grep -nE "parents=\[\]" spec.md                  # 期望仅自审注释行
   grep -nE "! *grep" spec.md                       # 期望 AC-9 1 处（带 test -f）
   grep -nE "2>/dev/null" spec.md                   # 期望仅自审注释行
   grep -cE "estimated_stage: stage-(2|4|6|7|9|10)" tasks.md  # 期望 6
   grep -cE "test -f|cd apps/api|grep -q|uv run python" spec.md  # 期望 ≥ 12
   ```

3. **SHOULD FIX 处理记录**：每条 SHOULD FIX 在 spec_v2.md 末追加 "## v2 evaluation against v1 review" 区块说明 accept / defer / reject 与理由，便于 v2 reviewer 快速核对。

4. **AC 验证命令真跑预检（防再次 SyntaxError）**：spec.md 末尾自审段加一行：
   ```bash
   # 对每条带 `python -c` 的 AC 验证命令做一次 dry-parse：
   for line in $(grep -oE 'python -c "[^"]+"' spec.md); do
     # 去掉外引号后用 python -c 跑 → 若 SyntaxError 立刻暴露
     ...
   done
   ```

提交 v2 后开 `spec_review_v2.md`，target_version=2 / review_version=1。
