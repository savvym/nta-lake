"""RepoService：Repository CRUD 业务逻辑（无 HTTP / 无 role 校验）。

职责（spec v2 tasks MUST FIX-3 明示）：
- visibility 过滤：public（任何人）/ internal（已登录）/ private（仅 admin）
- create 的 IntegrityError → 409
- update/delete 的 not-found → 404
- **service 不查 role / 不调 require_admin**——admin 权限由 router Depends(require_admin) 保证
"""

from __future__ import annotations

import uuid

from dataplat_core.protocols.auth import AuthenticatedUser
from dataplat_core.schemas import SchemaRegistry
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from dataplat_api.models import RepositoryORM
from dataplat_api.schemas.repo import RepositoryCreate, RepositoryUpdate


class RepoService:
    """无 state；方法都接受 session + 必要时 current_user。"""

    @staticmethod
    def _visibility_visible(
        repo_visibility: str,
        current_user: AuthenticatedUser | None,
    ) -> bool:
        """visibility 矩阵：public 任何人；internal 已登录；private 仅 admin。"""
        if repo_visibility == "public":
            return True
        if repo_visibility == "internal":
            return current_user is not None
        if repo_visibility == "private":
            return current_user is not None and current_user.role == "admin"
        return False  # 未知 visibility 一律不可见

    @staticmethod
    async def create(
        session: AsyncSession,
        payload: RepositoryCreate,
    ) -> RepositoryORM:
        # schema_id / row_format enforcement
        if payload.layer in ("silver", "gold"):
            if payload.schema_id is None:
                raise HTTPException(
                    status_code=422,
                    detail=f"layer={payload.layer} 必须传 schema_id",
                )
            if payload.row_format is None:
                raise HTTPException(
                    status_code=422,
                    detail=f"layer={payload.layer} 必须传 row_format ('parquet' | 'jsonl')",
                )
            if not SchemaRegistry.is_registered(payload.schema_id):
                raise HTTPException(
                    status_code=422,
                    detail=(
                        f"schema_id={payload.schema_id!r} 未注册；"
                        f"已注册: {SchemaRegistry.list_ids()}"
                    ),
                )
            entry = SchemaRegistry.get(payload.schema_id)
            if entry.layer != payload.layer:
                raise HTTPException(
                    status_code=422,
                    detail=(
                        f"schema_id={payload.schema_id!r} 是 {entry.layer} schema，"
                        f"不能用于 layer={payload.layer}"
                    ),
                )
        elif payload.layer == "bronze":
            if payload.schema_id is not None:
                raise HTTPException(
                    status_code=422,
                    detail="bronze repo 不能传 schema_id",
                )
            if payload.row_format is not None:
                raise HTTPException(
                    status_code=422,
                    detail="bronze repo 不能传 row_format",
                )

        repo = RepositoryORM(
            id=uuid.uuid4(),
            owner=payload.owner,
            name=payload.name,
            layer=payload.layer,
            subtype=payload.subtype,
            visibility=payload.visibility,
            description=payload.description,
            schema_id=payload.schema_id,
            row_format=payload.row_format,
        )
        session.add(repo)
        try:
            await session.commit()
        except IntegrityError as exc:
            await session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Repository {payload.owner}/{payload.name} 已存在",
            ) from exc
        await session.refresh(repo)
        return repo

    @staticmethod
    async def get_by_owner_name(
        session: AsyncSession,
        owner: str,
        name: str,
        current_user: AuthenticatedUser | None,
    ) -> RepositoryORM | None:
        """返回 None 表示不存在或对 caller 不可见——caller 应一律返 404 不区分。"""
        stmt = select(RepositoryORM).where(
            RepositoryORM.owner == owner,
            RepositoryORM.name == name,
        )
        repo = (await session.execute(stmt)).scalar_one_or_none()
        if repo is None:
            return None
        if not RepoService._visibility_visible(repo.visibility, current_user):
            return None
        return repo

    @staticmethod
    async def list(
        session: AsyncSession,
        *,
        limit: int,
        offset: int,
        layer: str | None,
        current_user: AuthenticatedUser | None,
    ) -> tuple[list[RepositoryORM], int]:
        """返回 (items, total)；total 反映 visibility 过滤后剩余数。"""
        # 构建 visibility 过滤的 WHERE 条件
        if current_user is None:
            # 匿名：仅 public
            visibility_filter = RepositoryORM.visibility == "public"
        elif current_user.role == "admin":
            # admin：全部可见
            visibility_filter = None
        else:
            # 已登录非 admin：public + internal
            visibility_filter = RepositoryORM.visibility.in_(("public", "internal"))

        base_stmt = select(RepositoryORM)
        count_stmt = select(func.count()).select_from(RepositoryORM)
        if visibility_filter is not None:
            base_stmt = base_stmt.where(visibility_filter)
            count_stmt = count_stmt.where(visibility_filter)
        if layer is not None:
            base_stmt = base_stmt.where(RepositoryORM.layer == layer)
            count_stmt = count_stmt.where(RepositoryORM.layer == layer)

        base_stmt = base_stmt.order_by(RepositoryORM.created_at.desc()).limit(limit).offset(offset)

        items = list((await session.execute(base_stmt)).scalars().all())
        total = int((await session.execute(count_stmt)).scalar_one())
        return items, total

    @staticmethod
    async def update(
        session: AsyncSession,
        owner: str,
        name: str,
        payload: RepositoryUpdate,
    ) -> RepositoryORM:
        """admin only（caller 保证）；不存在 raise 404；只更新非 None 字段。"""
        stmt = select(RepositoryORM).where(
            RepositoryORM.owner == owner,
            RepositoryORM.name == name,
        )
        repo = (await session.execute(stmt)).scalar_one_or_none()
        if repo is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Repository {owner}/{name} 不存在",
            )

        if payload.visibility is not None:
            repo.visibility = payload.visibility
        if payload.description is not None:
            repo.description = payload.description

        await session.commit()
        await session.refresh(repo)
        return repo

    @staticmethod
    async def delete(
        session: AsyncSession,
        owner: str,
        name: str,
    ) -> bool:
        """admin only（caller 保证）；返 True 表示真删除，False 表示原本不存在。"""
        stmt = select(RepositoryORM).where(
            RepositoryORM.owner == owner,
            RepositoryORM.name == name,
        )
        repo = (await session.execute(stmt)).scalar_one_or_none()
        if repo is None:
            return False
        await session.delete(repo)
        await session.commit()
        return True
