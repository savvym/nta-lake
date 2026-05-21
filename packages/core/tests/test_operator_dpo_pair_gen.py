"""DPOPairGenOperator 行为测试（W4-9，AC-1 + AC-2）。

6 tests：
  1. test_registry_lookup（AC-1 静态：registry 能取到 DPOPairGenOperator）
  2. test_dpo_happy_path（2 次成功 → stats.dpo_pairs 含 1 entry + prompt/chosen/rejected）
  3. test_dpo_short_text_skip（text < 50 → LLM 未调用，stats.skipped='short_text'）
  4. test_dpo_chosen_failure（第 1 次 exception → 不抛 + failures=1 + lineage success=False）
  5. test_dpo_rejected_failure（第 2 次 exception → 同上）
  6. test_dpo_empty_response（chosen 返 text="" → 视失败 + failures=1）

使用 inline FakeLLMClient（sequence-aware；call_count 记调用次数）；不依赖任何外部服务。
"""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from dataplat_core.operators.dpo_pair_gen import DPOPairGenOperator
from dataplat_core.operators.registry import OperatorRegistry
from dataplat_core.protocols.llm import LLMRequest, LLMResponse
from dataplat_core.protocols.loader import SilverRow

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_LONG_TEXT = "这是一段足够长的测试文本，用于触发 LLM 调用。" * 5  # >> 50 chars
_SHORT_TEXT = "短"  # 1 char < 50


class FakeLLMClient:
    """Sequence-aware FakeLLMClient。

    responses: 按调用顺序返回（list）；若为 Exception 则抛出。
    call_count 累计调用次数。
    """

    def __init__(self, responses: list[Any]) -> None:
        self.responses = list(responses)
        self.call_count = 0

    async def call(self, req: LLMRequest) -> LLMResponse:
        idx = self.call_count
        self.call_count += 1
        resp = self.responses[idx]
        if isinstance(resp, Exception):
            raise resp
        return LLMResponse(
            text=resp,
            model_id=req.model_id,
            input_tokens=10,
            output_tokens=20,
        )


def _make_row(text: str, stats: dict[str, Any] | None = None) -> SilverRow:
    return SilverRow(
        text=text,
        source_ref={"blob_sha": "abc123", "loader": "test"},
        stats=stats or {},
    )


def _make_ctx(llm: FakeLLMClient) -> object:
    return SimpleNamespace(
        logger=None,
        metrics=None,
        secrets=None,
        cancel_event=None,
        llm=llm,
    )


# ---------------------------------------------------------------------------
# Test 1: registry lookup
# ---------------------------------------------------------------------------


def test_registry_lookup() -> None:
    """AC-1：OperatorRegistry.get('dpo_pair_gen') 返回 DPOPairGenOperator 类。"""
    # 需确保 dpo_pair_gen 模块已 import（__init__.py 或 dpo_pair_gen 模块末尾注册）
    import dataplat_core.operators  # noqa: F401  触发 __init__.py 注册

    cls = OperatorRegistry.get("dpo_pair_gen")
    assert cls is DPOPairGenOperator


# ---------------------------------------------------------------------------
# Test 2: happy path
# ---------------------------------------------------------------------------


async def test_dpo_happy_path() -> None:
    """AC-2 happy：2 次成功 → stats.dpo_pairs 含 1 entry，prompt/chosen/rejected 齐全。"""
    chosen_text = "这是一份完整、准确、有条理的高质量回答。"
    rejected_text = "随便说说，细节略了。"
    llm = FakeLLMClient([chosen_text, rejected_text])
    ctx = _make_ctx(llm)
    op = DPOPairGenOperator()
    row = _make_row(_LONG_TEXT)

    results = await op.run(row, {"model_id": "fake-model"}, ctx)  # type: ignore[arg-type]

    assert len(results) == 1, "始终 1→1"
    out = results[0]

    # LLM 被调用 2 次
    assert llm.call_count == 2, f"期望 2 次 LLM 调用，实得 {llm.call_count}"

    # dpo_pairs 含 1 entry
    dpo_pairs = out.stats.get("dpo_pairs", [])
    assert len(dpo_pairs) == 1
    pair = dpo_pairs[0]
    assert "prompt" in pair
    assert "chosen" in pair
    assert "rejected" in pair
    assert pair["chosen"] == chosen_text
    assert pair["rejected"] == rejected_text
    assert pair["prompt"] == _LONG_TEXT[:200]

    # dpo_pair_count 递增
    assert out.stats.get("dpo_pair_count") == 1

    # dpo_pair_failures 不变
    assert out.stats.get("dpo_pair_failures", 0) == 0

    # lineage
    assert len(out.lineage_ops) == 1
    lop = out.lineage_ops[0]
    assert lop["op"] == "dpo_pair_gen"
    assert lop["success"] is True
    assert lop["model_id"] == "fake-model"
    assert "chosen_tokens" in lop
    assert "rejected_tokens" in lop


# ---------------------------------------------------------------------------
# Test 3: short text skip
# ---------------------------------------------------------------------------


async def test_dpo_short_text_skip() -> None:
    """AC-2 short_text_skip：text < 50 chars → LLM 未被调用；stats.skipped='short_text'。"""
    llm = FakeLLMClient(["never called 1", "never called 2"])
    ctx = _make_ctx(llm)
    op = DPOPairGenOperator()
    row = _make_row(_SHORT_TEXT)

    results = await op.run(row, {"model_id": "fake-model"}, ctx)  # type: ignore[arg-type]

    assert len(results) == 1, "始终 1→1"
    out = results[0]

    # LLM 未被调用
    assert llm.call_count == 0, f"期望 LLM call_count=0，实得 {llm.call_count}"

    # stats.skipped
    assert out.stats.get("skipped") == "short_text"

    # dpo_pairs 不存在
    assert "dpo_pairs" not in out.stats
    assert "dpo_pair_count" not in out.stats

    # lineage 追加 skipped 记录
    assert len(out.lineage_ops) == 1
    lop = out.lineage_ops[0]
    assert lop["op"] == "dpo_pair_gen"
    assert lop["skipped"] == "short_text"


# ---------------------------------------------------------------------------
# Test 4: chosen failure
# ---------------------------------------------------------------------------


async def test_dpo_chosen_failure() -> None:
    """AC-2 chosen_failure：第 1 次 LLM 调用抛 exception → 不抛 + failures=1 + lineage success=False。"""
    llm = FakeLLMClient([RuntimeError("chosen LLM error")])
    ctx = _make_ctx(llm)
    op = DPOPairGenOperator()
    row = _make_row(_LONG_TEXT)

    # 不应抛异常
    results = await op.run(row, {"model_id": "fake-model"}, ctx)  # type: ignore[arg-type]

    assert len(results) == 1, "始终 1→1"
    out = results[0]

    # LLM 仅被调用 1 次（chosen 失败后 rejected 不调）
    assert llm.call_count == 1, f"期望 1 次 LLM 调用，实得 {llm.call_count}"

    # dpo_pairs 不追加
    assert "dpo_pairs" not in out.stats
    assert out.stats.get("dpo_pair_count", 0) == 0

    # failures 计数
    assert out.stats.get("dpo_pair_failures") == 1

    # lineage success=False
    assert len(out.lineage_ops) == 1
    lop = out.lineage_ops[0]
    assert lop["op"] == "dpo_pair_gen"
    assert lop["success"] is False
    assert "reason" in lop


# ---------------------------------------------------------------------------
# Test 5: rejected failure
# ---------------------------------------------------------------------------


async def test_dpo_rejected_failure() -> None:
    """AC-2 rejected_failure：第 2 次 LLM 调用抛 exception → 不抛 + failures=1 + lineage success=False。"""
    chosen_text = "这是一份完整的回答。"
    llm = FakeLLMClient([chosen_text, RuntimeError("rejected LLM error")])
    ctx = _make_ctx(llm)
    op = DPOPairGenOperator()
    row = _make_row(_LONG_TEXT)

    # 不应抛异常
    results = await op.run(row, {"model_id": "fake-model"}, ctx)  # type: ignore[arg-type]

    assert len(results) == 1, "始终 1→1"
    out = results[0]

    # LLM 被调用 2 次（chosen 成功，rejected 失败）
    assert llm.call_count == 2, f"期望 2 次 LLM 调用，实得 {llm.call_count}"

    # dpo_pairs 不追加
    assert "dpo_pairs" not in out.stats
    assert out.stats.get("dpo_pair_count", 0) == 0

    # failures 计数
    assert out.stats.get("dpo_pair_failures") == 1

    # lineage success=False
    assert len(out.lineage_ops) == 1
    lop = out.lineage_ops[0]
    assert lop["op"] == "dpo_pair_gen"
    assert lop["success"] is False
    assert "reason" in lop


# ---------------------------------------------------------------------------
# Test 6: empty response (视为失败)
# ---------------------------------------------------------------------------


async def test_dpo_empty_response() -> None:
    """AC-2 empty_response：chosen 返 text='' → 视为失败，failures=1，不追 dpo_pairs。"""
    llm = FakeLLMClient([""])  # chosen 返空字符串
    ctx = _make_ctx(llm)
    op = DPOPairGenOperator()
    row = _make_row(_LONG_TEXT)

    results = await op.run(row, {"model_id": "fake-model"}, ctx)  # type: ignore[arg-type]

    assert len(results) == 1, "始终 1→1"
    out = results[0]

    # chosen 空响应后 rejected 不调（pair_failed 已标）
    assert llm.call_count == 1, f"期望 1 次 LLM 调用，实得 {llm.call_count}"

    # dpo_pairs 不追加
    assert "dpo_pairs" not in out.stats
    assert out.stats.get("dpo_pair_count", 0) == 0

    # failures 计数
    assert out.stats.get("dpo_pair_failures") == 1

    # lineage success=False
    assert len(out.lineage_ops) == 1
    lop = out.lineage_ops[0]
    assert lop["op"] == "dpo_pair_gen"
    assert lop["success"] is False
    assert "reason" in lop
