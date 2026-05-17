---
change_id: adapter-framework-20260517
target: spec.md
target_version: 1
review_version: 1
reviewer: claude-stage2-reviewer
reviewed_at: 2026-05-17T11:10:00Z
verdict: REVISION REQUIRED
---

# Spec Review v1

## 检查清单结论

> 引用 `.harness/skills/expert-reviewer/SKILL.md` §1（plan 模式 spec.md）+ `.harness/skills/request-analysis/SKILL.md` § 跨 AC 一致性自审清单。

- [x] 背景写明了为什么现在做（第 10-14 行：Phase 1 #2 仍 0%）。
- [x] 问题陈述对外部读者可理解（第 16-21 行 4 条诊断清晰）。
- [x] 范围 / 非范围都有（第 24-48 行；out-of-scope 9 条均挂 follow-up）。
- [ ] 每条验收标准可演示且可机械化——AC-9 反 grep 命令存在**沉默通过**漏洞（详见 MUST FIX #2，复跑实测确认 vacuous PASS）。
- [ ] 风险有缓解或显式 accept——commit parents 链断裂语义未识别为风险也未 accept（详见 MUST FIX #1）。
- [x] 没有把已有架构当新提案——SourceAdapter Protocol / CommitService 均明确标"已有，本变更不动"。
- [x] 待澄清问题段已清零（spec 没有该段，且范围内问题均决策完成）。

### 跨 AC 一致性自审清单回归（commit-api-mvp 反哺）

> 本次是反哺 checklist 后的**第一次正式回归**。结论：**checklist 部分生效，部分失效**——下文 MUST FIX #1 是 checklist 失效的典型证据，必须把该模式补回 SKILL。

| checklist 条目 | 本 spec 表现 | 评价 |
|---|---|---|
| 1. 四链路一致（schema ↔ hash 输入 ↔ idempotency key ↔ test fixture） | spec line 27 / AC-1 / AC-4 (step 4) / AC-5 / T-5 step 4 沿 `path → IngestFileRef.path = TreeEntryCreate.name`、`IngestFileRef.sha256 = TreeEntryCreate.target_hash`；ingest 幂等显式声明等于 CommitService canonical hash 幂等。**链路一致** | 生效 |
| 2. 事务边界声明 AC ↔ 风险 ↔ tasks 一字不差 | 本变更未引入新事务（沿用 CommitService）；spec §风险 #6 b 显式声明此点；AC / tasks 不出现"事务前/事务内/事务外"措辞。**一致** | 生效 |
| 3. AC 验证命令一行式可执行 | `grep -cE` 实测返 10 / 13 AC ≈ 77%。**达标**；但其中**至少 1 条（AC-9）形式合法但语义沉默通过**——checklist 漏抓 | **部分失效**：见 MUST FIX #2 |
| 4. 风险缓解 ↔ AC 测试列表 | 风险 #1 / #2 / #4 显式引到 AC-11 (b) / (a) / runner-design；#3 / #5 标 follow-up 而非 AC 覆盖；**OK** | 生效 |
| 隐式条目：commit 历史链（parents）连续性 | spec line 67 / T-5 step 4 写死 `parents=[]`；AC-6 `IngestRequest` 无 parents 字段；AC-11 无"两次 ingest 形成父子链"测试 | **失效**：见 MUST FIX #1 |

**结论**：checklist 的 4 条原始条目对 hash/事务/AC 命令/风险×测试都起到了约束作用（spec generator 此次未踩 commit-api-mvp 的字段集不一致 / 事务边界互斥坑），但**漏了"语义级 commit 历史连续性"和"反向 grep 文件不存在时沉默通过"**两个模式。建议把这两条作为 5th / 6th 条目补回 `request-analysis/SKILL.md`（见复检指引）。

## 问题列表

### MUST FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | spec.md line 67 (AC-4 step 4) + line 82 (AC-6 IngestRequest) + line 102-114 (AC-11 测试矩阵) | **ingest 永远创建 orphan commit，断裂 commit 历史链**。AC-4 step 4 / T-5 step 4 写死 `parents=[]`，且 `IngestRequest` 无 `parents` 字段。后果：repo 上已存在 `main → C1` 后，二次 ingest 创建独立的 C2（parents=[]）并通过 ref upsert 把 `main` 移到 C2——**C1 从 `main` 可达路径丢失**，违反 design.md §4.4 类 Git 模型（"Commit 是有向链"）。AC-11 (h) `test_h_ingest_with_ref_upserts` 只测 ref 是否被 upsert，不测父子关系。复现命令：`grep -nE "parents=\[\]" .harness/changes/adapter-framework-20260517/request_analysis/{spec.md,tasks.md}` 命中 2 处且 spec 无任何 accept/follow-up 说明 | 二选一：(a) 在 `IngestRequest` 加 `parents: list[SHA256] = Field(default_factory=list)`，由 client 显式传 parent（与 `CommitCreate.parents` 同构）；或 (b) Runner 内部读 `request.ref` 当前指向的 commit_hash 作为 parent（更符合"自动 commit"语义）。同时在 AC-11 加一条 `test_m_second_ingest_to_same_ref_creates_child`：第二次 ingest 后 `commit.parents == [first_commit.hash]`，且 `GET /commits/{first}` 仍可达。**若 MVP 确决定接受 orphan 语义**，必须在风险段加 #7 "ingest 创建 orphan commit，历史链由 client 用 `POST /commits` 手工延续" 并显式标 accept |
| 2 | spec.md line 92 (AC-9 验证命令) | **AC-9 反向 grep 沉默通过**（false positive vacuous PASS）。命令 `! grep -E "_visibility_visible" apps/api/dataplat_api/runner/ apps/api/dataplat_api/routers/ingest.py apps/api/dataplat_api/adapters/ -r 2>/dev/null` 在 T-1~T-6 完成**前**复跑——目录 / 文件全部不存在，grep 退码 2，`2>/dev/null` 吞掉 stderr，`!` 取反后退码 0 → AC-9 在零代码状态下"通过"。这正是 `[harness_lint_followup_memory]` 5 次预警的同型 bug（第 6 次证据），且 commit-api-mvp 反哺的 checklist 第 3 条"AC 验证命令一行式"漏抓此模式。复现命令：`bash -c '! grep -E "_visibility_visible" apps/api/dataplat_api/runner/ apps/api/dataplat_api/routers/ingest.py apps/api/dataplat_api/adapters/ -r 2>/dev/null; echo "exit=$?"'`（当前仓库实测 exit=0） | 把 AC-9 验证改为**正向断言** + **路径存在性前置**，例如：`test -f apps/api/dataplat_api/routers/ingest.py && grep -q "_resolve_repo\|RepoService.get_by_owner_name" apps/api/dataplat_api/routers/ingest.py && ! grep -rE "_visibility_visible" apps/api/dataplat_api/runner apps/api/dataplat_api/routers/ingest.py apps/api/dataplat_api/adapters`。要求：(1) `test -f` 前置确保目标文件存在；(2) 正向 grep 证明确实**复用**了 visibility helper；(3) `2>/dev/null` 删除以暴露路径错误。**同时**：把"反向 grep 必须配 `test -f` 前置 + 正向断言"作为第 5 条加入 `request-analysis/SKILL.md` § 跨 AC 一致性自审清单 |

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | spec.md line 67 (AC-4 step 4) vs tasks.md line 61 (T-5 step 4) | `TreeEntryCreate` 构造调用不一致：AC-4 缺 `entry_type="blob"`，T-5 显式写 `entry_type="blob"`。功能上等价（`entry_type: Literal["blob"] = "blob"` 有默认），但**跨 AC 一致性 checklist 条目 1 的精神**要求 generator 在两处一字不差——commit-api-mvp 反哺的"措辞一致"原则不仅适用事务边界，也适用 schema 构造调用 | 任选其一保持一致：spec line 67 显式加 `entry_type="blob"` 或 T-5 line 61 删除该 kwarg；并在跨 AC 自审 grep 加 `grep -c 'TreeEntryCreate' spec.md tasks.md` 验证两处用法对齐 |
| 2 | spec.md line 60-62 (AC-3) vs `packages/core/src/dataplat_core/protocols/runcontext.py` line 17-37 | `RunContext` Protocol 把 `logger` / `metrics` / `secrets` / `cancel_event` / `llm` 全部声明为 `@property`；spec / T-3 用 `@dataclass` 把它们做成普通字段。实测 `isinstance(ctx, RunContext)` 返 True（runtime_checkable 只查属性存在性），AC-3 通过。但 mypy `--strict` 在结构匹配 property vs attribute 时可能 warning（spec 风险段未识别）；且语义上 dataclass 字段 vs property 在未来若 RunContext 加 setter 限制（read-only 语义）时会破裂 | 在风险段补一条："StandardRunContext 用 dataclass 实现 RunContext Protocol 的 property 属性——runtime_checkable 通过、mypy 通过（实测）；若未来 Protocol 转为 read-only property（带 setter raise），实现需同步改为 `property + __init__`。**缓解**：AC-12 mypy 全 PASS 作为 gate" |
| 3 | spec.md line 126 (风险 #4) | "同步 adapter 阻塞 event loop ... RawFileUpload 是 pass-through 不阻塞但框架就绪"——措辞糊。`asyncio.to_thread` 把同步函数移到 thread pool 执行确实不阻塞 event loop，但 thread pool 默认 capacity 是 `min(32, cpu_count+4)`，**未来真长跑 adapter（PDF/Firecrawl）并发时会饱和**——这是一个隐藏的 capacity 风险，spec 未承诺任何阈值 | 改为："MVP 用 default ThreadPoolExecutor（容量 32+cpu）；真长跑 adapter（如 Firecrawl 抓取 1 分钟级）落 RQ worker 前需评估并发上限——已挂 follow-up `rq-worker-skeleton-*`"。一句话即可，留住 trace |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | spec.md line 78 (AC-5 验证命令) | RawFileUploadAdapter 单元测试调 `a.ingest({...}, None, None)`——`workspace=None, ctx=None`。SourceAdapter Protocol 签名是 `Path` / `RunContext` 非 Optional；实现端放宽到 `Path | None` / `RunContext | None` 走 contravariance 是合法 LSP 但读者会困惑 | 在 T-4 描述加一行注释：「RawFileUpload 不依赖 workspace 与 ctx，参数收 `| None` 让单元测试免构造 fixture；其他 adapter 应按 Protocol 严类型实现」 |
| 2 | spec.md line 119 (AC-13) | self_check 命令带显式 env vars，但没有 `set -a; source .env.test` 这种统一前置——会和已有 self_check 块不一致（仅本变更引入风格） | T-9 加一行：复用 `scripts/_self_check.sh` 现有 env 引导（已 export DATAPLAT_PG_PORT 等的现有模式） |

## Verdict

REVISION REQUIRED（MUST FIX = 2）

## 复检指引

作者修完 spec_v2.md 后**自查**：

1. **MUST FIX #1 闭合**：
   - `grep -nE "parents=\[\]" .harness/changes/adapter-framework-20260517/request_analysis/spec.md` 命中 0 处，**或**在风险段命中 1 条 `accept` 说明
   - 若选方案 (a)：`grep "parents:" .harness/changes/adapter-framework-20260517/request_analysis/spec.md` 命中 AC-6 IngestRequest schema 字段
   - 若选方案 (b)：spec 描述 runner 从 `RefORM.commit_hash` 读 parent 的步骤
   - 新增 AC-11 (m) test 描述 + 验证命令
2. **MUST FIX #2 闭合**：
   - AC-9 命令含 `test -f apps/api/dataplat_api/routers/ingest.py`
   - 命令含正向 grep（`_resolve_repo` 或 `RepoService.get_by_owner_name`）
   - 删 `2>/dev/null`
   - 在 spec_v2.md 末尾加一条 grep 自审：`bash -c "<AC-9 命令>"` 在当前空仓库（T-6 未实现）实跑 exit ≠ 0
3. **SKILL 反哺**：本 review 抓到的两个新模式（orphan commit 语义连续性 + 反向 grep 路径不存在沉默通过）应在 v2 提交前提交一份 `.harness/skills/request-analysis/SKILL.md` 追加补丁，把跨 AC 自审清单从 4 条扩到 6 条，并在 spec 末尾"流程偏离声明"段引用 SKILL 新版本号
4. **回归基线**：`cd packages/core && uv run pytest -q tests/test_protocols.py`（reviewer 实测 2 passed），spec 风险 #1 声明的"33 core 测试"也已实测 33 passed（`cd packages/core && uv run pytest -q`）——风险 #1 缓解措施在 v2 实现期可机械验证

提交 spec_v2.md 后开 `spec_review_v2.md`。

## 评审实跑证据

- `grep -nE "事务前|事务内|事务外" spec.md` → 1 行命中（注释行 147，非声明体）；**无 AC ↔ 风险 ↔ tasks 矛盾**
- `grep -nE "files|FileRef|sha256" spec.md` → 10 行命中；IngestResult.files ↔ IngestFileRef.sha256 ↔ TreeEntryCreate.target_hash 三链路一致
- `grep -cE "uv run python -c|test -f|bash scripts" spec.md` → **10**（spec 声明 ≥ 7，实测 10/13 AC ≈ 77%）
- `cd packages/core && uv run pytest -q tests/test_protocols.py` → 2 passed
- `cd packages/core && uv run pytest -q` → 33 passed（spec 风险 #1 基线确认）
- `bash -c '! grep -E "_visibility_visible" apps/api/dataplat_api/runner/ apps/api/dataplat_api/routers/ingest.py apps/api/dataplat_api/adapters/ -r 2>/dev/null; echo $?'` → **0**（vacuous PASS，证实 MUST FIX #2）
- StandardRunContext dataclass 满足 RunContext Protocol：`isinstance(ctx, RunContext)` 返 True（reviewer 实测；SHOULD FIX #2 mypy 风险仍有效）
