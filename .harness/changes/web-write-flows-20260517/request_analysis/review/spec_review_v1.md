---
change_id: web-write-flows-20260517
target: spec.md
target_version: 1
review_version: 1
reviewer: claude-stage2-reviewer
reviewed_at: 2026-05-17T15:40:00Z
verdict: APPROVED
---

# Spec Review v1

## 检查清单结论

> 引用 `.harness/skills/expert-reviewer/SKILL.md` §1 + `.harness/skills/request-analysis/SKILL.md` 8 条跨 AC 一致性自审。

### expert-reviewer §1 plan 模式 spec.md

- [x] 背景写明了为什么现在做（10 个变更后后端齐 / 9 路由零 UI / admin 必须 curl）。
- [x] 问题陈述对外部读者可理解。
- [x] 范围 / 非范围都有；非范围列出 4 个 follow-up 名（commits-list-api / jobs-list-api / Lineage viz / E2E 等）显式排除。
- [x] 13 AC 每条都可演示且都附一行式 shell 验证命令。
- [x] 6 条风险全部有缓解（5 条具体缓解 + 1 条 meta 自审说明）。
- [x] 没有把 design.md 已有架构当新提案——背景仅引用既有事实。
- [x] 无待澄清问题段（开发期内部决策已落到"关键决策"表）。

### request-analysis SKILL 8 条跨 AC 一致性回归（第四次正式回归）

| # | 条目 | 适用性 / 结果 |
|---|---|---|
| 1 | schema ↔ canonical hash ↔ idempotency key ↔ fixture 四链路 | **不适用**：本变更纯前端，无 hash/无 server canonical key。 |
| 2 | 事务边界 AC/风险/tasks 三处一致 | **不适用**：无数据库事务。`grep -nE "事务前\|事务内\|事务外" spec.md` = 0。 |
| 3 | AC 验证命令一行式可执行 | **PASS**：`grep -cE "test -f\|cd apps/web\|grep -q\|pnpm" spec.md` = 11；SKILL 第 3 条要求 ≥ AC 总数 × 0.5 = 6.5，11 > 6.5。spec generator 自审声称 ≥ 12 是自加严阈值，不影响 SKILL 判定。 |
| 4 | 风险缓解 ↔ AC 测试 | **PASS**：风险 #1（路由命名）→ AC-12 build 后 grep routeTree.gen.ts；风险 #2（多文件上传顺序）→ T-4 串行 await，AC-4 间接覆盖；风险 #3（轮询 stop）→ T-5 refetchInterval 函数形式 + AC-2；风险 #4（3-param URL）→ AC-12；风险 #5（invalidateQueries key）→ T-1 写死 4 个 key + AC-7 ≥ 3 次断言；风险 #6 meta 自审。 |
| 5 | commit 历史链 parents | **不适用**：前端不产 commit。`grep -nE "parents=\[\]" spec.md` = 0。 |
| 6 | 反向 grep + `test -f` 前置 | **不适用** / PASS：`grep -nE "! *grep" spec.md` = 0；AC 验证全部正向断言（`test -f && grep -q`）。无 `2>/dev/null` 吞 stderr（AC-11 的 `2>&1` 是合并到 stdout 给 grep 看，非吞错）。 |
| 7 | process_tasks 6 条必填 | **PASS**：`grep -cE "estimated_stage: stage-(2\|4\|6\|7\|9\|10)" tasks.md` = 6（T-11 stage-2 / T-12 stage-4 / T-13 stage-6 / T-14 stage-7 / T-15 stage-9 / T-16 stage-10）。 |
| 8 | AC 验证命令 dry-parse | **不适用**：spec 无 `python -c` 嵌套，全部 shell + `test -f` + `grep -q` + 数组算术 `[ "$(...)" -ge N ]`，shell 语义清晰。 |

第四次回归结论：8 条 checklist 全部生效，3 条直接 PASS（#3 #6 #7），5 条不适用但已显式标注（#1 #2 #5 #8 + 风险 #6 meta 自审）。回归窗口未触发新模式反哺。

## 问题列表

### MUST FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|

（无）

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| S-1 | spec.md AC-6 / T-1 useUploadBlob | spec 含糊"用 fetch + body=Blob/File；可见 octet-stream 处理（或借 fetchJson 内部）"。既有 `fetchJson` 在 client.ts:36-41 默认 `Content-Type: application/json`；若直接传 `body=Blob`，header 仍是 application/json → 后端 FastAPI `Request.stream()` 拿到 binary 但 header 不规范，可能引发后端 415 或日志噪音。AC-6 grep 只断言 `Blob\|File\|octet` 出现，不保证 header 真切换。 | 在 spec AC-6 验证里加 `grep -q "octet-stream" apps/web/src/lib/api/queries.ts`（断言 useUploadBlob 显式 override Content-Type），或 spec 文字明示 useUploadBlob 必须 override header。stage-3 实现期 reviewer 据此把关；不阻塞 stage-2。 |
| S-2 | spec.md 风险 #1 + AC-1 / AC-9 路由命名 | spec 风险 #1 已识别 v1 flat naming + directory mixing，缓解写了 build 后 grep + 回退方案，但**缓解动作未绑死到任何 AC 验证命令**。AC-1 / AC-9 / AC-12 都没显式 `grep "/repos/new" apps/web/src/routeTree.gen.ts`。tasks.md T-9 在描述里口头提了"grep /repos/new、/jobs/$job_id、/commits/$owner/$name/$hash in routeTree.gen.ts 真生成"，但未被任何 AC 一行式抓住。**Note**：v1 文档官方支持 flat + directory mixing（[TanStack Router v1 File-Based Routing](https://tanstack.com/router/v1/docs/framework/react/routing/file-based-routing) "It's extremely likely that a 100% directory or flat route structure won't be the best fit... TanStack Router allows you to mix both flat and directory routes"），技术上不会冲突；但已知 `index` vs `route` 命名歧义会引发 GH#6429 类问题，加 grep 兜底是低成本高收益。 | spec AC-12 末尾追加：`&& grep -q "/repos/new" apps/web/src/routeTree.gen.ts && grep -q "/jobs/\$job_id" apps/web/src/routeTree.gen.ts && grep -q "/commits/\$owner/\$name/\$hash" apps/web/src/routeTree.gen.ts`。stage-3 实现期 reviewer 据此把关；不阻塞 stage-2。 |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| N-1 | spec.md 风险 #5 invalidateQueries key 设计 | 4 个 key（`["repos"]` / `["repo", owner, name]` / `["job", id]` / `["commit", owner, name, hash]`）已固化，但仅写在风险段。queries.ts T-1 描述只提"成功后 invalidateQueries(["repos"]) + 对应 ["repo", o, n]"。可显式把 4 key 表格化进 spec 关键决策段，避免 coding 期分歧。 | 决策表新增一行"invalidateQueries key contract"列出 4 key。NICE，不阻塞。 |
| N-2 | spec.md AC-11 vitest 通过断言 | `pnpm test 2>&1 \| tail -5 \| grep -qE "passed"` 在 vitest 失败摘要里也可能含 "X passed, Y failed" 触发误判 PASS。 | 改为更严格的 `grep -qE "Test Files .* passed.*\(([0-9]+)\)" && ! grep -qE "[1-9][0-9]* failed"` 或直接 `pnpm test --run --reporter=default; [ $? -eq 0 ]`。NICE，stage-5/6 单测 reviewer 把关亦可。 |

## Verdict

**APPROVED**

MUST FIX 数 = 0。SHOULD FIX 2 条（S-1 / S-2），NICE TO HAVE 2 条。建议 generator 在进入 stage-3 前把 S-1 / S-2 的 AC grep 追加进 spec（或在 summary.md 写 deferred 理由）。S-1 / S-2 不阻塞进入 stage-3，因为：
- 它们都是 AC 验证粒度问题（机械化更严即可），不是范围 / 验收逻辑 / 缺失风险问题；
- 已在 spec 风险 / tasks 文字里显式提到，coding 期 reviewer 可作为 stage-4 关注点接住。

## 复检指引

若 generator 选择吸收 SHOULD FIX 产出 spec_v2：

1. 自检 S-1：`grep -q "octet-stream" .harness/changes/web-write-flows-20260517/request_analysis/spec.md`（AC-6 验证段含 octet-stream 断言）。
2. 自检 S-2：`grep -cE "routeTree.gen.ts" .harness/changes/web-write-flows-20260517/request_analysis/spec.md` ≥ 1（AC-12 含 routeTree.gen.ts grep）。
3. 自检 SKILL 8 条不变：第 3 条 grep ≥ 6.5、第 7 条 grep = 6 保持。
4. 若 deferred，summary.md 加段"stage-2 deferred SHOULD FIX 清单"并列 S-1 / S-2，stage-4 coding reviewer 必须 revisit。

若 generator 直接接受 v1：进入 stage-3，无须开 spec_review_v2.md。
