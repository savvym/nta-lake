---
change_id: repo-api-mvp-20260517
target: spec.md
target_version: 1
review_version: 1
reviewer: claude-agent:repo-api-mvp-stage2-reviewer
reviewed_at: 2026-05-17T07:30:00Z
verdict: REVISION REQUIRED
---

# Spec Review v1

## 总体判定

**REVISION REQUIRED**。需求方向正确（合理的 MVP 切片、与 design.md §4.4 / §11.6 一致、复用
auth-scaffold 依赖、未越界 commit/blob），但 AC-11 的验证命令存在 **shell 语法实证 BUG**
（`\|` 让计数断言永远 rc=2），visibility 矩阵在边角语义上欠精确（list 与 detail 一致性 / total
计数语义 / PATCH 窗口 / 创建即刻可见性），以及"仅 admin / service 与 router 职责分离"的契约
未在 spec 中明示。实证：description 字段在 RepositoryORM（apps/api/dataplat_api/models/repository.py:31）
+ 0001 migration:33 + core domain 已存在，**无需新增 migration**——这条澄清要写进 spec 避免实现期误判。

## 检查清单结论

- [x] 背景写明了为什么现在做（前端联调阻塞）。
- [x] 问题陈述对外部读者可理解。
- [x] 范围 / 非范围都有。
- [x] 每条验收标准可演示且可机械化（除 AC-11 的 `\|` 语法 BUG）。
- [x] 风险有缓解或显式 accept。
- [x] 没有把已有架构当新提案。
- [x] 待澄清问题已清零或显式 deferred。

## 问题列表

### MUST FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | spec §验收标准 AC-11 验证命令 | `[ "$(... 2>&1 \| grep -cE "::")" -ge 10 ]` 中 `\|` 是字面 `|` 不是管道；实证 `bash -c '[ "$(echo hello 2>&1 \| grep -cE "::")" -ge 10 ]'` 返 `[: hello \| grep -cE "::": integer expression expected` rc=2。即使 DB 起来 + pytest 通过，AC-11 第二段必然 FAIL。 | 去掉 `\`，改为正常管道 `\| grep` → `| grep`；或拆为两条 `run_ac`（一条跑 pytest，一条 collect-only 数 testid）。 |
| 2 | spec §AC-6 + AC-10 | AC-6 只定义 detail GET 矩阵；list GET 行为隐含一句带过。需钉死：list 对匿名 / user **过滤掉不可见 repo 而非返 401/403**，`total` 返回**过滤后**计数（不泄露 private 数量）。 | AC-6 矩阵显式扩展为 list × detail；AC-10 加一句 "total 反映 visibility 过滤后剩余数" + 文字"不可见 repo 在 list 中静默缺席，不报错"。 |
| 3 | spec §AC-11 (a~k) | 11 用例只断 detail × visibility；缺 list × visibility 至少 2 条（匿名 list 不含 private/internal；user list 不含 private），service.list 过滤逻辑无机械化覆盖。 | AC-11 扩到 (a~m) 13 用例：(l) 匿名 list 仅含 public；(m) user list 不含 private。 |
| 4 | spec §AC-6 PATCH 窗口 | AC-11 (j) 让 user 在 PATCH visibility public→private 后立即 GET 验 404；但 user 的 access cookie 是 PATCH 前签发的——隐含"visibility 检查基于实时 DB 行不缓存"。语义未明示，实现者可能误把 visibility 写进 access token claim。 | AC-6 加一句"visibility 检查基于实时 DB 行；access token 仅证身份不证可见性；旧 cookie 不构成缓存窗口"。 |

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | spec §AC-1 / AC-8 | RepositoryUpdate 全 Optional 默认 None：caller 传 `description=None` 与未传 description 在 Pydantic v2 默认行为下同义，service `if v is not None: setattr` 会让"显式清空 description"成 no-op。MVP 可接受 all-or-nothing replace，但需声明。 | spec §AC-8 加："PATCH 不支持显式清空 description（None 即未传）；清空操作留 Phase 2 用 `Unset` sentinel 或 `model_fields_set` 处理"。 |
| 2 | spec §AC-7 | POST visibility=public 后匿名可见时机未明示，实现者可能误加 approval / staging。 | AC-7 加一句"创建后**立即对匿名可见**，无 approval 流程"。 |
| 3 | spec §AC-2 / 范围 | service 接 current_user 用于 visibility 过滤，但 AC-7/8/9 "仅 admin POST/PATCH/DELETE" — service 内部是否要二次校验 admin？职责未分离。 | spec 显式声明："admin gate 由 router `Depends(require_admin)` 唯一负责；service 仅对**可见性过滤 GET** 负责，不重复 admin 校验，service 单测无需注入 admin 身份"。 |
| 4 | spec §风险表 | 缺 openapi.json 同步风险。implementor 若漏跑 `uv run python -m scripts.export_openapi` → `openapi.json` 与新路由不一致，前端 contract 漂移。 | 加风险条 + 缓解："T-7 self-check 加 `git diff --exit-code packages/api-types/openapi.json`；stage 7 push 前强制 codegen"。 |
| 5 | spec §风险表 | 缺 fixture teardown FK 级联风险。当前 RepositoryORM 无 FK 被引用，但 commit-api follow-up 加 `commits.repo_id FK → repositories(id)` 后，test_repos.py 残留 commit 行会让 `delete(RepositoryORM)` IntegrityError。 | 加 NOTE：fixture `delete` 包 try/except IntegrityError，或在 commit-api 同步改 teardown；现 MVP accept。 |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | spec §风险表"list count" | 大 offset 全表 count 性能 cliff，已列低概率。 | 加一句"MVP < 50 repo 可接受；> 5k 时切 keyset pagination"作 follow-up 锚点。 |
| 2 | spec §AC-6 矩阵 | DELETE 不存在的 repo 已在 AC-9 写 404，但矩阵表未体现。 | 矩阵表加一行 admin DELETE / 不存在 → 404。 |
| 3 | spec §AC-13 | self-check block 未约束行数，可能写出超长 block 拖慢 CI。 | spec 钉 "≤ 50 行"。 |

## Verdict

REVISION REQUIRED（MUST FIX = 4 > 0）。

## 复检指引

修复以上 4 MUST FIX + 5 SHOULD FIX 后送 spec_v2：

1. 自检：去掉 `\|` 后实跑 `bash -n` + 在 /tmp 跑 AC-11 命令片段验证 `[ "$cnt" -ge 10 ]` 不再报"integer expression expected"。
2. 自检：list visibility 用例 (l)(m) 出现在 AC-11 列表。
3. 自检：spec 中"description 字段已存在于 RepositoryORM + 0001 migration"显式声明，避免下游误加 0003。
4. 自检：visibility 实时检查 + 创建即刻可见 + service 不重复 admin 校验三条语义钉死。

提交 spec_v2 + 实证日志后开 spec_review_v2.md。
