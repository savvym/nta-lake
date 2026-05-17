"""DbRepoView：从 PG + BlobStore 拼接 RepoView Protocol（spec processor-framework AC-1）。

processor 通过 view.open(path) 读上游 commit 的 blob 字节流（StreamReader → bytes）。
iter_records 暂未实现（MVP；待 Schema Registry 落 parquet/jsonl 才能 driven）。
"""

from __future__ import annotations

import io
import uuid
from collections.abc import Iterable
from typing import Any, BinaryIO

from dataplat_core.protocols.storage import BlobStore
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from dataplat_api.models import CommitORM, TreeORM


class DbRepoView:
    """异步实现 RepoView Protocol 的最小子集。

    Note: RepoView Protocol 的 open() 是同步的；但 DbRepoView 内部读 DB + blob 是异步的。
    MVP 在 __init__ 时把 tree.entries 全部加载到内存（path→sha256 字典）；
    open(path) 走 blob_store.get（async iterator），asyncio.run + b''.join → BinaryIO。
    Processor 跑在 asyncio.to_thread 的 worker 线程里，可以同步调 .open。
    """

    def __init__(
        self,
        session: AsyncSession,
        store: BlobStore,
        repo_id: uuid.UUID,
        commit_hash: str,
    ) -> None:
        self._session = session
        self._store = store
        self._repo_id = repo_id
        self._commit_hash = commit_hash
        # 由 build() 异步填充
        self._path_to_sha: dict[str, str] = {}

    @property
    def repo_id(self) -> str:
        return str(self._repo_id)

    @property
    def commit_hash(self) -> str:
        return self._commit_hash

    async def load(self) -> None:
        """在 await 上下文加载 commit tree entries 到内存。

        必须在传给 processor 前调一次。
        """
        stmt = (
            select(CommitORM)
            .where(
                CommitORM.repo_id == self._repo_id,
                CommitORM.hash == self._commit_hash,
            )
            .options(selectinload(CommitORM.tree).selectinload(TreeORM.entries))
        )
        commit = (await self._session.execute(stmt)).scalar_one_or_none()
        if commit is None:
            raise ValueError(
                f"Commit {self._commit_hash} 在 repo {self._repo_id} 不存在"
            )
        self._path_to_sha = {e.name: e.target_hash for e in commit.tree.entries}

    def iter_paths(self) -> list[str]:
        return list(self._path_to_sha.keys())

    def open(self, path: str) -> BinaryIO:
        """同步 open（processor 在 thread pool 里调）。

        现实现：用 asyncio.run 把 async iterator 全量收成 bytes（小文件 OK）。
        大文件 follow-up 改为真流式。
        """
        import asyncio

        sha = self._path_to_sha.get(path)
        if sha is None:
            raise KeyError(f"path {path} 不在 commit {self._commit_hash} 的 tree 中")

        async def _read() -> bytes:
            chunks: list[bytes] = []
            async for c in self._store.get(sha):
                chunks.append(c)
            return b"".join(chunks)

        # 在线程里被调用，主线程的 event loop 不在；asyncio.run 合法
        data = asyncio.run(_read())
        return io.BytesIO(data)

    def iter_records(self) -> Iterable[dict[str, Any]]:
        raise NotImplementedError(
            "DbRepoView.iter_records 等待 Schema Registry 引入；MVP 暂不支持"
        )
