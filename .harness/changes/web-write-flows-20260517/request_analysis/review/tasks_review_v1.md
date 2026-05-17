---
change_id: web-write-flows-20260517
target: tasks.md
target_version: 1
review_version: 1
reviewer: claude-stage2-reviewer
reviewed_at: 2026-05-17T15:40:00Z
verdict: APPROVED
---

# Tasks Review v1

## 检查清单结论

> 引用 `.harness/skills/expert-reviewer/SKILL.md` §1 tasks 部分 + request-analysis SKILL 第 7 条 process_tasks。

- [x] 每个任务粒度合理（1-3 小时）：T-1 queries.ts 7 hook 含 mutate + invalidate 略偏 3-4h 上限，但仍是单文件原子任务，可接受；其余 T-2~T-10 均明显单页面 / 单组件粒度。
- [x] depends_on 形成 DAG，无循环：T-1/T-2 叶；T-3 ← T-1,T-2；T-4 ← T-1,T-2；T-5 ← T-1；T-6 ← T-1；T-7 独立；T-8 ← T-3,T-5,T-6；T-9 ← T-1~T-8；T-10 ← T-1~T-9；T-11~T-16 process 链单向。已绘图。
- [x] 评审 / 单测 / CI 对应任务存在：T-11 stage-2 / T-12 stage-4 / T-13 stage-6 / T-14 stage-7 / T-15 stage-9 / T-16 stage-10。SKILL 第 7 条 `grep -cE "estimated_stage: stage-(2\|4\|6\|7\|9\|10)" tasks.md` = 6，PASS。
- [x] 没有"做完整个系统"类目标任务：每个 T-* 都对应具体 AC 编号。
- [x] 每条 AC 都有非 process 任务覆盖：AC-1→T-3 / AC-2→T-5 / AC-3→T-6 / AC-4→T-4 / AC-5→T-1 / AC-6→T-1 / AC-7→T-1 / AC-8→T-2 / AC-9→T-7 / AC-10→T-4 / AC-11→T-8 / AC-12→T-9 / AC-13→T-10。覆盖矩阵在 tasks.md §AC 覆盖矩阵已显式列出，13 / 13 全覆盖。

## 问题列表

### MUST FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|

（无）

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| S-1 | tasks.md T-1 useUploadBlob 描述 | "useUploadBlob(owner, name)" 描述未说明 Content-Type override 策略（与 spec S-1 关联）。stage-3 coding 实现者可能直接套 fetchJson 默认 `application/json`，导致后端 header 不规范。 | T-1 描述加一句："useUploadBlob 必须 override Content-Type 为 `application/octet-stream`（fetchJson 默认 application/json 会与 binary body 冲突）"。 |
| S-2 | tasks.md T-9 build 验证 | T-9 文字提到"grep `/repos/new`、`/jobs/$job_id`、`/commits/$owner/$name/$hash` in routeTree.gen.ts 真生成"，但 AC-12 验证命令未抓这一行。risk #1 缓解动作落在 T-9 描述里、未落到 AC，存在"task 写了 / AC 没断言"的脱钩风险（review 历史上多次出现）。 | 与 spec S-2 联动：要么 AC-12 加 routeTree.gen.ts grep，要么 T-9 任务自检阶段把"grep 路由"作为子检查项写进 `_self_check.sh` block（即归并到 AC-13）。 |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| N-1 | tasks.md T-8 vitest 测试名 | T-8 列了 3 个测试文件但未点测试场景命名风格（既有 4 测试是 `login.test.tsx` / `repos.test.tsx`，命名 scenario 含义）。 | 在 T-8 描述加一句"测试名采用 `test_<场景描述>` 风格，避免 `test_1`/`test_a`"。NICE。 |
| N-2 | tasks.md T-4 改造范围 | T-4 一次完成 Edit + Delete + Ingest 三 section + admin 判断 + window.confirm，粒度上限。若 stage-3 实现遇阻可拆 T-4a (Edit/Delete) / T-4b (Ingest)。 | NICE，仅在实现卡顿时拆。 |
| N-3 | tasks.md process_tasks T-15 | T-15 标 "skipped 仅前端静态"，但依旧 estimated_stage: stage-9。SKILL 第 7 条只要求该 stage 有显式任务（即便 noop），符合规范。无需修改。 | 仅提示。 |

## Verdict

**APPROVED**

MUST FIX 数 = 0。两条 SHOULD FIX 都与 spec 评审的 SHOULD FIX 联动，不阻塞 stage-3 进入。

## 复检指引

若 generator 选择吸收 SHOULD FIX 产出 tasks_v2：

1. 自检 S-1：`grep -q "octet-stream" .harness/changes/web-write-flows-20260517/request_analysis/tasks.md`。
2. 自检 S-2：要么 AC-12 spec 改了（参见 spec_review_v1.md 复检指引第 2 条），要么 T-10 self_check block 把 routeTree.gen.ts grep 写进去。
3. 自检 process_tasks 6 条不变：`grep -cE "estimated_stage: stage-(2|4|6|7|9|10)" tasks.md` = 6。
4. 自检 AC 覆盖矩阵无新增 AC 时 13/13 不变。

若 generator 直接接受 v1：进入 stage-3，无须开 tasks_review_v2.md。
