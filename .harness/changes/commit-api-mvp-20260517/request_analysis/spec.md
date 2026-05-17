---
change_id: commit-api-mvp-20260517
version: 2
authored_at: 2026-05-17T09:45:00Z
status: draft
revisions:
  - v1 → v2 (2026-05-17T09:45:00Z)：消化 stage 2 reviewer 7 MUST FIX + 4 SHOULD FIX。
    关键修复：created_at 从 commit canonical hash **去除**（方案 B，与 CAS "同内容同 hash" 语义一致）；
    AC-1~AC-13 全部追加一行式验证命令；AC-11 测试矩阵从 13 增到 16 （含 hash 单元 + 2MB + lineage round-trip + user×internal/private commit visibility）；
    AC-8 + 风险 #3 统一为"blob 存在性校验在事务前"；AC-9 lineage canonical 钉死 `model_dump(mode="json")` + sort_keys 递归；
    race 测试显式 deferred 到 follow-up。
---

# Spec：Commit / Blob / Tree 写读 HTTP 路由（MVP）

## 背景

repo-api-mvp-20260517 已落地 Repository CRUD，但还没有任何路由能把内容（文件）实际推进去或读出来——Adapter 框架（design.md §9 Phase 1 #2）的写入侧因此被堵住。design.md §4.4 的 6 个 CAS 路由必须先落最小子集。

## 问题陈述

当前 dataplat：
- 有 `BlobStore` Protocol + `MinioBlobStore`（cas-storage），但没有 HTTP 入口让客户端 PUT/GET blob
- 有 `CommitORM` / `TreeORM` / `TreeEntryORM` / `RefORM` 模型 + alembic 迁移（core-domain-model），但没有路由让客户端创建/查询 commit
- 上游 SourceAdapter / Processor（Protocol 已定义，无实现）需要这些路由当出口

## 范围

In scope：

- `POST /repos/{owner}/{name}/blobs` — 单文件流式上传到 CAS，返回 `{sha256, size, storage_key, deduplicated}`
- `GET /repos/{owner}/{name}/blobs/{sha256}` — 流式下载（StreamingResponse）
- `POST /repos/{owner}/{name}/commits` — 创建 commit，body 含 `tree.entries[]`（引用已上传 blob sha256）+ `parents[]` + `author_id` + `message?` + `lineage?` + `ref?`
- `GET /repos/{owner}/{name}/commits/{hash}` — 返回 commit metadata + 完整 tree（含 entries）
- `GET /repos/{owner}/{name}/tree/{commit_hash}` — 返回 commit 对应 tree 的 entries
- 集成测试 ≥ 16 + self_check 13 AC

Out of scope（明确推后到 follow-up）：

- 批量上传 / multipart tar（client 端可循环单文件）
- Ref CRUD（除 commit POST 时 upsert）：留 `ref-api-mvp-*`
- Path 级 tree 浏览（`/tree/{ref}/{path}`）：留 `tree-path-browse-*`
- Lineage 图查询（`/lineage/graph`）：留 `lineage-query-graph-*`
- Sub-tree（嵌套目录）：MVP tree 仅单层 entries=blob；嵌套留 `tree-nested-*`
- Tag / signed commit：推后
- Resumable / chunked upload：推后；MVP 单 PUT 完成
- 上传配额 / 总大小限制：留 `quota-management-*`
- **并发 race 单测**：commit_hash 唯一约束 race 路径用 IntegrityError catch 实现，但 MVP 不写并发单测覆盖（pytest-asyncio + asyncpg 跨协程开销大）；留 follow-up `commit-race-load-test-*` 用 locust/k6 覆盖

## 验收标准（16 AC + 验证方式）

### 结构 / 接口（AC-1 ~ AC-5）

- **AC-1**：3 个 schema 文件齐全 + 字段定义。
  - 文件：`apps/api/dataplat_api/schemas/blob.py` + `schemas/tree.py` + `schemas/commit.py`
  - 类型：
    - `BlobUploadResponse(sha256: SHA256, size: int, storage_key: str, deduplicated: bool)`
    - `TreeEntryCreate(name: str, mode: int, entry_type: Literal["blob"]="blob", target_hash: SHA256)`
    - `TreeCreate(entries: list[TreeEntryCreate])`
    - `TreeEntryRead`（同 Create 字段）
    - `TreeRead(hash: SHA256, entries: list[TreeEntryRead])`
    - `CommitCreate(tree: TreeCreate, parents: list[SHA256]=[], author_id: str, message: str|None=None, lineage: Lineage|None=None, ref: str|None=None)`
    - `CommitRead(hash: SHA256, repo_id: str, tree_hash: SHA256, parents: list[SHA256], author_id: str, created_at: datetime, message: str|None, lineage: Lineage|None, tree: TreeRead, deduplicated: bool)`
  - 全 `extra="forbid"`；SHA256 = `Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]`（已在 `dataplat_core.domain.types` 定义）。
  - **注**：`CommitCreate` **不含 `created_at`**——服务端记录 created_at（`datetime.utcnow()`）但**不参与 commit canonical hash**（见 AC-9）。
  - **验证命令**：`cd apps/api && uv run python -c "from dataplat_api.schemas.blob import BlobUploadResponse; from dataplat_api.schemas.tree import TreeEntryCreate, TreeCreate, TreeEntryRead, TreeRead; from dataplat_api.schemas.commit import CommitCreate, CommitRead; from pydantic import ValidationError; assert 'created_at' not in CommitCreate.model_fields; assert CommitCreate.model_config.get('extra')=='forbid'"`

- **AC-2**：`BlobService` 仅 stream 转发 + 异常翻译。
  - `apps/api/dataplat_api/services/blob.py`：`BlobService.upload(store, stream, declared_size=None) -> BlobUploadResponse` + `BlobService.stream_get(store, sha256) -> AsyncIterator[bytes]`。
  - BlobService **不查 repo / 不查 role**——所有 repo 权限校验在 router。
  - **验证命令**：`cd apps/api && uv run python -c "from dataplat_api.services.blob import BlobService; import inspect; assert inspect.iscoroutinefunction(BlobService.upload); src=inspect.getsource(BlobService); assert 'AsyncSession' not in src and 'role' not in src"`

- **AC-3**：`CommitService` 含事务 + canonical hash + 幂等。
  - 公共 API：`create_commit(session, store, repo_id, payload) -> tuple[CommitORM, bool]`、`get_with_tree(session, repo_id, commit_hash) -> CommitORM|None`、`get_tree_by_commit(session, repo_id, commit_hash) -> TreeORM|None`。
  - 私有：`_canonical_tree_bytes` / `_tree_hash` / `_canonical_commit_bytes` / `_commit_hash` / `_lineage_to_canonical`。
  - **验证命令**：`cd apps/api && uv run python -c "from dataplat_api.services.commit import CommitService; import inspect; for m in ['create_commit','get_with_tree','get_tree_by_commit']: assert hasattr(CommitService, m), m; for h in ['_canonical_tree_bytes','_tree_hash','_canonical_commit_bytes','_commit_hash']: assert hasattr(CommitService, h), h"`

- **AC-4**：5 路由 + prefix 钉死。
  - `apps/api/dataplat_api/routers/commits.py`：`APIRouter(prefix='/repos', tags=['commits'])`。
  - 5 路由：`POST /{owner}/{name}/blobs`（admin）、`GET /{owner}/{name}/blobs/{sha256}`（visibility-aware）、`POST /{owner}/{name}/commits`（admin）、`GET /{owner}/{name}/commits/{hash}`（visibility-aware）、`GET /{owner}/{name}/tree/{commit_hash}`（visibility-aware）。
  - **验证命令**：`cd apps/api && uv run python -c "from dataplat_api.routers.commits import router; paths={r.path for r in router.routes}; need={'/repos/{owner}/{name}/blobs','/repos/{owner}/{name}/blobs/{sha256}','/repos/{owner}/{name}/commits','/repos/{owner}/{name}/commits/{hash}','/repos/{owner}/{name}/tree/{commit_hash}'}; assert need <= paths, paths"`

- **AC-5**：`main.py` include + OpenAPI 含 5 paths。
  - **验证命令**：`cd apps/api && uv run python -c "from dataplat_api.main import app; s=app.openapi(); need={'/repos/{owner}/{name}/blobs','/repos/{owner}/{name}/blobs/{sha256}','/repos/{owner}/{name}/commits','/repos/{owner}/{name}/commits/{hash}','/repos/{owner}/{name}/tree/{commit_hash}'}; assert need <= set(s['paths'].keys()), set(s['paths'].keys())"` + `make codegen` 后 `packages/api-types/openapi.json` 同步。

### 行为 / 安全（AC-6 ~ AC-10）

- **AC-6**：**Repo visibility 矩阵复用 repo-api-mvp 的 `RepoService.get_by_owner_name` + `_visibility_visible`**。
  - 读路由（GET blob/commit/tree）：repo 不可见或不存在 → 404 不区分。
  - 写路由（POST blob/commit）：先 `Depends(require_admin)`（非 admin → 403 早返）；admin 看 repo 不存在 → 404；不存在 case 不会到达 visibility 检查层。
  - 复用断言：路由实现 import `from dataplat_api.services.repo import RepoService` 且不自己写 `_visibility_visible` 副本。
  - **验证命令**：`grep -lE "_visibility_visible" apps/api/dataplat_api/services/commit.py apps/api/dataplat_api/services/blob.py apps/api/dataplat_api/routers/commits.py | wc -l` 期望 `0`（不重复实现）。

- **AC-7**：**Blob 完整性**。
  - `POST blobs` 调 cas-storage 6 步算法；响应 `sha256` 是服务端真实算的（不信任 client header）；`deduplicated` 反映 dedup。
  - 由 AC-11 (a)(b) 集成测试覆盖。

- **AC-8**：**Commit 事务一致性 + blob 存在性校验位置**（与 风险 #3 完全一致）。
  - `POST commits` 用 `async with session.begin()` 单事务包裹 tree + tree_entries + commit + ref 的 DB 写。
  - **Blob 存在性校验在事务前**完成（异步 `store.exists()` 串行调用），缺失 → 400 含 `missing_hashes: [...]`。
  - MVP **接受**「校验后/事务内 race 期间 blob 被删」作为非目标——cas-storage 当前无 GC 路径，blob 删除路径仅 admin 手动调用（design.md §10 #3 待讨论）。
  - 由 AC-11 (d)(e) 集成测试覆盖。

- **AC-9**：**Hash 确定性（canonical JSON 规则）**。
  - `_canonical_tree_bytes(entries)`：
    1. entries 按 `name` **升序**
    2. 每个 entry → `{"name": str, "mode": int, "entry_type": "blob", "target_hash": str}`（plain dict，无 Pydantic）
    3. `json.dumps([...], sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")`
  - `_tree_hash = sha256(canonical_bytes).hexdigest()`。
  - `_canonical_commit_bytes(tree_hash, parents, author_id, message, lineage_canonical)`：
    1. parents 列表 `sorted(parents)` 升序
    2. lineage_canonical = `Lineage.model_dump(mode="json")` 得到的 plain dict（Pydantic 已把 datetime/UUID 转 ISO string；嵌套全为 plain dict/list/scalar）or `None`
    3. `json.dumps({"tree_hash": str, "parents": sorted_list, "author_id": str, "message": str|None, "lineage": lineage_canonical}, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")`
  - **`created_at` 不参与 commit canonical hash**（方案 B；与 CAS"同内容同 hash"语义一致；created_at 由服务端记录用于 audit）。
  - `_commit_hash = sha256(canonical_bytes).hexdigest()`。
  - Lineage canonical 不变量：`Lineage.model_dump(mode="json")` 必须返回 plain JSON-native dict，不允许 lineage 内嵌任何 datetime / UUID / 自定义对象（mode="json" 已保证）。
  - 客户端**不传 hash**；服务端算并返回。
  - 由 AC-11 (g1)(g2) 单元测试覆盖（hash 函数本身）+ (h) 端到端覆盖。

- **AC-10**：**幂等**。
  - 同样 entries + 同样 commit metadata（author_id + message + parents + lineage；**不含 created_at**）→ 同样 commit_hash → 服务端不另插，返 `CommitRead{..., deduplicated=true}`。
  - 实现路径：(1) 算完 commit_hash → SELECT 命中 → 返 (existing, True)；(2) 否则事务 INSERT → IntegrityError race → catch + rollback + 重读 → 返 (existing, True)。
  - 由 AC-11 (g2) 顺序 dedup 端到端覆盖；race 路径用 IntegrityError catch 实现但**单测覆盖 deferred** 到 follow-up `commit-race-load-test-*`。

### 测试 / 质量 / 工具（AC-11 ~ AC-13）

- **AC-11**：`apps/api/tests/test_commits.py` 含 **≥ 16 测试**：
  - (a) admin POST blob 200 + sha256 与本地 hashlib 一致
  - (b) admin 重复 POST 相同字节 → deduplicated=true
  - (c) 非 admin POST blob → 403
  - (d) admin POST commit 1 entry → 200 + 服务端 hash 算出
  - (e) POST commit 引用不存在 blob → 400 含 `missing_hashes`
  - (f) POST commit 含 ref → ref upsert
  - (g1) **单元测试**：`CommitService._canonical_tree_bytes(unordered) == _canonical_tree_bytes(sorted)` + `_commit_hash(t, [p1, p2], ...) == _commit_hash(t, [p2, p1], ...)`（不需 DB / 不需 MinIO）
  - (g2) 顺序幂等：相同 payload 二次 POST → 200 + deduplicated=true
  - (h) GET commit by hash → 含 tree.entries
  - (i) GET commit by 不存在 hash → 404
  - (j) GET blob by sha256 → 流式字节正确
  - (k) GET blob 不存在 → 404
  - (l) 匿名 GET blob/commit/tree on private repo → 404
  - (m) anonymous GET public repo blob → 200
  - (n) **大文件流式**：admin POST 2MB+17 字节随机内容 → 200 + sha256 与本地 hashlib.sha256 一致；GET 同 sha256 → 流式字节完全相等
  - (o) **lineage round-trip**：POST commit 含 `Lineage(produced_by=ProducedBy(kind='processor', name='x', version='0.1', config_hash='c'*64), inputs=[InputRef(repo='r', commit='a'*64)], run_id='r1', env={'k':'v'})` → 200；GET 同 hash → lineage 字段反序列化为完整 Lineage 模型，produced_by.kind / inputs[0].repo / inputs[0].commit 字段全在
  - (p) user GET commit on internal repo → 200
  - (q) user GET commit on private repo → 404

- **AC-12**：`uv run ruff check apps/api packages/core` + `uv run mypy apps/api/dataplat_api packages/core/src` 全 PASS。
  - **验证命令**：`uv run ruff check apps/api packages/core && uv run mypy apps/api/dataplat_api packages/core/src`

- **AC-13**：`scripts/_self_check.sh commit-api-mvp` 13 AC 全 PASS（PG + MinIO 双探针；任一不可达 SKIP；与 cas-storage / repo-api-mvp 风格一致）。
  - **验证命令**：`DATAPLAT_PG_PORT=5433 DATAPLAT_MINIO_ENDPOINT=http://localhost:9000 bash scripts/_self_check.sh commit-api-mvp` → `PASS=13 FAIL=0`。

## 风险

1. **commit hash 序列化规范不严格**：dict 顺序 / Python 版本差异破坏幂等。**缓解**：AC-9 显式 canonical 规则 + AC-11 (g1) 单元回归。
2. **大文件上传内存爆炸**：FastAPI 默认 `UploadFile.read()` 全量到内存。**缓解**：用 `Request.stream()` async iterator + `tempfile.SpooledTemporaryFile(max_size=1<<20)` + 把 `tmp.seek(0)` 后传 `BlobService.upload`；AC-11 (n) 2MB 测试覆盖。
3. **事务里调异步 `store.exists()` 阻塞 SQL session**：AC-8 已规定 **blob 存在性校验在事务前**；事务内只做 DB 写。
4. **commit_hash 唯一约束 race**：并发相同 payload → IntegrityError → catch + rollback + 重读返 deduplicated=true。MVP 单测不覆盖 race 路径（deferred）；顺序 dedup AC-11 (g2) 覆盖。
5. **lineage round-trip**：commit.lineage 是 JSONB；POST Pydantic Lineage → JSON 存；GET 时反序列化回 Lineage。AC-11 (o) 覆盖。
6. **visibility 实时检查 vs 大 GET blob 开销**：每次 GET 多一次 SQL；MVP 接受；follow-up 可加 cache。

## 关键决策

| 决策 | 选项 | 选择 | 理由 |
|---|---|---|---|
| Blob 上传协议 | (a) multipart form (b) raw body (c) UploadFile | **(b) raw body** | 流式最干净；client 不需要 form 边界 |
| Tree 嵌套 | (a) MVP 仅单层 (b) 支持 nested | **(a)** | 隔离复杂度 |
| Hash 客户端 vs 服务端 | (a) 服务端算 (b) 客户端预算 server 校验 | **(a)** | §4.4 信任边界 |
| **created_at 是否参与 commit hash** | (A) 加入 CommitCreate schema client 控 (B) 完全去除 | **(B)** | "同内容同 hash" 的 CAS 语义；created_at 是 audit 字段非身份字段 |
| 幂等策略 | 唯一约束 + SELECT 主路径 + IntegrityError catch 兜底 | **采用** | 并发友好 |
| 事务粒度 | 单事务 tree+commit+ref | **采用** | §4.4 commit 原子性 |
| Blob 存在性校验位置 | (a) 事务内 (b) 事务前 | **(b)** | 避免事务内异步 IO 阻塞 |
| Ref upsert 语义 | POST commit 时若提供 ref，强制 upsert | **采用** | "推 main"语义 |
| Ref 名格式约束 | (a) 严 git ref 语法 (b) MVP 接受非空 ≤ 255 字符串 | **(b)** | 推后到 `ref-api-mvp-*` 收紧 |
| sha256 path 校验 | Pydantic Field pattern 64-hex | **采用** | 拒非法路径早 fail |
| canonical JSON | `sort_keys=True ensure_ascii=False separators=(",",":")` + entries/parents 升序 + lineage 用 `model_dump(mode="json")` | **采用** | 跨版本确定性 |
| race 单测 | (a) pytest-asyncio gather (b) deferred 到 load test | **(b)** | pytest-asyncio + asyncpg 跨协程开销大；顺序 dedup 已覆盖核心；race 路径仅靠 catch 实现 |

## 流程偏离声明

无功能性偏离。**反哺机会**：本次 spec generator 跨 AC consistency 检查不充分（v1 created_at 矛盾、AC-8 与 风险 #3 矛盾），将作为 follow-up `harness-tighten-cross-ac-consistency-*` 反哺到 `.harness/skills/request-analysis/SKILL.md`——增加 checklist「schema 字段 ↔ canonical hash 输入 ↔ idempotency key ↔ test fixture 四链路必须一致」。
