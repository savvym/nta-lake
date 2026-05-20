"""Repository CRUD 路由（spec repo-api-mvp-20260517）。

Prefix 钉死：`APIRouter(prefix="/repos")` + main `include_router(router)` 不再加 prefix
（auth-scaffold-20260517 stage 2 MUST FIX 已规则化）。

Auth 矩阵（spec AC-5/AC-6/AC-7/AC-8/AC-9）：
- POST/PATCH/DELETE: Depends(require_admin)
- GET (list + detail): Depends(get_optional_user)；不可见统一 404 不泄露存在性
"""

from __future__ import annotations

from typing import cast

from dataplat_core.domain.repository import Layer, Subtype, Visibility
from dataplat_core.protocols.auth import AuthenticatedUser
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from dataplat_api.auth.deps import get_optional_user, require_admin
from dataplat_api.db import get_session
from dataplat_api.models import RepositoryORM
from dataplat_api.schemas.ref import RefRead
from dataplat_api.schemas.repo import (
    RepositoryCreate,
    RepositoryListItem,
    RepositoryListResponse,
    RepositoryRead,
    RepositoryUpdate,
)
from dataplat_api.services.ref import RefService
from dataplat_api.services.repo import RepoService

router = APIRouter(prefix="/repos", tags=["repos"])


def _to_read(repo: RepositoryORM) -> RepositoryRead:
    return RepositoryRead(
        id=str(repo.id),
        owner=repo.owner,
        name=repo.name,
        layer=cast(Layer, repo.layer),
        subtype=cast(Subtype, repo.subtype),
        visibility=cast(Visibility, repo.visibility),
        description=repo.description,
        schema_id=repo.schema_id,
        row_format=repo.row_format,
        created_at=repo.created_at,
        updated_at=repo.updated_at,
    )


def _to_list_item(repo: RepositoryORM) -> RepositoryListItem:
    return RepositoryListItem(
        id=str(repo.id),
        owner=repo.owner,
        name=repo.name,
        layer=cast(Layer, repo.layer),
        subtype=cast(Subtype, repo.subtype),
        visibility=cast(Visibility, repo.visibility),
        description=repo.description,
        schema_id=repo.schema_id,
        row_format=repo.row_format,
        created_at=repo.created_at,
        updated_at=repo.updated_at,
    )


@router.post("", response_model=RepositoryRead, status_code=status.HTTP_201_CREATED)
async def create_repo(
    payload: RepositoryCreate,
    _admin: AuthenticatedUser = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> RepositoryRead:
    repo = await RepoService.create(session, payload)
    return _to_read(repo)


@router.get("", response_model=RepositoryListResponse)
async def list_repos(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    layer: Layer | None = Query(None),
    current_user: AuthenticatedUser | None = Depends(get_optional_user),
    session: AsyncSession = Depends(get_session),
) -> RepositoryListResponse:
    items, total = await RepoService.list(
        session,
        limit=limit,
        offset=offset,
        layer=layer,
        current_user=current_user,
    )
    return RepositoryListResponse(
        items=[_to_list_item(r) for r in items],
        total=total,
    )


@router.get("/{owner}/{name}", response_model=RepositoryRead)
async def get_repo(
    owner: str,
    name: str,
    current_user: AuthenticatedUser | None = Depends(get_optional_user),
    session: AsyncSession = Depends(get_session),
) -> RepositoryRead:
    repo = await RepoService.get_by_owner_name(session, owner, name, current_user)
    if repo is None:
        # 统一 404；不区分"不存在" vs "不可见"以避免存在性泄露
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository {owner}/{name} 不存在",
        )
    return _to_read(repo)


@router.patch("/{owner}/{name}", response_model=RepositoryRead)
async def update_repo(
    owner: str,
    name: str,
    payload: RepositoryUpdate,
    _admin: AuthenticatedUser = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> RepositoryRead:
    repo = await RepoService.update(session, owner, name, payload)
    return _to_read(repo)


@router.delete("/{owner}/{name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_repo(
    owner: str,
    name: str,
    _admin: AuthenticatedUser = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> None:
    ok = await RepoService.delete(session, owner, name)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository {owner}/{name} 不存在",
        )


@router.get(
    "/{owner}/{name}/refs/{ref_name}", response_model=RefRead
)
async def get_ref(
    owner: str,
    name: str,
    ref_name: str,
    current_user: AuthenticatedUser | None = Depends(get_optional_user),
    session: AsyncSession = Depends(get_session),
) -> RefRead:
    """visibility-aware：repo 不存在/不可见或 ref 不存在 → 统一 404 不泄露。"""
    repo = await RepoService.get_by_owner_name(session, owner, name, current_user)
    if repo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository {owner}/{name} 不存在",
        )
    ref = await RefService.get_by_name(session, repo.id, ref_name)
    if ref is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ref {ref_name} 在 {owner}/{name} 不存在",
        )
    return RefRead(name=ref.name, snapshot_hash=ref.commit_hash)
