---
change_id: stage9-followup-cleanup-20260518
target: tasks.md
target_version: 1
review_version: 1
reviewer: claude-agent:stage9-followup-cleanup-20260518-stage2-reviewer-v1
reviewed_at: 2026-05-18T11:25:00Z
verdict: REVISION REQUIRED
---

# Tasks Review v1

## 检查清单结论

- [x] 每个任务粒度合理（1-3 小时）：T-1（model 1 行改）/ T-2（新建 migration 50 行）/ T-3（真跑 3 条 alembic 命令 + SQL 查）/ T-4（_seed_bronze 加 4 行 uuid 前缀）/ T-5（真跑 pytest）/ T-6（self_check block）—— 全在合理范围。
- [x] depends_on 无环：DAG 段已画图 `T-1/T-2/T-4 → T-3 → T-5；T-1/T-2/T-4 → T-6`，无环。
- [x] 包含评审 / 单测 / CI / deploy / user-confirm：process_tasks 6 条齐全（P-spec-review/P-code-review/P-test-review/P-ci/P-deploy/P-user-confirm）。CI 标 self-attest（无 remote），deploy 显式不 self-attest（有 schema 改）。
- [x] 没有"做完整个系统"类目标任务：6 个 T-* 全是具体动作。
- [x] 每条 AC 都有 T-* 覆盖：AC-1→T-1+T-2+T-6；AC-2→T-2+T-3+T-6；AC-3→T-4+T-6；AC-4→T-5+T-6。验收覆盖矩阵段已显式列出。

## 设计合理性评估

### 1. T-2 alembic 0005 migration 实现策略
**SHOULD FIX**。tasks T-2 描述用裸 SQL `ALTER TABLE pipeline_cache DROP CONSTRAINT ... ADD CONSTRAINT ...` 表达意图，但**没明示用 alembic 高层 API `op.drop_constraint` + `op.create_foreign_key`**。0004 migration 用 `sa.ForeignKey(..., ondelete="RESTRICT")` inline 风格（参 `0004_pipeline_orchestrator.py` 第 99 行），与 0005 选裸 SQL 风格不一致。实现者可能纠结用 `op.execute("ALTER TABLE ...")` 字面 SQL vs `op.drop_constraint("pipeline_cache_output_commit_hash_fkey", "pipeline_cache", type_="foreignkey") + op.create_foreign_key("pipeline_cache_output_commit_hash_fkey", "pipeline_cache", "commits", ["output_commit_hash"], ["hash"], ondelete="CASCADE")`。**建议**：tasks T-2 description 明确写 alembic 高层 API 调用形态（伪代码），让裸 SQL 仅作为概念说明。

### 2. T-3 alembic 三连命令的 db 状态前置假设
**SHOULD FIX**。T-3 描述假设 dev db 当前在 0004（head）状态。但若开发者本地 db 已被其他 change 升到非 0004 / 或被人工 reset 过，三连命令会 fail。**建议**：T-3 第一步前加 `uv run alembic current` 输出捕获 + 期望 `0004 (head)`，再开始三连；否则提示开发者先 `alembic upgrade 0004` 把 db 对齐到 baseline。

### 3. T-4 加 uuid 前缀的实现伪代码
**合理**。T-4 description 给的伪代码：
```python
unique_content = f"# fixture-uuid {uuid.uuid4().hex}\n".encode() + content
r_blob = await c.post(f"/repos/{owner}/{name}/blobs", content=unique_content)
```
- 前缀放在 content 开头（避开 markdown 结尾 `\n` 影响）—— 合理。
- 用 `f"# fixture-uuid {hex}\n"` 形态：是 markdown 注释前缀（`#` 是 H1 标题），加在原 content 之前。**注意**：markdown-normalize processor 会否把这条 `# fixture-uuid <hex>` 当 H1 处理后产 silver content？如果会，silver 的 commit_hash 也会随之变 —— 但因 cache_key 公式包含 input commits + processor + config（参 `compute_cache_key([src_commit], ...)`），silver commit 跟着变是预期。**不影响断言语义**，且 spec AC-4 不断言 silver content 具体字串。
- 第 65/68 行 description 备注"测试断言不依赖 raw content 字串（已实读 6 处断言确认）" —— 实读确认对。

### 4. T-5 pytest 真跑覆盖
**合理**。T-5 description 期望"≥10 passed；test_cache_hit_* 三个全 PASS"。实测 test_pipeline_orchestrator.py 含 10 个 test_ 函数（4 sync + 6 async @pytestmark_int），≥10 期望正确。**但与 spec AC-4 描述"7 集成测试"数字打架**（spec 错，tasks 对）—— 需 spec 修齐。

### 5. T-6 self_check block 位置
**合理**。description 写"在 main 添加调用（pipeline-orchestrator-mvp block 之后、harness-ac-behavioral-tier-20260518 之前）"—— 这个排序与 change 时间顺序一致。但需注意 `run_ac_kind_lint` 与 `run_reviewer_lint` 是 global function（在所有 block 之前 / 之后跑），与 T-6 单 change block 不冲突。

### 6. AC-1 验证命令缺陷影响 T-6 self_check block 设计
**MUST FIX**（同 spec_review MUST FIX-1 联动）。T-6 description 写"AC-1：grep model + 0005 migration CASCADE，0004 保留 RESTRICT（test -f 前置）"—— 这条断言会照搬 spec AC-1 的 grep pattern。若 spec AC-1 修了（用 anchor `output_commit_hash: Mapped[str] = mapped_column` + `-A 3` 或 awk 范围限定），T-6 description 必须同步改。否则 self_check 永远 fail。**建议**：T-6 等 spec_v2 修完 AC-1 后再写 self_check block；description 加备注"AC-1 grep pattern 等 spec_v2 校准后照搬"。

### 7. DAG 段
**合理**。T-1/T-2/T-4 三个独立可并行；T-3 跨 T-2；T-5 跨 T-3+T-4；T-6 跨 T-1+T-2+T-4。无环。但**T-5 应不应该 depends_on T-1**？T-5 跑 pytest 时若 model 仍是 RESTRICT，cache_hit 测试会因 stage 9 残留 FK 删 commit 失败而误判 → 但 T-5 不直接 DELETE 测 commit（看 `_delete_repo_cascade` 实现可能会），且本机当前 db 状态未知。**NICE TO HAVE**：T-5 加 `depends_on: [T-1, T-3, T-4]` 显式（T-3 已含 T-2，间接含 T-1 必要前置，但 model 改不 cascade 到 alembic）。

## 问题列表

### MUST FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| MUST FIX-1 | tasks.md T-6 description "AC-1：grep model + 0005 migration CASCADE" | 联动 spec_review MUST FIX-1：spec AC-1 的 grep pattern `output_commit_hash.*ForeignKey` 同行匹配永远 fail（model 文件中 `output_commit_hash` 与 `ForeignKey` 分别在第 86 / 88 行）；T-6 self_check block 若照搬这个 pattern，也会永远 fail。 | 等 spec_v2 修完 AC-1 grep pattern 后，T-6 description 同步引用新 pattern；或现在加备注"AC-1 grep pattern 等 spec_v2 校准后照搬，不在此 inline 写死"。 |

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| SHOULD FIX-1 | tasks.md T-2 description | 用裸 SQL `ALTER TABLE ... DROP/ADD CONSTRAINT` 描述意图，但 alembic migration 通常用高层 API `op.drop_constraint` + `op.create_foreign_key`，与 0004 风格（`sa.ForeignKey` inline）不一致。实现者可能纠结裸 `op.execute("ALTER ...")` vs 高层 API。 | description 明示用高层 API：`op.drop_constraint("pipeline_cache_output_commit_hash_fkey", "pipeline_cache", type_="foreignkey")` + `op.create_foreign_key("pipeline_cache_output_commit_hash_fkey", "pipeline_cache", "commits", ["output_commit_hash"], ["hash"], ondelete="CASCADE")`；裸 SQL 仅作概念说明。 |
| SHOULD FIX-2 | tasks.md T-3 description | T-3 假设 dev db 当前 `0004 (head)` 状态，没有前置检查；若开发者本地 db 在其他 revision，三连会 fail 且原因混淆。 | T-3 description 第一步加 `uv run alembic current` 输出捕获 + 期望 `0004 (head)`，再开始三连；否则提示先 `alembic upgrade 0004`。 |
| SHOULD FIX-3 | tasks.md T-5 description "≥10 passed" 与 spec AC-4 描述"7 集成测试" | tasks 写 ≥10（对），spec AC-4 描述说"7 集成测试"（错；实测 10 个 test_ 函数）。两文件数字打架，实现者困惑用哪个断言。 | 等 spec_v2 修齐"10 个测试"后，tasks T-5 description 复核一致；建议 tasks T-5 也明示"4 个 sync 单元 + 6 个 @pytestmark_int 集成 = 10"。 |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| NTH-1 | tasks.md DAG 段 T-5 depends_on | T-5 当前 `depends_on: [T-3, T-4]`；T-3 间接含 T-2，但**不含 T-1**（T-1 改 model，T-2/T-3 alembic 不必经 T-1）。pytest 会反向校验 model 与 db 一致性？SQLAlchemy 反射不必，但 PipelineCacheORM 在测试代码被 import → ORM-level ondelete 影响 ORM cascade（应用层）。低风险但显式更稳。 | T-5 改 `depends_on: [T-1, T-3, T-4]` 显式（不影响并行度，T-1 与 T-3/T-4 仍可并发）。 |
| NTH-2 | tasks.md T-4 description uuid 前缀字串形态 | `f"# fixture-uuid {uuid.uuid4().hex}\n"` 用 `#` 开头是 markdown H1 注释。若未来某测试用 markdown-normalize 后验证 output 含特定结构（如标题层级），加 `#` 前缀会污染 silver。当前无此测试，但为防御性写法可用更"中性"前缀，如 `f"<!-- fixture-uuid {hex} -->\n"`（markdown HTML 注释，多数 normalize 会保留 / 直接 strip）。 | 评估是否改用 HTML 注释前缀；不阻塞 v2。 |
| NTH-3 | tasks.md 覆盖矩阵 | 矩阵已含 "AC kind" 列与 covers_ac，质量好。 | 无（保持）。 |

## Verdict

**REVISION REQUIRED**

理由：MUST FIX-1（联动 spec AC-1 grep pattern 缺陷）是阻塞型——T-6 self_check block 若照搬错的 pattern，整个 ac-kind / self_check 链路会持续误报。需先在 spec_v2 修好 AC-1 grep pattern，再让 tasks_v2 T-6 description 同步。MUST FIX 数：1。

## 复检指引

Generator 修 v2 后自查：

1. **依赖图 DAG 校验**：手画或 `grep "depends_on" tasks_v2.md` 列出每个 T-* 的 depends 关系，确认无环。
2. **覆盖矩阵**：每条 AC 至少一个非 process_tasks T-* 关联（当前 4/4 PASS，保持）。
3. **process_tasks 完整**：6 条齐全（spec-review/code-review/test-review/ci/deploy/user-confirm）。
4. **T-2 alembic API 明示**（SHOULD FIX-1）：description 含 `op.drop_constraint` + `op.create_foreign_key` 字面。
5. **T-3 前置检查**（SHOULD FIX-2）：description 含 `alembic current` 期望 `0004 (head)`。
6. **T-5 / spec AC-4 数字一致**（SHOULD FIX-3）：跟 spec_v2 AC-4 同步到"10 个测试"。
7. **T-6 description 引用 spec_v2 AC-1 新 pattern**（MUST FIX-1）。

提交 v2 后开 `tasks_review_v2.md`，复检 MUST FIX-1 状态。
