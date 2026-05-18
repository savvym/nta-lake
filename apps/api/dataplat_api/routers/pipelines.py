"""Pipeline HTTP 路由（spec pipeline-orchestrator-mvp-20260518 T-6a/b，AC-9）。

- ``POST /pipelines/runs``：JSON body ``RecipeCreateRequest{recipe: Recipe}``；
  admin only；预 INSERT PipelineRunORM(status=queued) → enqueue pipeline job → 202 + run_id/job_id。
- ``POST /pipelines/runs:from-yaml``：``text/yaml`` 文本入口（同上语义，仅解析方式不同）。
- ``GET /pipelines/runs/{run_id}``：返 run + 节点列表（含 cache_hit / output_commit_hash /
  input_commits / cache_key）。

入口校验：把 ``PipelineOrchestrator.validate_recipe`` 提前到 router 调用，让 422 在
enqueue **之前**返回，不浪费 worker 资源。
"""

from __future__ import annotations

import uuid

from dataplat_core.protocols.auth import AuthenticatedUser
from fastapi import APIRouter, Body, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dataplat_api.auth.deps import require_admin
from dataplat_api.db import get_session
from dataplat_api.jobs.service import JobsService
from dataplat_api.models import PipelineNodeRunORM, PipelineRunORM
from dataplat_api.runner.orchestrator import PipelineOrchestrator
from dataplat_api.schemas.pipeline import (
    PipelineNodeRunResponse,
    PipelineRunCreatedResponse,
    PipelineRunResponse,
    Recipe,
    RecipeCreateRequest,
    load_recipe,
)

router = APIRouter(prefix="/pipelines", tags=["pipelines"])


async def _create_run_and_enqueue(
    session: AsyncSession, recipe: Recipe, admin: AuthenticatedUser
) -> PipelineRunCreatedResponse:
    """共享 POST 入口：预 INSERT + enqueue + 返 202 体。"""
    # 入口校验（topo + processor 预检）— 失败 422
    try:
        PipelineOrchestrator.validate_recipe(recipe)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    run_id = uuid.uuid4()
    run = PipelineRunORM(
        id=run_id,
        recipe_name=recipe.name,
        recipe_json=recipe.model_dump(mode="json"),
        status="queued",
        created_by=admin.username,
    )
    session.add(run)
    await session.commit()
    await session.refresh(run)

    # v2 SHOULD FIX #2：enqueue 失败时回滚 PipelineRunORM，避免 orphan(status=queued) 残留
    try:
        job = await JobsService.enqueue(
            session,
            job_type="pipeline",
            payload={
                "run_id": str(run_id),
                "recipe": recipe.model_dump(mode="json"),
                "author_id": admin.username,
            },
        )
    except Exception:
        await session.delete(run)
        await session.commit()
        raise
    return PipelineRunCreatedResponse(run_id=str(run_id), job_id=str(job.id))


@router.post(
    "/runs",
    response_model=PipelineRunCreatedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_pipeline_run(
    body: RecipeCreateRequest,
    admin: AuthenticatedUser = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> PipelineRunCreatedResponse:
    return await _create_run_and_enqueue(session, body.recipe, admin)


@router.post(
    "/runs:from-yaml",
    response_model=PipelineRunCreatedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def create_pipeline_run_from_yaml(
    request: Request,
    admin: AuthenticatedUser = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
    body: str = Body(..., media_type="text/yaml"),  # noqa: B008
) -> PipelineRunCreatedResponse:
    del request  # 仅占位避免 OpenAPI 单参与 Body 冲突
    try:
        recipe = load_recipe(body)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"YAML 解析失败：{exc}",
        ) from exc
    return await _create_run_and_enqueue(session, recipe, admin)


@router.get("/runs/{run_id}", response_model=PipelineRunResponse)
async def get_pipeline_run(
    run_id: str,
    _admin: AuthenticatedUser = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> PipelineRunResponse:
    try:
        rid = uuid.UUID(run_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"非法 run_id {run_id!r}",
        ) from exc

    run = await session.get(PipelineRunORM, rid)
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"PipelineRun {run_id} 不存在",
        )

    node_stmt = (
        select(PipelineNodeRunORM)
        .where(PipelineNodeRunORM.run_id == rid)
        .order_by(PipelineNodeRunORM.started_at.asc())
    )
    node_rows = (await session.execute(node_stmt)).scalars().all()

    return PipelineRunResponse(
        run_id=str(run.id),
        recipe_name=run.recipe_name,
        status=run.status,
        error=run.error,
        created_by=run.created_by,
        node_runs=[
            PipelineNodeRunResponse(
                node_id=r.node_id,
                processor_name=r.processor_name,
                processor_version=r.processor_version,
                config=r.config_json,
                status=r.status,
                cache_hit=r.cache_hit,
                output_commit_hash=r.output_commit_hash,
                input_commits=(
                    list(r.input_commits_json)
                    if r.input_commits_json is not None
                    else None
                ),
                cache_key=r.cache_key,
                error=r.error,
            )
            for r in node_rows
        ],
    )
