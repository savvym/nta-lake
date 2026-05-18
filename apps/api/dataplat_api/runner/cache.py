"""Pipeline 节点 cache（spec pipeline-orchestrator-mvp-20260518 T-4）。

- ``_canonical_json``：跨语言确定的 JSON 序列化（同 services/commit.py 思路）
- ``_canonical_config_hash``：单独对 config 做 canonical + sha256，供
  ``lineage.produced_by.config_hash`` 使用（v2 MUST FIX #3：禁止把整体 cache_key 当 config_hash 写）
- ``compute_cache_key``：``sha256(canonical({inputs sorted, processor, config}))``
- ``CacheService.lookup`` / ``insert``：薄封装 pipeline_cache 表
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dataplat_api.models import PipelineCacheORM


def _canonical_json(obj: Any) -> bytes:
    return json.dumps(
        obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")


def _canonical_config_hash(config: dict[str, Any]) -> str:
    """对单个 config dict 做 canonical + sha256 hex（独立于 cache_key）。"""
    return hashlib.sha256(_canonical_json(config)).hexdigest()


def compute_cache_key(
    inputs_commits: list[str],
    processor_name: str,
    processor_version: str,
    config: dict[str, Any],
) -> str:
    """节点 cache_key：(inputs_commits sorted, processor@version, config) 的 canonical sha256。

    顺序无关性来自 ``sorted(inputs_commits)`` + ``sort_keys=True``；
    list-in-config 顺序保留（list 顺序属业务语义，纳入 canonical）。
    """
    payload = {
        "inputs": sorted(inputs_commits),
        "processor": f"{processor_name}@{processor_version}",
        "config": config,
    }
    return hashlib.sha256(_canonical_json(payload)).hexdigest()


class CacheService:
    """无 state；薄封装。"""

    @staticmethod
    async def lookup(
        session: AsyncSession, cache_key: str
    ) -> str | None:
        stmt = select(PipelineCacheORM).where(
            PipelineCacheORM.cache_key == cache_key
        )
        row = (await session.execute(stmt)).scalar_one_or_none()
        return row.output_commit_hash if row else None

    @staticmethod
    async def insert(
        session: AsyncSession, cache_key: str, output_commit_hash: str
    ) -> None:
        # 已存在则不报错（multi-run 并发 race 自然兜底）
        existing = await CacheService.lookup(session, cache_key)
        if existing is not None:
            return
        session.add(
            PipelineCacheORM(
                cache_key=cache_key, output_commit_hash=output_commit_hash
            )
        )
