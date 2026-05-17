---
change_id: adapter-framework-20260517
version: 2
authored_at: 2026-05-17T11:25:00Z
status: draft
revisions:
  - v1 → v2 (2026-05-17T11:25:00Z)：消化 stage 2 reviewer 2 MUST FIX + 3 SHOULD FIX。
    关键修复：(1) parents 链不再断裂——Runner 从 `request.ref` 当前指向 commit 自动读 parent；
    (2) AC-9 反向 grep 加 `test -f` 前置 + 正向断言 + 删 `2>/dev/null` 防沉默通过；
    AC-4 step 7 改为 3-tuple `(commit, dedup, result)` 与 tasks T-5 对齐；
    AC-11 加 (m) 父子链测试；
    风险段加 #7 thread pool capacity / #8 Protocol dataclass-vs-property；
    同步反哺 SKILL 跨 AC 自审清单 4 → 6 条（commit-history-continuity + reverse-grep-vacuous-pass）。
---

# Spec：Adapter Framework + RawFileUploadAdapter（MVP，in-process）

## 背景

7 个变更后 dataplat 数据底座完整：domain model + CAS + JWT auth + repo CRUD + commit/blob/tree HTTP 路由。但 design.md §9 Phase 1 #2 "Bronze 录入：手动上传 + 2 个 Adapter" 仍是 0%——`SourceAdapter` Protocol 已定义但无任何实现 / 无注册中心 / 无 runner。

本变更落 Adapter 框架最小子集：注册中心 + 同步 in-process runner + 1 个最小 adapter（`raw-file-upload`），让客户端可以把已上传的 blobs 组织成 Bronze layout 并自动 commit。

## 问题陈述

- `SourceAdapter` Protocol 已定义但**无机制**让平台发现 / 实例化 / 调用
- `IngestResult` 只含统计字段，**无路径机制**把 adapter 产出文件交给 commit 层
- 没有 HTTP 入口触发 adapter
- 上下游 demo（PDF → text → SFT pipeline）因此无法启动

## 范围

In scope：

- 修订 `IngestResult`：增加 `files: list[IngestFileRef]` 字段（`IngestFileRef(path, sha256, mode=33188)`）——adapter 通过此字段告诉 runner 要 commit 哪些 `(path → blob_sha256)` 映射
- `apps/api/dataplat_api/runner/`（新模块）：
  - `registry.py`：全局 `AdapterRegistry` 单例（按 `(name, version)` 索引）；module load 时静态注册内置 adapter
  - `runcontext.py`：最小 `StandardRunContext`（logger 真实可用；metrics/secrets/cancel/llm 占位 None）
  - `adapter_runner.py`：`AdapterRunner.run(...)` async；**自动接 parent 链**
- `apps/api/dataplat_api/adapters/raw_upload.py`：`RawFileUploadAdapter`，纯校验 + pass-through
- `apps/api/dataplat_api/schemas/ingest.py`：`IngestRequest` + `IngestResponse`（含 `ingest_summary`）
- `apps/api/dataplat_api/routers/ingest.py`：`POST /repos/{owner}/{name}/ingest`（admin only）
- module load 自动注册 RawFileUploadAdapter
- 集成 + 单元测试 ≥ 13 + self_check 13 AC

Out of scope（明确 follow-up）：

- 异步执行 / RQ：`rq-worker-skeleton-*`（next change）
- subprocess 隔离（L2 plugin）：`adapter-subprocess-isolation-*`
- 容器插件（L3）：Phase 2+
- 第二个 adapter（FirecrawlURL）：`adapter-firecrawl-*`
- PDF / Book / Arxiv adapter：各自 follow-up
- Adapter Registry DB 持久化 / UI / 动态注册：MVP 用代码 import
- Workspace 大小限制 / 超时：`quota-management-*`
- `RunContext.metrics/secrets/cancel/llm` 实质实现：对应 follow-up
- Pipeline / Recipe DSL：`pipeline-runner-*`
- 多 parent / merge commit via ingest：MVP 单 parent；merge 留 `commit-merge-api-*`

## 验收标准（13 AC + 验证方式）

### 结构 / 接口（AC-1 ~ AC-5）

- **AC-1**：`packages/core/src/dataplat_core/protocols/adapter.py` 含 `IngestFileRef(path: str, sha256: SHA256, mode: int=33188)` + `IngestResult.files: list[IngestFileRef]=Field(default_factory=list)`；既有字段（asset_count 等）保留；全 `extra="forbid"`。`protocols/__init__.py` 的 `__all__` 加 `IngestFileRef`。
  - **验证命令**：`cd packages/core && uv run python -c "from dataplat_core.protocols import IngestFileRef; from dataplat_core.protocols.adapter import IngestResult; r=IngestResult(files=[IngestFileRef(path='a.md', sha256='a'*64)]); assert r.files[0].mode==33188; assert r.asset_count==0"`

- **AC-2**：`apps/api/dataplat_api/runner/__init__.py` + `registry.py`：`AdapterRegistry` 类 + `get_registry() -> AdapterRegistry` 单例工厂；`register(adapter)` 幂等（重复 key → log warning 跳过）；`get(name, version)` / `list_all()`；module load 通过 `adapters/__init__.py` 自动注册 RawFileUploadAdapter。
  - **验证命令**：`cd apps/api && uv run python -c "import dataplat_api.adapters; from dataplat_api.runner import get_registry; reg=get_registry(); assert reg.get('raw-file-upload', '0.1') is not None; assert ('raw-file-upload','0.1') in reg.list_all()"`

- **AC-3**：`apps/api/dataplat_api/runner/runcontext.py`：`StandardRunContext` dataclass 实现 `RunContext` Protocol；`logger` 真实 Python logger；其余 4 字段（metrics/secrets/cancel_event/llm）允许 None。
  - **验证命令**：`cd apps/api && uv run python -c "from dataplat_core.protocols.runcontext import RunContext; from dataplat_api.runner.runcontext import StandardRunContext; import logging; ctx=StandardRunContext(logger=logging.getLogger('t')); assert isinstance(ctx, RunContext); ctx.logger.info('ok')"`

- **AC-4**：`apps/api/dataplat_api/runner/adapter_runner.py`：`AdapterRunner.run(session, store, repo_id, request: IngestRequest) -> tuple[CommitORM, bool, IngestResult]` async **3-tuple**（commit, dedup, result）：
  1. 从 registry 取 adapter；未找到 → `HTTPException(404, {"detail":"Adapter <n>@<v> 不存在", "available":[...]})`
  2. **parent 自动接链**：若 `request.parents` 非空 → 直接用；否则 if `request.ref` 非空 → SELECT `RefORM.commit_hash` for `(repo_id, ref=request.ref)`，命中则 `parents=[commit_hash]`，未命中（首次 ingest）→ `parents=[]`（root commit）
  3. `tempfile.mkdtemp(prefix="dataplat-ingest-")` 创建 workspace
  4. `result = await asyncio.to_thread(adapter.ingest, request.spec, Path(workspace), ctx)`
  5. 构造 `CommitCreate(tree=TreeCreate(entries=[TreeEntryCreate(name=f.path, mode=f.mode, entry_type="blob", target_hash=f.sha256) for f in result.files]), parents=resolved_parents, author_id=request.author_id, message=request.message, ref=request.ref)`
  6. `commit, dedup = await CommitService.create_commit(session, store, repo_id, commit_create)`
  7. `finally: shutil.rmtree(workspace, ignore_errors=True)`
  8. 返 `(commit, dedup, result)`
  - **验证命令**：`cd apps/api && uv run python -c "from dataplat_api.runner.adapter_runner import AdapterRunner; import inspect; assert inspect.iscoroutinefunction(AdapterRunner.run)"`

- **AC-5**：`apps/api/dataplat_api/adapters/raw_upload.py`：`RawFileUploadAdapter`：
  - `name="raw-file-upload"`, `version="0.1"`, `output_subtype="generic"`
  - `input_schema`：JSON Schema dict（含 `files`、`asset_id?`）
  - `ingest(spec, workspace, ctx) -> IngestResult`：校验 `files` 非空 + path 唯一 + 每个 sha256 64-hex；返 `IngestResult(file_count=len(files), files=[IngestFileRef(...)])`；不写 workspace；不依赖 ctx（参数允许 None 便于单元测试）
  - 在 `apps/api/dataplat_api/adapters/__init__.py` import 时调 `get_registry().register(RawFileUploadAdapter())`
  - **验证命令**：`cd apps/api && uv run python -c "from dataplat_core.protocols.adapter import SourceAdapter; from dataplat_api.adapters.raw_upload import RawFileUploadAdapter; a=RawFileUploadAdapter(); assert isinstance(a, SourceAdapter); r=a.ingest({'files':[{'path':'a.md','sha256':'a'*64}]}, None, None); assert r.file_count==1 and r.files[0].path=='a.md'"`

### 路由 / 行为 / 安全（AC-6 ~ AC-10）

- **AC-6**：`schemas/ingest.py`：`IngestRequest(adapter_name, adapter_version, spec: dict[str, Any], author_id, message: str|None=None, ref: str|None=None, parents: list[SHA256]=Field(default_factory=list))` + `IngestSummary(asset_count, file_count, bytes_written, notes)` + `IngestResponse(commit: CommitRead, ingest_summary: IngestSummary)`；全 `extra="forbid"`。
  - 新增 `parents` 字段允许 client 显式传父 commit；为空时 runner 走 AC-4 step 2 的 ref-based 自动接链。
  - **验证命令**：`cd apps/api && uv run python -c "from dataplat_api.schemas.ingest import IngestRequest, IngestSummary, IngestResponse; assert IngestRequest.model_config.get('extra')=='forbid'; assert 'parents' in IngestRequest.model_fields; assert 'ingest_summary' in IngestResponse.model_fields"`

- **AC-7**：`routers/ingest.py`：`APIRouter(prefix='/repos', tags=['ingest'])` + 路由 `POST /{owner}/{name}/ingest` `Depends(require_admin)` + repo 存在校验（不可见 / 不存在 → 404）→ 调 `AdapterRunner.run(...)` → 200 + `IngestResponse`。
  - **验证命令**：`cd apps/api && uv run python -c "from dataplat_api.routers.ingest import router; paths={r.path for r in router.routes}; assert '/repos/{owner}/{name}/ingest' in paths"`

- **AC-8**：`main.py` include + OpenAPI 含 `/repos/{owner}/{name}/ingest`。
  - **验证命令**：`cd apps/api && uv run python -c "from dataplat_api.main import app; s=app.openapi(); assert '/repos/{owner}/{name}/ingest' in s['paths']"`

- **AC-9**：**Repo visibility 复用**：写路由调 `RepoService.get_by_owner_name(session, owner, name, admin)` 不可见 / 不存在 → 404；非 admin → 403（require_admin gate）。**实现端不重复 `_visibility_visible`**。
  - **验证命令**（防沉默通过：先 `test -f` 确保文件存在 + 正向断言确认真复用 + 反向 grep 确认不重复实现；删 `2>/dev/null` 暴露路径错误）：`test -f apps/api/dataplat_api/routers/ingest.py && test -f apps/api/dataplat_api/runner/adapter_runner.py && grep -qE "_resolve_repo|RepoService.get_by_owner_name" apps/api/dataplat_api/routers/ingest.py && ! grep -rE "_visibility_visible" apps/api/dataplat_api/runner apps/api/dataplat_api/routers/ingest.py apps/api/dataplat_api/adapters`

- **AC-10**：**典型错误路径**：
  - 未找到 adapter → 404 含 `{detail: ..., available: [...]}`
  - adapter.ingest 抛 `ValidationError` / `ValueError` → 400
  - 同 spec 二次 POST → CommitService 幂等命中 → 200 + `commit.deduplicated=true` + 同 commit_hash
  - **父子链**：第二次 ingest 到同 ref（不同 spec）→ 新 commit.parents = [前一次 commit.hash]
  - 由 AC-11 (d)(f)(g)(l)(m) 覆盖

### 测试 / 质量（AC-11 ~ AC-13）

- **AC-11**：`apps/api/tests/test_ingest.py` ≥ 13 测试：
  - (a) **单元** `test_a_registry_register_get_list`
  - (b) **单元** `test_b_raw_adapter_ingest_pass_through`
  - (c) `test_c_admin_ingest_creates_commit_200`
  - (d) `test_d_ingest_with_missing_blob_returns_400`
  - (e) `test_e_user_ingest_returns_403`
  - (f) `test_f_unknown_adapter_returns_404`
  - (g) `test_g_ingest_idempotent_returns_dedup_true`
  - (h) `test_h_ingest_with_ref_upserts`
  - (i) `test_i_get_commit_after_ingest_includes_tree`
  - (j) `test_j_anonymous_ingest_private_repo_404`
  - (k) `test_k_ingest_multi_file_tree_structure_correct`
  - (l) `test_l_adapter_validation_error_returns_400`
  - **(m) `test_m_second_ingest_to_same_ref_creates_child`**：第一次 ingest 到 `ref=main` → C1.parents=[]；第二次 ingest 不同 spec → C2.parents=[C1.hash] 且 GET `/commits/{C1.hash}` 仍 200（C1 从历史链可达，未孤立）

- **AC-12**：`uv run ruff check apps/api packages/core` + `uv run mypy apps/api/dataplat_api packages/core/src` 全 PASS。**由 T-7b 显式覆盖**（v2 加）。
  - **验证命令**：`uv run ruff check apps/api packages/core && uv run mypy apps/api/dataplat_api packages/core/src`

- **AC-13**：`scripts/_self_check.sh adapter-framework` 13 AC 全 PASS。
  - **验证命令**：`DATAPLAT_PG_PORT=5433 DATAPLAT_MINIO_PORT=9100 DATAPLAT_MINIO_ACCESS_KEY=dataplat DATAPLAT_MINIO_SECRET_KEY=dataplat-secret bash scripts/_self_check.sh adapter-framework` → `PASS=13`。

## 风险

1. **修改 `IngestResult` 破坏既有 33 core 测试**。**缓解**：只新增 `files` 字段（带默认 `[]`）；既有字段全保留；reviewer 实测 33 passed 基线。
2. **adapter 注册重复**：module load 重复 import。**缓解**：`AdapterRegistry.register` 幂等（warning 跳过）；AC-11 (a) 覆盖。
3. **workspace 泄漏**：`try/finally shutil.rmtree(ignore_errors=True)`；进程崩溃残留留 `workspace-gc-*` follow-up。
4. **同步 adapter 阻塞**：runner 用 `asyncio.to_thread(...)`；MVP default ThreadPoolExecutor 容量 `min(32, cpu+4)`。**长跑 adapter（PDF/Firecrawl）并发饱和** 留给 `rq-worker-skeleton-*` 评估并发上限。
5. **HTTPException from service**：延续 commit-api-mvp 现状；`domain-errors-introduce-*` 已 deferred。
6. **跨 AC 一致性**（commit-api-mvp 反哺 checklist 回归用）：
   - 四链路：本变更 ingest 幂等 = commit 幂等（沿用 commit-api-mvp 固化的 CommitService canonical hash）
   - 事务边界：本变更不引入新事务（沿用 CommitService）
   - AC 验证命令一行式：AC-9 用 `test -f` + 正向 + 反向三重防沉默通过（v2 加）
7. **新增（v2）**：**Protocol 结构匹配 dataclass vs property**：`RunContext` Protocol 声明 `logger/...` 为 `@property`，`StandardRunContext` 用 dataclass 字段实现。`runtime_checkable` isinstance 通过；mypy 通过。**若未来 Protocol 升级为 read-only property（setter raise）**，dataclass 实现需同步改为 `property + __init__`。**缓解**：AC-12 mypy 作为 gate；改造小范围。
8. **新增（v2）**：**orphan commit / 父子链断裂**（reviewer MUST FIX-1）：v1 写死 `parents=[]`。v2 修复：runner 根据 `request.ref` 自动读 RefORM 当前 commit 作 parent；client 也可显式传 `parents`。AC-11 (m) 测试覆盖。**未覆盖 case**：第二次 ingest 不传 ref 也不传 parents → 走 root commit 路径，client 自负历史链。

## 关键决策

| 决策 | 选项 | 选择 | 理由 |
|---|---|---|---|
| Adapter 输出契约 | (a) 写 workspace (b) IngestResult.files refs | **(b)** | RawFileUpload 不写盘；不耦合 BlobStore |
| 注册机制 | (a) entrypoints (b) 代码 import 静态 | **(b) MVP** | entrypoints 留 L2 |
| 执行模型 | (a) sync in-process (b) RQ | **(a) MVP** | RQ 下个 change |
| Adapter 错误翻译 | service raise HTTPException | **采用** | 与 commit-api-mvp 一致 |
| IngestResult schema 升级 | (a) 加字段 (b) 新类型 | **(a)** | 不破坏既有字段 |
| RawFileUpload manifest.yaml | (a) 自动生成 (b) client 上传 | **(b) MVP** | 减依赖 |
| ingest 路由 prefix | (a) `/repos` 共享 (b) 独立 | **(a)** | 与 commit-api 一致 |
| **AC-4 返回类型** | (a) 2-tuple (commit, result) (b) 3-tuple (commit, dedup, result) | **(b) v2** | T-6 构造 IngestResponse 需要 dedup；与 CommitService 接口同构 |
| **parent 链接策略** | (a) 写死 `parents=[]` (b) ref-based 自动 (c) client 显式 | **(b) 主路径 + (c) override** | 自动模式符合"推 main" 直觉；显式参数留控制 |

## 跨 AC 自审 grep（commit-api-mvp 反哺 checklist 回归 + v2 反哺第 5/6 条）

```bash
grep -nE "事务前|事务内|事务外" spec.md                     # 无矛盾（实测仅本行注释）
grep -nE "files|FileRef|sha256" spec.md                    # 三链路一致
grep -cE "uv run python -c|test -f|bash scripts" spec.md    # AC 验证命令 ≥ 7
grep -nE "parents=\[\]" spec.md                            # 0 次裸出现（v2 修复）；或仅在风险段被讨论
grep -nE "2>/dev/null" spec.md                             # AC 验证命令不许吞 stderr（v2 修复）
```

## 流程偏离声明

无功能性偏离。**反哺**：本评审周期暴露两个 spec generator 失败模式 → 已同步反哺 `.harness/skills/request-analysis/SKILL.md` 跨 AC 自审清单 4 → 6 条：
- 第 5 条：**commit 历史链连续性**（parents 自动接链 OR 显式 accept orphan）
- 第 6 条：**反向 grep 必须配 `test -f` 前置 + 正向断言**（防文件不存在沉默通过；同型 bug 已是 [project-followup-harness-lint] 第 6 次证据）

此外 reviewer 发现 `process_tasks` 在 7/8 既有 change 系统性缺失（commit-api-mvp 仅 1 个 T-8）→ tasks v2 补 T-10~T-15，并反哺 SKILL 步骤 5 加 "process_tasks 6 条必填"。
