"""EvalGenOperator：对每条 SilverRow 调 LLM 生成 1 道多选题（question + 4 options + answer）。

W4-8：bench 风格 multiple-choice eval generation。
- 首个真调 LLM 的 Operator（ctx.llm.call，非 import LLMGateway）
- parse failure 不抛；降级写 eval_items: [{"error": "parse_failed", ...}]
- short text（< skip_if_text_chars_lt）跳过 LLM 调用，1→1 仅追加 lineage_ops
- 始终 1→1

Out of scope（留 follow-up）：
  n_per_row > 1、retry on parse fail、prompt 模板从 file 加载
"""

from __future__ import annotations

import asyncio
import json
import re
from typing import Any

from dataplat_core.protocols.llm import LLMMessage, LLMRequest
from dataplat_core.protocols.loader import SilverRow
from dataplat_core.protocols.operator import OperatorSpec
from dataplat_core.protocols.runcontext import RunContext

# ---------------------------------------------------------------------------
# 默认 prompt 模板
# ---------------------------------------------------------------------------

_DEFAULT_PROMPT_TEMPLATE = """\
根据以下文本生成 1 道多选题（中文输出 JSON，禁止任何额外文字）。
要求：
- 题干 question 简洁明确
- 4 个选项 A/B/C/D 单一正确答案
- answer 是单字符 'A' 'B' 'C' 'D'
- 题目内容必须能由文本支持，不可外推

文本：
```
{text}
```

JSON schema：
{{
  "question": "string",
  "options": {{"A": "string", "B": "string", "C": "string", "D": "string"}},
  "answer": "A" | "B" | "C" | "D"
}}"""

# 合法 answer 值
_VALID_ANSWERS = {"A", "B", "C", "D"}

# markdown code fence 正则（```json ... ``` 或 ``` ... ```）
_FENCE_RE = re.compile(r"^```(?:json)?\s*\n?(.*?)\n?```\s*$", re.DOTALL)


def _strip_fence(text: str) -> str:
    """去掉 markdown code fence（如有）。"""
    stripped = text.strip()
    m = _FENCE_RE.match(stripped)
    if m:
        return m.group(1).strip()
    return stripped


def _parse_eval_item(raw_text: str) -> dict[str, Any] | None:
    """尝试将 LLM 返回文本解析为合法 eval item。

    返 None 表示解析失败；调用方负责写 error 记录。

    合法条件：
    - JSON 可解析
    - 含 question（str）、options（dict，含 A/B/C/D 四 key）、answer（A/B/C/D 之一）
    """
    try:
        cleaned = _strip_fence(raw_text)
        obj = json.loads(cleaned)
    except (json.JSONDecodeError, ValueError):
        return None

    if not isinstance(obj, dict):
        return None

    question = obj.get("question")
    options = obj.get("options")
    answer = obj.get("answer")

    if not isinstance(question, str):
        return None
    if not isinstance(options, dict):
        return None
    if set(options.keys()) != {"A", "B", "C", "D"}:
        return None
    if answer not in _VALID_ANSWERS:
        return None

    return {"question": question, "options": options, "answer": answer}


# ---------------------------------------------------------------------------
# Operator
# ---------------------------------------------------------------------------


class EvalGenOperator:
    """多选题生成算子。

    async def run：
      1. short text（< skip_if_text_chars_lt）→ skip，仅追加 lineage_ops + stats.skipped
      2. 拼 prompt → ctx.llm.call → 解析 JSON
      3. 解析成功 → stats.eval_items + eval_gen_count + lineage_op(parse_ok=True)
      4. 解析失败 → stats.eval_items[error 记录] + eval_gen_parse_errors + lineage_op(parse_ok=False)
      5. 始终返 [new_row]（1→1）
    """

    name: str = "eval_gen"
    version: str = "1.0"
    spec: OperatorSpec = OperatorSpec(
        name="eval_gen",
        version="1.0",
        config_schema={
            "type": "object",
            "properties": {
                "model_id": {
                    "type": "string",
                    "description": "LLM model id；CI 默认 fake-model（rate=0，不被 cost budget 阻断）",
                },
                "max_tokens": {
                    "type": "integer",
                    "description": "LLM 最大输出 tokens",
                },
                "prompt_template": {
                    "type": "string",
                    "description": "Prompt 模板；可用变量 {text}、{lang}",
                },
                "n_per_row": {
                    "type": "integer",
                    "description": "每行生成题目数（预留；本 change 只实现 1）",
                },
                "skip_if_text_chars_lt": {
                    "type": "integer",
                    "description": "短文本阈值（char 数）；text 长度小于此值则跳过 LLM 调用",
                },
            },
            "additionalProperties": False,
        },
    )

    async def run(
        self,
        row: SilverRow,
        config: dict[str, Any],
        ctx: RunContext,
    ) -> list[SilverRow]:
        """对 SilverRow 调 LLM 生成多选题；始终返 [new_row]（1→1）。

        Args:
            row:    输入 SilverRow（不被 mutate）。
            config: Operator 配置 dict（键见 config_schema）。
            ctx:    RunContext；ctx.llm 须满足 LLMClient Protocol（async call）。

        Returns:
            含追加 eval_items / lineage_ops / stats 的新 SilverRow 列表（长度 1）。
        """
        model_id: str = config.get("model_id", "fake-model")
        max_tokens: int = config.get("max_tokens", 512)
        prompt_template: str = config.get("prompt_template", _DEFAULT_PROMPT_TEMPLATE)
        skip_if_text_chars_lt: int = config.get("skip_if_text_chars_lt", 50)
        # n_per_row 预留字段；本 change 锁定为 1
        # n_per_row: int = config.get("n_per_row", 1)

        # ------------------------------------------------------------------
        # 1. short text skip
        # ------------------------------------------------------------------
        if len(row.text) < skip_if_text_chars_lt:
            new_row = row.model_copy(
                update={
                    "stats": {**row.stats, "skipped": "short_text"},
                    "lineage_ops": [
                        *row.lineage_ops,
                        {"op": "eval_gen", "version": "1.0", "skipped": "short_text"},
                    ],
                }
            )
            return [new_row]

        # ------------------------------------------------------------------
        # 2. 拼 prompt
        # ------------------------------------------------------------------
        lang = row.stats.get("lang") or getattr(row, "lang", None) or "unknown"
        prompt = prompt_template.format(text=row.text, lang=lang)

        # ------------------------------------------------------------------
        # 3. 构造 LLMRequest + 调用
        # ------------------------------------------------------------------
        req = LLMRequest(
            model_id=model_id,
            messages=[LLMMessage(role="user", content=prompt)],
            max_tokens=max_tokens,
        )
        resp = await ctx.llm.call(req)

        # ------------------------------------------------------------------
        # 4 & 5. 解析 + 写 stats / lineage
        # ------------------------------------------------------------------
        parsed = _parse_eval_item(resp.text)

        if parsed is not None:
            # 解析成功
            new_eval_items = list(row.stats.get("eval_items", [])) + [parsed]
            new_eval_count = row.stats.get("eval_gen_count", 0) + 1
            new_stats = {
                **row.stats,
                "eval_items": new_eval_items,
                "eval_gen_count": new_eval_count,
            }
            new_lineage = [
                *row.lineage_ops,
                {
                    "op": "eval_gen",
                    "version": "1.0",
                    "model_id": model_id,
                    "parse_ok": True,
                },
            ]
        else:
            # 解析失败；graceful 降级，不抛
            error_item: dict[str, Any] = {
                "error": "parse_failed",
                "raw": resp.text[:200],
            }
            new_eval_items = list(row.stats.get("eval_items", [])) + [error_item]
            new_parse_errors = row.stats.get("eval_gen_parse_errors", 0) + 1
            new_stats = {
                **row.stats,
                "eval_items": new_eval_items,
                "eval_gen_parse_errors": new_parse_errors,
            }
            new_lineage = [
                *row.lineage_ops,
                {
                    "op": "eval_gen",
                    "version": "1.0",
                    "model_id": model_id,
                    "parse_ok": False,
                },
            ]

        new_row = row.model_copy(
            update={
                "stats": new_stats,
                "lineage_ops": new_lineage,
            }
        )
        return [new_row]


# ---------------------------------------------------------------------------
# 模块末尾注册（与 W2-1 同模式）
# ---------------------------------------------------------------------------

from dataplat_core.operators.registry import OperatorRegistry  # noqa: E402

try:
    OperatorRegistry.register("eval_gen", EvalGenOperator)
except ValueError:
    pass  # 模块重复 import 场景
