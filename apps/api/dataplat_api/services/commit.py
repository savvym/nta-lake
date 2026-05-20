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

from dataplat_api.models import CommitORM, TreeEntryORM, TreeORM
from dataplat_api.schemas._commit_internal import CommitCreate
from dataplat_api.schemas.tree import TreeEntryCreate
from dataplat_api.services.ref import RefService


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


# ---------- tree-nested-domain-20260520: 路径校验 + nested 化 ----------

_DIR_MODE = 0o040000  # 16384


def _validate_tree_paths(entries: list[TreeEntryCreate]) -> None:
    """校验扁平 entries 的 name 合法性 + entry_type 必须为 blob。

    任一命中 → ValueError 含详细错误（路由层翻 400）。
    本函数是**唯一校验边界**：所有非 blob 输入应在这里被拒，_normalize_to_nested
    不再做 entry_type 二次校验（仅信任 blob 输入）。
    """
    seen_full_names: set[str] = set()
    for e in entries:
        name = e.name
        if e.entry_type != "blob":
            raise ValueError(
                f"tree entry {name!r} 只接受 entry_type='blob' 扁平输入；"
                f"嵌套结构由 service 内部生成，调用方不要直接传 type='tree'；"
                f"实收 type={e.entry_type!r}"
            )
        if name == "":
            raise ValueError("tree entry name 不能为空字符串")
        if name.startswith("/") or name.endswith("/"):
            raise ValueError(
                f"tree entry name {name!r} 不能以 '/' 起或结尾"
            )
        if "//" in name:
            raise ValueError(f"tree entry name {name!r} 含连续 '/'")
        if name in seen_full_names:
            raise ValueError(f"tree entry name {name!r} 重复")
        seen_full_names.add(name)

        segments = name.split("/")
        for seg in segments:
            if seg in (".", ".."):
                raise ValueError(
                    f"tree entry name {name!r} 含非法 segment {seg!r}"
                )
            if seg.strip() == "":
                raise ValueError(
                    f"tree entry name {name!r} 含空白 segment {seg!r}"
                )

    # blob 名等于另一个 entry 的目录前缀
    for e in entries:
        prefix_parts = e.name.split("/")
        # 取所有真前缀（不含本身）
        for i in range(1, len(prefix_parts)):
            prefix = "/".join(prefix_parts[:i])
            if prefix in seen_full_names:
                raise ValueError(
                    f"tree entry {prefix!r} 同时作为 blob 与 {e.name!r} 的目录前缀冲突"
                )


def _normalize_to_nested(
    entries: list[TreeEntryCreate],
) -> tuple[str, list[tuple[str, list[TreeEntryCreate]]]]:
    """把扁平 entries（name 可含 `/`）转为嵌套 tree。

    返 (root_tree_hash, all_trees)。
    all_trees: list of (tree_hash, entries_at_that_level)；子 tree 在前，root 最后。
    持久化时按这个顺序 upsert，FK 引用不会断。

    空 entries 视为合法空 root tree：返 (_tree_hash([]), [(root_hash, [])])。
    """
    # in-memory trie
    # 节点：{"_blobs": list[TreeEntryCreate]（叶子）, "<seg>": <子节点>}
    root_node: dict[str, object] = {"_blobs": []}

    for e in entries:
        # entry_type 已在 _validate_tree_paths 校验为 "blob"；此处不重复
        segments = e.name.split("/")
        node = root_node
        # 走前 N-1 个 segment（中间目录）
        for seg in segments[:-1]:
            children = node  # alias
            if seg in children:
                sub = children[seg]
                if not isinstance(sub, dict):
                    raise ValueError(
                        f"path conflict at segment {seg!r} (already a blob leaf)"
                    )
                node = sub
            else:
                new_node: dict[str, object] = {"_blobs": []}
                children[seg] = new_node
                node = new_node
        # 末段：作为 blob 挂在当前节点
        last_seg = segments[-1]
        if last_seg in node:
            raise ValueError(
                f"path conflict: {e.name!r} segment {last_seg!r} 已被占用（同名子目录或 blob）"
            )
        # 把 entry 改为"只含末 segment 的 name"
        leaf_entry = TreeEntryCreate(
            name=last_seg,
            mode=e.mode,
            entry_type="blob",
            target_hash=e.target_hash,
        )
        blobs = node["_blobs"]
        assert isinstance(blobs, list)
        blobs.append(leaf_entry)
        # 保留 last_seg 以触发同层重名检测
        # 直接 mark 该 segment 已被占用（同 dict key）；用 "_blobs" list 已经记，
        # 这里加 mark 以便子目录段重复使用同名时 path conflict 触发
        node[last_seg] = leaf_entry

    all_trees: list[tuple[str, list[TreeEntryCreate]]] = []

    def _walk(node: dict[str, object]) -> str:
        """递归算节点的 tree hash；emit 子 tree 到 all_trees；返该层 hash。"""
        level_entries: list[TreeEntryCreate] = []
        # blob 叶子
        blobs = node["_blobs"]
        assert isinstance(blobs, list)
        for leaf in blobs:
            level_entries.append(leaf)
        # 子目录
        for key, child in node.items():
            if key == "_blobs":
                continue
            if isinstance(child, dict):
                sub_hash = _walk(child)
                level_entries.append(
                    TreeEntryCreate(
                        name=key,
                        mode=_DIR_MODE,
                        entry_type="tree",
                        target_hash=sub_hash,
                    )
                )
            # 否则是 mark 过的 blob leaf，已在 _blobs 里处理过；跳过
        # 同层 name 不能重（在 trie 结构里 dict key 已天然唯一；这里防御一次）
        names = [e.name for e in level_entries]
        if len(names) != len(set(names)):
            raise ValueError(
                f"_normalize_to_nested 内部错误：同层 name 重复 {names!r}"
            )
        h = _tree_hash(level_entries)
        all_trees.append((h, level_entries))
        return h

    root_hash = _walk(root_node)
    return root_hash, all_trees


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

        # 步骤 2：路径校验 → nested 化 → 算 tree_hash + commit_hash
        # 注意：步骤 1 blob 存在性校验保持原位（对扁平 entries 校验；
        # 全 type=blob，target_hash 全是 blob hash）。不要把校验移到 normalize
        # 之后，否则会用子 tree hash 调 store.exists 永远 miss → 400。
        try:
            _validate_tree_paths(payload.tree.entries)
            tree_hash, all_trees = _normalize_to_nested(payload.tree.entries)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc
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
            # upsert 所有层 tree（子 tree 在前；遍历 all_trees 按顺序写）
            for sub_tree_hash, entries_at_level in all_trees:
                existing_tree = await session.get(TreeORM, sub_tree_hash)
                if existing_tree is not None:
                    continue
                session.add(TreeORM(hash=sub_tree_hash, repo_id=repo_id))
                sorted_entries = sorted(
                    entries_at_level, key=lambda e: e.name
                )
                for pos, e in enumerate(sorted_entries):
                    session.add(
                        TreeEntryORM(
                            tree_hash=sub_tree_hash,
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

            # upsert ref（pipeline-orchestrator-mvp-20260518 T-0：抽出 helper）
            if payload.ref:
                await RefService.upsert_ref(
                    session, repo_id, payload.ref, commit_hash
                )

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
