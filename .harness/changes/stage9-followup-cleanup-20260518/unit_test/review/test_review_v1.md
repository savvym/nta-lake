---
change_id: stage9-followup-cleanup-20260518
target: test_report_v1.md
target_version: 1
review_version: 1
reviewer: claude-agent:stage9-followup-cleanup-20260518-stage6-reviewer-v1
reviewed_at: 2026-05-18T12:25:00Z
verdict: APPROVED
---

# Test Review v1

> 评审范围：`unit_test/test_report_v1.md` + 实际测试载体（`apps/api/tests/test_pipeline_orchestrator.py` 中 `_seed_bronze` / `_delete_repo_cascade` / 3 个 cache_hit 测试 + stage 3 偏离扩展）+ self_check block (`scripts/_self_check.sh::run_stage9_followup_cleanup`)。
> 工作 SOP：expert-reviewer SKILL artifact 模式 + reviewer-agent §5。
> 模式：artifact（spec → test report 覆盖核对）。

## 检查清单结论（expert-reviewer §1 artifact 模式）

| 检查项 | 结论 | 备注 |
|---|---|---|
| 每条 spec AC 都映射到至少一条具体测试用例 | PASS | AC-1..AC-4 均映射到 self_check 子断言 + （行为型）真跑 |
| 没有空跑断言（assert True / != None 充数） | PASS | cache_hit 三测试断言具体语义：`call_count["n"] == 0` / `ref.commit_hash == src_commit` / `input_commits_json == [src_commit]` / `ck == cache_key` |
| Mock 范围与 coding-style §1.7 一致（数据访问层禁 mock） | PASS | DB / MinIO / Redis 全真跑；只 fake LLM provider；`ProcessorRunner.run` 用 spy 不替换语义 |
| 测试名能反映场景 | PASS | `test_cache_hit_skips_processor` / `test_cache_hit_updates_ref` / `test_cache_hit_writes_audit_fields` 命名清楚 |

## 跨 AC 自审（独立复核 spec ↔ test 覆盖）

| 维度 | 结论 |
|---|---|
| AC-1（static FK CASCADE 双重锚定） | self_check 4 条 grep 全锚定（model awk 状态机 + 0005 ls + 0005 grep + 0004 RESTRICT 保留） |
| AC-2（behavioral alembic 三连 + delete_rule） | **部分覆盖**（见 SHOULD #1）：手动证据三连真跑通过；self_check 只查 "current=0005 + delete_rule=CASCADE" 后状态，不机械化跑三连 |
| AC-3（static uuid 前缀注入） | 测试载体真改：第 284-286 行 `unique_content = f"<!-- fixture-uuid {uuid.uuid4().hex} -->\n".encode() + content`；self_check awk 状态机锚定 _seed_bronze 函数体 + `uuid.uuid4().hex.*content\|unique_content.*=.*uuid` 正则真命中 |
| AC-4（behavioral pytest 10/10） | reviewer 本人真跑两个 cache_hit 测试（`test_cache_hit_updates_ref` + `test_cache_hit_writes_audit_fields`）→ **2 passed in 2.84s**；self_check 全 10 测试也通过 |
| stage 3 偏离（跨 repo refs cleanup）覆盖 | **PASS（reviewer 实证）**：见下文 §"stage 3 偏离 独立验证" |
| 边界场景（silver/tgt ref → bronze commit 残留） | reviewer 手工构造残留场景 → cleanup 不报错（见 §残留实证） |

## reviewer 真跑实证

### 1) cache_hit 测试单跑（验 test report §测试真跑证据 AC-4）

```text
$ cd apps/api && DATAPLAT_DATABASE_URL=... DATAPLAT_JWT_SECRET=... \
  DATAPLAT_MINIO_ENDPOINT=http://localhost:9100 \
  DATAPLAT_MINIO_ACCESS_KEY=dataplat DATAPLAT_MINIO_SECRET_KEY=dataplat-secret \
  DATAPLAT_REDIS_URL=... DATAPLAT_LLM_PROVIDER=fake \
  uv run pytest -v tests/test_pipeline_orchestrator.py::test_cache_hit_updates_ref \
                   tests/test_pipeline_orchestrator.py::test_cache_hit_writes_audit_fields

tests/test_pipeline_orchestrator.py::test_cache_hit_updates_ref PASSED   [ 50%]
tests/test_pipeline_orchestrator.py::test_cache_hit_writes_audit_fields PASSED [100%]
============================== 2 passed in 2.84s ===============================
```

→ test_report v1 §测试真跑证据声明的 cache_hit 真跑可复现。

### 2) alembic 当前状态独立查（验 AC-2 后置）

```text
$ cd apps/api && DATAPLAT_DATABASE_URL=... uv run alembic current
0005 (head)
```

→ 与 test_report v1 §AC-2 真跑证据声明一致。

### 3) stage 3 偏离 独立验证：残留 silver ref → bronze commit + cache 行场景下 cleanup 不报错

**构造**：手工 INSERT 一条 silver.main ref 指向 bronze commit + 一条 pipeline_cache 指向同 bronze commit，**不**走 orchestrator（绕过 cache_hit 测试本身），模拟"测试中途异常退出 / fixture 残留"边界。

```text
PRE: cross_repo_refs=1, cache_rows=1
CLEANUP src (_delete_repo_cascade owner src bronze): OK (no FK violation)
CLEANUP tgt (_delete_repo_cascade owner tgt silver): OK
POST: commits=0, refs=0, cache=0
ALL OK
```

→ 验证：`_delete_repo_cascade` 加的两段逻辑（"DELETE FROM refs WHERE commit_hash IN (SELECT hash FROM commits WHERE repo_id=:r)" + 显式 pipeline_cache cleanup）真起作用，跨 repo refs 残留 + cache 残留都被清理；后续 commits/repos 删除不撞 FK。脚本 `/tmp/test_residual_cleanup.py` 已留存于本机供复核。

## 问题列表

### MUST FIX

无。

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| SHOULD #1 | `scripts/_self_check.sh::run_ac AC-2` (line 1324-1325) | AC-2 spec 定义是 **alembic upgrade head → downgrade 0004 → re-upgrade head 三连**（spec.md AC-2 验证方式）+ delete_rule 终态断言。self_check 实现只查 `alembic current` 当前等于 0005 + delete_rule=CASCADE，**不**真跑三连 → upgrade 路径 idempotency / downgrade 路径 RESTRICT 恢复未被机械化覆盖。手动证据（coding_report v1 §Fixture-bug 真跑闭环）跑过一次，但脱离 self_check 不可复跑。 | 考虑给 AC-2 加 self_check 子断言：`alembic downgrade 0004 && alembic upgrade head && <delete_rule 检查>`（或拆 AC-2a/2b：2a 终态 grep，2b 真跑三连）；如不修需在 summary.md deferred 段记录"AC-2 三连覆盖只在手动 coding 阶段，self_check 不复跑"以满足偏离记录硬约束 |
| SHOULD #2 | `apps/api/tests/test_pipeline_orchestrator.py::_delete_repo_cascade` (line 219-227) | cleanup 序列假设"先 src 后 tgt"或"先 tgt 后 src"都安全，**但**如果 fixture 抛在 `_create_silver_repo` 之后、`_run_orchestrator` 之前，`_delete_repo_cascade(owner, src)` 在 finally 中先跑 → 此时 silver 还没有跨 ref → cleanup 正常；若 cache_hit 跑了一半异常（orchestrator 已 update silver.main → bronze commit），`_delete_repo_cascade(owner, src)` 先跑时 step 2（跨 repo refs）已覆盖；**但** `_delete_repo_cascade(owner, tgt)` 若先跑会 step 1（删 silver 自己的 refs）已清了跨 ref，再删 src 时 step 2 不再命中——两种顺序都安全 ✓。但 test 用例总是 src 在前 tgt 在后（line 472-473, 540-541, 591-592, 653-654, 711-712, 767-768），未独立测试"逆序删除"边界 → 这只是 **不变量观察**，非阻塞 | 不阻塞；建议在 coding_report 或 summary.md "复盘"段记录"cleanup 顺序对 cross-ref 都安全的不变量"作为未来 refactor 的护栏 |
| SHOULD #3 | `test_pipeline_orchestrator.py` 全文件 | 单元测试（无 DB）共 4 个（`test_unknown_processor` / `test_cycle` / `test_unknown_node_ref` / `test_multi_input_rejected`）均不依赖 `_seed_bronze`，不会撞 commits.hash PK。但本 change AC-3 仅修 `_seed_bronze`，未影响这 4 个单元测试，coverage 完整。**仅记录**：spec 风险表 "test_pipeline_e2e.py 同名 _seed_bronze 未跟修" 已 explicit accept + follow-up `test-fixture-isolation-other-files-*`，符合 deferred 流程；reviewer 不重复阻塞 | 不阻塞 |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| NTH #1 | `test_report_v1.md` §覆盖维度 表 "markdown-normalize 对 HTML 注释前缀的处理 ✓ stage 4 reviewer 实读 processors/markdown_normalize.py" | 此条说"stage 4 reviewer 实读"，但 stage 4 review 文件尚未生成（summary.md stage=unit_test_review，coding_review pending）。措辞有时间穿越嫌疑 | 改措辞为"coding 阶段 generator 自查 processors/markdown_normalize.py 不当作 markdown H1 处理"或留待 stage 4 review 写后再回填证据 |
| NTH #2 | `test_report_v1.md` §测试文件清单 | "4 sync + 6 async@pytestmark_int" 但实际看 test_pipeline_orchestrator.py：4 sync (60-133 行) + 6 async 集成（test_lineage_written_on_cache_miss / test_cache_hit_skips_processor / test_cache_hit_updates_ref / test_node_value_error_marks_failed_with_null_audit / test_node_400_marks_failed / test_cache_hit_writes_audit_fields） — 数对，但 "@pytestmark_int" 实际是 module-level 变量 `pytestmark_int` 不是装饰器宏定义，建议明示"每个 async 测试用 @pytestmark_int 装饰跳过条件" | 措辞精确化 |
| NTH #3 | `_self_check.sh::run_ac AC-3` | grep regex `"uuid\.uuid4\(\)\.hex.*content\|unique_content.*=.*uuid"` 两个分支都能命中现状（`unique_content = f"<!-- fixture-uuid {uuid.uuid4().hex} -->\n".encode() + content`），但 `uuid.uuid4().hex.*content` 分支命中的是 `uuid.uuid4().hex} -->\n".encode() + content`，跨字串属于巧合；如果未来重构改为 `prefix = uuid_str; content = prefix + content` 第一分支仍命中而无 unique_content 字面量也无明确语义保护——锚定虽然可保护命名变迁，**但**保护强度有限 | 强化为 `unique_content.*=.*uuid\.uuid4\(\)\.hex` 单一分支（既要变量名也要 uuid 注入），或加 `<!-- fixture-uuid` 字面量锚定。低优先级 |

## Mock 范围审查（unit-test-write SKILL §核对）

| 类别 | 实际做法 | 与 coding-style §1.7 一致？ |
|---|---|---|
| DB（PG） | 真跑（DATAPLAT_DATABASE_URL→local 5433）| ✓ 数据访问层未 mock |
| Blob（MinIO） | 真跑（`_override_blob_store` fixture monkeypatch 到 uuid 唯一 bucket）| ✓ 数据访问层未 mock；只换 bucket name |
| Redis | 真连（`_redis_reachable` 探针）| ✓ |
| LLM provider | `DATAPLAT_LLM_PROVIDER=fake` | ✓ 业务外部依赖允许 fake |
| `ProcessorRunner.run`（cache_hit 测试） | spy（call_count++ 后 `return await original_run(*args, **kwargs)`） | ✓ 不替换语义，只观测调用次数；本质是断言辅助 |
| `ProcessorRunner.run`（test_node_400_marks_failed） | monkeypatch 抛 HTTPException(400) 模拟外部 processor 错误 | ✓ 边界注入，等价 fault-injection，符合 unit-test-write SKILL 允许范围 |

**结论**：Mock 范围审查 PASS。

## Verdict

**APPROVED**。

理由：
1. AC-1..AC-4 覆盖完整；2 条 behavioral AC（AC-2 + AC-4）真跑可复现，reviewer 独立复跑 cache_hit 测试 + alembic current 探针 + 残留场景 cleanup 全 PASS。
2. stage 3 偏离（_delete_repo_cascade 加跨 repo refs cleanup）reviewer 独立构造残留场景验证有效，不只 "happy path 通过 cleanup 失败静默"。
3. Mock 范围符合 coding-style §1.7。
4. MUST FIX 数 = 0；SHOULD #1（AC-2 self_check 三连机械化不全）建议但不阻塞，generator 可选择修或在 summary.md deferred 段记录偏离。
5. 测试断言具体，无空跑；测试命名清晰。

## 复检指引

generator 收到 APPROVED 后：
1. 推 stage 7（commit + push 或 self-attest CI）；本 change branch=main 无 remote，按 deferred 处理。
2. **若决定修 SHOULD #1**（AC-2 self_check 三连机械化）：改 `scripts/_self_check.sh::run_stage9_followup_cleanup` AC-2 子断言，加 `alembic downgrade 0004 && alembic upgrade head` 二步；运行 `bash scripts/_self_check.sh` 期望 AC-2 仍 PASS + 整体 252/252 不退化。
3. **若选择 deferred SHOULD #1**：在 summary.md "Deferred 项" 段新增"AC-2 三连覆盖只在 coding 手动证据，self_check 不复跑；理由：成本 / 优先级；跟进：follow-up `self-check-alembic-cycle-coverage-*` 或不跟进"。
4. 同步 summary.md stage 6 子项追加：`v1`、verdict=APPROVED、MUST FIX=0、报告路径=`unit_test/review/test_review_v1.md`。
5. 进入 stage 7（推送 / self-attest）和 stage 9（deploy_verify 必须真跑——0005 migration + 测试 fixture 改）。
