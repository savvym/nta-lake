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
from collections.abc import AsyncIterator

from dataplat_core.domain.lineage import Lineage
from dataplat_core.protocols.auth import AuthenticatedUser
from dataplat_core.protocols.storage import BlobStore
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Path,
    Request,
    status,
)
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from dataplat_api.auth.deps import get_optional_user, require_admin
from dataplat_api.db import get_session
from dataplat_api.models import CommitORM, RepositoryORM
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


@router.get(
    "/{owner}/{name}/tree/{commit_hash}",
    response_model=TreeRead,
)
async def get_tree(
    owner: str,
    name: str,
    commit_hash: str = Path(pattern=_SHA256_PATTERN),
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
