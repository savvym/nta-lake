"""CommitService：事务 + canonical hash + 幂等（spec commit-api-mvp-20260517 AC-3/8/9/10）。

# Canonical JSON 规则（spec AC-9，跨版本/跨语言确定性的基石）

`json.dumps(..., sort_keys=True, ensure_ascii=False, separators=(",", ":"))`
+ 列表元素显式预排序（entries 按 name 升序；parents 按 hash 升序）
+ Pydantic 嵌套结构用 `model_dump(mode="json")` 取 plain JSON-native dict
  （把 datetime/UUID 转 ISO string；保证 sort_keys 递归生效）

# Commit hash 公式（spec AC-9 方案 B）

commit canonical bytes 输入字段：
- tree_hash: str
- parents: list[str]（升序）
- author_id: str
- message: str | None
- lineage: dict | None（model_dump(mode="json")）

**不含 `created_at`**——created_at 由服务端记录用于 audit 但不参与 hash；
与 CAS"同内容同 hash"语义一致。

# 事务边界（spec AC-8）

1. 事务外：blob 存在性校验（异步 `store.exists`）→ 缺失 raise HTTPException 400
2. 事务外：算 tree_hash + commit_hash
3. 事务外：SELECT commit_hash 命中 → 返 (existing, True)
4. 事务内 `async with session.begin()`：upsert tree + bulk insert entries + insert commit + upsert ref
5. 兜底 race：IntegrityError → rollback + 重读 → 返 (existing, True)
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import UTC, datetime

# 避免循环 import 用 TYPE_CHECKING 不行（运行时 store 参数需要类型）；
# 直接 import Protocol 即可，no cycle。
from dataplat_core.protocols.storage import BlobStore  # noqa: E402
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from dataplat_api.models import CommitORM, RefORM, TreeEntryORM, TreeORM
from dataplat_api.schemas.commit import CommitCreate
from dataplat_api.schemas.tree import TreeEntryCreate


def _canonical_tree_bytes(entries: list[TreeEntryCreate]) -> bytes:
    sorted_entries = sorted(entries, key=lambda e: e.name)
    plain = [
        {
            "name": e.name,
            "mode": e.mode,
            "entry_type": e.entry_type,
            "target_hash": e.target_hash,
        }
        for e in sorted_entries
    ]
    return json.dumps(
        plain, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")


def _tree_hash(entries: list[TreeEntryCreate]) -> str:
    return hashlib.sha256(_canonical_tree_bytes(entries)).hexdigest()


def _lineage_to_canonical(lineage_obj: object) -> dict[str, object] | None:
    if lineage_obj is None:
        return None
    # Pydantic Lineage → plain JSON-native dict（datetime / UUID 已转）
    dumped = lineage_obj.model_dump(mode="json")  # type: ignore[attr-defined]
    return dumped  # type: ignore[no-any-return]


def _canonical_commit_bytes(
    tree_hash: str,
    parents: list[str],
    author_id: str,
    message: str | None,
    lineage_canonical: dict[str, object] | None,
) -> bytes:
    payload = {
        "tree_hash": tree_hash,
        "parents": sorted(parents),
        "author_id": author_id,
        "message": message,
        "lineage": lineage_canonical,
    }
    return json.dumps(
        payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")


def _commit_hash(
    tree_hash: str,
    parents: list[str],
    author_id: str,
    message: str | None,
    lineage_canonical: dict[str, object] | None,
) -> str:
    return hashlib.sha256(
        _canonical_commit_bytes(tree_hash, parents, author_id, message, lineage_canonical)
    ).hexdigest()


class CommitService:
    """无 state；方法均为 staticmethod。"""

    # 暴露私有函数作为类方法属性供测试 (g1) 直接 import 单元测试
    _canonical_tree_bytes = staticmethod(_canonical_tree_bytes)
    _tree_hash = staticmethod(_tree_hash)
    _canonical_commit_bytes = staticmethod(_canonical_commit_bytes)
    _commit_hash = staticmethod(_commit_hash)
    _lineage_to_canonical = staticmethod(_lineage_to_canonical)

    @staticmethod
    async def create_commit(
        session: AsyncSession,
        store: BlobStore,
        repo_id: uuid.UUID,
        payload: CommitCreate,
    ) -> tuple[CommitORM, bool]:
        # 步骤 1：事务外 blob 存在性校验
        target_hashes = {e.target_hash for e in payload.tree.entries}
        missing: list[str] = []
        for h in sorted(target_hashes):
            if not await store.exists(h):
                missing.append(h)
        if missing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"missing_hashes": missing},
            )

        # 步骤 2：算 tree_hash + commit_hash
        tree_hash = _tree_hash(payload.tree.entries)
        lineage_canonical = _lineage_to_canonical(payload.lineage)
        commit_hash = _commit_hash(
            tree_hash,
            payload.parents,
            payload.author_id,
            payload.message,
            lineage_canonical,
        )

        # 步骤 3：SELECT 命中 → 返 dedup
        existing = await CommitService._fetch_with_tree(session, repo_id, commit_hash)
        if existing is not None:
            return existing, True

        # 步骤 4：单事务写（auto-begin；commit 收尾；race → rollback）
        try:
            # upsert tree
            tree = await session.get(TreeORM, tree_hash)
            if tree is None:
                tree = TreeORM(hash=tree_hash, repo_id=repo_id)
                session.add(tree)
                # bulk add entries（按 name 升序，position 同步）
                sorted_entries = sorted(
                    payload.tree.entries, key=lambda e: e.name
                )
                for pos, e in enumerate(sorted_entries):
                    session.add(
                        TreeEntryORM(
                            tree_hash=tree_hash,
                            position=pos,
                            name=e.name,
                            mode=e.mode,
                            entry_type=e.entry_type,
                            target_hash=e.target_hash,
                        )
                    )

            # insert commit
            commit = CommitORM(
                hash=commit_hash,
                repo_id=repo_id,
                tree_hash=tree_hash,
                parents=list(payload.parents),
                author_id=payload.author_id,
                created_at=datetime.now(UTC),
                message=payload.message,
                lineage_json=lineage_canonical,
            )
            session.add(commit)

            # upsert ref
            if payload.ref:
                ref_stmt = select(RefORM).where(
                    RefORM.repo_id == repo_id,
                    RefORM.name == payload.ref,
                )
                ref_existing = (await session.execute(ref_stmt)).scalar_one_or_none()
                if ref_existing is None:
                    session.add(
                        RefORM(
                            id=uuid.uuid4(),
                            repo_id=repo_id,
                            name=payload.ref,
                            commit_hash=commit_hash,
                        )
                    )
                else:
                    ref_existing.commit_hash = commit_hash

            await session.commit()
        except IntegrityError:
            # 步骤 5：race 兜底
            await session.rollback()
            existing = await CommitService._fetch_with_tree(session, repo_id, commit_hash)
            if existing is None:
                raise  # 真异常，非 race
            return existing, True

        # 重读 with tree
        created = await CommitService._fetch_with_tree(session, repo_id, commit_hash)
        if created is None:
            raise RuntimeError(f"commit {commit_hash} 创建后立即查不到，事务异常")
        return created, False

    @staticmethod
    async def get_with_tree(
        session: AsyncSession,
        repo_id: uuid.UUID,
        commit_hash: str,
    ) -> CommitORM | None:
        return await CommitService._fetch_with_tree(session, repo_id, commit_hash)

    @staticmethod
    async def get_tree_by_commit(
        session: AsyncSession,
        repo_id: uuid.UUID,
        commit_hash: str,
    ) -> TreeORM | None:
        commit = await CommitService._fetch_with_tree(session, repo_id, commit_hash)
        if commit is None:
            return None
        tree_stmt = (
            select(TreeORM)
            .where(TreeORM.hash == commit.tree_hash)
            .options(selectinload(TreeORM.entries))
        )
        return (await session.execute(tree_stmt)).scalar_one_or_none()

    @staticmethod
    async def _fetch_with_tree(
        session: AsyncSession,
        repo_id: uuid.UUID,
        commit_hash: str,
    ) -> CommitORM | None:
        stmt = (
            select(CommitORM)
            .where(
                CommitORM.repo_id == repo_id,
                CommitORM.hash == commit_hash,
            )
            .options(selectinload(CommitORM.tree).selectinload(TreeORM.entries))
        )
        return (await session.execute(stmt)).scalar_one_or_none()
