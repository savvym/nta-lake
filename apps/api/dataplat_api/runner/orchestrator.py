"""PipelineOrchestrator：Recipe 编排引擎（spec pipeline-orchestrator-mvp-20260518 T-5b~e）。

执行流程（节点串行；MVP 不做节点级并行）：

1. 入口校验：``build_node_deps(recipe) → topo_sort`` 抛 ValueError → caller 422；
   每节点 ``ProcessorRegistry.get`` 预检 → 缺失抛 ValueError；
   每节点 ``inputs`` 长度必须 == 1（MVP single-input only；多源 processor 推后续 change）。
2. INSERT PipelineRunORM(status=running)。
3. 按 topo 顺序串行执行节点：
   - 解析 ``inputs[0]``：``@<node-id>`` 取上游 node_run.output_commit_hash；
     ``<layer>/<owner>/<name>@<ref>`` 查 repositories + refs 解析 commit hash。
   - ``compute_cache_key``。
   - ``CacheService.lookup``：
     * hit：**不**调 ProcessorRunner；``RefService.upsert_ref`` 更新 output ref；
       INSERT PipelineNodeRunORM(cache_hit=true, output_commit_hash=hit, status=succeeded,
       input_commits_json=sorted([upstream]), cache_key=key)
     * miss：构造 Lineage(produced_by=ProducedBy(kind=processor, name, version,
       config_hash=_canonical_config_hash(node.config)), inputs=[InputRef(repo, commit)],
       run_id=str(run_id), env={}); 调 ProcessorRunner.run(... lineage=lineage)；
       CacheService.insert；INSERT PipelineNodeRunORM(cache_hit=false, status=succeeded, ...)
   - 异常：catch (HTTPException, Exception) 双路；记 node_run.error；break；run.status=failed。
4. 全部 succeeded → run.status=succeeded。
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime

from dataplat_core.domain.lineage import InputRef, Lineage, ProducedBy
from dataplat_core.protocols.storage import BlobStore
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dataplat_api.models import (
    PipelineNodeRunORM,
    PipelineRunORM,
    RepositoryORM,
)
from dataplat_api.runner.cache import (
    CacheService,
    _canonical_config_hash,
    compute_cache_key,
)
from dataplat_api.runner.dag import build_node_deps, topo_sort
from dataplat_api.runner.processor_registry import get_processor_registry
from dataplat_api.runner.processor_runner import ProcessorRunner
from dataplat_api.schemas.pipeline import (
    Recipe,
    RecipeNode,
    parse_input_ref,
    parse_output_ref,
    parse_processor_ref,
)
from dataplat_api.services.ref import RefService

_logger = logging.getLogger("dataplat.orchestrator")


class PipelineOrchestrator:
    """无 state；静态方法。"""

    @staticmethod
    def validate_recipe(recipe: Recipe) -> list[str]:
        """入口校验：返回 topo 顺序的 node id 列表。

        抛 ValueError（caller 转 422）：
        - DAG 有环 / 引用未知 node id
        - 节点 inputs 长度 != 1（MVP single-input only）
        - 节点 processor 未在 ProcessorRegistry 注册
        """
        deps = build_node_deps(recipe)
        order = topo_sort(deps)

        registry = get_processor_registry()
        for node in recipe.nodes:
            if len(node.inputs) != 1:
                raise ValueError(
                    f"node {node.id!r} inputs 长度 {len(node.inputs)}；"
                    f"MVP single-input only（多源 processor 推到 follow-up "
                    f"multi-input-processor-*）"
                )
            name, version = parse_processor_ref(node.processor)
            if registry.get(name, version) is None:
                available = [f"{n}@{v}" for n, v in registry.list_all()]
                raise ValueError(
                    f"node {node.id!r} processor {node.processor!r} 未注册；"
                    f"可用：{available}"
                )

        return order

    @staticmethod
    async def run_pipeline(
        session: AsyncSession,
        store: BlobStore,
        recipe: Recipe,
        author_id: str,
        run_id: uuid.UUID,
    ) -> PipelineRunORM:
        """编排执行入口。""run_id"" 由 caller (router) 预生成，
        外部已经把 PipelineRunORM(status=queued) 插好；本方法把 status 推到
        running → succeeded / failed。
        """
        run = await session.get(PipelineRunORM, run_id)
        if run is None:
            raise RuntimeError(f"PipelineRunORM {run_id} 不存在")

        try:
            order = PipelineOrchestrator.validate_recipe(recipe)
        except ValueError as exc:
            run.status = "failed"
            run.error = str(exc)
            run.completed_at = datetime.now(UTC)
            await session.commit()
            return run

        run.status = "running"
        run.started_at = datetime.now(UTC)
        await session.commit()

        node_by_id: dict[str, RecipeNode] = {n.id: n for n in recipe.nodes}
        node_output_commits: dict[str, str] = {}

        for nid in order:
            node = node_by_id[nid]
            node_failed = False
            error: str | None = None
            try:
                await PipelineOrchestrator._run_node(
                    session=session,
                    store=store,
                    node=node,
                    run_id=run_id,
                    author_id=author_id,
                    upstream_commits=node_output_commits,
                )
            except HTTPException as exc:  # noqa: PERF203  # node 级 try/except 是设计
                node_failed = True
                # v2 MUST FIX #2：统一 500 字符截断（HTTPException.detail 可能是 dict，
                # 含大 list 时序列化会超长）
                error = str(getattr(exc, "detail", exc))[:500]
            except Exception as exc:  # noqa: BLE001
                node_failed = True
                error = repr(exc)[:500]

            if node_failed:
                # 记节点失败（输入解析或预检失败时 _run_node 已自行写过 node_run；
                # 若发生在 _run_node 之前的解析阶段，这里兜底写一条 failed）
                latest = await PipelineOrchestrator._fetch_latest_node_run(
                    session, run_id, nid
                )
                if latest is None:
                    fb_name, fb_version = parse_processor_ref(node.processor)
                    session.add(
                        PipelineNodeRunORM(
                            id=uuid.uuid4(),
                            run_id=run_id,
                            node_id=nid,
                            processor_name=fb_name,
                            processor_version=fb_version,
                            config_json=node.config,
                            status="failed",
                            cache_hit=False,
                            # stage 4 SHOULD #1：解析未完成时写 NULL（避免空串混淆索引语义）
                            input_commits_json=None,
                            cache_key=None,
                            error=error,
                            started_at=datetime.now(UTC),
                            completed_at=datetime.now(UTC),
                        )
                    )
                else:
                    latest.status = "failed"
                    latest.error = error
                    latest.completed_at = datetime.now(UTC)

                run.status = "failed"
                run.error = f"node {nid!r} failed: {error}"
                run.completed_at = datetime.now(UTC)
                await session.commit()
                return run

            # 成功 → 把 output commit 记入 node_output_commits 供下游引用
            latest = await PipelineOrchestrator._fetch_latest_node_run(
                session, run_id, nid
            )
            if latest is not None and latest.output_commit_hash is not None:
                node_output_commits[nid] = latest.output_commit_hash

        run.status = "succeeded"
        run.completed_at = datetime.now(UTC)
        await session.commit()
        return run

    # ---------------------------------------------------------------- helpers

    @staticmethod
    async def _run_node(
        *,
        session: AsyncSession,
        store: BlobStore,
        node: RecipeNode,
        run_id: uuid.UUID,
        author_id: str,
        upstream_commits: dict[str, str],
    ) -> None:
        proc_name, proc_version = parse_processor_ref(node.processor)
        started_at = datetime.now(UTC)

        # 解析 input[0]
        ref = node.inputs[0]
        kind, parts = parse_input_ref(ref)
        if kind == "node":
            upstream_id = parts["node_id"]
            if upstream_id not in upstream_commits:
                raise ValueError(
                    f"node {node.id!r} 引用未运行的上游 {upstream_id!r}"
                )
            source_commit_hash = upstream_commits[upstream_id]
            source_repo_id = await PipelineOrchestrator._resolve_source_repo_id_from_commit(
                session, source_commit_hash
            )
            source_repo_qualified = await PipelineOrchestrator._qualified_repo_id(
                session, source_repo_id
            )
        else:
            source_repo_id = await PipelineOrchestrator._resolve_repo_id_by_layer_owner_name(
                session, parts["layer"], parts["owner"], parts["name"]
            )
            ref_row = await RefService.get_by_name(
                session, source_repo_id, parts["ref"]
            )
            if ref_row is None:
                raise ValueError(
                    f"node {node.id!r} input ref 不存在：{ref}"
                )
            source_commit_hash = ref_row.commit_hash
            source_repo_qualified = (
                f"{parts['layer']}/{parts['owner']}/{parts['name']}"
            )

        # 解析 output
        out_parts = parse_output_ref(node.output)
        target_repo_id = await PipelineOrchestrator._resolve_repo_id_by_layer_owner_name(
            session, out_parts["layer"], out_parts["owner"], out_parts["name"]
        )
        target_ref = out_parts["ref"] if out_parts["ref"] != "auto" else "main"

        # cache_key
        inputs_commits = [source_commit_hash]
        cache_key = compute_cache_key(
            inputs_commits, proc_name, proc_version, node.config
        )

        hit = await CacheService.lookup(session, cache_key)
        if hit is not None:
            # cache hit 分支：不调 ProcessorRunner；upsert ref；写审计字段
            await RefService.upsert_ref(
                session, target_repo_id, target_ref, hit
            )
            session.add(
                PipelineNodeRunORM(
                    id=uuid.uuid4(),
                    run_id=run_id,
                    node_id=node.id,
                    processor_name=proc_name,
                    processor_version=proc_version,
                    config_json=node.config,
                    status="succeeded",
                    cache_hit=True,
                    output_commit_hash=hit,
                    input_commits_json=sorted(inputs_commits),
                    cache_key=cache_key,
                    started_at=started_at,
                    completed_at=datetime.now(UTC),
                )
            )
            await session.commit()
            return

        # cache miss 分支：构造 Lineage 调 ProcessorRunner
        lineage = Lineage(
            produced_by=ProducedBy(
                kind="processor",
                name=proc_name,
                version=proc_version,
                config_hash=_canonical_config_hash(node.config),
            ),
            inputs=[
                InputRef(
                    repo=source_repo_qualified, commit=source_commit_hash
                )
            ],
            run_id=str(run_id),
            env={},
        )
        commit, _dedup, _result = await ProcessorRunner.run(
            session=session,
            store=store,
            source_repo_id=source_repo_id,
            source_commit_hash=source_commit_hash,
            target_repo_id=target_repo_id,
            processor_name=proc_name,
            processor_version=proc_version,
            config=node.config,
            author_id=author_id,
            message=f"pipeline run {run_id} node {node.id}",
            ref=target_ref,
            lineage=lineage,
        )
        await CacheService.insert(session, cache_key, commit.hash)
        session.add(
            PipelineNodeRunORM(
                id=uuid.uuid4(),
                run_id=run_id,
                node_id=node.id,
                processor_name=proc_name,
                processor_version=proc_version,
                config_json=node.config,
                status="succeeded",
                cache_hit=False,
                output_commit_hash=commit.hash,
                input_commits_json=sorted(inputs_commits),
                cache_key=cache_key,
                started_at=started_at,
                completed_at=datetime.now(UTC),
            )
        )
        await session.commit()

    @staticmethod
    async def _resolve_repo_id_by_layer_owner_name(
        session: AsyncSession, layer: str, owner: str, name: str
    ) -> uuid.UUID:
        stmt = select(RepositoryORM).where(
            RepositoryORM.layer == layer,
            RepositoryORM.owner == owner,
            RepositoryORM.name == name,
        )
        row = (await session.execute(stmt)).scalar_one_or_none()
        if row is None:
            raise ValueError(
                f"repository {layer}/{owner}/{name} 不存在"
            )
        return row.id

    @staticmethod
    async def _qualified_repo_id(
        session: AsyncSession, repo_id: uuid.UUID
    ) -> str:
        row = await session.get(RepositoryORM, repo_id)
        if row is None:
            raise RuntimeError(f"repo {repo_id} 不存在")
        return f"{row.layer}/{row.owner}/{row.name}"

    @staticmethod
    async def _resolve_source_repo_id_from_commit(
        session: AsyncSession, commit_hash: str
    ) -> uuid.UUID:
        from dataplat_api.models import CommitORM  # 内部 import 避免顶部循环

        row = await session.get(CommitORM, commit_hash)
        if row is None:
            raise ValueError(f"commit {commit_hash} 不存在")
        return row.repo_id

    @staticmethod
    async def _fetch_latest_node_run(
        session: AsyncSession, run_id: uuid.UUID, node_id: str
    ) -> PipelineNodeRunORM | None:
        stmt = (
            select(PipelineNodeRunORM)
            .where(
                PipelineNodeRunORM.run_id == run_id,
                PipelineNodeRunORM.node_id == node_id,
            )
            .order_by(PipelineNodeRunORM.started_at.desc())
            .limit(1)
        )
        return (await session.execute(stmt)).scalar_one_or_none()
