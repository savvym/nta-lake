"""LLMQAGenProcessor：silver text-corpus → gold sft 数据集（design.md §2.3 / §3.3）。

对上游 .md/.txt/.markdown 文件逐个调 ctx.llm.call N 次（spec.records_per_doc），
要求 LLM 返回 `{prompt, response}` JSON；解析容错三层：
1. json.loads 直接成功
2. 提 ```json ... ``` 代码块再 json.loads
3. fallback：把 LLM raw text 当 response，固定 prompt 占位

所有 records 拼接成 `sft.jsonl` 单文件 blob（每行一条 JSON 对象，含 prompt /
response / meta）。
"""

from __future__ import annotations

import asyncio
import json
import re
from io import BytesIO
from pathlib import Path
from typing import Any

from dataplat_core.protocols.adapter import IngestFileRef
from dataplat_core.protocols.llm import LLMMessage, LLMRequest
from dataplat_core.protocols.processor import (
    ProcessResult,
    RepoSelector,
    RepoSpec,
    RepoView,
)
from dataplat_core.protocols.runcontext import RunContext
from pydantic import BaseModel, ConfigDict

_TEXT_SUFFIXES = (".md", ".txt", ".markdown")
_DEFAULT_MODEL = "claude-haiku-4-5-20251001"
_DEFAULT_MAX_TOKENS = 512
_DEFAULT_TEXT_TRUNCATE = 6000
_DEFAULT_PROMPT_TEMPLATE = (
    "Read the following text and generate {n} high-quality QA pair(s) as a "
    "JSON object with keys 'prompt' and 'response'. Output JSON only. "
    "Text:\n\n{text}"
)

_CODE_BLOCK_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)


class LLMQAGenSpec(BaseModel):
    """llm-qa-gen 配置。"""

    model_config = ConfigDict(extra="forbid")

    records_per_doc: int = 1
    prompt_template: str = _DEFAULT_PROMPT_TEMPLATE
    model_id: str = _DEFAULT_MODEL
    max_tokens: int = _DEFAULT_MAX_TOKENS
    text_truncate: int = _DEFAULT_TEXT_TRUNCATE


_INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "records_per_doc": {"type": "integer", "minimum": 1},
        "prompt_template": {"type": "string"},
        "model_id": {"type": "string"},
        "max_tokens": {"type": "integer", "minimum": 1},
        "text_truncate": {"type": "integer", "minimum": 1},
    },
    "additionalProperties": False,
}


def _parse_qa_response(text: str) -> dict[str, str]:
    """三层 fallback 解析 LLM 输出为 {prompt, response} dict。"""
    stripped = text.strip()
    # 1. 直接 json.loads
    try:
        obj = json.loads(stripped)
        if isinstance(obj, dict) and "prompt" in obj and "response" in obj:
            return {"prompt": str(obj["prompt"]), "response": str(obj["response"])}
    except (json.JSONDecodeError, TypeError):
        pass
    # 2. 提 ```json ... ``` 代码块
    m = _CODE_BLOCK_RE.search(text)
    if m:
        try:
            obj = json.loads(m.group(1))
            if isinstance(obj, dict) and "prompt" in obj and "response" in obj:
                return {
                    "prompt": str(obj["prompt"]),
                    "response": str(obj["response"]),
                }
        except (json.JSONDecodeError, TypeError):
            pass
    # 3. fallback：返 raw 作 response
    return {
        "prompt": "Summarize the following text.",
        "response": stripped[:1000],
    }


class LLMQAGenProcessor:
    """无 state；调 ctx.llm 多次生成 sft.jsonl。"""

    name: str = "llm-qa-gen"
    version: str = "0.1"
    config_schema: dict[str, Any] = _INPUT_SCHEMA
    accepts: list[RepoSelector] = [RepoSelector()]
    produces: RepoSpec = RepoSpec(layer="gold", subtype="sft")

    def run(
        self,
        inputs: list[RepoView],
        config: dict[str, Any],
        workspace: Path,
        ctx: RunContext,
    ) -> ProcessResult:
        del workspace
        try:
            parsed = LLMQAGenSpec.model_validate(config)
        except Exception as exc:  # noqa: BLE001
            raise ValueError(f"LLMQAGenSpec 非法：{exc}") from exc

        if not inputs:
            raise ValueError("llm-qa-gen 需至少 1 个上游 RepoView")
        llm = getattr(ctx, "llm", None)
        if llm is None:
            raise ValueError("llm-qa-gen 需 ctx.llm；ProcessorRunner 未注入 gateway")
        blob_store = getattr(ctx, "blob_store", None)
        if blob_store is None:
            raise ValueError("llm-qa-gen 需 ctx.blob_store；ProcessorRunner 未注入")

        view = inputs[0]
        all_paths = list(view.iter_paths())  # type: ignore[attr-defined]
        paths = [p for p in all_paths if p.lower().endswith(_TEXT_SUFFIXES)]
        if not paths:
            raise ValueError(
                f"llm-qa-gen 上游无 .md/.txt/.markdown 文件（共 {len(all_paths)} 个）"
            )

        # 同步预读所有 .md 文件（在线程里调；view.open 内部 asyncio.run 合法）；
        # 之后的 asyncio.run(_run_all) 才不会嵌套到 view.open 的事件循环。
        texts: list[tuple[str, str]] = []
        for path in paths:
            stream = view.open(path)
            raw = stream.read() if hasattr(stream, "read") else b"".join(stream)
            if not isinstance(raw, bytes):
                raw = bytes(raw)
            texts.append((path, raw.decode("utf-8", errors="replace")))

        records, size, sha = asyncio.run(
            _run_all(texts, parsed, llm, blob_store)
        )
        return ProcessResult(
            record_count=records,
            file_count=1,
            bytes_written=size,
            notes=(
                f"llm-qa-gen: {len(paths)} docs × {parsed.records_per_doc} records "
                f"= {records} sft entries (model={parsed.model_id})"
            ),
            files=[IngestFileRef(path="sft.jsonl", sha256=sha)],
        )


async def _run_all(
    texts: list[tuple[str, str]],
    parsed: LLMQAGenSpec,
    llm: Any,
    blob_store: Any,
) -> tuple[int, int, str]:
    records: list[dict[str, Any]] = []
    for path, text in texts:
        for i in range(parsed.records_per_doc):
            prompt_text = parsed.prompt_template.format(
                text=text[: parsed.text_truncate], n=parsed.records_per_doc
            )
            resp = await llm.call(
                LLMRequest(
                    model_id=parsed.model_id,
                    messages=[LLMMessage(role="user", content=prompt_text)],
                    max_tokens=parsed.max_tokens,
                )
            )
            qa = _parse_qa_response(resp.text)
            qa["meta"] = json.dumps(
                {"source_path": path, "model_id": parsed.model_id, "idx": i}
            )
            records.append(qa)

    jsonl_text = (
        "\n".join(json.dumps(r, ensure_ascii=False) for r in records) + "\n"
    )
    jsonl_bytes = jsonl_text.encode("utf-8")
    put = await blob_store.put(BytesIO(jsonl_bytes), declared_size=len(jsonl_bytes))
    return len(records), put.size, put.sha256
