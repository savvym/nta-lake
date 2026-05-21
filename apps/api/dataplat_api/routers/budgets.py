"""Budget 路由（W4-5）：per-repo LLM cost budget 管理。

端点（admin only）：
- POST   /repos/{owner}/{name}/llm-budget  → 设 / 更新预算
- GET    /repos/{owner}/{name}/llm-budget  → 查询当前用量 + breakdown
- DELETE /repos/{owner}/{name}/llm-budget  → 清预算 + reset ledger

scope 编码：`repo:{repo_id}`（uuid str）。
"""

from __future__ import annotations

from dataplat_core.protocols.auth import AuthenticatedUser
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from dataplat_api.auth.deps import require_admin
from dataplat_api.db import get_session
from dataplat_api.llm.cost import get_cost_controller
from dataplat_api.schemas.budget import (
    BudgetBreakdownItem,
    BudgetDeleteResponse,
    BudgetResponse,
    BudgetSetBody,
)
from dataplat_api.services.repo import RepoService

router = APIRouter(prefix="/repos", tags=["budgets"])


def _scope(repo_id: str) -> str:
    """scope 编码：`repo:{repo_id}`。"""
    return f"repo:{repo_id}"


async def _get_repo_or_404(
    owner: str,
    name: str,
    session: AsyncSession,
    current_user: AuthenticatedUser,
):
    repo = await RepoService.get_by_owner_name(session, owner, name, current_user)
    if repo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository {owner}/{name} 不存在",
        )
    return repo


@router.post(
    "/{owner}/{name}/llm-budget",
    response_model=BudgetResponse,
    status_code=status.HTTP_200_OK,
)
async def set_budget(
    owner: str,
    name: str,
    body: BudgetSetBody,
    _admin: AuthenticatedUser = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> BudgetResponse:
    """设或更新 repo 的月度 LLM 预算。"""
    repo = await _get_repo_or_404(owner, name, session, _admin)
    scope = _scope(str(repo.id))
    ctrl = get_cost_controller()
    ctrl.set_budget(scope, body.limit_usd)
    current = ctrl.total_usd(scope)
    breakdown = [BudgetBreakdownItem(**item) for item in ctrl.breakdown(scope)]
    return BudgetResponse(
        scope=scope,
        limit_usd=body.limit_usd,
        current_usd=current,
        breakdown=breakdown,
    )


@router.get(
    "/{owner}/{name}/llm-budget",
    response_model=BudgetResponse,
)
async def get_budget(
    owner: str,
    name: str,
    _admin: AuthenticatedUser = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> BudgetResponse:
    """查询 repo 当前 LLM 用量 + 预算。"""
    repo = await _get_repo_or_404(owner, name, session, _admin)
    scope = _scope(str(repo.id))
    ctrl = get_cost_controller()
    limit = ctrl.get_budget(scope)
    current = ctrl.total_usd(scope)
    breakdown = [BudgetBreakdownItem(**item) for item in ctrl.breakdown(scope)]
    return BudgetResponse(
        scope=scope,
        limit_usd=limit,
        current_usd=current,
        breakdown=breakdown,
    )


@router.delete(
    "/{owner}/{name}/llm-budget",
    response_model=BudgetDeleteResponse,
    status_code=status.HTTP_200_OK,
)
async def delete_budget(
    owner: str,
    name: str,
    _admin: AuthenticatedUser = Depends(require_admin),
    session: AsyncSession = Depends(get_session),
) -> BudgetDeleteResponse:
    """清 repo 的预算限制 + reset ledger（进程内）。"""
    repo = await _get_repo_or_404(owner, name, session, _admin)
    scope = _scope(str(repo.id))
    ctrl = get_cost_controller()
    await ctrl.reset(scope)
    return BudgetDeleteResponse(scope=scope, cleared=True)
