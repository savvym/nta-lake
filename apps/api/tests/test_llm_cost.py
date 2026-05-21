"""LLMGateway + CostController 集成测试（W4-5 AC-2/AC-3）。

3 tests（env-free，走 FakeLLMProvider + test-model rate；无 DB / Redis 依赖）：
1. test_gateway_records_cost_to_ledger
   FakeLLMProvider + CostController(test-model) 跑 3 次 → ledger.total_usd > 0
2. test_gateway_raises_budget_exceeded（AC-3）
   预算 0.0001 USD + 跑到累计 > 限额 → 下一次 raise BudgetExceeded
   scope / current / limit 字段正确
3. test_gateway_no_budget_never_raises
   预算 None → 反复跑不 raise
"""

from __future__ import annotations

import asyncio

import pytest

from dataplat_core.cost import (
    BudgetExceeded,
    CostRate,
    DEFAULT_RATES,
    compute_cost,
)
from dataplat_core.protocols.llm import LLMMessage, LLMRequest
from dataplat_api.llm.cost import CostController
from dataplat_api.llm.gateway import LLMGateway
from dataplat_api.llm.providers.fake import FakeLLMProvider


# test-model: non-zero rate，已在 DEFAULT_RATES 中
_TEST_RATES = DEFAULT_RATES  # 含 "test-model"


def _make_req(n: int = 0) -> LLMRequest:
    """构造唯一 req（不同 seed 保证不同 cache key；cache=None 时无意义但保持一致）。"""
    return LLMRequest(
        model_id="test-model",
        messages=[LLMMessage(role="user", content=f"hello {n}")],
        max_tokens=64,
        seed=n,
    )


# ---------------------------------------------------------------------------
# Test 1: ledger 记账正确
# ---------------------------------------------------------------------------


def test_gateway_records_cost_to_ledger() -> None:
    """FakeLLMProvider + test-model + CostController；3 次调用后 total_usd > 0。"""
    ctrl = CostController()
    gw = LLMGateway(
        provider=FakeLLMProvider(),
        cache=None,
        max_retries=0,
        cost=ctrl,
        rates=_TEST_RATES,
        scope="test-scope",
    )

    for i in range(3):
        asyncio.run(gw.call(_make_req(i)))

    total = ctrl.total_usd("test-scope")
    assert total > 0, f"expected cost > 0, got {total}"


# ---------------------------------------------------------------------------
# Test 2: 预算 0.0001 USD → 超额 raise BudgetExceeded（AC-3）
# ---------------------------------------------------------------------------


def test_gateway_raises_budget_exceeded() -> None:
    """预算 0.0001 USD；跑到累计超过后下一次 raise BudgetExceeded。

    验证：BudgetExceeded.scope / .current_usd / .limit_usd 字段正确。
    """
    limit = 0.0001
    scope = "test-budget-scope"
    ctrl = CostController()
    ctrl.set_budget(scope, limit)
    gw = LLMGateway(
        provider=FakeLLMProvider(),
        cache=None,
        max_retries=0,
        cost=ctrl,
        rates=_TEST_RATES,
        scope=scope,
    )

    # 持续调用直到超额（max 200 次防死循环）
    raised: BudgetExceeded | None = None
    for i in range(200):
        try:
            asyncio.run(gw.call(_make_req(i)))
        except BudgetExceeded as exc:
            raised = exc
            break

    assert raised is not None, "Expected BudgetExceeded to be raised"
    assert raised.scope == scope
    assert raised.limit_usd == pytest.approx(limit)
    assert raised.current_usd >= 0.0
    # 现有 current + projected > limit 触发；current 不一定 > limit（预检用估算上界）
    assert raised.current_usd + compute_cost(
        _TEST_RATES["test-model"], 64, 64
    ) > limit


# ---------------------------------------------------------------------------
# Test 3: 预算 None → 永远不 raise
# ---------------------------------------------------------------------------


def test_gateway_no_budget_never_raises() -> None:
    """scope 无预算限制 → 跑 20 次不 raise。"""
    ctrl = CostController()
    # 不调 set_budget → None
    gw = LLMGateway(
        provider=FakeLLMProvider(),
        cache=None,
        max_retries=0,
        cost=ctrl,
        rates=_TEST_RATES,
        scope="unbounded-scope",
    )

    for i in range(20):
        asyncio.run(gw.call(_make_req(i)))

    # 不 raise 即通过
    assert ctrl.total_usd("unbounded-scope") >= 0
