---
change_id: commit-api-mvp-20260517
version: 2
authored_at: 2026-05-17T09:45:00Z
revisions:
  - v1 → v2 (2026-05-17T09:45:00Z)：消化 stage 2 tasks reviewer 3 MUST FIX + 4 SHOULD FIX。
    T-2 depends_on 改 T-1；T-3 与 spec v2 created_at 一致（不入 hash）；T-6 测试数 ≥ 16；
    T-3 事务边界 explicit；T-4 复用现成 get_blob_store；T-4 request.stream 拆步；T-6 PG 探针；
    依赖图修正。
---

# Tasks

> 任务粒度 1-3 小时。每个任务都要标明 `depends_on` 与 `estimated_stage`。

## T-1 Pydantic schemas（blob + tree + commit）

- 新建 `apps/api/dataplat_api/schemas/blob.py`：`BlobUploadResponse(sha256: SHA256, size: int, storage_key: str, deduplicated: bool)`，`extra="forbid"`。
- 新建 `apps/api/dataplat_api/schemas/tree.py`：
  - `TreeEntryCreate(name: str, mode: int, entry_type: Literal["blob"]="blob", target_hash: SHA256)`
  - `TreeCreate(entries: list[TreeEntryCreate])`
  - `TreeEntryRead(name, mode, entry_type, target_hash)`
  - `TreeRead(hash: SHA256, entries: list[TreeEntryRead])`
  - 全 `extra="forbid"`。
- 新建 `apps/api/dataplat_api/schemas/commit.py`：
  - `CommitCreate(tree: TreeCreate, parents: list[SHA256]=[], author_id: str, message: str|None=None, lineage: Lineage|None=None, ref: str|None=None)` — **不含 `created_at`**（spec v2 AC-9 方案 B）
  - `CommitRead(hash, repo_id, tree_hash, parents, author_id, created_at: datetime, message, lineage, tree: TreeRead, deduplicated: bool)`
  - 全 `extra="forbid"`。
- `SHA256` 复用 `dataplat_core.domain.types.SHA256`。
- 更新 `schemas/__init__.py`：export 7 个新类型。
- depends_on: 无
- estimated_stage: stage-3
- AC 覆盖：AC-1

## T-2 BlobService（stream 转发 + 异常翻译）

- 新建 `apps/api/dataplat_api/services/blob.py`：
  - `BlobService.upload(store: BlobStore, stream: BinaryIO, declared_size: int|None=None) -> BlobUploadResponse`：调 `await store.put(stream, declared_size=...)` → 把 `BlobPutResult` 映射到 `BlobUploadResponse`（同名字段直拷）。
  - `BlobService.stream_get(store: BlobStore, sha256: str) -> AsyncIterator[bytes]`：直返 `store.get(sha256)`；调用方处理 KeyError → 404。
  - **不依赖 session / 不查 role**（spec v2 AC-2）。
- 更新 `services/__init__.py`：export `BlobService`。
- **depends_on: T-1**（import `BlobUploadResponse` 必须先有 T-1）
- estimated_stage: stage-3
- AC 覆盖：AC-2, AC-7

## T-3 CommitService（事务 + canonical hash + 幂等）

- 新建 `apps/api/dataplat_api/services/commit.py`，顶部 module docstring 写明 canonical JSON 规则（与 spec v2 AC-9 一字不差对齐）。
- **关键私有函数**：
  - `_canonical_tree_bytes(entries: list[TreeEntryCreate]) -> bytes`：entries `sorted(... , key=lambda e: e.name)` → 序列化 plain dict list → `json.dumps(..., sort_keys=True, ensure_ascii=False, separators=(",",":")).encode("utf-8")`
  - `_tree_hash(entries) -> str`：`sha256(_canonical_tree_bytes).hexdigest()`
  - `_lineage_to_canonical(lineage: Lineage | None) -> dict | None`：`lineage.model_dump(mode="json") if lineage else None`
  - `_canonical_commit_bytes(tree_hash, parents, author_id, message, lineage_canonical) -> bytes`：参数列表**不含 `created_at`**；`sorted(parents)` 升序；`json.dumps({"tree_hash":..., "parents":..., "author_id":..., "message":..., "lineage":...}, sort_keys=True, ensure_ascii=False, separators=(",",":")).encode("utf-8")`
  - `_commit_hash(...) -> str`：sha256 hexdigest
- **公共方法**：
  - `create_commit(session, store, repo_id, payload: CommitCreate) -> tuple[CommitORM, bool]`（bool=deduplicated）：
    - **步骤 1（事务外）**：`for h in {e.target_hash for e in payload.tree.entries}: if not await store.exists(h): missing.append(h)` → missing 非空 raise `HTTPException(400, detail={"missing_hashes": sorted(missing)})`
    - **步骤 2（事务外）**：算 `tree_hash` + `commit_hash`（**不含 created_at**）
    - **步骤 3（事务外）**：SELECT `CommitORM.where(repo_id, hash=commit_hash)` 命中 → eager load → 返 (existing, True)
    - **步骤 4（事务内 `async with session.begin()`）**：
      - upsert `TreeORM(hash=tree_hash, repo_id=repo_id)`（先 SELECT，无则 INSERT；忽略 race）
      - 对新 tree bulk insert `TreeEntryORM(...)`（sorted by name）
      - `INSERT CommitORM(hash, repo_id, tree_hash, parents, author_id, created_at=datetime.utcnow(), message, lineage_json)`
      - 若 `payload.ref`：upsert `RefORM(repo_id, name=payload.ref, commit_hash=commit_hash)`
    - **步骤 5（兜底 race）**：捕获 `IntegrityError` → `session.rollback()` → 重读 → 返 (existing, True)
  - `get_with_tree(session, repo_id, commit_hash) -> CommitORM | None`：`selectinload(CommitORM.tree).selectinload(TreeORM.entries)`
  - `get_tree_by_commit(session, repo_id, commit_hash) -> TreeORM | None`：commit → tree.hash → load
- 更新 `services/__init__.py`：export `CommitService`。
- depends_on: T-1
- estimated_stage: stage-3
- AC 覆盖：AC-3, AC-8, AC-9, AC-10

## T-4 commits Router（5 路由 + stream 上传）

- 新建 `apps/api/dataplat_api/routers/commits.py`：`APIRouter(prefix="/repos", tags=["commits"])`
- BlobStore DI：**复用** 既有 `apps/api/dataplat_api/storage/__init__.py::get_blob_store()`（cas-storage 已落地，无需新建）。
- 5 路由：
  1. **`POST /{owner}/{name}/blobs`**：`Depends(require_admin)` + `Depends(get_blob_store)` + `Depends(get_session)`
     - 校 repo 存在（`RepoService.get_by_owner_name(session, owner, name, admin)` → None 时 404）
     - **大文件流式拆步**（spec 风险 #2）：
       ```python
       tmp = SpooledTemporaryFile(max_size=1<<20)
       async for chunk in request.stream():
           tmp.write(chunk)
       tmp.seek(0)
       declared = request.headers.get("content-length")
       resp = await BlobService.upload(store, tmp, declared_size=int(declared) if declared else None)
       ```
     - 返 201 + `BlobUploadResponse`
  2. **`GET /{owner}/{name}/blobs/{sha256}`**：`Depends(get_optional_user)` + visibility 校验（404 不区分）+ Pydantic `Path(pattern=r"^[0-9a-f]{64}$")` → `BlobService.stream_get(store, sha256)` 包成 `StreamingResponse(media_type="application/octet-stream")`；KeyError → 404
  3. **`POST /{owner}/{name}/commits`**：`Depends(require_admin)` + 校 repo 存在 → `CommitService.create_commit(session, store, repo.id, payload)` → 200 + `CommitRead(deduplicated=bool)`（注意：deduplicated 字段反映 service 返回的 bool）
  4. **`GET /{owner}/{name}/commits/{hash}`**：`Depends(get_optional_user)` + visibility → `CommitService.get_with_tree` → None 时 404，否则 200 + `CommitRead(deduplicated=False)`
  5. **`GET /{owner}/{name}/tree/{commit_hash}`**：`Depends(get_optional_user)` + visibility → `CommitService.get_tree_by_commit` → None 时 404，否则 200 + `TreeRead`
- **复用约束**（spec v2 AC-6）：路由不自己写 `_visibility_visible`；所有 visibility 决策走 `RepoService.get_by_owner_name(...)`。
- 更新 `main.py` `include_router(commits_router)`（router 自带 prefix）。
- depends_on: T-1, T-2, T-3
- estimated_stage: stage-3
- AC 覆盖：AC-4, AC-5, AC-6

## T-5 OpenAPI codegen

- `make codegen` → 同步 `packages/api-types/openapi.json`。
- 验证 5 新 paths 在 spec 里 + 含 sha256 path-param pattern（`^[0-9a-f]{64}$`）。
- depends_on: T-4
- estimated_stage: stage-3
- AC 覆盖：AC-5

## T-6 集成测试 + 单元测试 ≥ 16

- 新建 `apps/api/tests/test_commits.py`：
  - **PG 探针 + MinIO 探针**：`pytestmark = pytest.mark.skipif(not (DATAPLAT_DATABASE_URL and DATAPLAT_MINIO_ENDPOINT))`（spec v2 AC-13；与 cas-storage / repo-api-mvp 一致）。
  - Fixtures：`admin_user` / `normal_user`（fresh engine + 直插 UserORM + teardown 删）+ `public_repo(admin_user)` / `private_repo(admin_user)` / `internal_repo(admin_user)`（POST /repos 建好；teardown 通过 DELETE 接口或直接 DELETE FROM）。
  - **测试列表**（16 个，对应 spec v2 AC-11 a~q）：
    - (a) `test_a_admin_post_blob_200_sha256_correct`
    - (b) `test_b_admin_dedup_returns_true`
    - (c) `test_c_user_post_blob_403`
    - (d) `test_d_admin_post_commit_with_one_entry`
    - (e) `test_e_post_commit_missing_blob_returns_400`
    - (f) `test_f_post_commit_with_ref_upserts`
    - (g1) `test_g1_canonical_hash_is_deterministic`（**单元，不依赖 PG/MinIO**：直接 import `CommitService._canonical_tree_bytes` / `_commit_hash`，断言 entries / parents 排序不变性）
    - (g2) `test_g2_idempotent_repeat_post_dedup_true`
    - (h) `test_h_get_commit_includes_tree_entries`
    - (i) `test_i_get_commit_unknown_hash_404`
    - (j) `test_j_get_blob_streams_correct_bytes`
    - (k) `test_k_get_blob_unknown_404`
    - (l) `test_l_anonymous_private_repo_returns_404`
    - (m) `test_m_anonymous_public_repo_blob_200`
    - (n) `test_n_2mb_streaming_roundtrip`
    - (o) `test_o_lineage_roundtrip`
    - (p) `test_p_user_get_internal_commit_200`
    - (q) `test_q_user_get_private_commit_404`
- depends_on: T-1~T-5
- estimated_stage: stage-3
- AC 覆盖：AC-11

## T-7 self_check commit-api-mvp block

- `scripts/_self_check.sh` 追加 `run_commit_api_mvp` 函数（13 AC，每个对应 spec v2 验证命令）+ filter `commit-api-mvp`（与现有 cas-storage / repo-api-mvp 风格一致，单短名）。
- AC-11 走 PG + MinIO 双探针；任一不可达 SKIP。
- 主 case 块追加 `run_commit_api_mvp`。
- depends_on: T-1~T-6
- estimated_stage: stage-3
- AC 覆盖：AC-13

## T-8（process）反哺 cross-AC consistency check

- 把"schema 字段 ↔ canonical hash 输入 ↔ idempotency key ↔ test fixture 四链路必须一致"反哺到 `.harness/skills/request-analysis/SKILL.md` checklist。
- 关联 [[project-followup-harness-lint]] 演化窗口（第 6 次触发点）。
- depends_on: 无（独立流程改进）
- estimated_stage: stage-10（close 时统一做）
- AC 覆盖：流程改进，无 AC 直接覆盖

## 任务依赖图

```
T-1 (schemas) ─┬──→ T-2 (BlobService) ─┐
               └──→ T-3 (CommitService) ─┼──→ T-4 (router) ──→ T-5 (codegen) ──→ T-6 (tests) ──→ T-7 (self_check)
                                          
T-8 (反哺) — 独立 process task
```

T-2 / T-3 都依赖 T-1（schema 接口）；T-4 依赖 T-1+T-2+T-3；后续串行。
