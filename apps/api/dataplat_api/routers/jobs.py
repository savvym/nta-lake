"""Jobs HTTP 路由（spec rq-worker-skeleton-20260517 AC-7~9）。

`POST /jobs/ingest`：admin only + repo visibility 复用 RepoService.get_by_owner_name
`GET /jobs/{job_id}`：任何已登录用户可读（MVP；ACL 留 follow-up `job-acl-*`）
"""

from __future__ import annotations

import uuid

from dataplat_core.protocols.auth import AuthenticatedUser
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from dataplat_api.auth.deps import get_current_user, require_admin
from dataplat_api.db import get_session
from dataplat_api.jobs.service import JobsService
from dataplat_api.models import JobORM
from dataplat_api.schemas.job import JobIngestRequest, JobListResponse, JobRead
from dataplat_api.services.repo import RepoService

_ALLOWED_STATUS = {"queued", "running", "succeeded", "failed"}
_ALLOWED_TYPE = {"ingest", "process", "pipeline"}

router = APIRouter(prefix="/jobs", tags=["jobs"])


def _to_read(job: JobORM) -> JobRead:
    return JobRead(
        id=str(job.id),
        type=job.type,
        status=job.status,
        payload=job.payload,
        result=job.result,
        error=job.error,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
    )


@router.post(
    "/ingest", response_model=JobRead, status_code=status.HTTP_201_CREATED
)
async def enqueue_ingest_job(
    payload: JobIngestRequest,
    admin: AuthenticatedUser = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> JobRead:
    repo = await RepoService.get_by_owner_name(
        session, payload.owner, payload.name, admin
    )
    if repo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository {payload.owner}/{payload.name} 不存在",
        )

    # payload 持久化为 plain dict（Pydantic v2 model_dump）
    job_payload = payload.model_dump(mode="json")
    job = await JobsService.enqueue(session, job_type="ingest", payload=job_payload)
    return _to_read(job)


@router.get("", response_model=JobListResponse)
async def list_jobs(
    status_filter: str | None = Query(None, alias="status"),
    job_type: str | None = Query(None, alias="type"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    _admin: AuthenticatedUser = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> JobListResponse:
    """admin only。spec web-jobs-list-page-20260520 AC-3。"""
    if status_filter is not None and status_filter not in _ALLOWED_STATUS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"status {status_filter!r} 非白名单；允许：{sorted(_ALLOWED_STATUS)}",
        )
    if job_type is not None and job_type not in _ALLOWED_TYPE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"type {job_type!r} 非白名单；允许：{sorted(_ALLOWED_TYPE)}",
        )
    items, total = await JobsService.list_jobs(
        session,
        status=status_filter,
        job_type=job_type,
        limit=limit,
        offset=offset,
    )
    return JobListResponse(
        items=[_to_read(j) for j in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/{job_id}", response_model=JobRead)
async def get_job(
    job_id: str,
    _user: AuthenticatedUser = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> JobRead:
    try:
        uuid.UUID(job_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} 不存在",
        ) from exc

    job = await JobsService.get_by_id(session, job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} 不存在",
        )
    return _to_read(job)
