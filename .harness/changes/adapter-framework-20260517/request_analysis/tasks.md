---
change_id: adapter-framework-20260517
version: 2
authored_at: 2026-05-17T11:25:00Z
revisions:
  - v1 → v2 (2026-05-17T11:25:00Z)：消化 stage 2 tasks reviewer 2 MUST FIX + 3 SHOULD FIX。
    T-5 step 8 改 3-tuple + 加 parent 自动接链；T-1 显式 `Field` import；
    新增 T-7b lint+mypy 覆盖 AC-12；新增 T-10~T-15 process_tasks（stage 2/4/6/7/9/10）；
    依赖图重画。
---

# Tasks

## T-1 修订 IngestResult + IngestFileRef（packages/core）

- 修订 `packages/core/src/dataplat_core/protocols/adapter.py`：
  - 在 `from pydantic import ...` 行追加 `Field`（v2 SHOULD FIX）
  - 新增 `IngestFileRef(BaseModel, extra="forbid")`：`path: str`、`sha256: SHA256`（复用 `dataplat_core.domain.types.SHA256`）、`mode: int=33188`
  - `IngestResult` 加字段 `files: list[IngestFileRef] = Field(default_factory=list)`；既有字段全保留
- 更新 `packages/core/src/dataplat_core/protocols/__init__.py`：`__all__` 数组追加 `IngestFileRef`
- depends_on: 无
- estimated_stage: stage-3
- AC 覆盖：AC-1

## T-2 AdapterRegistry + get_registry 单例

- 新建 `apps/api/dataplat_api/runner/__init__.py`：export `get_registry`、`AdapterRegistry`
- 新建 `apps/api/dataplat_api/runner/registry.py`：
  - `class AdapterRegistry`：`_adapters: dict[tuple[str, str], SourceAdapter] = {}` + 方法 `register(adapter)` / `get(name, version) -> SourceAdapter | None` / `list_all() -> list[tuple[str, str]]`
  - register 幂等：重复 key 记 `logger.warning` 跳过（不 raise）
- module-level 单例 `_registry = AdapterRegistry()`；`get_registry()` 返之
- depends_on: 无
- estimated_stage: stage-3
- AC 覆盖：AC-2

## T-3 StandardRunContext

- 新建 `apps/api/dataplat_api/runner/runcontext.py`：
  - `@dataclass class StandardRunContext`：`logger: logging.Logger`、其余 4 字段（`metrics: Any=None`, `secrets: Any=None`, `cancel_event: Any=None`, `llm: Any=None`）
  - 必须满足 `RunContext` Protocol（runtime_checkable）
- depends_on: 无
- estimated_stage: stage-3
- AC 覆盖：AC-3

## T-4 RawFileUploadAdapter

- 新建 `apps/api/dataplat_api/adapters/__init__.py`：import RawFileUploadAdapter 后调 `get_registry().register(RawFileUploadAdapter())`
- 新建 `apps/api/dataplat_api/adapters/raw_upload.py`：
  - `class RawFileUploadAdapter`（实现 SourceAdapter Protocol）
  - 类属性：`name="raw-file-upload"`、`version="0.1"`、`output_subtype="generic"`、`input_schema={...}` JSON Schema dict
  - `ingest(self, spec: dict, workspace: Path | None, ctx: RunContext | None) -> IngestResult`：
    - 内部 Pydantic 模型校验 spec：`files: list[{path: str, sha256: SHA256}]` 非空 + path 唯一 → 失败 raise `ValueError`
    - 返 `IngestResult(file_count=len(files), files=[IngestFileRef(path=f.path, sha256=f.sha256) for f in files])`
    - 不写 workspace
  - **注释**：`workspace` / `ctx` 类型放宽到 `| None` 让单元测试可传 None；其他 adapter 应按 Protocol 严类型实现
- depends_on: T-1, T-2, T-3
- estimated_stage: stage-3
- AC 覆盖：AC-5

## T-5 AdapterRunner（v2：3-tuple + parent 自动接链）

- 新建 `apps/api/dataplat_api/runner/adapter_runner.py`：
  - `class AdapterRunner` 静态方法 `async run(session, store, repo_id, request: IngestRequest) -> tuple[CommitORM, bool, IngestResult]`（**v2: 3-tuple**）：
    1. 从 `get_registry().get(request.adapter_name, request.adapter_version)`；None → `HTTPException(404, {"detail": ..., "available": [...]})`
    2. **parent 自动接链**（v2 修 MUST FIX-1）：
       ```python
       if request.parents:
           resolved_parents = list(request.parents)
       elif request.ref:
           ref_row = (await session.execute(select(RefORM).where(RefORM.repo_id == repo_id, RefORM.name == request.ref))).scalar_one_or_none()
           resolved_parents = [ref_row.commit_hash] if ref_row else []
       else:
           resolved_parents = []
       ```
    3. `workspace = Path(tempfile.mkdtemp(prefix="dataplat-ingest-"))`；`logger = logging.getLogger("dataplat.ingest")`；`ctx = StandardRunContext(logger=logger)`
    4. 在 `try`：`result = await asyncio.to_thread(adapter.ingest, request.spec, workspace, ctx)`
       - except `ValueError | ValidationError` → `HTTPException(400, detail=str(exc))`
    5. 构造 `CommitCreate(tree=TreeCreate(entries=[TreeEntryCreate(name=f.path, mode=f.mode, entry_type="blob", target_hash=f.sha256) for f in result.files]), parents=resolved_parents, author_id=request.author_id, message=request.message, lineage=None, ref=request.ref)`
    6. `commit, dedup = await CommitService.create_commit(session, store, repo_id, commit_create)`
    7. `finally: shutil.rmtree(workspace, ignore_errors=True)`
    8. 返 `(commit, dedup, result)` **3-tuple**
- depends_on: T-1, T-2, T-3
- estimated_stage: stage-3
- AC 覆盖：AC-4, AC-10

## T-6 ingest schemas + router

- 新建 `apps/api/dataplat_api/schemas/ingest.py`：
  - `IngestRequest(adapter_name: str, adapter_version: str, spec: dict[str, Any], author_id: str, message: str | None = None, ref: str | None = None, parents: list[SHA256] = Field(default_factory=list))` `extra="forbid"`（**v2 加 parents**）
  - `IngestSummary(asset_count: int=0, file_count: int=0, bytes_written: int=0, notes: str | None=None)` `extra="forbid"`
  - `IngestResponse(commit: CommitRead, ingest_summary: IngestSummary)` `extra="forbid"`
- 更新 `schemas/__init__.py` export 3 个新类型
- 新建 `apps/api/dataplat_api/routers/ingest.py`：
  - `APIRouter(prefix="/repos", tags=["ingest"])`
  - `POST /{owner}/{name}/ingest`：`Depends(require_admin)` + `_resolve_repo`（**inline 同款逻辑或从 commits router import**）→ 调 `AdapterRunner.run(...)`
  - 200 + `IngestResponse(commit=_commit_to_read(commit, dedup), ingest_summary=IngestSummary(asset_count=result.asset_count, file_count=result.file_count, bytes_written=result.bytes_written, notes=result.notes))`
- 更新 `main.py` `include_router(ingest_router)`
- 验证 `from dataplat_core.protocols import IngestFileRef` 不报错（T-1 跨链验证）
- depends_on: T-1, T-4, T-5
- estimated_stage: stage-3
- AC 覆盖：AC-6, AC-7, AC-8, AC-9

## T-7 OpenAPI codegen

- `make codegen` → `packages/api-types/openapi.json` 同步
- depends_on: T-6
- estimated_stage: stage-3
- AC 覆盖：AC-8

## T-7b lint + type gate（v2 加，AC-12 显式主）

- `uv run ruff check apps/api packages/core` → All checks passed
- `uv run mypy apps/api/dataplat_api packages/core/src` → no issues
- 若 mypy 在 StandardRunContext dataclass vs RunContext Protocol property 上报错 → 转 property + __init__（spec 风险 #7 缓解）
- depends_on: T-7
- estimated_stage: stage-3
- AC 覆盖：AC-12

## T-8 测试 ≥ 13（单元 + 集成）

- 新建 `apps/api/tests/test_ingest.py`：
  - 探针：PG + MinIO 双 skipif（与 test_commits 一致）
  - Fixture：`admin_user` / `normal_user` / `_override_blob_store`（**优先 import 自 `apps/api/tests/conftest.py` 已有 fixtures**；未提供再本地新增）
  - 测试列表（spec v2 AC-11 a~m，13 个）：
    - (a) **单元** registry register/get/list（fresh `AdapterRegistry()` 起；含幂等 / 重复注册 warning）
    - (b) **单元** `RawFileUploadAdapter().ingest({files:[{path:'a.md',sha256:'a'*64}]}, None, None)`
    - (c)~(m) 集成 11 个，包括 **(m) parent 链测试**：第一次 ingest 到 ref=main → C1.parents=[]；第二次 ingest 不同 spec → C2.parents=[C1.hash]
- depends_on: T-1~T-7b
- estimated_stage: stage-3
- AC 覆盖：AC-11

## T-9 self_check adapter-framework block

- `scripts/_self_check.sh` 追加 `run_adapter_framework` 函数（13 AC，每个对应 spec v2 验证命令）+ filter `adapter-framework`
- AC-11 走 PG + MinIO 双探针（复用既有 `run_ac_skipif_no_pg_or_minio`）
- AC-9 验证命令**严禁** `2>/dev/null`；必须含 `test -f` 前置 + 正向断言
- depends_on: T-1~T-8
- estimated_stage: stage-3
- AC 覆盖：AC-13

## T-10 stage-2 spec/tasks review（process）

- 已落地：`request_analysis/review/{spec,tasks}_review_v1.md`（v1 REVISION REQUIRED → v2 fix）+ 待 `..._review_v2.md`（reviewer v2 APPROVED）
- description：独立 reviewer 子会话评审 spec.md + tasks.md，verdict 落到 review/v* 文档；spec/tasks 改完 v2 后重新评审
- owner：由 reviewer agent 完成
- depends_on: T-1~T-9（v1 spec/tasks 完）
- estimated_stage: stage-2

## T-11 stage-4 coding review（process）

- description：独立 reviewer 子会话评审 working-tree diff 对 coding_report v1 的真实性，给 `coding/review/code_review_v1.md`
- depends_on: T-1~T-9 编码全完
- estimated_stage: stage-4

## T-12 stage-5/6 test_report + unit-test review（process）

- description：写 `unit_test/test_report_v1.md` 描述 AC ↔ 测试映射；独立 reviewer 给 `unit_test/review/test_review_v1.md`
- depends_on: T-8（测试落完）
- estimated_stage: stage-6

## T-13 stage-7 CI 验证（process）

- description：跑 `bash scripts/_self_check.sh` 全仓 PASS=N 写到 `ci_result/ci_result_v1.md`
- depends_on: T-9, T-12
- estimated_stage: stage-7

## T-14 stage-9 deploy verify（process，skipped）

- description：本变更无运行时部署面；deploy_verify_v1.md 写 `status: skipped`，说明"仅新增 FastAPI 路由 + service + ORM relationship，无 docker / cron / migration"
- depends_on: T-13
- estimated_stage: stage-9

## T-15 stage-10 close + 反哺 SKILL（process）

- description：
  - summary.md 更新 stage=`closed` / status=`closed` / `closed_at`
  - 反哺 `.harness/skills/request-analysis/SKILL.md` § 跨 AC 自审清单：4 → 6 条（commit-history-continuity + reverse-grep-vacuous-pass + process_tasks 6 条必填）
  - 反哺 [project-followup-harness-lint] 第 6 次证据
  - 更新 [session-handoff-20260517] 8 个 closed change
- depends_on: T-13, T-14
- estimated_stage: stage-10

## 任务依赖图

```
T-1 (IngestResult.files) ─┐
T-2 (Registry) ───────────┤
T-3 (RunContext) ─────────┤
                          ├──→ T-4 (RawAdapter) ─┐
                          ├──→ T-5 (Runner) ─────┤
                                                  ├──→ T-6 (router) ──→ T-7 (codegen) ──→ T-7b (lint+mypy) ──→ T-8 (tests) ──→ T-9 (self_check)
                                                  
T-9 ──→ T-10 (stage-2 review) ──→ T-11 (stage-4 review) ──→ T-12 (stage-6 review) ──→ T-13 (CI) ──→ T-14 (deploy noop) ──→ T-15 (close + SKILL reflect)
```

T-1 / T-2 / T-3 并行；T-4 / T-5 依赖前三；T-6 依赖 T-4+T-5；之后串行；T-10~T-15 process 节点。

## AC 覆盖矩阵（v2 加，确保无孤儿）

| AC | 覆盖 task |
|---|---|
| AC-1 | T-1 |
| AC-2 | T-2 |
| AC-3 | T-3 |
| AC-4 | T-5 |
| AC-5 | T-4 |
| AC-6 | T-6 |
| AC-7 | T-6 |
| AC-8 | T-6, T-7 |
| AC-9 | T-6 |
| AC-10 | T-5 |
| AC-11 | T-8 |
| AC-12 | T-7b |
| AC-13 | T-9 |
