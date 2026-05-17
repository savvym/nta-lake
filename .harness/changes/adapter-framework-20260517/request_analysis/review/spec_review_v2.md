---
change_id: adapter-framework-20260517
target: spec.md
target_version: 2
review_version: 2
reviewer: claude-stage2-reviewer-v2
reviewed_at: 2026-05-17T11:35:00Z
verdict: APPROVED
---

# Spec Review v2

## 检查清单结论

> 引用 `.harness/skills/expert-reviewer/SKILL.md` §1（plan 模式 spec.md）+ `.harness/skills/request-analysis/SKILL.md` § 跨 AC 一致性自审清单（v2 扩到 7 条）。

- [x] 背景写明了为什么现在做（line 18-22：Phase 1 #2 仍 0%）。
- [x] 问题陈述对外部读者可理解（line 24-29 四条诊断清晰）。
- [x] 范围 / 非范围都有（line 32-57；out-of-scope 9 条均挂 follow-up）。
- [x] **每条验收标准可演示且可机械化**——AC-9 v2 已修复沉默通过（详见 v1 MUST FIX #2 复核）。
- [x] **风险有缓解或显式 accept**——commit parents 链断裂在 v2 风险 #8 明确识别且配方案（详见 v1 MUST FIX #1 复核）。
- [x] 没有把已有架构当新提案——SourceAdapter Protocol / CommitService 均明确标"已有，本变更不动"。
- [x] 待澄清问题段已清零。

### v1 MUST FIX 复核

| v1 MUST FIX | v2 修复证据 | 状态 |
|---|---|---|
| **#1 orphan commit / 父子链断裂** | (a) AC-4 step 2（line 74）加 parent 自动接链：`if request.parents: ...; elif request.ref: SELECT RefORM.commit_hash ...; else: parents=[]`；(b) AC-6（line 92）`IngestRequest` 加 `parents: list[SHA256]=Field(default_factory=list)` 字段；(c) AC-11 (m)（line 127）`test_m_second_ingest_to_same_ref_creates_child` 测试：C1.parents=[] → C2.parents=[C1.hash] 且 GET `/commits/{C1.hash}` 仍 200；(d) 风险段 #8（line 147）显式记录该决策与未覆盖 case；(e) 关键决策表（line 161）记录"(b) ref-based 自动 + (c) client 显式"为主路径 | **CLOSED** |
| **#2 AC-9 反向 grep 沉默通过** | (a) line 103 验证命令加 `test -f apps/api/dataplat_api/routers/ingest.py && test -f apps/api/dataplat_api/runner/adapter_runner.py` 前置；(b) 加正向断言 `grep -qE "_resolve_repo\|RepoService.get_by_owner_name"` 证明真复用；(c) 删 `2>/dev/null`；(d) reviewer 实测当前空仓库 `bash -c "<AC-9 命令>"` → `exit=1`（非 0），证明**反向 grep 不再沉默通过** | **CLOSED** |

### v1 SHOULD FIX 复核

| v1 SHOULD FIX | v2 修复证据 | 状态 |
|---|---|---|
| **#1 TreeEntryCreate 跨文档不一致** | spec AC-4 step 5（line 77）已显式写 `entry_type="blob"`，与 tasks T-5 step 5（line 78）一致 | CLOSED |
| **#2 RunContext dataclass-vs-property** | spec 风险段 #7（line 146）显式识别该模式 + 用 AC-12 mypy 作为 gate；T-7b（tasks line 110-117）显式覆盖 AC-12 + 包含"若 mypy 报错 → 转 property + __init__"回退方案 | CLOSED |
| **#3 thread pool capacity 风险措辞糊** | 风险 #4（line 140）改为："MVP default ThreadPoolExecutor 容量 `min(32, cpu+4)`。长跑 adapter（PDF/Firecrawl）并发饱和留给 `rq-worker-skeleton-*` 评估并发上限" | CLOSED |

### 跨 AC 一致性自审清单回归（v2 SKILL 7 条）

> v2 SKILL 已从 4 条扩到 7 条（commit-history-continuity / reverse-grep-vacuous-pass / process_tasks 6 条必填），本次为反哺后的**第一次正式回归**。

| checklist 条目 | 本 spec v2 表现 | 评价 |
|---|---|---|
| 1. 四链路一致（schema ↔ hash ↔ idempotency ↔ fixture） | 沿 v1 路径，未引入新链路（仅加 `parents` schema 字段不影响 hash 输入；commit canonical hash 由 CommitService 沿用） | 生效 |
| 2. 事务边界 AC ↔ 风险 ↔ tasks | 未引入新事务；风险 #6 显式声明 | 生效 |
| 3. AC 验证命令一行式可执行 | 实测 `grep -cE "uv run python -c\|test -f\|bash scripts" spec.md` ≥ 7 | 生效 |
| 4. 风险缓解 ↔ AC 测试 | 风险 #1/#2/#4/#7/#8 全部点名 AC-11 / AC-12 测试覆盖 | 生效 |
| 5. **commit 历史链连续性**（v1 反哺） | AC-4 step 2 parent 接链 + AC-6 parents 字段 + AC-11 (m) 父子链测试 + 关键决策表记录 | **生效**：v1 失效模式已被 v2 消化 |
| 6. **反向 grep 配 `test -f` + 正向断言 + 不吞 stderr**（v1 反哺） | AC-9 line 103 三重防护全在 | **生效**：v1 失效模式已被 v2 消化 |
| 7. process_tasks 6 条必填 | spec 未直接含 tasks 编号，但反哺已落到 SKILL；tasks v2 已加 T-10~T-15（spec line 179 流程偏离声明引用） | **生效**：见 tasks_review_v2 |

**结论**：v2 spec 把 v1 暴露的两个新失效模式（orphan commit / 反向 grep 沉默通过）全部消化，且 SKILL 反哺已落地——下一个 spec generator 在 stage 1 即可受益。**未发现新 MUST FIX**。

## 问题列表

### MUST FIX

无。

### SHOULD FIX

无新增；v1 三条已全部消化（见上表）。

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | spec.md line 74 (AC-4 step 2) | parent 接链伪代码用自然语言描述 "SELECT `RefORM.commit_hash` for `(repo_id, ref=request.ref)`"，未显式给出 SQLAlchemy 查询。T-5 step 2（tasks line 70）补全了 `select(RefORM).where(RefORM.repo_id == repo_id, RefORM.name == request.ref)` 的具体写法——spec 与 tasks 看起来分工合理（spec 写 what / tasks 写 how），但对独立读者来说要跨文档读才知道 `ref` 字段名是 `name` 而不是 `ref` | 可选：spec AC-4 step 2 加一行注 `(RefORM.name 是 ref 名称字段)`。不阻塞 |
| 2 | spec.md line 147 (风险 #8 未覆盖 case) | "第二次 ingest 不传 ref 也不传 parents → 走 root commit 路径，client 自负历史链" 是个**隐含坑**——MVP 接受但未在 AC-11 加显式测试或在 AC-10 错误路径列出。若 client 误用，会创建多个 orphan commit 散布在 PG 但不在任何 ref 上 | 可选：AC-11 加 (n) test_n_ingest_without_ref_and_parents_creates_root_commit_no_chain 显式锁定语义，或在 API doc 加 warning。不阻塞 MVP |

## Verdict

**APPROVED**（MUST FIX = 0）

## 复检指引

v2 已通过 stage 2 spec review，可进入 stage 3 coding。

下游 coding agent 自查（实施 T-1~T-7b 时）：

1. **AC-4 step 2 parent 接链实现**：runner/adapter_runner.py 必须含 `if request.parents: ... elif request.ref: select(RefORM)... else: parents=[]` 三分支，与 spec line 74 / tasks line 65-74 一字不差；coding review 时 `grep -nE "resolved_parents" apps/api/dataplat_api/runner/adapter_runner.py` 期望命中 ≥ 3。
2. **AC-9 复用 visibility helper**：实现 routers/ingest.py 时**从 routers/commits.py import** `_resolve_repo` 或调 `RepoService.get_by_owner_name`，**绝不复制 `_visibility_visible`**。stage 4 review 时复跑 spec line 103 验证命令期望 exit=0。
3. **AC-11 (m) 父子链测试落地**：test_ingest.py 必须有 `test_m_second_ingest_to_same_ref_creates_child`，断言 `commit2.parents == [commit1.hash]`。
4. **AC-12 lint + mypy 显式跑**：实现期间每改一次 runner / adapter / router 都跑一遍 `uv run ruff check apps/api packages/core && uv run mypy apps/api/dataplat_api packages/core/src`，避免堆到 T-7b 一次性修一堆。
5. **风险 #7 dataclass-vs-property 兜底**：若 mypy 在 StandardRunContext 实现 RunContext Protocol 时报错，按 T-7b 兜底方案转 property + __init__。

## 评审实跑证据

```bash
# 自审 grep 全部通过
grep -nE "事务前|事务内|事务外" spec.md       # 1 行（注释行 166），无矛盾
grep -nE "parents=\[\]" spec.md             # 5 处全部为合规出现（fallback 描述 / 测试断言 / 风险段说明 / 决策表）
grep -nE "! *grep" spec.md                  # 1 处（AC-9）配 test -f 前置
grep -nE "2>/dev/null" spec.md              # 仅出现在描述/grep 自审注释，AC 实际命令无吞 stderr

# 父子链三链路确认
grep -nE "resolved_parents|RefORM.commit_hash" spec.md  # AC-4 step 2 + step 5 + 风险段
grep -nE "parents: list\[SHA256\]" spec.md              # AC-6 schema 字段
grep -nE "test_m_second_ingest" spec.md                 # AC-11 (m)

# 3-tuple 一致性确认
grep -nE "3-tuple|commit, dedup, result" spec.md        # AC-4 + 决策表 + revisions
grep -nE "3-tuple|commit, dedup, result" tasks.md       # T-5 + revisions（一字不差）

# AC-9 反向 grep 不再沉默通过
bash -c "test -f apps/api/dataplat_api/routers/ingest.py && grep -qE '_resolve_repo|RepoService.get_by_owner_name' apps/api/dataplat_api/routers/ingest.py && ! grep -rE '_visibility_visible' apps/api/dataplat_api/runner apps/api/dataplat_api/routers/ingest.py apps/api/dataplat_api/adapters"
# exit=1（路由文件未实现）— v1 同条命令为 exit=0（vacuous PASS）。证明 v2 修复有效。

# SKILL 反哺落地
sed -n '101,134p' .harness/skills/request-analysis/SKILL.md
# 含第 5 条 commit-history-continuity / 第 6 条 reverse-grep-vacuous-pass / 第 7 条 process_tasks 6 条必填
```

**v1 → v2 修复完整性**：4 MUST FIX（spec 2 + tasks 2）+ 3 SHOULD FIX + SKILL 反哺均闭合；无新 MUST FIX。verdict **APPROVED**。
