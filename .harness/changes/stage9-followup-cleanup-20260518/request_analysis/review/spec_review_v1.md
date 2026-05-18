---
change_id: stage9-followup-cleanup-20260518
target: spec.md
target_version: 1
review_version: 1
reviewer: claude-agent:stage9-followup-cleanup-20260518-stage2-reviewer-v1
reviewed_at: 2026-05-18T11:25:00Z
verdict: REVISION REQUIRED
---

# Spec Review v1

## stage 2 AC kind 字段必查（expert-reviewer SKILL § "stage 2 AC kind 字段必查"）

| 必查项 | 结果 | 证据 |
|---|---|---|
| (i) AC 表存在 `kind` 列 | **PASS** | `awk '/^## 验收标准/{p=1;next} p && /^## /{exit} p' spec.md \| grep -E '^\|[^\|]*\|[[:space:]]*kind[[:space:]]*\|'` 命中 `\| ID \| kind \| 描述 \| 验证方式 \| 期望 \|` |
| (ii) ≥1 行 AC kind 单元格真为 `behavioral`（AC 行 regex 锚定） | **PASS** | `awk ... \| grep -E '^\|[[:space:]]*AC-[0-9]+[a-z]?[[:space:]]*\|[[:space:]]*(\*\*)?behavioral(\*\*)?[[:space:]]*\|'` 命中 2 行：AC-2 + AC-4，均以 `**behavioral**` 形式出现 |
| (iii) frontmatter 是否声明 `ac_kind_lint: exempt` | **N/A**（未声明） | `grep -c "ac_kind_lint" spec.md` = 0；本 change 不在自声明豁免清单；跳过 git diff 复核（按 SKILL 规约） |

必查 3 项全 PASS（机械化守门通过）。

## 跨 AC 一致性自审 9 条复检（request-analysis SKILL）

| # | 条目 | 结果 | 备注 |
|---|---|---|---|
| 1 | 跨 AC 矛盾词（事务内/前/外） | PASS | `grep -nE "事务内\|事务前\|事务外" spec.md` 无命中 |
| 2 | hash 字段 ↔ schema ↔ idempotency ↔ fixture 四链路 | PASS | 本 change 不涉及新 hash 字段；只是修 FK + fixture |
| 3 | 每条 AC 一行式验证命令 | PASS | 4 AC 全有；命令计数 ≥ 5（实测 5 行 grep 计数） |
| 4 | 风险缓解 ↔ AC 测试列表 | PASS | 风险 #1 缓解→AC-2；风险 #2 缓解→AC-4 |
| 5 | parents=[] 检查 | PASS | spec 无 `parents=[]` 字面 |
| 6 | 反向 grep 配 test -f + 不吞 stderr | PASS | 无 `! grep`；无 `2>/dev/null` |
| 7 | process_tasks 6 条必填 | PASS | tasks.md 中 P-spec-review/P-code-review/P-test-review/P-ci/P-deploy/P-user-confirm 齐 |
| 8 | AC 验证命令 dry-parse | PASS | AC-1/2/3 命令 `bash -n -c "..."` 退码 0；AC-4 是直接 pytest 调用无复合语句风险 |
| 9 | summary.md 模板占位符残留 | PASS | `grep -cE "<feature-slug>\|<YYYY-MM-DDTHH:MM:SSZ>\|<复述\|<bullet list>" summary.md` = 0 |

跨 AC 自审 9 条全 PASS。

## 检查清单结论

- [x] 背景写明了为什么现在做（继承自 pipeline-orchestrator-mvp stage 9 deploy_verify follow-up，实证起源清晰）
- [x] 问题陈述对外部读者可理解（Bug 1 / Bug 2 各自 1 段说明）
- [x] 范围 / 非范围都有（4 AC + 5 条 out of scope 显式列出 follow-up）
- [x] 每条 AC 可演示且可机械化（kind 列 + 一行式验证命令）
- [x] 风险有缓解或显式 accept（4 条风险全有缓解）
- [x] 没有把已有架构当新提案（明确不改 commits.hash PK 语义、不改 0004 migration）
- [x] 待澄清问题已清零（v1 启动时已澄清）
- [x] dogfood 新 AC 分层规约（AC-2 + AC-4 标 behavioral；满足 ≥1）

## 设计合理性评估

### 1. alembic 0005 DROP CONSTRAINT + ADD CONSTRAINT 模式
**合理**。PostgreSQL 标准做法，FK constraint name `pipeline_cache_output_commit_hash_fkey` 是 stage 9 错误日志已验证存在的隐式默认名。但 spec 决策表只描述"ALTER TABLE ... SQL"语义，未明示 alembic 高层 API（`op.drop_constraint` + `op.create_foreign_key`），实现者可能纠结裸 `op.execute("ALTER ...")` vs 高层 API。属 tasks 实现细节问题（详 tasks_review）。

### 2. `_seed_bronze` 加 uuid 前缀的影响
**合理但措辞需校准**。实读 6 个调用点（test_pipeline_orchestrator.py 第 406/478/532/589/654/703 行）：
- 第 406/478/532/703 行：用 `_src_repo, src_commit = await _seed_bronze(...)` 返回的 `src_commit` 进 `compute_cache_key([src_commit], ...)` —— 因 uuid 前缀后 content 不同 → 新 blob_sha → 新 commit_hash 自动反映在返回值，**断言全用返回值，不依赖 raw content**。
- 第 589/654 行：只 `await _seed_bronze(...)` 抛弃返回值 —— 更无关。
- spec 第 60 行决策表写"测试断言不依赖 raw content 字串"，**技术上对**但措辞模糊；更准确表达："测试断言依赖的是 `_seed_bronze` 返回的 commit_hash，content 内容只在 seed 期被 hashed，不被任何 assertion 读取"。**NICE TO HAVE**：精化决策表理由。

### 3. test_pipeline_e2e.py 也有 `_seed_bronze` 但 spec 显式不改
**勉强可接受，但风险未在 risk 表显式记录**。该文件第 172 行也有同名 `_seed_bronze`（独立函数），第 305 行 `raw = b"hello\r\nworld   \r\n\r\n\r\n\r\nend\r\n"` —— 与 test_pipeline_orchestrator 的 hardcoded content 不同字串，与 stage 9 demo 用的 `sample.md` 内容也不同。stage 9 没 trigger 撞是事实。但隐患是**未来同测试多次重跑撞自己**（同 content 第二次进 db 必撞 commits.hash PK）—— spec 在"不受影响但易混淆模块"段说"如未来累积证据再 follow-up"，但**未在 risk 表显式列出**。**SHOULD FIX**：在 risk 表加一条"test_pipeline_e2e.py 同名 fixture 隐患"，附 follow-up `test-fixture-isolation-other-files-*` 显式 accept。

### 4. FK 选 CASCADE vs SET NULL 决策不充分
**SHOULD FIX**。spec 决策表第 56 行只说"cache_key 指向无效 commit 无意义"，但**真正硬约束是 `PipelineCacheORM.output_commit_hash` 当前 `nullable=False`**（model 第 86-90 行）—— SET NULL **物理上违反 NOT NULL 约束**，根本行不通。spec 漏掉这个技术硬约束，理由只停留在语义层。**建议**：决策表加一句"PipelineCacheORM.output_commit_hash nullable=False，SET NULL 不可行（需先改 NOT NULL，超出 scope）"。

### 5. AC-2 / AC-4 真 behavioral？
**真 behavioral**（L3 / L2）：
- AC-2：真跑 `alembic upgrade head` + `alembic downgrade 0004` + `alembic upgrade head` 三连，并查 `information_schema.referential_constraints.delete_rule` 后置 SQL 断言 → L3（脚本真跑断言）
- AC-4：`uv run pytest -q apps/api/tests/test_pipeline_orchestrator.py` 全集成测试真跑 → L2（ASGITransport in-process roundtrip）

满足 SKILL § "AC 分层规约"硬约束（≥1 条 behavioral AC）。

## 问题列表

### MUST FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| MUST FIX-1 | spec.md §验收标准 AC-1 验证命令 | `grep -A 2 "output_commit_hash.*ForeignKey" apps/api/dataplat_api/models/pipeline.py \| grep -q 'ondelete="CASCADE"'` **永远 fail**，因为 model 文件中 `output_commit_hash` 与 `ForeignKey` **不在同一行**（第 86 行 `output_commit_hash: Mapped[str] = mapped_column(` 后换行，第 88 行才是 `ForeignKey(...)`）。pattern `"output_commit_hash.*ForeignKey"` 同行匹配 anchor 永远不命中 → 即使 T-1 改 RESTRICT→CASCADE 也无法满足 AC。实测：当前文件 `grep -A 2 "output_commit_hash.*ForeignKey" pipeline.py` 返空。 | 改为 `grep -A 3 "output_commit_hash: Mapped\[str\] = mapped_column" pipeline.py \| grep -q 'ondelete="CASCADE"'`（anchor 锚 PipelineCacheORM 的字段定义起点，不锚第 68 行 PipelineNodeRunORM 的 `Mapped[str \| None]`），或用 `awk '/^class PipelineCacheORM/,/^class /' pipeline.py \| grep -q 'ondelete="CASCADE"'`（范围限定到 PipelineCacheORM）。务必本地 dry-run pre-T-1 + post-T-1 两轮，确保 pre 状态 fail、post 状态 pass。 |

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| SHOULD FIX-1 | spec.md §关键决策（在 summary.md，FK CASCADE 理由） | 理由只写"cache_key 指向无效 commit 无意义"语义层，漏掉技术硬约束：`PipelineCacheORM.output_commit_hash` 当前 `nullable=False`（model 第 86-90 行），SET NULL 物理不可行（违反 NOT NULL）。这条硬约束让 CASCADE 几乎是唯一选项，理由更扎实。 | 决策表加一句："PipelineCacheORM.output_commit_hash nullable=False，SET NULL 违反 NOT NULL 约束，需先改 nullable=True，超出本 change scope，故 CASCADE 是当下唯一可行选项"。 |
| SHOULD FIX-2 | spec.md §风险 表 | risk 表未显式记录 test_pipeline_e2e.py 也有同名 `_seed_bronze` 且也用 hardcoded `b"hello\r\nworld   \r\n\r\n\r\n\r\nend\r\n"`，未来该测试多次重跑同 db 必撞 commits.hash PK。spec 只在"不受影响但易混淆模块"段一句话提及，但隐患不在 risk 表 → 评审者 / 实现者容易遗漏。 | risk 表加一条："test_pipeline_e2e.py 同名 _seed_bronze 未跟修；本 change 显式 accept（stage 9 未 trigger 撞，CI 单跑也不撞）；follow-up `test-fixture-isolation-other-files-*` 待累积证据再处理"。 |
| SHOULD FIX-3 | spec.md §验收标准 AC-4 描述 vs 期望 | AC-4 描述说"7 集成测试全 PASS"，但期望写"N ≥ 10"；实测 test_pipeline_orchestrator.py 含 **10 个 test_** 函数（4 个 sync + 6 个 @pytestmark_int async）。"7"是错的，"≥10"对（覆盖 sync 单元 4 个 + async 集成 6 个全跑）。两处数字打架 → 实现者会困惑用哪个数字断言。 | AC-4 描述改为"`test_pipeline_orchestrator.py` 全部 10 个测试 PASS（4 个 sync 单元 + 6 个 @pytestmark_int 集成；含 stage 9 后曾 FAIL 的 3 个 cache_hit 测试）"。 |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| NTH-1 | spec.md §关键决策（_seed_bronze uuid 前缀） | "测试断言不依赖 raw content 字串"措辞略模糊；更准确："测试断言依赖 `_seed_bronze` 返回的 commit_hash，content 只在 seed 期被 hashed，不被任何 assertion 读取" | 决策表第 3 行措辞精化（不阻塞）。 |
| NTH-2 | spec.md §验收标准 AC-1 0005 文件 glob | `test -f apps/api/alembic/versions/0005_*.py` 用 `test -f` + shell glob，若未来同期出现多个 0005 变体会 `too many arguments`。当前 0 / 1 个匹配 OK，但形态脆弱。 | 改为 `ls apps/api/alembic/versions/0005_*.py >/dev/null 2>&1 && grep -q "CASCADE" apps/api/alembic/versions/0005_*.py`（ls 不报多匹配错；后续 grep 多文件本来就支持）。或用具体文件名 `test -f apps/api/alembic/versions/0005_pipeline_cache_fk_cascade.py`（与 T-2 文件名约定一致）。 |
| NTH-3 | spec.md §验收标准 AC-1 0004 grep RESTRICT | `grep -q "RESTRICT" 0004_pipeline_orchestrator.py` 用裸 RESTRICT，未来若有其他无关字串含 RESTRICT 可误命中。更精确：`grep -q 'ondelete="RESTRICT"' 0004_pipeline_orchestrator.py`。 | 加 `ondelete="..."` 前缀锚定。 |

## Verdict

**REVISION REQUIRED**

理由：MUST FIX-1（AC-1 grep pattern 永远 fail，因为 model 文件 `output_commit_hash` 与 `ForeignKey` 不在同一行）是阻塞型缺陷——T-1 改对了代码 spec AC 也会判定 FAIL，self_check 会持续误报。必须修后再评。MUST FIX 数：1 → verdict 唯一判据未通过。

## 复检指引

Generator 修 v2 后自查：

1. **修复 AC-1 grep pattern**：在 dev 本机两轮 dry-run：
   ```bash
   # pre-T-1：模型仍 RESTRICT
   <新 AC-1 第一段命令>; echo "pre-T-1 exit=$? expect=非0"
   # post-T-1：手动模拟改成 CASCADE
   sed -i 's/ondelete="RESTRICT"/ondelete="CASCADE"/' apps/api/dataplat_api/models/pipeline.py
   <新 AC-1 第一段命令>; echo "post-T-1 exit=$? expect=0"
   git checkout apps/api/dataplat_api/models/pipeline.py  # 回滚
   ```
   确认 pre fail / post pass，再写进 spec_v2。

2. **决策表加 nullable=False 硬约束理由**（SHOULD FIX-1）。

3. **risk 表加 test_pipeline_e2e.py 隐患条目**（SHOULD FIX-2）。

4. **AC-4 数字校准**：`grep -cE "^(async )?def test_" apps/api/tests/test_pipeline_orchestrator.py` 期望 10；spec 描述改为 10 与命令的 ≥10 一致（SHOULD FIX-3）。

5. NICE TO HAVE 三条可选改进；不阻塞 v2 通过。

6. 提交 v2 后开 `spec_review_v2.md`，复检上述 MUST FIX 状态。
