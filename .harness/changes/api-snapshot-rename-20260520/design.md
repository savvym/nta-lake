---
change_id: api-snapshot-rename-20260520
phase: design
status: reviewing
authored_at: 2026-05-20T16:45:00Z
author: application-owner-agent
model_used: opus
ac_kind_lint: enforce
---

# Design：API / SDK / UI Commit → Snapshot 词汇统一

> 这是 Phase 1 的唯一产物。spec + tasks 合并在这里。Phase 2 sonnet 按本文件落地，Phase 3 reviewer 对照本文件验收。

## 一句话目标

API / SDK / UI 把 Commit 改成 Snapshot；parents 列表退化为 parent 单链。

## 背景

`.harness/design.md` § 北极星 已把平台定位为"LLM 训练数据工厂"，并在 `.harness/rules/data-not-code-pivot.md` 的旧→新术语表里把 Commit 标记为 Snapshot 的同义词、把 `parents: list[str]`（DAG）标记为应退化为 `parent: str | None`（线性单链）。但 22 个 v1 闭环 change 跑出来的 API / SDK / UI 还是 Commit 词汇 + `parents[]`，跟北极星语言不一致。`roadmap.md` § Wave 1 把"对外重命名"列为 W1-1（Wave 1 起点 + 4 个 change 串行的第一步），目的是先把对外语言定死，后续 W1-2 Operator Protocol / W1-3 silver schema / W1-4 loader 重构都基于 Snapshot 心智写。

本 change 是**纯对外语言改名 + 字段单数化**，不动 DB schema、不动业务逻辑、不动 Processor / Loader / Operator 抽象。DB 列名保留 `commit` 是 D-1 已经定的方向（避免大规模 alembic 迁移 + 不破坏老数据 + 历史 v1 commit-api-mvp 闭环 AC 不回归）。

## 范围

In scope：

- `apps/api/dataplat_api/routers/commits.py` 文件改名 `snapshots.py`，router prefix 保留 `/repos`，tag 改 `snapshots`
- 上述文件内 2 个跟 commit 强相关的端点路径改名：`POST /repos/{owner}/{name}/commits` → `/snapshots`、`GET /repos/{owner}/{name}/commits/{hash}` → `/snapshots/{hash}`；`GET /tree/{commit_hash}` 路径里的 path param 名改 `snapshot_hash`（路径段 `tree` 保留，仅参数名变更，避免影响 `/trees/{tree_hash}` 子树端点）
- `apps/api/dataplat_api/main.py` `commits_router` import 名改 `snapshots_router`
- `apps/api/dataplat_api/schemas/commit.py` 内 `CommitCreate` / `CommitRead` 改名 `SnapshotCreate` / `SnapshotRead`；字段 `parents: list[SHA256]` 改 `parent: SHA256 | None`（CommitCreate 内 default `None`；CommitRead 内可空）；文件改名 `schemas/snapshot.py`
- `apps/api/dataplat_api/schemas/ref.py` `RefRead.commit_hash` 字段改名 `snapshot_hash`
- `apps/api/dataplat_api/routers/commits.py` 的 `_commit_to_read` 工具函数与 import 同步改名 `_snapshot_to_read`；内部把 ORM 的 `commit.parents: list[str]` 取 `parents[0] if parents else None` 装到 `SnapshotRead.parent`
- 对**老路径** `/repos/{owner}/{name}/commits` + `/repos/{owner}/{name}/commits/{hash}` 加 **308 Permanent Redirect**（FastAPI `RedirectResponse(status_code=308)`），保留 1 个版本周期供 sdk / web 老客户端过渡；redirect 端点定义在 `routers/snapshots.py` 同文件以便后续整体撤
- `packages/api-types/openapi.json` 通过 `python scripts/export_openapi.py` 重新生成；`packages/api-types/src/generated.ts` 通过 `pnpm --filter @dataplat/api-types generate` 重新生成；产物里不再出现 schema 名 `CommitCreate` / `CommitRead`（路径 `/commits/...` 仅剩 redirect 端点 operation，schema 里不含 Commit*）
- `packages/sdk-py/src/dataplat_sdk/client.py`：方法 `create_commit(...)` 改名 `create_snapshot(...)`，参数 `parents: list[str] | None = None` 改 `parent: str | None = None`，POST 目标改 `/snapshots`，payload 顶层 `parents` 改 `parent`（None 时省略字段）
- `packages/sdk-py/src/dataplat_sdk/cli.py`：子命令组 `commit_app` → `snapshot_app`、`@app.add_typer(snapshot_app, name="snapshot")`、命令名 `commit create` → `snapshot create`；`--parents` flag 改 `--parent`（接受单 sha256 而非 JSON list）；module docstring 路径串同步
- `apps/web/src/routes/commits.$owner.$name.$hash.tsx` + `.test.tsx` 移到 folder 形式 `apps/web/src/routes/snapshots/$owner.$name.$hash.tsx` + `.test.tsx`（D-7 决策；保留可扩展性）；TanStack `createFileRoute` 字符串同步改 `/snapshots/$owner/$name/$hash`
- `apps/web/src/routes/__root.tsx` / `routes/jobs/$job_id.tsx` / `routes/repos/$owner.$name.tsx` 内所有 `<Link to="/commits/$owner/$name/$hash">` 改 `/snapshots/...`
- `apps/web/src/lib/api/queries.ts`：interface `CommitRead` 改 `SnapshotRead`、字段 `parents: string[]` 改 `parent: string | null`；hook `useCommit` 改 `useSnapshot`；queryKey `"commit"` 改 `"snapshot"`；fetch URL `/commits/${hash}` 改 `/snapshots/${hash}`
- `apps/web/src/routeTree.gen.ts` 重新生成（vite dev / build 自动）
- `scripts/_self_check.sh` 新增 `run_api_snapshot_rename` block + case 派发 `api-snapshot-rename|api-snapshot-rename-20260520) run_api_snapshot_rename ;;`，覆盖下文每条 AC

Out of scope（非范围）：

- **不动 DB schema** （D-1）：`commits` 表名、`refs.commit_hash` 列名、`CommitORM`、`RefORM`、`alembic/versions/` 不动；ORM 类名保留 `CommitORM`；理由：避免大规模迁移 + 不破坏 22 个 v1 闭环 change 的 AC。DB → API 边界在 `_snapshot_to_read` / service 层做翻译。后续如需 DB 改名走独立 change `db-snapshot-rename-*`
- **不撤 ORM `parents: list[str]` 列、不撤 `lineage_json`**：DB 仍存 list（兼容历史 row）；API 层只取 `parents[0]`；理由：v1 时期生成的 commit 行多数 `parents=[]`，少数有一个；如果存在 list 长度 > 1 的历史数据，API 层取第一个不报错，并在 `_snapshot_to_read` 加 `if len(parents) > 1: log.warning(...)`（一行日志，不报错）
- **不动 `refs` 表 / `RefORM`**：D-1；ORM 内部仍用 `commit_hash` 列；API 响应里 `RefRead.snapshot_hash` 在序列化层翻译
- **不撤 `/repos/{owner}/{name}/refs/{ref_name}` 端点**：refs 在新模型里仍代表"指向某个 snapshot 的可变指针"，语义不变；本 change 只动响应字段名
- **不动 processors / adapters / lineage / pipeline 模块**：跟 commit 词汇关联较弱（`Lineage` 内部字段叫 `commit_hash` 的会在 `models/pipeline.py` 与 `domain/lineage.py`，本 change 仅扫到 `models/pipeline.py` 与 `schemas/pipeline.py` 的 `output_commit_hash` / `input_commits` / `source_commit_hash` 字段；这些是 Pipeline 内部状态字段，不在用户 facing API surface 的 Commit / Snapshot 主线上）；统一留给 W1-2 / W2-5 处理
- **不动 `models/refs.py` 命名 / 不撤 `/branches` 路径**：实际代码搜索证实**没有** `/branches` 复数 API（dashboard § 代码扫描快照 "branch 这个 v1 概念是否也要清理" 是基于 `models/refs.py` 文件名误读；refs 表是 git-style refs，名字概念中性，不等于 branch）；本 change 不引入新清理工作
- **不引入新的 deprecated 注释机制**：老路径直接 308 重定向，不保留并行响应；下游一旦 redirect 至新路径 1 个版本周期，下一个 change 直接删 redirect
- **不动 `apps/web/src/routes/blob.$owner.$name.$hash.tsx`**：blob 路径与 commit 改名解耦；blob 仅是 CAS 概念，不属于 Commit / Snapshot
- **不动 v1 闭环 change 的 self_check block / 历史 AC**：v1 时期 `run_commit_api_mvp` 等 block 保留原样，不回写为 snapshot 词汇

## 验收标准

每条必须可演示且可机械化。`kind` 二选一：

- `static`：grep / test -f / dry-import / 文件结构断言
- `behavioral`：真跑代码并断言行为（HTTP roundtrip / pytest 集成 / curl smoke / bash fixture）

**本 change 至少 1 条 behavioral AC**（D-2 规则禁止 ac_kind_lint exempt）。

| ID | kind | 描述 | 验证方式 | 期望 |
|---|---|---|---|---|
| AC-1 | static | `routers/snapshots.py` 存在 + 包含 `tags=["snapshots"]` + 至少 `POST /{owner}/{name}/snapshots` 与 `GET /{owner}/{name}/snapshots/{hash}` 路径 | `bash -c 'test -f apps/api/dataplat_api/routers/snapshots.py && grep -q "tags=\[\"snapshots\"\]" apps/api/dataplat_api/routers/snapshots.py && grep -q "/snapshots\"" apps/api/dataplat_api/routers/snapshots.py && grep -q "/snapshots/{hash}\"" apps/api/dataplat_api/routers/snapshots.py'` | exit 0 |
| AC-2 | static | 旧文件 `routers/commits.py` 已不存在（已重命名） | `bash -c 'test ! -e apps/api/dataplat_api/routers/commits.py'` | exit 0 |
| AC-3 | static | `schemas/snapshot.py` 含 `class SnapshotCreate` 与 `class SnapshotRead`，`SnapshotCreate.parent` 类型注解为 `SHA256 \| None`，无 `parents:` 字段 | `bash -c 'test -f apps/api/dataplat_api/schemas/snapshot.py && grep -q "class SnapshotCreate" apps/api/dataplat_api/schemas/snapshot.py && grep -q "class SnapshotRead" apps/api/dataplat_api/schemas/snapshot.py && grep -q "parent: SHA256 \| None" apps/api/dataplat_api/schemas/snapshot.py && ! grep -q "parents:" apps/api/dataplat_api/schemas/snapshot.py'` | exit 0 |
| AC-4 | static | `packages/api-types/src/generated.ts` 含 `SnapshotCreate` 与 `SnapshotRead` 类型，且不含 `CommitCreate` / `CommitRead` schema 名 | `bash -c 'grep -q "SnapshotCreate" packages/api-types/src/generated.ts && grep -q "SnapshotRead" packages/api-types/src/generated.ts && ! grep -q "CommitCreate" packages/api-types/src/generated.ts && ! grep -q "CommitRead" packages/api-types/src/generated.ts'` | exit 0 |
| AC-5 | static | `openapi.json` 含 `/repos/{owner}/{name}/snapshots` 与 `/repos/{owner}/{name}/snapshots/{hash}` 路径键 | `bash -c 'grep -q "/repos/{owner}/{name}/snapshots\"" packages/api-types/openapi.json && grep -q "/repos/{owner}/{name}/snapshots/{hash}\"" packages/api-types/openapi.json'` | exit 0 |
| AC-6 | static | SDK client 含 `def create_snapshot(` + `parent: str \| None`，不含 `def create_commit(`；CLI 含 `@snapshot_app.command("create")` 且 typer flag `--parent` | `bash -c 'grep -q "def create_snapshot(" packages/sdk-py/src/dataplat_sdk/client.py && grep -q "parent: str \| None" packages/sdk-py/src/dataplat_sdk/client.py && ! grep -q "def create_commit(" packages/sdk-py/src/dataplat_sdk/client.py && grep -q "snapshot_app.command(\"create\")" packages/sdk-py/src/dataplat_sdk/cli.py && grep -q "\"--parent\"" packages/sdk-py/src/dataplat_sdk/cli.py'` | exit 0 |
| AC-7 | static | web 路由 folder 化：`apps/web/src/routes/snapshots/$owner.$name.$hash.tsx` 存在 + 含 `createFileRoute("/snapshots/$owner/$name/$hash")`；旧 flat 文件 `commits.$owner.$name.$hash.tsx` 与其测试不存在 | `bash -c 'test -f apps/web/src/routes/snapshots/\$owner.\$name.\$hash.tsx && grep -q "createFileRoute(\"/snapshots/\\\$owner/\\\$name/\\\$hash\")" apps/web/src/routes/snapshots/\$owner.\$name.\$hash.tsx && test ! -e apps/web/src/routes/commits.\$owner.\$name.\$hash.tsx && test ! -e apps/web/src/routes/commits.\$owner.\$name.\$hash.test.tsx'` | exit 0 |
| AC-8 | static | web queries.ts 含 `interface SnapshotRead` + 字段 `parent: string \| null`，`export function useSnapshot(`，且不含 `interface CommitRead` / `useCommit` | `bash -c 'grep -q "interface SnapshotRead" apps/web/src/lib/api/queries.ts && grep -q "parent: string \| null" apps/web/src/lib/api/queries.ts && grep -q "export function useSnapshot(" apps/web/src/lib/api/queries.ts && ! grep -q "interface CommitRead" apps/web/src/lib/api/queries.ts && ! grep -q "export function useCommit(" apps/web/src/lib/api/queries.ts'` | exit 0 |
| AC-9 | behavioral | pytest 端到端：创建 repo + upload blob + `POST /repos/{owner}/{name}/snapshots` 返回 200 + 响应 JSON 含 `parent` 字段（不含 `parents`），随后 `GET /repos/{owner}/{name}/snapshots/{hash}` 返回 200 + `hash` 一致 | `cd apps/api && uv run pytest tests/test_snapshots_api.py -x -q` | passed |
| AC-10 | behavioral | 308 兼容：`POST /repos/{o}/{n}/commits` 与 `GET /repos/{o}/{n}/commits/{hash}` 返回 308 + `Location` header 指向对应 `/snapshots` / `/snapshots/{hash}` 路径 | `cd apps/api && uv run pytest tests/test_snapshots_api.py::test_old_commits_path_redirects_308 -x -q` | passed |
| ~~AC-11~~ | ~~static~~ | **D-13 豁免**：self_check 不再每 change 加 block；业务覆盖靠 `test_snapshots_api.py` 单测 | — | — |
| ~~AC-12~~ | ~~behavioral~~ | **D-13 豁免**：self_check current 不再作为门禁；Phase 2 sonnet 只保证 `cd apps/api && uv run pytest tests/test_snapshots_api.py` + `pnpm --filter web test` 不回归 | — | — |

> ⚠ Phase 1 reviewer 必须**真去跑** AC 命令验证语法可执行 + 当前未实现时如预期失败（AC-1..AC-8、AC-11 当前应全 FAIL；AC-9、AC-10、AC-12 需 sonnet 在 Phase 2 写完后才能 PASS）。

## 任务清单

粒度 30-90 分钟。每条标 `covers_ac`。

| Task | 描述 | covers_ac | 依赖 |
|---|---|---|---|
| T-1 | schemas 改名：`schemas/commit.py` → `schemas/snapshot.py`；`CommitCreate/Read` → `SnapshotCreate/Read`；`parents: list[SHA256]` → `parent: SHA256 \| None`；同步 `schemas/__init__.py` import；`schemas/ref.py` 内 `RefRead.commit_hash` → `snapshot_hash` | AC-3 | — |
| T-2 | router 文件改名：`routers/commits.py` → `routers/snapshots.py`；router prefix 不变（仍 `/repos`），tag 改 `snapshots`；2 个 commit 强相关端点路径 `/commits` → `/snapshots`、`/commits/{hash}` → `/snapshots/{hash}`；`/tree/{commit_hash}` path param 名改 `snapshot_hash`；blob / tree / trees 端点保留不动；`_commit_to_read` → `_snapshot_to_read` + ORM `parents[0] if parents else None` 翻译；`main.py` import 改名 | AC-1, AC-2 | T-1 |
| T-3 | 308 兼容：在 `routers/snapshots.py` 内额外注册 2 个 redirect 端点 `POST /{owner}/{name}/commits` 与 `GET /{owner}/{name}/commits/{hash}`，统一返回 `RedirectResponse(url=..., status_code=308)` | AC-10 | T-2 |
| T-4 | regenerate openapi + api-types：跑 `uv run python scripts/export_openapi.py && pnpm --filter @dataplat/api-types generate` 重新生成 `openapi.json` + `generated.ts` | AC-4, AC-5 | T-1..T-3 |
| T-5 | sdk-py 改名：`client.create_commit` → `create_snapshot` + `parent` 单数；`cli.py` 子命令组 `commit` → `snapshot`、`--parents` flag → `--parent`；module docstring 路径串同步 | AC-6 | T-2 |
| T-6 | web 路由迁移 + queries.ts 改名：移 `routes/commits.$owner.$name.$hash.{tsx,test.tsx}` → `routes/snapshots/$owner.$name.$hash.{tsx,test.tsx}`（git mv 保留历史），改路径常量 + queryKey + URL；queries.ts `CommitRead` → `SnapshotRead`、`useCommit` → `useSnapshot`、`parents: string[]` → `parent: string \| null`；同步所有 `<Link to="/commits/...">` 改 `/snapshots/...`；vite dev/build 自动重生 `routeTree.gen.ts` | AC-7, AC-8 | T-1..T-2 |
| T-7 | 加 pytest（D-13：不再加 self_check block）：`apps/api/tests/test_snapshots_api.py` 含 happy path + 308 redirect 两个用例；老 `run_commit_api_mvp` 不动；vitest 已有的 `commits.$owner.$name.$hash.test.tsx` 迁移到 `snapshots/$owner.$name.$hash.test.tsx` 同步改名 + 跑通 | AC-9, AC-10 | T-2, T-3, T-6 |

## 风险

| 风险 | 概率 | 影响 | 缓解 |
|---|---|---|---|
| `/commits/{hash}` 的 308 redirect 与 path param 冲突：FastAPI 在 redirect 端点同时声明 `hash` path param 时，必须显式构造 `RedirectResponse` 的 url（不能用 `response_class=RedirectResponse`），否则 308 不会带上目标 path | 中 | AC-10 fail | T-3 显式 `RedirectResponse(url=f"/repos/{owner}/{name}/snapshots/{hash}", status_code=308)`；pytest 同时验证 Location header 字面值 |
| api-types 生成器找不到 / openapi.json 路径不对 | 低 | AC-4/AC-5 fail | T-4 显式两步命令；`scripts/export_openapi.py` 已存在 + 路径已钉死 `packages/api-types/openapi.json`；若 pnpm 不可用，单独把 npx openapi-typescript 写到任务备注 |
| web `routeTree.gen.ts` 没自动重生 → vite build 跑老 route 名 | 中 | AC-7 fail / vite build 报错 | T-6 在 sonnet 端到端阶段必须跑 `pnpm --filter web build`；如 generator 没触发，手动 `rm routeTree.gen.ts && pnpm --filter web dev` 一次 |
| 历史 row `commit.parents` 长度 > 1（v1 时期可能存在 merge-style row）→ 退化为 `parent[0]` 后语义丢失 | 极低 | 用户感知数据不一致 | `_snapshot_to_read` 加一行 `if len(commit.parents) > 1: log.warning(...)`；不报错；监控 logs 是否出现该警告 |
| pipeline / lineage 模块字段名 `output_commit_hash` / `input_commits` 与本 change 词汇不一致 | 低 | reviewer 误以为漏改 | 在 § 非范围 显式声明本 change 不动这些字段；留给 W2-5 recipe-yaml-v2 统一处理 |
| 308 redirect 老路径保留期不明 → 后续未及时清理 | 低 | tech debt 累积 | 在 follow-up 列出 `api-snapshot-rename-cleanup-*`，建议在 W2 结束前清；本 change merge 时 dashboard 加 follow-up 行 |

## 决策日志

| 时间 | 决策 | 出处 |
|---|---|---|
| 2026-05-20 16:30 | DB schema **不**动；改名只动 API / SDK / UI 三层，DB 内部仍叫 commit | dashboard.md § 代码扫描快照 + D-1（决策 D-10 已暗含）+ 本 change 设计权衡：v1 commit-api-mvp 已闭环 + 5 个 alembic migration 涉及 commits 表，迁移代价 >> 改名收益 |
| 2026-05-20 16:31 | 路径风格选 A：`/repos/{owner}/{name}/snapshots/{sha}`（复数 + 单数 hash） | 与 `/blobs/{sha}` / `/trees/{tree_hash}` REST 习惯一致；后续 list endpoint 可直接 `GET /snapshots` 复用 prefix |
| 2026-05-20 16:32 | 兼容期 308 redirect，**不**做并行响应 | 308 是 permanent + method-preserving，老 sdk / web 客户端无感切换；并行响应会让 schema 维护翻倍 + 测试翻倍 |
| 2026-05-20 16:33 | `commit.parents: list[str]` → `snapshot.parent: str \| None`（API 层），DB 列保留 list | data-not-code-pivot.md § 旧→新术语表已定调 "DAG → 线性单链"；DB 列保留 list 是 D-1 决策的延伸；翻译在 `_snapshot_to_read` 做 |
| 2026-05-20 16:34 | api-types 27 处不手改：跑生成器重生 `openapi.json` + `generated.ts` | `packages/api-types/package.json` scripts.generate + `scripts/export_openapi.py` 已存在；手改生成产物 = 反模式 |
| 2026-05-20 16:35 | web 路由从 flat-dot 改 folder 形式：`routes/snapshots/$owner.$name.$hash.tsx` | MEMORY § feedback_tanstack_routing_folder_form 偏好；当前虽未触发 "index + $param 并存"，但本 change 已经在改路由名，借机 folder 化为后续 W4-1/W4-2 加 list 页让路 |
| 2026-05-20 16:36 | `models/refs.py` **不**清理：实际无 `/branches` 复数 API，refs 概念中性可保留 | dashboard § 代码扫描快照对 "branches" 是基于文件名（refs.py 注释提及 branch/tag）的误读；grep 证实 routes 无 `/branches/` 字面值；本 change scope 已足够，引入额外清理违反"不超 500 行 design / 不超 7 task" |

## 交叉引用清单（reviewer 必查）

- 引用但不修改的文件：
  - `.harness/design.md` § 北极星
  - `.harness/rules/data-not-code-pivot.md` § 旧→新术语对照表（Commit → Snapshot 行）
  - `.harness/orchestration/north-star-rollout-20260520/roadmap.md` § Wave 1 § W1-1
  - `.harness/orchestration/north-star-rollout-20260520/decisions.md` D-1 / D-10 / D-11
  - `apps/api/dataplat_api/models/commit.py` / `models/refs.py`（ORM 保持不动）
  - `apps/api/alembic/versions/`（不新增 migration）
- 应当不动的文件 / 目录（防 scope creep）：
  - `apps/api/dataplat_api/models/` 全目录
  - `apps/api/dataplat_api/services/commit.py`（内部仍可叫 commit）
  - `apps/api/dataplat_api/processors/` 与 `adapters/`（W1-4 / W2 处理）
  - `apps/api/dataplat_api/schemas/pipeline.py` 内 `output_commit_hash` / `input_commits` / `source_commit_hash`（留给 W2-5）
  - `packages/core/dataplat_core/domain/`（W1-2 Operator Protocol 时统一）
  - v1 时期 22 个 change 的 `scripts/_self_check.sh` 块
- 引用的其他 change：
  - 上游：`platform-north-star-pivot-20260520`（北极星 + 永不做清单）
  - 下游：`operator-protocol-20260520` (W1-2) 依赖 Snapshot 词汇

## 关联 follow-up（如有）

- `api-snapshot-rename-cleanup-<YYYYMMDD>`：在 W2 结束前删 308 redirect 端点（依赖：所有 sdk / web 调用方已切到新路径）
- `db-snapshot-rename-<YYYYMMDD>`（可选）：如未来真有需求把 DB 列改名（commits → snapshots 表 / commit_hash → snapshot_hash 列），单独走 alembic migration change；当前不做
- W2-5 `recipe-yaml-v2-20260520`：统一 pipeline / lineage 字段词汇（`output_commit_hash` → `output_snapshot_hash` 等）
