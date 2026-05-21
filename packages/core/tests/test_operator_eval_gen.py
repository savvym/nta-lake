"""EvalGenOperator 行为测试（W4-8，AC-2）。

5 tests：
  1. happy path（合法 JSON → eval_items 含 4 选项 + answer + parse_ok=True）
  2. short_text_skip（text < 50 char → 未调 llm，1→1 仅追加 lineage_op + stats.skipped）
  3. parse_failed（非 JSON → eval_items 含 error 不抛）
  4. markdown_fence（```json wrap → 仍能解析成功）
  5. invalid_answer（answer="E" → parse_failed）

使用 inline FakeLLMClient（counter 记 call 次数）；不依赖任何外部服务。
"""

from __future__ import annotations

import json
from types import SimpleNamespace
from typing import Any

import pytest

from dataplat_core.operators.eval_gen import EvalGenOperator
from dataplat_core.protocols.llm import LLMRequest, LLMResponse
from dataplat_core.protocols.loader import SilverRow

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_VALID_EVAL_JSON = json.dumps(
    {
        "question": "这段文本的主要主题是什么？",
        "options": {
            "A": "科技发展",
            "B": "历史事件",
            "C": "自然现象",
            "D": "经济政策",
        },
        "answer": "A",
    }
)

_LONG_TEXT = "x" * 200  # 200 chars，> 50（skip 阈值）


class FakeLLMClient:
    """测试用 FakeLLMClient；call_count 记调用次数。"""

    def __init__(self, response_text: str) -> None:
        self.response_text = response_text
        self.call_count = 0

    async def call(self, req: LLMRequest) -> LLMResponse:
        self.call_count += 1
        return LLMResponse(
            text=self.response_text,
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
# Test 1: happy path
# ---------------------------------------------------------------------------


async def test_eval_gen_happy_path() -> None:
    """AC-2 happy：合法 JSON → stats.eval_items 含 1 题 4 选项 + answer='A' + lineage parse_ok=True。"""
    llm = FakeLLMClient(_VALID_EVAL_JSON)
    ctx = _make_ctx(llm)
    op = EvalGenOperator()
    row = _make_row(_LONG_TEXT)

    results = await op.run(row, {"model_id": "fake-model"}, ctx)  # type: ignore[arg-type]

    assert len(results) == 1, "始终 1→1"
    out = results[0]

    # eval_items
    eval_items = out.stats.get("eval_items", [])
    assert len(eval_items) == 1
    item = eval_items[0]
    assert item["answer"] == "A"
    assert set(item["options"].keys()) == {"A", "B", "C", "D"}
    assert "error" not in item

    # eval_gen_count 递增
    assert out.stats.get("eval_gen_count") == 1

    # lineage
    assert len(out.lineage_ops) == 1
    lop = out.lineage_ops[0]
    assert lop["op"] == "eval_gen"
    assert lop["parse_ok"] is True
    assert lop["model_id"] == "fake-model"

    # LLM 被调用 1 次
    assert llm.call_count == 1


# ---------------------------------------------------------------------------
# Test 2: short text skip
# ---------------------------------------------------------------------------


async def test_eval_gen_short_text_skip() -> None:
    """AC-2 short_text_skip：text < 50 chars → LLM 未被调用；stats.skipped='short_text'；lineage 追加。"""
    llm = FakeLLMClient(_VALID_EVAL_JSON)
    ctx = _make_ctx(llm)
    op = EvalGenOperator()
    row = _make_row("short")  # 5 chars < 50

    results = await op.run(row, {"model_id": "fake-model"}, ctx)  # type: ignore[arg-type]

    assert len(results) == 1, "始终 1→1"
    out = results[0]

    # LLM 未被调用
    assert llm.call_count == 0, f"期望 LLM call_count=0，实得 {llm.call_count}"

    # stats.skipped
    assert out.stats.get("skipped") == "short_text"

    # eval_items 不存在（未生成）
    assert "eval_items" not in out.stats

    # lineage 追加 skipped 记录
    assert len(out.lineage_ops) == 1
    lop = out.lineage_ops[0]
    assert lop["op"] == "eval_gen"
    assert lop["skipped"] == "short_text"


# ---------------------------------------------------------------------------
# Test 3: parse failure
# ---------------------------------------------------------------------------


async def test_eval_gen_parse_failed() -> None:
    """AC-2 parse_failed：LLM 返非 JSON → eval_items 含 error='parse_failed' 且不抛；eval_gen_parse_errors 递增。"""
    llm = FakeLLMClient("not json at all")
    ctx = _make_ctx(llm)
    op = EvalGenOperator()
    row = _make_row(_LONG_TEXT)

    results = await op.run(row, {"model_id": "fake-model"}, ctx)  # type: ignore[arg-type]

    assert len(results) == 1
    out = results[0]

    eval_items = out.stats.get("eval_items", [])
    assert len(eval_items) == 1
    item = eval_items[0]
    assert item["error"] == "parse_failed"
    assert "raw" in item

    # parse errors 计数
    assert out.stats.get("eval_gen_parse_errors") == 1

    # eval_gen_count 不递增
    assert out.stats.get("eval_gen_count", 0) == 0

    # lineage parse_ok=False
    lop = out.lineage_ops[0]
    assert lop["parse_ok"] is False


# ---------------------------------------------------------------------------
# Test 4: markdown fence wrapping
# ---------------------------------------------------------------------------


async def test_eval_gen_markdown_fence() -> None:
    """AC-2 markdown_fence：LLM 返 ```json...``` 包裹的合法 JSON → 仍能解析成功。"""
    fenced = f"```json\n{_VALID_EVAL_JSON}\n```"
    llm = FakeLLMClient(fenced)
    ctx = _make_ctx(llm)
    op = EvalGenOperator()
    row = _make_row(_LONG_TEXT)

    results = await op.run(row, {"model_id": "fake-model"}, ctx)  # type: ignore[arg-type]

    assert len(results) == 1
    out = results[0]

    eval_items = out.stats.get("eval_items", [])
    assert len(eval_items) == 1
    item = eval_items[0]
    assert "error" not in item
    assert item["answer"] == "A"
    assert set(item["options"].keys()) == {"A", "B", "C", "D"}

    # 解析成功
    assert out.stats.get("eval_gen_count") == 1
    assert out.lineage_ops[0]["parse_ok"] is True


# ---------------------------------------------------------------------------
# Test 5: invalid answer (not in ABCD)
# ---------------------------------------------------------------------------


async def test_eval_gen_invalid_answer() -> None:
    """AC-2 invalid_answer：answer='E' → 视为 parse_failed；eval_items 含 error 记录。"""
    bad_json = json.dumps(
        {
            "question": "题目？",
            "options": {"A": "A选项", "B": "B选项", "C": "C选项", "D": "D选项"},
            "answer": "E",  # 非法
        }
    )
    llm = FakeLLMClient(bad_json)
    ctx = _make_ctx(llm)
    op = EvalGenOperator()
    row = _make_row(_LONG_TEXT)

    results = await op.run(row, {"model_id": "fake-model"}, ctx)  # type: ignore[arg-type]

    assert len(results) == 1
    out = results[0]

    eval_items = out.stats.get("eval_items", [])
    assert len(eval_items) == 1
    item = eval_items[0]
    assert item["error"] == "parse_failed"

    assert out.stats.get("eval_gen_parse_errors") == 1
    assert out.stats.get("eval_gen_count", 0) == 0
    assert out.lineage_ops[0]["parse_ok"] is False
