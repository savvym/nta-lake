"""Budget API schemas（W4-5）。"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class BudgetSetBody(BaseModel):
    """POST /repos/{owner}/{name}/llm-budget 请求体。"""

    model_config = ConfigDict(extra="forbid")

    limit_usd: float = Field(..., ge=0, description="月度预算上限（USD）；0 = 立即超额")
    reset_window: str = Field(
        "monthly",
        description="预留字段；当前仅 'monthly'；进程重启即清，真月度重置是 follow-up",
    )


class BudgetBreakdownItem(BaseModel):
    """单个 model_id 的用量汇总。"""

    model_config = ConfigDict(extra="forbid")

    model_id: str
    input_tokens: int
    output_tokens: int
    usd: float


class BudgetResponse(BaseModel):
    """POST / GET /repos/{owner}/{name}/llm-budget 响应体。"""

    model_config = ConfigDict(extra="forbid")

    scope: str
    limit_usd: float | None
    current_usd: float
    breakdown: list[BudgetBreakdownItem] = Field(default_factory=list)


class BudgetDeleteResponse(BaseModel):
    """DELETE /repos/{owner}/{name}/llm-budget 响应体。"""

    model_config = ConfigDict(extra="forbid")

    scope: str
    cleared: bool
