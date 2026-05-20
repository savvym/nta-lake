"""ProcessorRunner：(processor_name, source_commit, target_repo) → 下游 CommitORM（spec AC-3）。

执行流程：
1. registry 取 processor；未找到 → HTTPException 404 含 available
2. DbRepoView.load 上游 commit tree
3. ref→parent 自动接链（target_repo 的 ref；与 AdapterRunner 同模式）
4. mkdtemp workspace
5. asyncio.to_thread(processor.run, [view], config, workspace, ctx)
   - ctx.blob_store 注入；processor 直接 put 新 blob
   - ValueError / ValidationError → 400
6. ProcessResult.files → CommitCreate → CommitService.create_commit
7. finally rmtree workspace
8. 返 (commit, dedup, result)
"""

from __future__ import annotations

import asyncio
import logging
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import Any

from dataplat_core.domain.lineage import Lineage
from dataplat_core.protocols.processor import ProcessResult
from dataplat_core.protocols.storage import BlobStore
from fastapi import HTTPException, status
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dataplat_api.llm.factory import get_llm_gateway
from dataplat_api.models import CommitORM, RefORM
from dataplat_api.runner.processor_registry import get_processor_registry
from dataplat_api.runner.repo_view import DbRepoView
from dataplat_api.runner.runcontext import StandardRunContext
from dataplat_api.schemas._commit_internal import CommitCreate
from dataplat_api.schemas.tree import TreeCreate, TreeEntryCreate
from dataplat_api.services.commit import CommitService

_logger = logging.getLogger("dataplat.process")


class ProcessorRunner:
    """无 state；静态方法。"""

    @staticmethod
    async def run(
        session: AsyncSession,
        store: BlobStore,
        source_repo_id: uuid.UUID,
        source_commit_hash: str,
        target_repo_id: uuid.UUID,
        processor_name: str,
        processor_version: str,
        config: dict[str, Any],
        author_id: str,
        message: str | None = None,
        ref: str | None = None,
        parents: list[str] | None = None,
        lineage: Lineage | None = None,
    ) -> tuple[CommitORM, bool, ProcessResult]:
        registry = get_processor_registry()
        processor = registry.get(processor_name, processor_version)
        if processor is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "detail": f"Processor {processor_name}@{processor_version} 不存在",
                    "available": [f"{n}@{v}" for n, v in registry.list_all()],
                },
            )

        # 加载上游 view
        view = DbRepoView(session, store, source_repo_id, source_commit_hash)
        try:
            await view.load()
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(exc),
            ) from exc

        # parent 自动接链（target_repo 的 ref）
        resolved_parents: list[str]
        if parents:
            resolved_parents = list(parents)
        elif ref:
            ref_stmt = select(RefORM).where(
                RefORM.repo_id == target_repo_id, RefORM.name == ref
            )
            ref_row = (await session.execute(ref_stmt)).scalar_one_or_none()
            resolved_parents = [ref_row.commit_hash] if ref_row else []
        else:
            resolved_parents = []

        workspace = Path(tempfile.mkdtemp(prefix="dataplat-process-"))
        ctx = StandardRunContext(
            logger=_logger, blob_store=store, llm=get_llm_gateway()
        )
        try:
            try:
                # processor.run 是同步的；用 to_thread
                result: ProcessResult = await asyncio.to_thread(
                    processor.run, [view], config, workspace, ctx
                )
            except (ValueError, ValidationError) as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=str(exc),
                ) from exc

            # ProcessResult.files 与 IngestResult.files 同形态（IngestFileRef）
            files = getattr(result, "files", None) or []
            commit_create = CommitCreate(
                tree=TreeCreate(
                    entries=[
                        TreeEntryCreate(
                            name=f.path,
                            mode=f.mode,
                            entry_type="blob",
                            target_hash=f.sha256,
                        )
                        for f in files
                    ]
                ),
                parents=resolved_parents,
                author_id=author_id,
                message=message,
                lineage=lineage,
                ref=ref,
            )
            commit, dedup = await CommitService.create_commit(
                session, store, target_repo_id, commit_create
            )
            return commit, dedup, result
        finally:
            shutil.rmtree(workspace, ignore_errors=True)
