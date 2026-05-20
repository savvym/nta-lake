"""AdapterRunner：(adapter_name, spec, repo) → CommitORM（spec AC-4 / AC-10）。

执行流程（spec 已固化）：
1. registry 取 adapter；未找到 → 404 含 available 列表
2. **parent 自动接链**（spec v2 修 MUST FIX-1）：
   - request.parents 非空 → 直接用
   - request.ref 非空 → SELECT RefORM.commit_hash for (repo_id, ref) 命中作 parent
   - 都空或 ref 未命中 → parents=[]（root commit）
3. mkdtemp workspace
4. asyncio.to_thread(adapter.ingest, spec, workspace, ctx)
   - ValueError / ValidationError → 400
5. 构造 CommitCreate + 调 CommitService.create_commit
6. finally: shutil.rmtree(workspace)
7. 返 (commit, dedup, result) 3-tuple
"""

from __future__ import annotations

import asyncio
import logging
import shutil
import tempfile
import uuid
from pathlib import Path

from dataplat_core.protocols.adapter import IngestResult
from dataplat_core.protocols.storage import BlobStore
from fastapi import HTTPException, status
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dataplat_api.llm.factory import get_llm_gateway
from dataplat_api.models import CommitORM, RefORM
from dataplat_api.runner.registry import get_registry
from dataplat_api.runner.runcontext import StandardRunContext
from dataplat_api.schemas._commit_internal import CommitCreate
from dataplat_api.schemas.ingest import IngestRequest
from dataplat_api.schemas.tree import TreeCreate, TreeEntryCreate
from dataplat_api.services.commit import CommitService

_logger = logging.getLogger("dataplat.ingest")


class AdapterRunner:
    """无 state；静态方法。"""

    @staticmethod
    async def run(
        session: AsyncSession,
        store: BlobStore,
        repo_id: uuid.UUID,
        request: IngestRequest,
    ) -> tuple[CommitORM, bool, IngestResult]:
        registry = get_registry()
        adapter = registry.get(request.adapter_name, request.adapter_version)
        if adapter is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "detail": f"Adapter {request.adapter_name}@{request.adapter_version} 不存在",
                    "available": [f"{n}@{v}" for n, v in registry.list_all()],
                },
            )

        # parent 自动接链
        resolved_parents: list[str]
        if request.parents:
            resolved_parents = list(request.parents)
        elif request.ref:
            ref_stmt = select(RefORM).where(
                RefORM.repo_id == repo_id, RefORM.name == request.ref
            )
            ref_row = (await session.execute(ref_stmt)).scalar_one_or_none()
            resolved_parents = [ref_row.commit_hash] if ref_row else []
        else:
            resolved_parents = []

        workspace = Path(tempfile.mkdtemp(prefix="dataplat-ingest-"))
        ctx = StandardRunContext(
            logger=_logger, blob_store=store, llm=get_llm_gateway()
        )
        try:
            try:
                result = await asyncio.to_thread(
                    adapter.ingest, request.spec, workspace, ctx
                )
            except (ValueError, ValidationError) as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(exc),
                ) from exc

            commit_create = CommitCreate(
                tree=TreeCreate(
                    entries=[
                        TreeEntryCreate(
                            name=f.path,
                            mode=f.mode,
                            entry_type="blob",
                            target_hash=f.sha256,
                        )
                        for f in result.files
                    ]
                ),
                parents=resolved_parents,
                author_id=request.author_id,
                message=request.message,
                lineage=None,
                ref=request.ref,
            )
            commit, dedup = await CommitService.create_commit(
                session, store, repo_id, commit_create
            )
            return commit, dedup, result
        finally:
            shutil.rmtree(workspace, ignore_errors=True)
