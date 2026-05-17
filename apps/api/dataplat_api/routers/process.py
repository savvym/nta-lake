"""Process HTTP 路由（spec processor-framework-20260517 AC-6）。

`POST /process`（admin only）→ 创建 process job → RQ enqueue → 201 + JobRead；
worker 异步跑 ProcessorRunner.run。
"""

from __future__ import annotations

from dataplat_core.protocols.auth import AuthenticatedUser
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from dataplat_api.auth.deps import require_admin
from dataplat_api.db import get_session
from dataplat_api.jobs.service import JobsService
from dataplat_api.routers.jobs import _to_read  # 复用 jobs router 的 JobRead 映射
from dataplat_api.schemas.job import JobRead
from dataplat_api.schemas.process import ProcessRequest
from dataplat_api.services.repo import RepoService

router = APIRouter(prefix="/process", tags=["process"])


@router.post("", response_model=JobRead, status_code=status.HTTP_201_CREATED)
async def enqueue_process_job(
    payload: ProcessRequest,
    admin: AuthenticatedUser = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> JobRead:
    # 验证 source / target 都对 admin 可见（admin 能见所有）
    source_repo = await RepoService.get_by_owner_name(
        session, payload.source_owner, payload.source_name, admin
    )
    if source_repo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Source repository {payload.source_owner}/{payload.source_name} 不存在",
        )
    target_repo = await RepoService.get_by_owner_name(
        session, payload.target_owner, payload.target_name, admin
    )
    if target_repo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Target repository {payload.target_owner}/{payload.target_name} 不存在",
        )

    job_payload = payload.model_dump(mode="json")
    job = await JobsService.enqueue(session, job_type="process", payload=job_payload)
    return _to_read(job)
