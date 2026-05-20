---
change_id: api-snapshot-rename-20260520
phase: verify
reviewer: claude-agent:opus-phase3-reviewer
model_used: opus
authored_at: 2026-05-20T18:30:00Z
verdict: APPROVED
---

# Verify Review

> Phase 3 reviewer 产物。对照 design.md（10 条业务 AC，AC-11/AC-12 已 D-13 豁免）+ implementation.md + `git diff main...change/api-snapshot-rename-20260520`。本次 reviewer **真去跑每一条 AC 命令**，未凭 git diff 猜测。

## 输入

- **Design**：`.harness/changes/api-snapshot-rename-20260520/design.md`
- **Design Review (Phase 1)**：`design_review.md`，verdict SMALL REVISIONS（AC-4 反向 grep 转义 bug 已修，确认在当前 design.md AC-4 行为 `! grep -q "CommitCreate" ... && ! grep -q "CommitRead" ...` 两条独立子句）
- **Implementation**：`implementation.md`，base_commit `0e4bf66`，head_commit `f3c997e`，含 D-1 偏离声明（`CommitCreate` 内部移入 `_commit_internal.py`）
- **Git log**（main..change/api-snapshot-rename-20260520）：
  - `f3c997e` Phase 2 主提交（commits→snapshots rename + sdk + web migration）
  - `6719db2` Phase 2 修订（service 层保留 `create_commit`；snapshot→commit 转换内联到 router）
  - `22030c5` implementation.md 回填 head_commit
  - `82ffbb6` test fixture 类型修复（Phase 3 前置；同步 fixture 用 `Generator`）
- **Decisions**：D-1（DB 不动）/ D-11（每 change 单 commit；本 change 因 verify 前置修订共 4 commit，合理）/ D-12（template reviewer 字段 hotfix）/ D-13（self_check per-change block 豁免）

## AC 对照表

每条业务 AC 真跑命令验证。AC-11 / AC-12 已 D-13 豁免，未验证。

| AC | kind | reviewer 跑的命令 | 结果 | PASS/FAIL |
|---|---|---|---|---|
| AC-1 | static | `test -f apps/api/dataplat_api/routers/snapshots.py && grep -q 'tags=["snapshots"]' ... && grep -q '/snapshots"' ... && grep -q '/snapshots/{hash}"' ...` | exit 0 | PASS |
| AC-2 | static | `test ! -e apps/api/dataplat_api/routers/commits.py` | exit 0 | PASS |
| AC-3 | static | `test -f schemas/snapshot.py && grep -q "class SnapshotCreate" ... && grep -q "class SnapshotRead" ... && grep -q "parent: SHA256 \| None" ... && ! grep -q "parents:" snapshot.py` | exit 0 | PASS |
| AC-4 | static | `grep -q "SnapshotCreate" generated.ts && grep -q "SnapshotRead" generated.ts && ! grep -q "CommitCreate" generated.ts && ! grep -q "CommitRead" generated.ts` | exit 0 | PASS（Phase 1 reviewer MUST FIX #1 的修法已落地，反向 grep 真生效） |
| AC-5 | static | `grep -q '"/repos/{owner}/{name}/snapshots"' openapi.json && grep -q '"/repos/{owner}/{name}/snapshots/{hash}"' openapi.json` | exit 0 | PASS |
| AC-6 | static | `grep -q "def create_snapshot(" client.py && grep -q "parent: str \| None" client.py && ! grep -q "def create_commit(" client.py && grep -q 'snapshot_app.command("create")' cli.py && grep -q '"--parent"' cli.py` | exit 0 | PASS |
| AC-7 | static | `test -f routes/snapshots/$owner.$name.$hash.tsx && grep -q 'createFileRoute("/snapshots/$owner/$name/$hash")' ... && test ! -e routes/commits.$owner.$name.$hash.tsx && test ! -e routes/commits.$owner.$name.$hash.test.tsx` | exit 0 | PASS（folder 形式 D-7 MEMORY 偏好已兑现） |
| AC-8 | static | `grep -q "interface SnapshotRead" queries.ts && grep -q "parent: string \| null" queries.ts && grep -q "export function useSnapshot(" queries.ts && ! grep -q "interface CommitRead" queries.ts && ! grep -q "export function useCommit(" queries.ts` | exit 0 | PASS |
| AC-9 | behavioral | `set -a && source .env.local && set +a && cd apps/api && uv run pytest tests/test_snapshots_api.py::test_create_snapshot_then_get_200 -x -v` | 1 passed in 1.90s | PASS（happy path：POST `/snapshots` 200 + `parent` 字段在响应 + 不含 `parents` + GET `/snapshots/{hash}` 200 + hash 一致） |
| AC-10 | behavioral | `set -a && source .env.local && set +a && cd apps/api && uv run pytest tests/test_snapshots_api.py::test_old_commits_path_redirects_308 -x -v` | 1 passed in 1.90s | PASS（308 兼容：POST/GET `/commits[/{hash}]` 返回 308 + `Location` header 指向新路径） |
| ~~AC-11~~ | ~~static~~ | D-13 豁免，未验 | — | EXEMPT |
| ~~AC-12~~ | ~~behavioral~~ | D-13 豁免，未验 | — | EXEMPT |

**结论**：10/10 业务 AC 全 PASS；AC-11/AC-12 豁免不验。

## 机械化检查日志

```text
$ git rev-parse HEAD
82ffbb6b7c937d5486e8245ea651864feb7af494

$ git log --oneline main..change/api-snapshot-rename-20260520
82ffbb6 fix(api): test_snapshots_api 同步 fixture 用 Generator 类型 (W1-1)
6719db2 fix(api): service 层保留 create_commit；snapshot→commit 转换内联到 router (W1-1)
22030c5 docs(harness): api-snapshot-rename implementation.md head_commit 回填 f3c997e
f3c997e feat(api): commits→snapshots rename + sdk + web migration (W1-1)

# AC-1..AC-8 静态命令（每条独立跑，全部 exit 0）
$ bash -c '<AC-N 整条命令> && echo "AC-N exit=$?"'
AC-1 exit=0
AC-2 exit=0
AC-3 exit=0
AC-4 exit=0
AC-5 exit=0
AC-6 exit=0
AC-7 exit=0
AC-8 exit=0

# AC-9 + AC-10 behavioral
$ set -a && source .env.local && set +a
$ cd apps/api && uv run pytest tests/test_snapshots_api.py -x -v
tests/test_snapshots_api.py::test_create_snapshot_then_get_200 PASSED    [ 50%]
tests/test_snapshots_api.py::test_old_commits_path_redirects_308 PASSED  [100%]
============================== 2 passed in 1.90s ===============================

# 308 redirect 显式构造（risk 表第 1 行 + prompt 注意点）
$ grep -n "RedirectResponse\|status_code=308\|response_class=RedirectResponse" apps/api/dataplat_api/routers/snapshots.py
35:from fastapi.responses import RedirectResponse, StreamingResponse
398:async def _redirect_create_commit(
401:) -> RedirectResponse:
403:    return RedirectResponse(
405:        status_code=308,
410:async def _redirect_get_commit(
414:) -> RedirectResponse:
416:    return RedirectResponse(
418:        status_code=308,
# 两处均 `RedirectResponse(url=..., status_code=308)` 显式构造（**未** 用 response_class=RedirectResponse 装饰器），符合 design.md 风险表第 1 行预防

# 模板 hotfix（D-12）守住
$ grep "reviewer:" .harness/changes/_template/{design_review,verify_review}.md
.harness/changes/_template/verify_review.md:reviewer: claude-agent:opus-phase3-reviewer
.harness/changes/_template/design_review.md:reviewer: claude-agent:opus-phase1-reviewer

# self_check global lint（per-change block 已 D-13 豁免，仅看全局 lint）
$ bash scripts/_self_check.sh current api-snapshot-rename-20260520 2>&1 | tail -10
PASS  reviewer-lint  reviewer 字段独立性守门（反向×2 + 白名单）
PASS  ac-kind-lint   AC 分层规约守门（kind 列存在 + AC 行 kind=behavioral 锚定 regex）
PASS  script-syntax  self_check 与 harness_new_change bash 语法
# 其他 4 个 FAIL 均为 v1 时期遗留的 spec.md / tasks.md / summary 占位符检查，v2 单文件 design.md 不适用；非业务 AC fail，符合 D-13 + prompt 注意点 #5 的指引（忽略）
```

## D-1 边界审计（DB / 内部 commit 语义守住？）

逐项核查 prompt 提示的 D-1 边界：

| 边界项 | 期望 | 实测 | PASS/FAIL |
|---|---|---|---|
| DB schema (alembic / models) 不动 | `git diff --stat main...change/... -- apps/api/alembic/ apps/api/dataplat_api/models/` 输出空 | 输出空 | PASS |
| `services/commit.py` 内部仍叫 commit（`CommitORM` / `CommitService.create_commit` 名字保留） | grep 命中 `class CommitORM`、`def create_commit`、`CommitORM(` 等关键标识 | 命中 7 处；唯一 diff 是 `from dataplat_api.schemas.commit` → `from dataplat_api.schemas._commit_internal`（import path 改名，函数体未动） | PASS |
| `models/refs.py` 不动 | `git diff` 输出空 | 输出空 | PASS |
| `schemas/pipeline.py` 不动 | `git diff` 输出空 | 输出空 | PASS |

D-1 边界 4/4 PASS。

## 隐式偏离审计

> reviewer 对比 design.md § 范围 / implementation.md § 偏离 / `git diff --name-only`，列出 implementation.md 没显式声明但 diff 里实际修改的文件。

**git diff 涉及的 36 个文件**（含 .harness / template）逐一核对：

| 文件 | 在 implementation.md § 改动文件清单 列出？ | 是否在 design § 范围 暗含？ | 隐式偏离？ |
|---|---|---|---|
| `apps/api/dataplat_api/schemas/_commit_internal.py` (new) | ✅ 显式列出 + 标注"隔离 AC-3 negation grep" | design § 非范围未禁止；属 AC-3 兑现的必要内部拆分 | 否；implementation.md § 偏离 D-1 已显式声明 |
| `apps/api/dataplat_api/services/commit.py` | ✅（只改 import path） | design § 非范围明确"services/commit.py 内部仍可叫 commit" | 否 |
| `apps/api/dataplat_api/runner/adapter_runner.py` / `processor_runner.py` | ✅ 显式列出（import path 改） | design § 范围未提；属 schema 拆分的连带 import 修复，等同 D-1 偏离的延伸 | 否；连带影响合理 |
| `apps/api/dataplat_api/routers/ingest.py` / `repos.py` | ✅ 显式列出 | design § 范围未直接列出，但 § 范围有 `RefRead.commit_hash` → `snapshot_hash`（routers/repos.py 是该 schema 唯一实例化点）+ `_snapshot_to_read` 重命名连带（routers/ingest.py 是唯一外部 import 点） | 否；连带修复合理 |
| `apps/api/dataplat_api/schemas/ingest.py` | ✅ 显式列出（`IngestResponse.commit: CommitRead` → `snapshot: SnapshotRead`） | design § 范围未列出 ingest schema 改名 | **半隐式偏离（轻微）**：design § 范围仅列了 commit / ref schemas，没列 ingest schema；但这是 CommitRead → SnapshotRead 改名的连带修复（IngestResponse 引用 CommitRead），不修则 `! grep CommitRead` 全局检查会爆。属合理连带；不是 scope creep | 否；连带修复必需 |
| `apps/web/src/routes/blob.test.tsx` / `repos.tabs.test.tsx` / `repos.ingest-section.test.tsx` / `repos.files-section.test.tsx` / `jobs/$job_id.test.tsx` | ✅ 显式列出（"mock `useSnapshot`"） | design § 范围未直接列；属 `useCommit` → `useSnapshot` 改名的连带 mock 替换 | 否；连带修复合理 |
| `apps/api/tests/test_snapshots_api.py` | ✅ 显式列出 | T-7 任务直接覆盖 AC-9 + AC-10 | 否 |
| `apps/web/src/routeTree.gen.ts` | ✅ 显式列出（"TanStack Router 自动生成"） | design § 范围："自动重生" | 否 |
| `.harness/changes/_template/{design_review,verify_review}.md` | ❌ implementation.md 未列出 | design § 范围未列出 | **轻微隐式偏离**：D-12 hotfix 把模板 reviewer 字段从 `opus-phase[13]-reviewer` 改成 `claude-agent:opus-phase[13]-reviewer`；这是 harness meta scope，按 D-3 应单独开 `harness-*` change。**但**：(a) decisions.md 已为 D-12 单独建档 + 标注"影响 27 个 follow-up change"；(b) 不修模板，后续 W1-2..W4-10 每个 change 都要手动 patch reviewer 字段，违反 D-12 "本 rollout 27 个 change 都受益，无需每 change 手动修"；(c) 改动 2 字符 × 2 文件 = 总共 4 字符；属应急 hotfix 性质 | **轻微偏离，但有 D-12 记录兜底，不构成 MUST FIX** |

**隐式偏离结论**：35/36 文件符合 implementation.md 或合理连带；唯一 1 个 harness 模板 hotfix 跨 scope，但有 D-12 单独决策兜底，不构成 MUST FIX。

## 问题列表

### MUST FIX

无。

### SHOULD FIX

无。所有静态 AC + 行为 AC + D-1 边界 + 隐式偏离审计均 PASS；模板 hotfix 跨 scope 已被 D-12 record 兜底。

### NICE TO HAVE

- **NTH #1**：`schemas/_commit_internal.py` 是 W1-1 的"私有内部 schema"妥协，未来 `db-snapshot-rename-*`（design § follow-up）落地后可整体撤除（DB 列直接叫 `parent`，则不需要再做 list/单数翻译，CommitCreate 内部 schema 也可与 SnapshotCreate 合并）。本 change 不必处理。
- **NTH #2**：design § 范围 第 6 行 "`/tree/{commit_hash}` 路径里的 path param 名改 `snapshot_hash`" 在 design_review.md SHOULD FIX #2 提到无 AC 兜底；reviewer 顺手 grep `apps/api/dataplat_api/routers/snapshots.py` 命中 `snapshot_hash: str = Path(`（已落地，但未机械化 AC）。可在 `api-snapshot-rename-cleanup-*` follow-up 顺手加。
- **NTH #3**：implementation.md § 改动文件清单 未列出 `.harness/changes/_template/` 的 D-12 hotfix patch；可在 close change 时回填一行"meta：D-12 模板 hotfix（跨 harness scope 应急；详 decisions.md D-12）"，方便后人审计 git diff 与 implementation.md 一致性。本 change 不必处理。

## Verdict

**APPROVED**

- 10/10 业务 AC 全 PASS（含 2 条 behavioral pytest 真跑通过）
- AC-11 / AC-12 已 D-13 豁免，不验
- D-1 边界 4/4 守住（DB schema / models / refs / pipeline schemas 全部 0 修改；`services/commit.py` 内部 `CommitORM` + `create_commit` 名字保留）
- 隐式偏离审计 35/36 文件合理；唯一跨 scope 的模板 hotfix 有 D-12 decisions 兜底
- 308 redirect 显式 `RedirectResponse(url=..., status_code=308)` 构造，命中 design § 风险表第 1 行预防
- 全局 lint（reviewer-lint / ac-kind-lint / script-syntax）PASS；4 个 v1 stage-file 残留 FAIL 按 D-13 + prompt #5 忽略
- 无引入回归：implementation.md 已附 `pytest tests/ --ignore=tests/test_snapshots_api.py` 46/46 PASS + `vitest --run` 47/47 PASS + `tsc --noEmit` 0 errors

## 后续指引

1. **可以 merge** `change/api-snapshot-rename-20260520` 到 `main`。建议 squash 4 个 commit（f3c997e / 22030c5 / 6719db2 / 82ffbb6）为单 commit，message：`feat(api): commits→snapshots rename + sdk + web migration (W1-1)`，符合 D-11"每 change 一个 commit"。
2. **close change**：在 `.harness/changes/api-snapshot-rename-20260520/summary.md` 写完结摘要 + dashboard 回写 W1-1 verify APPROVED + closed。
3. **启动 W1-2**：`operator-protocol-20260520`（Wave 1 严格串行，D-4）；进入 Phase 1 Design。
4. **deferred follow-up**：
   - `api-snapshot-rename-cleanup-<YYYYMMDD>`：W2 结束前删 308 redirect 端点（依赖：所有 sdk / web 调用方完成切换到新路径）
   - `db-snapshot-rename-<YYYYMMDD>` (可选)：DB 层 commits 表 → snapshots 表 + parents list → parent 单列改名；W4 末评估
   - `recipe-yaml-v2-20260520` (W2-5)：统一 pipeline / lineage 字段 `output_commit_hash` → `output_snapshot_hash` 等
5. **harness v3 流程文档**（D-13 收官）：merge 后单独开 harness meta change，把 development-process.md v2 → v3、application-owner.md 同步、`harness_new_change.sh` 模板精简、删 design_review.md 默认生成、移除 self_check per-change block 强制要求。
