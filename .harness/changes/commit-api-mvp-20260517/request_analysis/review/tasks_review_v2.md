---
change_id: commit-api-mvp-20260517
target: tasks.md
target_version: 2
review_version: 2
reviewer: claude-stage2-reviewer-v2
reviewed_at: 2026-05-17T10:00:00Z
verdict: APPROVED
---

# Tasks Review v2

> 本次只复核 v1 MUST FIX（3 条）的消化情况，并扫描 v2 是否引入新 MUST FIX。SHOULD FIX / NICE TO HAVE 不重复评审。

## 检查清单结论

> 引用 `.harness/skills/expert-reviewer/SKILL.md` §1 plan 模式 tasks 列表。

- [x] 每个任务粒度合理（T-1~T-8 均在 1-3h 范围；T-3 含 hash + 事务 + 幂等三块，仍可控）。
- [x] depends_on 形成 DAG，无循环（T-1 → {T-2, T-3} → T-4 → T-5 → T-6 → T-7；T-8 独立 process task）。依赖图 L155-160 与各 task 头部 depends_on 字段一致。
- [x] 评审 / 单测 / CI 阶段对应任务都存在（T-6 单测、T-7 self_check；process_tasks 由 summary.md 跟踪，与 cas-storage / repo-api-mvp 节奏一致）。
- [x] 没有"做完整个系统"类目标任务（粒度精确到文件路径）。
- [x] 每条 AC 都有非 process_tasks 任务覆盖（AC-1→T-1, AC-2/7→T-2, AC-3/8/9/10→T-3, AC-4/5/6→T-4, AC-5→T-5, AC-11→T-6, AC-12 由 ruff/mypy 命令在 T-7 self_check 块自跑或 CI 阶段; AC-13→T-7）。

## v1 MUST FIX 消化复核（3/3）

| # | v1 问题摘要 | 复核位置 | 消化状态 | 证据 |
|---|---|---|---|---|
| 1 | T-2 depends_on 标"无（可并行）"违反 DAG 实际 | tasks L42 | **CLOSED** | T-2 显式 `**depends_on: T-1**（import BlobUploadResponse 必须先有 T-1）`，依赖图 L156 同步（`T-1 (schemas) ─┬──→ T-2 (BlobService)`）。 |
| 2 | T-3 created_at 与 spec v2 必须一致 | tasks L26、L53、L58、L63 | **CLOSED** | (a) L26 CommitCreate **不含** created_at（spec v2 AC-9 方案 B）；(b) L53 `_canonical_commit_bytes(tree_hash, parents, author_id, message, lineage_canonical)` 参数列表**不含 created_at**；(c) L58 步骤 2 "算 tree_hash + commit_hash（**不含 created_at**）"；(d) L63 INSERT 时仍存 `created_at=datetime.utcnow()` 作 audit 字段（与 spec v2 一致：record 但不参与 hash）。四链路完全对齐。 |
| 3 | T-6 测试数与 spec v2 AC-11 ≥ 15 (16) 一致 | tasks L113-131 | **CLOSED** | 显式列出 18 个测试函数：a, b, c, d, e, f, g1, g2, h, i, j, k, l, m, n, o, p, q（其中 g1 是 hash 单元、n 是 2MB round-trip、o 是 lineage round-trip、p/q 是 user×internal/private commit visibility），完全覆盖 spec v2 AC-11 a~q。awk grep 实跑命中 18 条。 |

**MUST FIX 残留 = 0**

## 复检命令实跑结果

```
awk '/^## T-2/,/^## T-3/' tasks.md | grep -E "depends_on:\s*T-1" → 命中 "**depends_on: T-1**"
grep -nE "created_at" tasks.md → 6 处，全部语义一致（CommitCreate 不含 / _canonical_commit_bytes 参数不含 / 步骤 2 不含 / INSERT 时记录作 audit）
awk '/^## T-6/,/^## T-7/' tasks.md | grep -cE "^\s*-.*\([a-z][0-9]?\)" → 18 个测试 ID 行
awk '/^## T-3/,/^## T-4/' tasks.md | grep -E "事务外|事务内" → 4 条命中（步骤 1 事务外 / 步骤 2 事务外 / 步骤 3 事务外 / 步骤 4 事务内），明示事务边界
awk '/^## T-4/,/^## T-5/' tasks.md | grep -E "async for chunk|request\.stream\(\)|SpooledTemporaryFile" → 3 行命中（tmp = SpooledTemporaryFile / async for chunk / request.stream()）
awk '/^## T-6/,/^## T-7/' tasks.md | grep -E "PG 探针|DATAPLAT_DATABASE_URL|socket" → 命中 "PG 探针 + MinIO 探针 + DATAPLAT_DATABASE_URL"
```

## v1 SHOULD FIX 顺带核实

虽然按 SKILL 要求 SHOULD FIX 不阻塞本轮 verdict，但作者明确声明"消化 3 MUST FIX + 4 SHOULD FIX"，实际消化情况：

- SHOULD FIX-1（事务边界明示）：**已消化**（T-3 步骤 1/2/3 显式"事务外"，步骤 4 "事务内 `async with session.begin()`"）。
- SHOULD FIX-2（get_blob_store 归属确认）：**已消化**（T-4 L76 写"**复用** 既有 storage/__init__.py::get_blob_store()（cas-storage 已落地，无需新建）"；reviewer 实地核验 `apps/api/dataplat_api/storage/__init__.py:23 def get_blob_store()` 确实已存在）。
- SHOULD FIX-3（async stream 拆步）：**已消化**（T-4 L80-88 显式 4 步拆解，与 spec 风险 #2 一致）。
- SHOULD FIX-4（PG 探针）：**已消化**（T-6 L111 `pytestmark = pytest.mark.skipif(not (DATAPLAT_DATABASE_URL and DATAPLAT_MINIO_ENDPOINT))`）。

## 新发现问题（v2 引入）

无新 MUST FIX。

**轻量观察**（不阻塞）：

- T-8 是新增 process task（反哺 cross-AC consistency check），estimated_stage 标 stage-10，符合 [[project-followup-harness-lint]] 演化窗口的"在 close 时统一做"惯例。无问题。
- 依赖图 ASCII（L155-160）箭头与各 task header depends_on 一致，已修复 v1 NICE TO HAVE-1。

## Verdict

**APPROVED**（MUST FIX 残留 = 0；无新 MUST FIX）

可进入 Stage 3 / Stage 4 coding。spec_v2 同步评审见 `spec_review_v2.md`。

## 复检指引（给后续阶段）

- Stage 3 开始 T-1 前确认 `dataplat_core.domain.types.SHA256` 与 schemas 复用路径无误。
- Stage 4 实现 T-3 时，按 tasks L53 的 `_canonical_commit_bytes` 参数顺序严格落地，**禁止**临时加 created_at 参数——若加，AC-9 / AC-10 / AC-11 (g1)(g2) 全线崩。
- Stage 4 实现 T-6 (g1) 时优先跑该单元，单元 PASS 后再跑集成 (g2)（定位力更强）。
