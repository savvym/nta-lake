---
change_id: adapter-framework-20260517
target_head: working-tree (base c1a9e0a)
review_version: 1
reviewer: claude-stage4-reviewer
reviewed_at: 2026-05-17T12:00:00Z
verdict: APPROVED
---

# Code Review v1

## 1. 范围与作者声明对照

coding_report v1 声明 16 个改动文件（含 .harness/skills 反哺）；实际 `git status --short`：

| 类型 | 路径 | 一致？ |
|---|---|---|
| M | `.harness/skills/request-analysis/SKILL.md` | yes |
| M | `apps/api/dataplat_api/main.py` | yes |
| M | `apps/api/dataplat_api/schemas/__init__.py` | yes |
| M | `packages/api-types/openapi.json` | yes |
| M | `packages/core/src/dataplat_core/protocols/__init__.py` | yes |
| M | `packages/core/src/dataplat_core/protocols/adapter.py` | yes |
| M | `scripts/_self_check.sh` | yes |
| ?? | `apps/api/dataplat_api/runner/{__init__,registry,runcontext,adapter_runner}.py` | yes (4) |
| ?? | `apps/api/dataplat_api/adapters/{__init__,raw_upload}.py` | yes (2) |
| ?? | `apps/api/dataplat_api/routers/ingest.py` | yes |
| ?? | `apps/api/dataplat_api/schemas/ingest.py` | yes |
| ?? | `apps/api/tests/test_ingest.py` | yes |
| ?? | `.harness/changes/adapter-framework-20260517/` | yes（变更目录本身） |

声明清单与 working tree **完全一致**；改动全部落在 spec v2 §范围 in-scope 之内；目录归属符合 `engineering-structure.md`（runner/ + adapters/ 是 spec 引入的新顶层模块，spec §范围段明文允许）。

## 2. 正确性 / 安全 / 架构审查

逐文件读 diff 后的发现，**按反馈重点 1~6 + 通审项分级**。

### MUST FIX

无。

### SHOULD FIX

| # | 文件:行 | 问题 | 建议 |
|---|---|---|---|
| S1 | `apps/api/dataplat_api/adapters/raw_upload.py:76` | `except Exception as exc: ... # noqa: BLE001` 把 Pydantic ValidationError 与未知异常一锅端，吃 `BLE001`。Pydantic 的 `model_validate` 抛 `ValidationError`（pydantic）就够了；裸 `Exception` 把潜在 bug（如 `TypeError`）也翻成 `ValueError`。 | 缩窄到 `except ValidationError as exc:`（与 runner 端 `try/except ValueError, ValidationError` 同型）。当前不阻塞——runner 端 except 仍兜底翻 400；但未来 adapter 数量上升后会掩盖编程错误。 |
| S2 | `apps/api/tests/test_ingest.py:125` | `except Exception: pass` 吞 bucket teardown 异常。`coding-style.md` §1.5 明禁——必须 `logger.exception(...)` 留痕。 | 改 `logging.getLogger(__name__).exception("test bucket teardown failed: %s", bucket)`，或显式 narrow 到 boto3 ClientError。 |
| S3 | `apps/api/dataplat_api/runner/adapter_runner.py:78` | `mkdtemp` 在 ref 查询之后、`asyncio.to_thread` 之前；若 RefORM 查询抛异常，workspace 不会创建，OK——但若 `CommitService.create_commit` 内部抛异常，workspace 在 `finally` 清理。逻辑正确，但 dataclass `StandardRunContext(logger=_logger)` 用了模块级 logger，未注入 trace_id / run_id；后续 `rq-worker-skeleton-*` 应替换为带 ingest_run_id 的 child logger。 | follow-up 时把 ctx 升级为 `BoundLogger(run_id=...)`；当前 MVP 不阻塞。 |
| S4 | `apps/api/dataplat_api/routers/ingest.py:28-41` | `_resolve_repo` 与 `routers/commits.py:47-60` 几乎逐字重复（仅 docstring 措辞略不同）。`coding-style.md` §0 提"三处相似考虑抽公共"——这是第 2 处。 | 不在本变更修；开 follow-up `router-resolve-repo-helper-*` 抽到 `routers/_helpers.py`。**留 deferred**，跟踪位置：下次 router 系列改动时开。 |
| S5 | `apps/api/dataplat_api/runner/adapter_runner.py:91-108` | `CommitCreate` 字段构造里 `lineage=None` 写死——RawFileUpload 不产 lineage 合理，但后续 PDF/Firecrawl adapter 应有 `Lineage(produced_by=ProducedBy(kind="adapter", name=..., version=..., config_hash=...))`。 | spec 已声明 lineage 由后续 adapter 自填；MVP 接受。当前不阻塞。 |

### NICE TO HAVE

| # | 位置 | 提示 |
|---|---|---|
| N1 | `runner/runcontext.py` `Any=None` × 4 | spec 风险 #7 提了 Protocol property vs dataclass field 的潜在 mypy 摩擦——目前 mypy 通过。N.B.：未来 Protocol 升 read-only `@property` 时同步改为 `property + __init__`。 |
| N2 | `adapters/raw_upload.py:70-71` `workspace: Path \| None` / `ctx: RunContext \| None` | 类型放宽到 Optional 是单元测试便利；其他 adapter 实现应按 Protocol 严类型签名。注释已点明，可加 `# type: ignore[override]` 让意图更显式（若 Protocol 严类型）。当前 Protocol `ingest` 签名是 `Path` / `RunContext`，但 `runtime_checkable` 仅检查方法存在不查签名——MVP 接受。 |
| N3 | `runner/adapter_runner.py` | 没有 `_logger.info(...)` 在关键节点（adapter 调用前 / commit 创建后）；可观测性留 follow-up（`telemetry-bootstrap-*`）。 |
| N4 | `test_ingest.py` | `_make_user / _delete_user / _delete_repo_cascade` 与 `test_commits.py:50-103` 逐字重复——可抽到 `conftest.py` 共享 fixture；不强求，留 `test-fixture-consolidation-*` follow-up。 |

## 3. 针对作者列出的 6 个 reviewer 重点

### 3.1 parent 自动接链正确性（MUST FIX-1 修复验证）

`adapter_runner.py:66-76` 实现：
```python
if request.parents:
    resolved_parents = list(request.parents)
elif request.ref:
    ref_stmt = select(RefORM).where(RefORM.repo_id == repo_id, RefORM.name == request.ref)
    ref_row = (await session.execute(ref_stmt)).scalar_one_or_none()
    resolved_parents = [ref_row.commit_hash] if ref_row else []
else:
    resolved_parents = []
```

逐条 vs spec v2 AC-4 step 2：
- request.parents 非空 → 直接用 ✓
- request.parents 空 + request.ref 非空 → SELECT RefORM ✓
- ref 未命中 → `parents=[]`（root commit，首次 ingest）✓
- 都空 → `parents=[]` ✓

test_m（`test_ingest.py:551-592`）端到端覆盖：
- 第一次 ingest ref=main，无 RefORM → C1.parents=[] ✓
- 第二次 ingest 不同 spec 同 ref → C2.parents=[C1.hash] ✓
- GET `/commits/{C1.hash}` 仍 200 → 历史链可达 ✓

**结论**：MUST FIX-1 修复落地、test 覆盖完整。

### 3.2 AC-9 反向 grep 修复

执行 `grep -rE "_visibility_visible" apps/api/dataplat_api/runner apps/api/dataplat_api/routers/ingest.py apps/api/dataplat_api/adapters`：

```
（无输出，exit=1）
```

正向：`ingest.py:35` 调用 `RepoService.get_by_owner_name(...)`（与 commits router 同款复用）。`services/repo.py` 是 `_visibility_visible` 的唯一实现。

self_check AC-9 实测 `PASS`。**结论**：[project-followup-harness-lint] 第 6 次教训反哺成功。

### 3.3 adapter 注册时机

`main.py:11`：
```python
from dataplat_api import adapters as _adapters  # noqa: F401
```

在 `include_router(ingest_router)`（line 40）**之前** import。Python module 导入是 idempotent：
1. `dataplat_api.adapters.__init__` 触发 `RawFileUploadAdapter()` register
2. 任何后续 import（路由内 `from dataplat_api.runner ...`）使用同一 `_registry` module-level 单例

即便 router 模块本身 import 顺序晚于 `_adapters`，registry 单例已 mutated。**结论**：注册时机正确。

唯一隐患：若有人未来直接 `from dataplat_api.routers.ingest import router` 而不经过 main.py（如导出 OpenAPI 脚本），registry 不会注册。**当前不阻塞**——`scripts/export_openapi.py` 走 main.py 入口；若新增脚本绕过，加 follow-up `adapter-registry-eager-load-*`。

### 3.4 dependency_overrides 漏关 + 跨 test 共存

`test_ingest.py:107-126` 的 `_override_blob_store` fixture：
- `app.dependency_overrides[get_blob_store] = lambda: store`
- `finally: app.dependency_overrides.pop(get_blob_store, None)` + `raw.delete_bucket(...)`

`test_commits.py:120-140` 同款模式（`store = MinioBlobStore(...)` + `dependency_overrides[get_blob_store]` + `pop` + `delete_bucket`）。

实测：`pytest tests/test_commits.py tests/test_ingest.py` → **31 passed in 14.79s**，无 fixture 污染。

**唯一 SHOULD FIX**：S2 提到的 `except Exception: pass` 吞 teardown 异常——bucket 残留时 next-run 用不同 `uuid.hex[:8]` 名字，**不会污染**但留日志盲区。

### 3.5 asyncio.to_thread 正确使用

`adapter_runner.py:82-84`：
```python
result = await asyncio.to_thread(
    adapter.ingest, request.spec, workspace, ctx
)
```

**非** `await adapter.ingest(...)`（adapter.ingest 是 sync def），**正确**。RawFileUpload 是 pass-through（微秒级）；spec 风险 #4 提到的"长跑 adapter（PDF/Firecrawl）并发饱和" 留给 `rq-worker-skeleton-*`。MVP OK。

### 3.6 IngestResult.files 加字段无回归

`packages/core/tests/`：**33 passed in 0.22s**，0 回归。

`IngestResult.files: list[IngestFileRef] = Field(default_factory=list)`——既有 4 字段保留（asset_count/file_count/bytes_written/notes），新字段带默认空数组，向后兼容。

`packages/sdk-py` 是空壳（spec 风险 #6 已注明），无 SDK 客户端需同步。

## 4. 风格审查（按 coding-style.md 逐项）

| 项 | 通过？ |
|---|---|
| 类型完整性（公共 API 全类型） | yes |
| async 一致性（runner / router 全 async；adapter.ingest sync 包 to_thread） | yes |
| 命名（snake_case / PascalCase） | yes |
| 注释（少而精，docstring 写 contract） | yes，模块顶端 docstring 标 spec AC 索引 |
| 错误处理（HTTPException 翻译；不裸 `except Exception: pass`） | mostly；S1/S2 两处 SHOULD FIX |
| 日志（structlog/logging，结构化） | partial；N3 提到关键节点缺 info |
| 测试组织（test_<被测>_<场景>_<期望>） | yes（a~m 覆盖矩阵） |
| LLM Gateway / Pydantic v2 / extra=forbid | yes（IngestRequest/Summary/Response 全 forbid） |
| TS 用 @dataplat/api-types（codegen 同步） | yes（openapi.json 含 IngestRequest/Response + /ingest path） |

## 5. 性能与可观测性

| 项 | 结论 |
|---|---|
| N+1 查询 | runner 1 次 ref SELECT；commit 创建走 CommitService 既有事务边界（无新增 N+1）。 |
| 大对象一次性 read | adapter 不读 blob（pass-through refs）；commit 服务复用 cas-storage 流式 IO。 |
| 列表接口分页 | 本变更无列表接口，N/A。 |
| 日志结构化 | logger 注入 ctx，但调用点缺 info（N3）。 |
| metric / span | 未接入；项目尚无 telemetry 基础。 |

## 6. 验证证据

| 命令 | 结果 |
|---|---|
| `bash scripts/_self_check.sh adapter-framework`（PG 5433 + MinIO 9100） | **PASS=13 FAIL=0 SKIP=0** |
| `uv run ruff check apps/api packages/core` | All checks passed |
| `uv run mypy apps/api/dataplat_api packages/core/src` | Success: no issues found in 57 source files |
| `uv run pytest tests/test_commits.py tests/test_ingest.py` (apps/api) | 31 passed in 14.79s（跨 test 共存无污染） |
| `uv run pytest tests/` (packages/core) | 33 passed in 0.22s（IngestResult 加字段无回归） |
| `grep -rE "_visibility_visible" apps/api/dataplat_api/runner apps/api/dataplat_api/routers/ingest.py apps/api/dataplat_api/adapters` | exit=1（0 命中，反向 grep 修复落地） |
| `grep "asyncio.to_thread" apps/api/dataplat_api/runner/adapter_runner.py` | line 82 命中（非裸 await） |

## 7. 跨改动观察

- **复用模式延续**：本变更继承 commit-api-mvp 的"router 不重复实现 visibility，统一走 RepoService"约定；AC-9 反向 grep 是这条约定的**回归 fence**。良好。
- **harness lint 第 6 次教训反哺**：spec v2 + SKILL.md v2 + AC-9 修复三处闭环；session-handoff-20260517 应在 stage 10 close 时记录"反向 grep 沉默通过"已固化为 SKILL §跨 AC 自审清单第 6 条。
- **process_tasks 补齐**：tasks.md v2 新增 T-10~T-15 process 节点——这是 commit-api-mvp 后第 1 个完整覆盖 stage-2/4/6/7/9/10 的 change，质量门禁可被机械化校验。

## 8. Deferred 列表（SHOULD FIX / NICE TO HAVE 不阻塞 verdict）

| 项 | 跟踪位置 |
|---|---|
| S1 缩窄 raw_upload.py except 到 ValidationError | follow-up `adapter-error-narrow-*`（可与下个 adapter 落地时一起做） |
| S2 test bucket teardown 留痕 | follow-up `test-fixture-consolidation-*` |
| S3 ctx 升级 BoundLogger(run_id) | `rq-worker-skeleton-*` 含 |
| S4 `_resolve_repo` 抽公共 | `router-resolve-repo-helper-*`（下次 router 改动时开） |
| S5 lineage 由具体 adapter 自填 | 每个 adapter follow-up 内含 |
| N1 Protocol property vs dataclass | 风险 #7 监控；mypy 升级时回归 |
| N2 adapter 类型严格化 | 下个 adapter 实现时复核 |
| N3 关键节点 info 日志 | `telemetry-bootstrap-*` |
| N4 fixture 抽公共 | `test-fixture-consolidation-*` |

## 9. Verdict

**APPROVED**

- MUST FIX = **0**
- SHOULD FIX = 5（全部 deferred 到 follow-up，不阻塞）
- NICE TO HAVE = 4

13 / 13 AC 实测 PASS；spec v2 修复的 MUST FIX-1（parent 自动接链）+ MUST FIX-2（AC-9 反向 grep 沉默通过）两条均有正向断言 + 反向断言双重覆盖。改动范围与 spec / tasks 对齐，无 scope creep。

## 10. 复检指引（如需修 SHOULD FIX）

```bash
# 风格 / 类型
uv run ruff check apps/api packages/core
uv run mypy apps/api/dataplat_api packages/core/src

# 端到端
DATAPLAT_PG_PORT=5433 DATAPLAT_MINIO_PORT=9100 \
DATAPLAT_MINIO_ACCESS_KEY=dataplat DATAPLAT_MINIO_SECRET_KEY=dataplat-secret \
bash scripts/_self_check.sh adapter-framework

# 跨 test 共存
DATAPLAT_DATABASE_URL=postgresql+asyncpg://dataplat:dataplat@localhost:5433/dataplat \
DATAPLAT_JWT_SECRET=test-secret-not-prod-x32-bytes-xxxxx \
DATAPLAT_MINIO_ENDPOINT=http://localhost:9100 \
DATAPLAT_MINIO_ACCESS_KEY=dataplat DATAPLAT_MINIO_SECRET_KEY=dataplat-secret \
(cd apps/api && uv run pytest -q --tb=line tests/test_commits.py tests/test_ingest.py)
```

期望：所有 PASS；ruff All checks passed；mypy Success；self_check PASS=13 FAIL=0；pytest 31 passed。
