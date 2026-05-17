"""Adapter ingest HTTP 路由（spec adapter-framework-20260517 AC-7 / AC-8 / AC-9）。

Prefix 钉死：`APIRouter(prefix="/repos")` + main `include_router(router)` 不再加 prefix
（与 commits / repos 一致）。

`POST /{owner}/{name}/ingest`：admin only + repo visibility 复用 RepoService。
"""

from __future__ import annotations

from dataplat_core.protocols.auth import AuthenticatedUser
from dataplat_core.protocols.storage import BlobStore
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from dataplat_api.auth.deps import require_admin
from dataplat_api.db import get_session
from dataplat_api.models import RepositoryORM
from dataplat_api.routers.commits import _commit_to_read
from dataplat_api.runner.adapter_runner import AdapterRunner
from dataplat_api.schemas.ingest import IngestRequest, IngestResponse, IngestSummary
from dataplat_api.services.repo import RepoService
from dataplat_api.storage import get_blob_store

router = APIRouter(prefix="/repos", tags=["ingest"])


async def _resolve_repo(
    session: AsyncSession,
    owner: str,
    name: str,
    current_user: AuthenticatedUser | None,
) -> RepositoryORM:
    """visibility-aware lookup；不可见 / 不存在 → 404 统一（复用 commit-api 同款规则）。"""
    repo = await RepoService.get_by_owner_name(session, owner, name, current_user)
    if repo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository {owner}/{name} 不存在",
        )
    return repo


@router.post("/{owner}/{name}/ingest", response_model=IngestResponse)
async def ingest(
    owner: str,
    name: str,
    payload: IngestRequest,
    _admin: AuthenticatedUser = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
    store: BlobStore = Depends(get_blob_store),
) -> IngestResponse:
    repo = await _resolve_repo(session, owner, name, _admin)
    commit, dedup, result = await AdapterRunner.run(session, store, repo.id, payload)
    return IngestResponse(
        commit=_commit_to_read(commit, dedup),
        ingest_summary=IngestSummary(
            asset_count=result.asset_count,
            file_count=result.file_count,
            bytes_written=result.bytes_written,
            notes=result.notes,
        ),
    )
