"""packages/core cost 单元测试（W4-5 AC-2）。

4 tests（纯函数 + ledger，env-free）：
1. compute_cost 非零计算
2. fake-model rate = 0 → cost = 0
3. CostLedger.record + total_usd 累计正确
4. CostLedger.reset(scope) 清目标 scope；其他 scope 不受影响
(bonus) BudgetExceeded 携带 scope / current / limit 字段
"""

from __future__ import annotations

import asyncio

import pytest

from dataplat_core.cost import (
    BudgetExceeded,
    CostLedger,
    CostLedgerEntry,
    CostRate,
    DEFAULT_RATES,
    compute_cost,
)


# ---------------------------------------------------------------------------
# Test 1: compute_cost 非零计算
# ---------------------------------------------------------------------------


def test_compute_cost_nonzero() -> None:
    """1k input + 1k output with non-zero rate → non-zero cost."""
    rate = CostRate(
        model_id="test-model",
        input_per_1k_usd=0.003,
        output_per_1k_usd=0.015,
    )
    cost = compute_cost(rate, 1000, 1000)
    assert cost == pytest.approx(0.018, rel=1e-6)
    assert cost > 0


# ---------------------------------------------------------------------------
# Test 2: fake-model rate = 0 → cost = 0
# ---------------------------------------------------------------------------


def test_compute_cost_fake_model_zero() -> None:
    """fake-model rate = 0/0 → cost = 0；CI 不被预算阻断。"""
    rate = DEFAULT_RATES["fake-model"]
    assert rate.input_per_1k_usd == 0.0
    assert rate.output_per_1k_usd == 0.0
    cost = compute_cost(rate, 10000, 10000)
    assert cost == 0.0


# ---------------------------------------------------------------------------
# Test 3: CostLedger.record + total_usd 累计正确
# ---------------------------------------------------------------------------


def test_ledger_record_and_total_usd() -> None:
    """两次 record 后 total_usd 正确累计。"""
    ledger = CostLedger()
    rate = CostRate(model_id="test-model", input_per_1k_usd=0.003, output_per_1k_usd=0.015)

    e1 = CostLedgerEntry(
        model_id="test-model",
        input_tokens=1000,
        output_tokens=500,
        usd=compute_cost(rate, 1000, 500),
        scope="scope-a",
    )
    e2 = CostLedgerEntry(
        model_id="test-model",
        input_tokens=2000,
        output_tokens=1000,
        usd=compute_cost(rate, 2000, 1000),
        scope="scope-a",
    )

    asyncio.run(ledger.record(e1))
    asyncio.run(ledger.record(e2))

    expected = e1.usd + e2.usd
    assert ledger.total_usd("scope-a") == pytest.approx(expected, rel=1e-9)
    # 其他 scope 不受影响
    assert ledger.total_usd("scope-b") == 0.0


# ---------------------------------------------------------------------------
# Test 4: CostLedger.reset(scope) 清目标 scope；其他 scope 不受影响
# ---------------------------------------------------------------------------


def test_ledger_reset_scope_isolation() -> None:
    """reset('scope-a') 不影响 'scope-b'。"""
    ledger = CostLedger()
    rate = CostRate(model_id="test-model", input_per_1k_usd=0.003, output_per_1k_usd=0.015)

    ea = CostLedgerEntry(
        model_id="test-model",
        input_tokens=1000,
        output_tokens=1000,
        usd=compute_cost(rate, 1000, 1000),
        scope="scope-a",
    )
    eb = CostLedgerEntry(
        model_id="test-model",
        input_tokens=500,
        output_tokens=500,
        usd=compute_cost(rate, 500, 500),
        scope="scope-b",
    )

    asyncio.run(ledger.record(ea))
    asyncio.run(ledger.record(eb))

    usd_b_before = ledger.total_usd("scope-b")
    assert ledger.total_usd("scope-a") > 0

    asyncio.run(ledger.reset("scope-a"))

    assert ledger.total_usd("scope-a") == 0.0
    assert ledger.total_usd("scope-b") == pytest.approx(usd_b_before)


# ---------------------------------------------------------------------------
# Test (bonus): BudgetExceeded 携带 scope / current / limit
# ---------------------------------------------------------------------------


def test_budget_exceeded_fields() -> None:
    """BudgetExceeded 异常携带正确的 scope / current_usd / limit_usd 字段。"""
    exc = BudgetExceeded(scope="repo:abc", current_usd=0.05, limit_usd=0.04)
    assert exc.scope == "repo:abc"
    assert exc.current_usd == pytest.approx(0.05)
    assert exc.limit_usd == pytest.approx(0.04)
    assert isinstance(exc, Exception)
