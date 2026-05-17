---
change_id: repo-api-mvp-20260517
target: tasks.md
target_version: 1
review_version: 1
reviewer: claude-agent:repo-api-mvp-stage2-reviewer
reviewed_at: 2026-05-17T07:35:00Z
verdict: REVISION REQUIRED
---

# Tasks Review v1

## 总体判定

**REVISION REQUIRED**。任务切分合理（7 个 T-* + 7 个 P-* 覆盖 13 AC、DAG 无循环），但下游
依赖 spec 的修订——AC-11 测试用例从 11 扩到 ≥ 13 必须同步反映到 T-6；T-2 重构 `get_current_user`
的兼容性保证缺位（auth-scaffold 11 个 test_auth.py 测试可能被破）；T-3 service 层职责契约模糊
（admin 校验是 router 唯一负责还是 service 双重保险？）；codegen / openapi.json 同步缺独立任务步骤。
其余结构良好，修完即可承接 Stage 3。

## 检查清单结论

- [x] 每个任务粒度合理（1-3 小时）。
- [x] depends_on 无环：T-1 → T-3 → T-4 → T-5 → T-6 → T-7；T-2 与 T-1 并行。
- [x] 包含评审 / 单测 / CI 阶段对应任务（P-* 7 项齐全）。
- [x] 没有 "做完整个系统" 类目标任务。
- [x] 每条 AC 都有非 process_tasks 任务覆盖（但 AC-6~AC-10 在 T-6 应明列见 MUST FIX #2）。

## 问题列表

### MUST FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | tasks T-2 | 重构 `get_current_user` 时缺"原行为不破"硬契约。实证 deps.py:21-66 当前 `get_current_user` 在 7 条路径全 raise 401（无 cookie / token 解码失败 / typ != access / sub 缺 / sub 非 UUID / user 不存在 / user inactive）。重构后两件事必须保证：(a) `get_current_user` 仍是七路径全 raise 401；(b) `get_optional_user` 等价 7 路径返 None（含 user inactive 也返 None 不 raise）。当前 T-2 仅一句"tests 同步更新（已有测试 not break）"过于含糊。 | T-2 描述显式列硬验收：apps/api/tests/test_auth.py 11 个测试（test_a ~ test_k）全 PASS；`get_optional_user` 在 7 条等价路径返 None；列出共享函数签名 `_decode_user_from_cookie(request, session) -> AuthenticatedUser | None`。 |
| 2 | tasks T-6 | 测试数与 AC-11 不同步。spec MUST FIX #3 要求扩到 ≥ 13 测试（加 list visibility 2 条），T-6 仍写 11 集成。covers_ac 应显式包含 AC-6~AC-10，不仅 AC-11。 | T-6 描述改为"13 集成测试覆盖 detail + list × 3-visibility × 3-caller 矩阵"；covers_ac 列 [AC-6, AC-7, AC-8, AC-9, AC-10, AC-11]。 |
| 3 | tasks T-3 | service 层职责模糊。当前 T-3 写 `update / delete ... 仅 admin 调用` —— "仅 admin 调用" 是契约性约定（caller 保证）还是 service 内部校验？必须明示前者，否则 service 单测被迫造 admin 身份。 | T-3 改为："service.update/delete **假设 caller（router）已通过 require_admin 守卫**；service 自身仅处理：(a) get_by_owner_name / list 的 visibility 过滤（current_user 为 None / user / admin 三档）；(b) create 的 IntegrityError → 409；(c) update/delete 的 not-found → 404。**service 不查 role**。" |

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | tasks T-1 | schema 字段缺约束声明。`owner` / `name` 进 URL 需 `min_length=1` + 正则禁斜杠/空格；`layer` 应是 `Literal["bronze","silver","gold"]`；`visibility` 应是 `Literal["public","internal","private"]`。 | T-1 描述补字段约束清单，避免实现期漏。 |
| 2 | tasks T-4 | 5 路由缺 `response_model` / `status_code` 显式声明。OpenAPI 准确性 + AC-7 "201" / AC-9 "204" 机械化验证依赖此。 | T-4 加一句"每路由显式 `response_model=RepositoryRead/RepositoryListItem` + `status_code=200/201/204`"。 |
| 3 | tasks T-7 | self-check block 缺 codegen 同步校验（对应 spec SHOULD FIX #4）。 | T-7 加 AC：`run_ac AC-CODEGEN "openapi.json 同步" bash -c 'uv run python -m scripts.export_openapi && git diff --exit-code packages/api-types/openapi.json'`。 |
| 4 | tasks DAG | 缺独立"openapi.json regenerate" step。当前 T-5 include_router 后无显式 codegen 任务，DAG 上隐式。 | 加 T-5.5 或在 T-5 描述末尾追加"立即跑 `uv run python -m scripts.export_openapi` 并 commit 生成的 openapi.json"。 |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | tasks T-6 | fixture 复用 auth-scaffold 的 `created_admin` / `created_user` 仅一句"复用模式"，实现路径不清（copy-paste 还是共享 conftest）。 | T-6 明示"通过 apps/api/tests/conftest.py 共享 created_admin / created_user fixture，不 copy"。 |
| 2 | tasks P-user-confirm | 标 pending 但描述空。 | 加一句"前端可手动 curl 5 路由 ≥ 1 次成功 + AC-11 13/13 PASS 作为 UAT 标准"。 |

## DAG / 覆盖矩阵核查

- DAG 无循环：T-1 → T-3 → T-4 → T-5 → T-6 → T-7；T-2 与 T-1/T-3 可并行。
- AC 覆盖：AC-1~AC-13 全有 T-* 落点；AC-6~AC-10 在 T-6 的覆盖应明列（见 MUST FIX #2）。
- 缺 codegen / openapi.json regenerate 显式 step（见 SHOULD FIX #4）。

## Verdict

REVISION REQUIRED（MUST FIX = 3 > 0）。

## 复检指引

修完 3 MUST FIX + 4 SHOULD FIX 后送 tasks_v2：

1. T-2 描述列出"原有 11 个 test_auth 全 PASS"作为硬验收 + `_decode_user_from_cookie` 签名。
2. T-6 描述用例扩到 ≥ 13；covers_ac 列 AC-6~AC-11。
3. T-3 描述声明"service 不查 role；admin gate 唯一在 router"。
4. T-5 / T-7 显式包含 codegen 同步。

提交 tasks_v2 后开 tasks_review_v2.md。
