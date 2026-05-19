---
change_id: processor-pdf-mineru-20260519
target: tasks.md
target_version: 1
review_version: 1
reviewer: claude-agent:processor-pdf-mineru-20260519-stage2-reviewer-v1
reviewed_at: 2026-05-19T10:30:00Z
verdict: REVISION REQUIRED
---

# Tasks Review v1

## v0 MUST FIX 复检

不适用（本次为 v1 首次评审）。

---

## 检查清单结论（plan 模式 tasks.md）

| 项 | 结论 | 说明 |
|---|---|---|
| 每个任务粒度合理（1-3 小时） | PASS | T-1～T-6 均为单文件级别实现或本地验证，粒度合理 |
| depends_on 形成 DAG，没有循环 | PASS | 依赖链 T-1 → T-2 → T-3 → T-4 → T-5 → T-6，无环；T-4 也明确 depends_on [T-2, T-3] |
| 评审 / 单测 / CI / 部署阶段对应任务都存在 | PASS | process_tasks 含 P-spec-review / P-code-review / P-test-review / P-push / P-ci / P-deploy / P-user-confirm 全 7 项 |
| 没有 "做完整个系统" 类目标性任务 | PASS | 每个任务均指向具体文件或具体操作 |
| 每条 AC 至少有一个非 process_tasks 任务覆盖 | PASS | 覆盖矩阵显示 AC-1～AC-13 均有 T-1～T-6 中的至少一个覆盖 |
| T-5 _self_check.sh 集成方式与测试是否需要真实服务一致 | **FAIL** | T-5 指定 `run_ac_skipif_no_pg_minio_redis` for AC-10，但 test_pdf_mineru.py 不需要 pg/minio/redis（见 MUST FIX-4） |

---

## 问题列表

### MUST FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| MUST FIX-4 | tasks.md T-5 description 第 3 行 | **AC-10 错误使用 `run_ac_skipif_no_pg_minio_redis`**：T-5 写道 "AC-10 用 `run_ac_skipif_no_pg_minio_redis`（与 firecrawl 对齐）"。但 `test_firecrawl.py` 需要 pg/minio/redis 是因为它调用真实 `MinioBlobStore` + 真实 Redis queue；spec.md 明确说 `test_pdf_mineru.py` 使用 `monkeypatch.setattr("httpx.AsyncClient", _FakeAsyncClient)`，**不需要任何真实外部服务**。使用 `run_ac_skipif_no_pg_minio_redis` 会在无 pg/minio/redis 的 CI 环境中**静默 SKIP** AC-10 这条关键 behavioral AC，导致 "≥6 tests 全 PASS" 的行为强制形同虚设。已验证：`run_ac_skipif_no_pg_minio_redis` 在 pg 不通时直接 `SKIP++; return 0`，不运行 pytest。 | 将 T-5 中 AC-10 的调用改为无条件 `run_ac`，与 spec.md 中 "无真实 MinerU 依赖" + "monkeypatch httpx" 的设计一致。无需 `skipif` 包装。如果 pytest 本身的 fixture 在没有 pg/minio/redis 的环境下也会自行 skip，应在 test 层面用 `pytest.mark.skipif` 处理，而非在 _self_check.sh 层面隐藏整个 AC。 |

### SHOULD FIX

（本次无 SHOULD FIX 项。）

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| NICE-1 | tasks.md T-5 `covers_ac` 字段 | T-5 的 `covers_ac: [AC-11, AC-13]` 包含 AC-11（ruff+mypy 全 PASS），但 T-5 只是"追加 _self_check.sh 的 AC block"，AC-11 的**实际执行与验证**发生在 T-6（"本地 lint + 单测 + self_check current 全绿"）。T-5 声称覆盖 AC-11 略微夸大，覆盖矩阵将 AC-11 归到 T-5+T-6 中 T-6 是主要覆盖点。 | 可将 T-5 的 `covers_ac` 改为 `[AC-13]`（只负责 self_check 入口注册），AC-11 仅保留在 T-6，使语义更精确。不阻塞通过，但有助于 stage 6 reviewer 定位覆盖责任。 |

---

## Verdict

**REVISION REQUIRED**

存在 1 条 MUST FIX：

- MUST FIX-4：T-5 用 `run_ac_skipif_no_pg_minio_redis` 包装 AC-10，会在 pg/minio/redis 不通时静默 SKIP behavioral AC，削弱本次 change 的核心质量门禁。AC-10 是 "≥6 tests 全 PASS" 的行为验证入口，不可被环境因素跳过。

须将 T-5 AC-10 改为 `run_ac`（无条件），修后重提 tasks_review_v2。

---

## 复检指引

Generator 修完 tasks_v2 后，reviewer 复检命令：

```bash
# 复检 MUST FIX-4：T-5 不再使用 run_ac_skipif_no_pg_minio_redis
grep -n "run_ac_skipif_no_pg_minio_redis" \
  .harness/changes/processor-pdf-mineru-20260519/request_analysis/tasks.md \
  && echo "STILL USING SKIPIF - FAIL" || echo "PASS: no skipif in tasks.md"

# 复检 DAG 无环：依赖链还是 T-1→T-2→T-3→T-4→T-5→T-6
grep "depends_on" .harness/changes/processor-pdf-mineru-20260519/request_analysis/tasks.md

# 复检 process_tasks 仍含 6 节点
grep -cE "estimated_stage:.*(request_analysis_review|coding_review|unit_test_review|stage-7|deployment|user_confirmation)" \
  .harness/changes/processor-pdf-mineru-20260519/request_analysis/tasks.md

# 复检 AC-10 覆盖任务存在
grep "AC-10" .harness/changes/processor-pdf-mineru-20260519/request_analysis/tasks.md
```
