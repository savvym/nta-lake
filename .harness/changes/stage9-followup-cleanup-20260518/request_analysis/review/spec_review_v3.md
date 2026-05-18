---
change_id: stage9-followup-cleanup-20260518
target: spec.md
target_version: 3
review_version: 3
reviewer: claude-agent:stage9-followup-cleanup-20260518-stage2-reviewer-v3
reviewed_at: 2026-05-18T11:45:00Z
verdict: APPROVED
---

# Spec Review v3

## v2 MUST FIX / SHOULD / NICE 复检

| # | v2 类别 | v2 issue 摘要 | v3 状态 | 证据 |
|---|---|---|---|---|
| MUST FIX-1 | AC-3 grep -A 15 窗口（15 行）<<距 _seed_bronze→unique_content 的 27 行；同型 v1 MUST #1 bug | **CLOSED** | spec v3 AC-3 验证命令第 74 行改为 awk 状态机 `awk '/^async def _seed_bronze/{p=1;next} p && /^async def \|^def /{exit} p' apps/api/tests/test_pipeline_orchestrator.py \| grep -qE "uuid\.uuid4\(\)\.hex.*content\|unique_content.*=.*uuid"`。reviewer 本机两轮 dry-run 真跑：(a) pre-T-4（当前源码 `_seed_bronze` 内无 uuid 前缀）→ exit=1（fail，符合预期）；(b) python 注入 `unique_content = f"<!-- fixture-uuid {uuid.uuid4().hex} -->\n".encode() + content` 一行模拟 T-4 后跑 → exit=0（pass，符合预期）。awk 状态机捕获 _seed_bronze 函数体 67 行（pre 状态），远超原 -A 15 窗口；模式状态机敏感 |
| SHOULD FIX-1 | AC-2 缺 `alembic current` 前置 + tasks T-3 第 0 步对齐缺口 | **CLOSED** | spec v3 AC-2 验证命令第 73 行扩展为 `cd apps/api && export DATAPLAT_DATABASE_URL=... && uv run alembic current 2>&1 \| grep -q "0004" && uv run alembic upgrade head && uv run alembic downgrade 0004 && uv run alembic upgrade head && docker exec dataplat-pg-test psql -U dataplat -d dataplat -tA -c "SELECT delete_rule FROM information_schema.referential_constraints WHERE constraint_name='pipeline_cache_output_commit_hash_fkey';" \| grep -q "CASCADE"`。**前置** alembic current = 0004 + **后置** information_schema referential_constraints.delete_rule = CASCADE 双层断言齐全。期望表第 73 行同步注 "前置 alembic current = 0004；三连 upgrade/downgrade/upgrade 退码 0；最终 delete_rule = CASCADE" |
| NICE TO HAVE-1 | AC-3 grep 备用 pattern `uuid_prefix.*content` 与 T-4 描述（`unique_content = ...`）不一致冗余 | **CLOSED**（意外修） | spec v3 AC-3 grep 备用 pattern 由 `uuid_prefix.*content` 改为 `unique_content.*=.*uuid`，与 T-4 description 第 99 行 `unique_content = f"<!-- fixture-uuid {{uuid.uuid4().hex}} -->\n".encode() + content` 完全一致 |
| NICE TO HAVE-2 | 引用列表未含 v1/v2 review 路径作为审计链 | OPEN（不阻塞） | spec v3 引用段第 105-110 行仍未含 v1/v2 review 路径；不影响 verdict（NICE 项不阻塞）；可作 v4 优化或 close 时 deferred 记录 |

v2 全部 1 MUST FIX + 1 SHOULD FIX + 1/2 NICE TO HAVE 真闭环。

## stage 2 AC kind 字段必查（expert-reviewer SKILL § "stage 2 AC kind 字段必查"）

| 必查项 | 结果 | 证据 |
|---|---|---|
| (i) AC 表存在 `kind` 列 | **PASS** | `awk '/^## 验收标准/{p=1;next} p && /^## /{exit} p' spec.md \| grep -E '^\|[^\|]*\|[[:space:]]*kind[[:space:]]*\|'` 命中表头 `\| ID \| kind \| 描述 \| 验证方式 \| 期望 \|` |
| (ii) ≥1 行 AC kind 单元格真为 `behavioral`（AC 行 regex 锚定，**不接受裸字串 grep**） | **PASS** | `awk ... \| grep -E '^\|[[:space:]]*AC-[0-9]+[a-z]?[[:space:]]*\|[[:space:]]*(\*\*)?behavioral(\*\*)?[[:space:]]*\|'` 命中 2 行：AC-2 + AC-4，均以 `**behavioral**` 形式出现 |
| (iii) frontmatter 是否声明 `ac_kind_lint: exempt` | **N/A**（未声明） | `grep -c "ac_kind_lint" spec.md` = 0；本 change 不在自声明豁免清单；跳过 git diff 复核 |

必查 3 项全 PASS（与 v2 一致）。

## 跨 AC 一致性自审 9 条复检（request-analysis SKILL）

| # | 条目 | 结果 | 备注 |
|---|---|---|---|
| 1 | 跨 AC 矛盾词（事务内/前/外） | PASS | `grep -nE "事务内\|事务前\|事务外" spec.md` 无命中 |
| 2 | hash 字段 ↔ schema ↔ idempotency ↔ fixture 四链路 | PASS | 本 change 不涉及新 hash 字段 |
| 3 | 每条 AC 一行式验证命令 | PASS | 4 AC 全有 |
| 4 | 风险缓解 ↔ AC 测试列表 | PASS | 风险 #1→AC-2；风险 #2→AC-4；风险 #5（test_pipeline_e2e）显式 accept + follow-up |
| 5 | parents=[] 检查 | PASS | spec 无 `parents=[]` 字面 |
| 6 | 反向 grep 配 test -f + 不吞 stderr | PASS | 无 `! grep`；无 `2>/dev/null` |
| 7 | process_tasks 6 条必填 | PASS | tasks.md 含 6 条 process 节点 |
| 8 | AC 验证命令 dry-parse + dry-run | **PASS（v2 同型 bug 已修）** | AC-3 awk 状态机 pre/post 双轮 dry-run 全符合预期（详 v2 MUST FIX-1 闭环表证据段） |
| 9 | summary.md 模板占位符残留 | PASS | `grep -cE "<feature-slug>\|<YYYY-MM-DDTHH:MM:SSZ>\|<复述\|<bullet list>" summary.md` = 0 |

## 检查清单结论

- [x] 背景写明了为什么现在做（继承 pipeline-orchestrator-mvp stage 9 deploy_verify follow-up）
- [x] 问题陈述对外部读者可理解（Bug 1 / Bug 2 各自一段）
- [x] 范围 / 非范围都有（4 AC + 5 条 out of scope）
- [x] 每条 AC 可演示且可机械化 — AC-3 awk 状态机 pre/post dry-run 全符合预期，自此 AC-1/AC-2/AC-3/AC-4 全可机械化验证
- [x] 风险有缓解或显式 accept（5 条风险全有缓解，含 test_pipeline_e2e accept）
- [x] 没有把已有架构当新提案
- [x] 待澄清问题已清零
- [x] dogfood AC 分层规约（AC-2 + AC-4 标 behavioral；≥1 满足）

## 设计合理性评估

### 1. AC-3 awk 状态机修复（v2 MUST FIX-1 修复方案）

**合理且通过 reviewer 双轮 dry-run 验证**。reviewer 真跑：

```bash
# pre-T-4（当前 _seed_bronze 函数体无 unique_content）
awk '/^async def _seed_bronze/{p=1;next} p && /^async def |^def /{exit} p' \
    apps/api/tests/test_pipeline_orchestrator.py \
  | grep -qE "uuid\.uuid4\(\)\.hex.*content|unique_content.*=.*uuid"
# exit=1 ✓ (fail，符合 pre 预期；当前源码 _seed_bronze 内无 uuid 注入)

# post-T-4（python 注入 unique_content 行）
# 模拟 T-4：在 r_blob = await c.post(...) 之前插入
#   unique_content = f"<!-- fixture-uuid {uuid.uuid4().hex} -->\n".encode() + content
awk ... | grep -qE "uuid\.uuid4\(\)\.hex.*content|unique_content.*=.*uuid"
# exit=0 ✓ (pass，符合 post 预期)
```

awk 状态机锚定 `^async def _seed_bronze` 起、`^async def |^def ` 止——精准捕获函数体，不会跨入下一个函数，也不漏跨多行的 unique_content 行。grep 主备 pattern `uuid\.uuid4\(\)\.hex.*content` 与 `unique_content.*=.*uuid` 均能命中 T-4 实施形态。模式状态机敏感 + 形态包容。

### 2. AC-2 alembic current 前置 + information_schema 后置断言（v2 SHOULD FIX-1 修复方案）

**合理且断言完整**。

- **前置**：`alembic current 2>&1 | grep -q "0004"` — 验证 baseline 在 0004，避免 db 状态偏移时三连命令误判
- **三连**：upgrade head → downgrade 0004 → upgrade head — 验证 0005 migration upgrade/downgrade 双向干净
- **后置**：`docker exec ... psql -tA -c "SELECT delete_rule FROM information_schema.referential_constraints WHERE constraint_name='pipeline_cache_output_commit_hash_fkey'" | grep -q "CASCADE"` — 真查 PG catalog 验证 FK constraint 切换到 CASCADE。**这是真 behavioral**：不依赖 alembic 内部状态，直接从 PG information_schema 拿地面真相

期望段第 73 行三条断言齐全：前置 alembic current = 0004 / 三连退码 0 / 最终 delete_rule = CASCADE。tasks T-3 第 0 步与 spec AC-2 前置完全对齐。

### 3. AC-3 备用 pattern 与 T-4 实施形态对齐（v2 NICE TO HAVE-1 意外闭合）

**v3 把备用 pattern 从 `uuid_prefix.*content` 改成 `unique_content.*=.*uuid`，与 T-4 description 第 99 行 `unique_content = f"<!-- fixture-uuid {{uuid.uuid4().hex}} -->\n".encode() + content` 完全契合**。两个 pattern 形成"主（hex 字面）+ 备（变量名）"双保险，防御 T-4 实施时小幅措辞偏移（如局部变量改命名）。NICE 项意外闭合，质量提升。

### 4. v3 是否引入新缺陷？

reviewer 全文 diff + dry-run 排查：

- **AC-1 awk pattern 未动**（仍 v2 已验证的 PipelineCacheORM 类范围锚定，pre-T-1 RESTRICT 命中 / CASCADE 不命中；正确）
- **AC-2 加前置 + 后置断言不引入新风险**（前置 `grep -q "0004"` 期望 0004 baseline 与 tasks T-3 第 0 步一致；后置 information_schema 查询是 PG catalog 标准 API）
- **AC-3 awk 状态机仅替换 v2 `grep -A 15` 部分**，pattern 主备改为 `uuid\.uuid4\(\)\.hex.*content|unique_content.*=.*uuid`，dry-run 两轮全符合预期，无新风险
- **AC-4 未动**（行为型 pytest 真跑 10 个测试）
- **风险表 / 非范围 / 决策表均未动**
- **frontmatter version=3 / prior_version=2 / prior_review=v2.md** — 版本链规范

**reviewer 确认：v3 不引入新缺陷**。

### 5. AC-2 / AC-4 真 behavioral 复核

仍真 behavioral：

- AC-2 → L3（脚本真跑断言）：alembic upgrade/downgrade 三连 + information_schema referential_constraints 真查
- AC-4 → L2（ASGITransport in-process roundtrip via pytest 集成）：10 个测试真跑

满足 SKILL § "AC 分层规约" ≥1 条 behavioral AC 硬约束。

## 问题列表

### MUST FIX

无。

### SHOULD FIX

无。

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| NTH-1 | spec.md §引用 | 引用列表仍未含 v1/v2 review 路径作为审计链（v2 NICE TO HAVE-2 仍 open，可选） | 加 `request_analysis/review/spec_review_v1.md` + `spec_review_v2.md` 到引用，方便追溯；不阻塞 v3 通过 |

## Verdict

**APPROVED**

理由：MUST FIX 数 = 0 → verdict 唯一判据满足。v2 全部 1 MUST FIX + 1 SHOULD FIX + 1/2 NICE TO HAVE 真闭环（reviewer 双轮 dry-run + diff 复核）。v3 不引入新缺陷。AC-3 awk 状态机模式状态机敏感（pre fail / post pass）；AC-2 前置 + 后置断言完整；AC-3 备用 pattern 与 T-4 实施形态对齐。AC kind 必查 3 项全 PASS。9 条跨 AC 自审全 PASS（其中第 8 条 v2 失败项已通过 awk 修复 + 真跑 dry-run 转 PASS）。可进入 stage 3 coding。

## 复检指引

stage 3 generator 开始 coding 前自查：

1. **T-1 实施确认**：`apps/api/dataplat_api/models/pipeline.py` 第 88 行 `PipelineCacheORM.output_commit_hash` ForeignKey `ondelete="RESTRICT"` → `ondelete="CASCADE"`；跑 AC-1 awk pattern 确认 pre 失败 → post 成功
2. **T-2 实施确认**：新建 `apps/api/alembic/versions/0005_pipeline_cache_fk_cascade.py` 含 `revision="0005"; down_revision="0004"; branch_labels=None`；upgrade/downgrade 用 `op.drop_constraint` + `op.create_foreign_key` 高层 API
3. **T-3 三连真跑**：`alembic current` 期望 0004 → `upgrade head` → `downgrade 0004` → `upgrade head`；三步退码 0；最终 information_schema referential_constraints.delete_rule = CASCADE
4. **T-4 实施确认**：`_seed_bronze` 函数体加 `unique_content = f"<!-- fixture-uuid {{uuid.uuid4().hex}} -->\n".encode() + content` 一行；r_blob post 用 `content=unique_content`；跑 AC-3 awk pattern 确认命中
5. **T-5 pytest 真跑**：10 passed（4 sync + 6 async @pytestmark_int；含 3 个 cache_hit 测试）
6. **T-6 self_check block**：scripts/_self_check.sh 加 `run_stage9_followup_cleanup`；引用 spec v3 AC-1..AC-4 awk pattern；run_ac 计数 +1
