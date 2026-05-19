"""Commit / Blob / Tree HTTP 路由（spec commit-api-mvp-20260517 AC-4/5/6）。

Prefix 钉死：`APIRouter(prefix="/repos")` + main `include_router(router)` 不再加 prefix
（与 repo-api-mvp / auth-scaffold 规则一致）。

Auth + visibility 矩阵：
- POST blob / POST commit：`Depends(require_admin)` + repo 存在性校验
- GET blob / commit / tree：`Depends(get_optional_user)` + `RepoService.get_by_owner_name`
  做 visibility 过滤（404 不区分"不存在 vs 不可见"避免存在性泄露）
"""

from __future__ import annotations

import tempfile
import uuid
from collections.abc import AsyncIterator

from dataplat_core.domain.lineage import Lineage
from dataplat_core.protocols.auth import AuthenticatedUser
from dataplat_core.protocols.storage import BlobStore
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Path,
    Query,
    Request,
    status,
)
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from dataplat_api.auth.deps import get_optional_user, require_admin
from dataplat_api.db import get_session
from dataplat_api.models import CommitORM, RepositoryORM, TreeEntryORM, TreeORM
from dataplat_api.schemas.blob import BlobMetaResponse, BlobUploadResponse
from dataplat_api.schemas.commit import CommitCreate, CommitRead
from dataplat_api.schemas.tree import TreeEntryRead, TreeRead
from dataplat_api.services.blob import BlobService
from dataplat_api.services.commit import CommitService
from dataplat_api.services.repo import RepoService
from dataplat_api.storage import get_blob_store

router = APIRouter(prefix="/repos", tags=["commits"])

_SHA256_PATTERN = r"^[0-9a-f]{64}$"


async def _resolve_repo(
    session: AsyncSession,
    owner: str,
    name: str,
    current_user: AuthenticatedUser | None,
) -> RepositoryORM:
    """visibility-aware lookup；不可见 / 不存在 → 404 统一。"""
    repo = await RepoService.get_by_owner_name(session, owner, name, current_user)
    if repo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository {owner}/{name} 不存在",
        )
    return repo


def _commit_to_read(commit: CommitORM, deduplicated: bool) -> CommitRead:
    tree_entries = [
        TreeEntryRead(
            name=e.name,
            mode=e.mode,
            entry_type=e.entry_type,  # type: ignore[arg-type]
            target_hash=e.target_hash,
        )
        for e in sorted(commit.tree.entries, key=lambda x: x.position)
    ]
    lineage = (
        Lineage.model_validate(commit.lineage_json)
        if commit.lineage_json is not None
        else None
    )
    return CommitRead(
        hash=commit.hash,
        repo_id=str(commit.repo_id),
        tree_hash=commit.tree_hash,
        parents=list(commit.parents),
        author_id=commit.author_id,
        created_at=commit.created_at,
        message=commit.message,
        lineage=lineage,
        tree=TreeRead(hash=commit.tree_hash, entries=tree_entries),
        deduplicated=deduplicated,
    )


@router.post(
    "/{owner}/{name}/blobs",
    response_model=BlobUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_blob(
    owner: str,
    name: str,
    request: Request,
    _admin: AuthenticatedUser = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
    store: BlobStore = Depends(get_blob_store),
) -> BlobUploadResponse:
    await _resolve_repo(session, owner, name, _admin)
    # spec 风险 #2：流式上传到磁盘 SpooledTemporaryFile，不全量读到内存
    tmp = tempfile.SpooledTemporaryFile(max_size=1 << 20)
    try:
        async for chunk in request.stream():
            tmp.write(chunk)
        tmp.seek(0)
        cl = request.headers.get("content-length")
        declared = int(cl) if cl and cl.isdigit() else None
        return await BlobService.upload(store, tmp, declared_size=declared)  # type: ignore[arg-type]
    finally:
        tmp.close()


@router.get("/{owner}/{name}/blobs/{sha256}")
async def download_blob(
    owner: str,
    name: str,
    sha256: str = Path(pattern=_SHA256_PATTERN),
    current_user: AuthenticatedUser | None = Depends(get_optional_user),
    session: AsyncSession = Depends(get_session),
    store: BlobStore = Depends(get_blob_store),
) -> StreamingResponse:
    await _resolve_repo(session, owner, name, current_user)
    iterator = BlobService.stream_get(store, sha256)

    # 先 peek 第一个 chunk：cas-storage 约定 KeyError 在首次 __anext__ 抛出（不存在）
    try:
        first = await iterator.__anext__()
    except StopAsyncIteration:
        first = b""
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Blob {sha256} 不存在",
        ) from exc

    async def _streaming() -> AsyncIterator[bytes]:
        if first:
            yield first
        async for chunk in iterator:
            yield chunk

    return StreamingResponse(_streaming(), media_type="application/octet-stream")


@router.get(
    "/{owner}/{name}/blobs/{sha256}/meta",
    response_model=BlobMetaResponse,
)
async def get_blob_meta(
    owner: str,
    name: str,
    sha256: str = Path(pattern=_SHA256_PATTERN),
    current_user: AuthenticatedUser | None = Depends(get_optional_user),
    session: AsyncSession = Depends(get_session),
    store: BlobStore = Depends(get_blob_store),
) -> BlobMetaResponse:
    await _resolve_repo(session, owner, name, current_user)
    size = await store.get_size(sha256)
    if size is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Blob {sha256} 不存在",
        )
    return BlobMetaResponse(sha256=sha256, size=size)


@router.post(
    "/{owner}/{name}/commits",
    response_model=CommitRead,
)
async def create_commit(
    owner: str,
    name: str,
    payload: CommitCreate,
    _admin: AuthenticatedUser = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
    store: BlobStore = Depends(get_blob_store),
) -> CommitRead:
    repo = await _resolve_repo(session, owner, name, _admin)
    commit, dedup = await CommitService.create_commit(session, store, repo.id, payload)
    return _commit_to_read(commit, dedup)


@router.get(
    "/{owner}/{name}/commits/{hash}",
    response_model=CommitRead,
)
async def get_commit(
    owner: str,
    name: str,
    hash: str = Path(pattern=_SHA256_PATTERN),
    current_user: AuthenticatedUser | None = Depends(get_optional_user),
    session: AsyncSession = Depends(get_session),
) -> CommitRead:
    repo = await _resolve_repo(session, owner, name, current_user)
    commit = await CommitService.get_with_tree(session, repo.id, hash)
    if commit is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Commit {hash} 在 {owner}/{name} 不存在",
        )
    return _commit_to_read(commit, deduplicated=False)


async def _load_subtree_entries(
    session: AsyncSession,
    repo_id: uuid.UUID,
    tree_hash: str,
) -> list[TreeEntryORM] | None:
    """按 (tree_hash, repo_id) 取该层 entries（含子 tree entry）；不存在 → None。"""
    from sqlalchemy import select  # local import 减少 module-level deps

    tree_stmt = (
        select(TreeORM)
        .where(TreeORM.hash == tree_hash, TreeORM.repo_id == repo_id)
        .options(selectinload(TreeORM.entries))
    )
    tree = (await session.execute(tree_stmt)).scalar_one_or_none()
    if tree is None:
        return None
    return sorted(tree.entries, key=lambda x: x.position)


_MAX_TREE_RECURSION_DEPTH = 64


async def _expand_tree_recursive(
    session: AsyncSession,
    repo_id: uuid.UUID,
    root_tree_hash: str,
) -> list[TreeEntryRead]:
    """BFS 批量展开嵌套 tree → leaf blob entry 列表（name 为扁平全路径）。

    O(depth) 查询而非 O(tree_count)：每层用 `WHERE hash IN (...)` 一次批量取所有 subtree。
    递归深度上限 _MAX_TREE_RECURSION_DEPTH（防恶意 / 异常的深嵌套耗 DB）。
    """
    from sqlalchemy import select

    out: list[TreeEntryRead] = []
    # 待处理：(tree_hash, prefix_for_children) 列表，按层批量取
    pending: list[tuple[str, str]] = [(root_tree_hash, "")]
    depth = 0
    while pending:
        if depth >= _MAX_TREE_RECURSION_DEPTH:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"tree 嵌套深度 > {_MAX_TREE_RECURSION_DEPTH}，拒绝展开",
            )
        hashes_this_layer = [h for h, _ in pending]
        prefix_map: dict[str, list[str]] = {}
        for h, p in pending:
            prefix_map.setdefault(h, []).append(p)
        # 单次 batch SELECT 取本层所有 tree
        stmt = (
            select(TreeORM)
            .where(
                TreeORM.repo_id == repo_id,
                TreeORM.hash.in_(hashes_this_layer),
            )
            .options(selectinload(TreeORM.entries))
        )
        trees = (await session.execute(stmt)).scalars().all()
        tree_by_hash = {t.hash: t for t in trees}
        next_pending: list[tuple[str, str]] = []
        for h in hashes_this_layer:
            tree = tree_by_hash.get(h)
            if tree is None:
                continue
            sorted_entries = sorted(tree.entries, key=lambda x: x.position)
            # 该 hash 可能对应多个 prefix（同子树被多处引用，理论上极少）
            for prefix in prefix_map[h]:
                for e in sorted_entries:
                    full_name = f"{prefix}{e.name}" if prefix else e.name
                    if e.entry_type == "tree":
                        next_pending.append((e.target_hash, f"{full_name}/"))
                    else:
                        out.append(
                            TreeEntryRead(
                                name=full_name,
                                mode=e.mode,
                                entry_type=e.entry_type,  # type: ignore[arg-type]
                                target_hash=e.target_hash,
                            )
                        )
        pending = next_pending
        depth += 1
    return out


@router.get(
    "/{owner}/{name}/tree/{commit_hash}",
    response_model=TreeRead,
)
async def get_tree(
    owner: str,
    name: str,
    commit_hash: str = Path(pattern=_SHA256_PATTERN),
    recursive: bool = Query(False, description="True: 递归展开所有 type=tree entry 为 leaf blob 列表"),
    current_user: AuthenticatedUser | None = Depends(get_optional_user),
    session: AsyncSession = Depends(get_session),
) -> TreeRead:
    repo = await _resolve_repo(session, owner, name, current_user)
    tree = await CommitService.get_tree_by_commit(session, repo.id, commit_hash)
    if tree is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tree for commit {commit_hash} 在 {owner}/{name} 不存在",
        )
    if recursive:
        entries = await _expand_tree_recursive(session, repo.id, tree.hash)
    else:
        entries = [
            TreeEntryRead(
                name=e.name,
                mode=e.mode,
                entry_type=e.entry_type,  # type: ignore[arg-type]
                target_hash=e.target_hash,
            )
            for e in sorted(tree.entries, key=lambda x: x.position)
        ]
    return TreeRead(hash=tree.hash, entries=entries)


@router.get(
    "/{owner}/{name}/trees/{tree_hash}",
    response_model=TreeRead,
)
async def get_subtree_by_hash(
    owner: str,
    name: str,
    tree_hash: str = Path(pattern=_SHA256_PATTERN),
    current_user: AuthenticatedUser | None = Depends(get_optional_user),
    session: AsyncSession = Depends(get_session),
) -> TreeRead:
    """按任意 tree hash（root 或 subtree）取该层 entries。

    跨 repo 不暴露：即便 hash 相同，请求 repo 与 owner 不匹配 → 404。
    """
    repo = await _resolve_repo(session, owner, name, current_user)
    entries_orm = await _load_subtree_entries(session, repo.id, tree_hash)
    if entries_orm is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tree {tree_hash} 在 {owner}/{name} 不存在",
        )
    entries = [
        TreeEntryRead(
            name=e.name,
            mode=e.mode,
            entry_type=e.entry_type,  # type: ignore[arg-type]
            target_hash=e.target_hash,
        )
        for e in entries_orm
    ]
    return TreeRead(hash=tree_hash, entries=entries)
