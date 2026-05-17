---
change_id: commit-api-mvp-20260517
target: tasks.md
target_version: 1
review_version: 1
reviewer: claude-stage2-reviewer
reviewed_at: 2026-05-17T09:35:00Z
verdict: REVISION REQUIRED
---

# Tasks Review v1

## 检查清单结论

> 引用 `.harness/skills/expert-reviewer/SKILL.md` §1 plan 模式 tasks 部分。

- [x] 每个任务粒度合理（T-1~T-7 均在 1-3h 范围；T-3 因含 hash + 事务 + 幂等三块逻辑接近上限，但仍可控）。
- [ ] **depends_on 形成 DAG，没有循环（T-2 的 depends_on 标注不准确，见 MUST FIX-1）**。
- [x] 评审 / 单测 / CI 阶段对应任务都存在（按 nta-lake 项目惯例，process_tasks 由 `summary.md` 跟踪而非 tasks.md；repo-api-mvp tasks.md 同样只列工程任务，T-6/T-7 已覆盖单测 + self_check）。
- [x] 没有"做完整个系统"类目标任务（粒度精确到文件路径）。
- [ ] **每条 AC 都有非 process_tasks 任务覆盖（部分 AC 与 spec MUST FIX 联动后需调整 tasks，见 MUST FIX-2）**。

## 问题列表

### MUST FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | tasks.md T-2 L29 "depends_on: 无（不依赖 T-1，但响应类型要复用 schema；可并行写）" | T-2 描述 L24 明确返回 `BlobUploadResponse`（spec AC-1 L45 定义在 T-1 创建的 `schemas/blob.py`）。若并行写，T-2 import 时 `BlobUploadResponse` 不存在 → import error。形式上还是必须先有 T-1 才能完成 T-2。复现命令：`cd apps/api && uv run python -c "from dataplat_api.services.blob import BlobService"` 在 T-1 未完成时必失败。| 改为 `depends_on: T-1`。或显式：`depends_on: T-1 (schema 接口)`，移除"可并行"措辞。"软并行"在依赖图里不算 DAG 节点关系，会误导执行顺序。 |
| 2 | tasks.md T-3 L33-57 与 spec MUST FIX-2（created_at 一致性）联动 | spec_review_v1 MUST FIX-2 指出 `CommitCreate` schema 是否含 `created_at` 是 spec 内矛盾。tasks T-3 L44 写"`created_at = datetime.utcnow()`（服务端算）"——若 spec_v2 选方案 (A) client 控，T-3 此行错；若选方案 (B) 从 canonical 去掉 created_at，T-3 `_canonical_commit_bytes(...)` 的参数列表（L38）需要去掉 `created_at`。任一选择都必须 tasks_v2.md 同步。| tasks_v2.md T-3 与 spec_v2.md AC-9 措辞同步。复现命令：`grep -nE "created_at" tasks_v2.md`，结果必须与 `grep -nE "created_at" spec_v2.md` 在 commit canonical 公式上一致。 |
| 3 | tasks.md T-6 L82-90 测试数量与 spec MUST FIX-5/6/7 联动 | spec_review_v1 MUST FIX-5/6/7 要求 AC-11 测试从 13 增到 ≥ 15（hash 单元 + 2MB blob + lineage round-trip）；tasks T-6 L87 写"测试 a~m 13 个对应 AC-11"。spec_v2 增测试后 tasks T-6 必须同步。| tasks_v2.md T-6 L87 改为"测试 (a)~(o) ≥ 15 个对应 AC-11"，且把 (n) 大文件 + (o) lineage round-trip + (g1) hash 单元（或独立 T-3a 单元测试任务）显式列出。复现命令：`grep -cE "^\s*-.*\([a-z]\)" tasks_v2.md` 应 ≥ 15。 |

### SHOULD FIX

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | tasks.md T-3 L41-51 CommitService.create_commit 步骤 3 vs 步骤 5 路径 | 步骤 3 「先查 commit_hash 是否存在」放在事务外（在 `async with session.begin()` 之前）；步骤 5 IntegrityError 兜底。逻辑正确但 step 顺序在 tasks 里没显式说"step 3 在事务外、step 4 在事务内"——读者可能误以为 step 3 也在事务内。会影响 coding 阶段实现者。| T-3 步骤 3 行首改写为：「事务**外**：先查 commit_hash …」；步骤 4 行首明确"事务**内** `async with session.begin()`：…"；与 spec_v2 AC-8 措辞对齐。 |
| 2 | tasks.md T-4 L63 "注入 BlobStore 单例" | 写"新增 `apps/api/dataplat_api/storage/__init__.py` 暴露 `get_blob_store()` Depends（首次创建 MinioBlobStore，env 读凭据）；如已存在则复用。" 但 cas-storage-20260517 spec L116 已写 `apps/api/dataplat_api/storage/__init__.py` 在 cas-storage 阶段就建好。需要确认 `get_blob_store()` Depends 是 cas-storage 已有 / 还是 commit-api 新增；若 cas-storage 已有则任务措辞应是「复用」；若没有则 T-4 应**独立列出** T-4a "新增 get_blob_store() Depends + 单例缓存策略 + 单测"。粒度差异影响估时。| 检查 cas-storage 落地代码是否含 `get_blob_store()`。若没有，从 T-4 中分出 T-4a「新增 storage DI helper」作为独立任务，且在 cas-storage close note 中追溯遗漏。 |
| 3 | tasks.md T-4 L64 `request.stream()` 包装成 `BinaryIO` (用 `tempfile.SpooledTemporaryFile`) | 这是 spec 风险 #2 的实现路径。`request.stream()` 是 async iterator，写入 `SpooledTemporaryFile.write()` 是 sync 调用；如何把 async chunks 写入 sync file-like 需要明示：循环 `async for chunk in request.stream(): tmp.write(chunk)` 然后 `tmp.seek(0)` 传给 `BlobService.upload`。tasks 没拆步，coding 阶段可能写出问题路径（如先 `await request.body()` 全量读 → 风险 #2 复现）。| T-4 路由 1 步骤拆细：(a) `tmp = SpooledTemporaryFile(max_size=1<<20)` (b) `async for chunk in request.stream(): tmp.write(chunk)` (c) `tmp.seek(0)` (d) `BlobService.upload(store, tmp, declared_size=request.headers.get("content-length"))`。或在 T-4 末尾追加单元测试断言"上传 2MB 字节时 `request.body()` 不被调用"（mock spy）。 |
| 4 | tasks.md T-6 L86 fixture 设计 | "MinIO 探针：env `DATAPLAT_MINIO_ENDPOINT` 未设 → 全 skipif"——但 spec L57 AC-13 + cas-storage AC-15 提到"PG + MinIO 双探针；任一不可达 SKIP"。tasks T-6 只写 MinIO 探针，没写 PG 探针。PG 不可达时 fixture 创建 admin_user / repo 会失败 → 整 test_commits.py 红。| T-6 fixture 增加 PG 探针：`socket.connect((PG_HOST, PG_PORT))` 失败 → `pytest.skip`；与 cas-storage T 单测一致。 |

### NICE TO HAVE

| # | 位置 | 问题 | 建议 |
|---|---|---|---|
| 1 | tasks.md L102-106 依赖图 ASCII | 「T-1 (schemas) ─┐\n T-2 (BlobService) ─┐」 — T-2 已纠正为 depends_on T-1 后（MUST FIX-1），ASCII 图应同步：T-1 → T-2 / T-3 / T-4。| 修 ASCII 图箭头。 |
| 2 | tasks.md T-7 L94 `scripts/_self_check.sh` filter `commit-api-mvp\|commit-api-mvp-20260517` | 两个 filter 等价（短名 + 全名），与 cas-storage T-self_check 一致；但 filter 内逻辑 OR 而非 AND，spec L57 只写 `commit-api-mvp`，建议保持单短名以与 self_check.sh 调用习惯一致。| 单 filter 即可。或与现有 `_self_check.sh` 已有的 cas-storage / repo-api-mvp filter 风格对齐（不限制本评审，让 coding 阶段按现有 script 习惯写）。 |
| 3 | tasks.md 整体 | 没有"反哺 .harness/" 任务 — 本变更如果发现 spec generator 跨 AC 自相矛盾（spec MUST FIX-2/4），应有 T-8「将 cross-AC consistency check 反哺到 `.harness/skills/request-analysis/SKILL.md`」作为流程改进，与 [[project-followup-harness-lint]] 演化窗口一致。| 可选追加 T-8（process task）；若选不加，则 summary.md 末尾的反哺项必须显式列出。 |

## Verdict

REVISION REQUIRED（MUST FIX 数 = 3）

## 复检指引

作者写 `tasks_v2.md` 时按下述命令自查：

1. **MUST FIX-1（T-2 依赖修正）**：
   ```bash
   awk '/^## T-2/,/^## T-3/' tasks_v2.md | grep -E "depends_on:\s*T-1"
   ```
   结果非空。

2. **MUST FIX-2（T-3 与 spec_v2 created_at 一致）**：
   ```bash
   grep -nE "created_at" tasks_v2.md
   ```
   人工核对：T-3 中 created_at 措辞与 spec_v2.md AC-9 commit canonical 公式一致；若 spec 走方案 (B) 去掉 created_at，则 tasks T-3 `_canonical_commit_bytes` 参数列表也不应含 `created_at`。

3. **MUST FIX-3（T-6 测试数）**：
   ```bash
   awk '/^## T-6/,/^## T-7/' tasks_v2.md | grep -cE "^\s*-.*\([a-z]\)"
   ```
   结果 ≥ 15（对应 spec_v2 AC-11 增加的 hash 单元 / 2MB blob / lineage round-trip）。

4. **SHOULD FIX-1（T-3 事务边界明示）**：
   ```bash
   awk '/^## T-3/,/^## T-4/' tasks_v2.md | grep -E "事务外|事务内"
   ```
   各出现 ≥ 1 次。

5. **SHOULD FIX-2（get_blob_store Depends 归属确认）**：
   人工或脚本检查 `apps/api/dataplat_api/storage/__init__.py` 当前是否已含 `get_blob_store` 函数；若无，tasks_v2 须有独立 T-4a。

6. **SHOULD FIX-3（async stream 写入 tmp 拆步明示）**：
   ```bash
   awk '/^## T-4/,/^## T-5/' tasks_v2.md | grep -E "async for chunk|request\.stream\(\)|SpooledTemporaryFile"
   ```
   ≥ 2 行命中。

7. **SHOULD FIX-4（PG 探针）**：
   ```bash
   awk '/^## T-6/,/^## T-7/' tasks_v2.md | grep -E "PG 探针|DATAPLAT_DATABASE_URL|socket"
   ```
   非空。

8. DAG 校验：人工查依赖图箭头与各 task 的 depends_on 一致。

提交 v2 后开 `tasks_review_v2.md`。
