"""DPOPairGenOperator：对每条 SilverRow 调 LLM 2 次（chosen / rejected）→ 写 stats.dpo_pairs。

W4-9：DPO preference pair generation。
- 串行 2 次 LLM 调用（chosen 高质量指令 / rejected 降级指令）
- 任一调用失败（exception / 空文本）→ graceful 不抛，标 pair_failed
- short text（< skip_if_text_chars_lt）跳过 LLM 调用，1→1 仅追加 lineage_ops
- 始终 1→1

Out of scope（留 follow-up）：
  asyncio.gather 并行、混合 model_id、真 prompt 抽取、retry on error
"""

from __future__ import annotations

from typing import Any

from dataplat_core.protocols.llm import LLMMessage, LLMRequest
from dataplat_core.protocols.loader import SilverRow
from dataplat_core.protocols.operator import OperatorSpec
from dataplat_core.protocols.runcontext import RunContext

# ---------------------------------------------------------------------------
# 默认 prompt 模板
# ---------------------------------------------------------------------------

_DEFAULT_PROMPT_TEMPLATE = """\
根据以下文本生成 1 个开放式问题，并给出回答。

文本：
```
{text}
```

问题（请基于文本生成一个有信息量的开放式问题，不要求选择题）：
然后请按 {instruction} 回答这个问题。"""

_DEFAULT_CHOSEN_INSTRUCTION = "请仔细阅读以上文本，写一份完整、准确、有条理的回答。"
_DEFAULT_REJECTED_INSTRUCTION = "请用简单粗暴的方式回答，可省略细节，可包含小错误。"


# ---------------------------------------------------------------------------
# Operator
# ---------------------------------------------------------------------------


class DPOPairGenOperator:
    """DPO 偏好对生成算子。

    async def run：
      1. short text（< skip_if_text_chars_lt）→ skip，仅追加 lineage_ops + stats.skipped
      2. 拼 chosen prompt → ctx.llm.call → 失败（exception / 空文本）→ 标 pair_failed=True
      3. 拼 rejected prompt → ctx.llm.call → 失败同上
      4. 任一失败 → stats.dpo_pair_failures += 1 + lineage_op(success=False, reason)
      5. 两次成功 → stats.dpo_pairs 追加 {prompt, chosen, rejected} + dpo_pair_count += 1
         + lineage_op(success=True, chosen_tokens, rejected_tokens)
      6. 始终返 [new_row]（1→1）
    """

    name: str = "dpo_pair_gen"
    version: str = "1.0"
    spec: OperatorSpec = OperatorSpec(
        name="dpo_pair_gen",
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
                    "description": "Prompt 模板；可用变量 {text}、{lang}、{instruction}",
                },
                "chosen_instruction": {
                    "type": "string",
                    "description": "高质量回答指令（chosen response 用）",
                },
                "rejected_instruction": {
                    "type": "string",
                    "description": "降级回答指令（rejected response 用）",
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
        """对 SilverRow 调 LLM 2 次生成 DPO 偏好对；始终返 [new_row]（1→1）。

        Args:
            row:    输入 SilverRow（不被 mutate）。
            config: Operator 配置 dict（键见 config_schema）。
            ctx:    RunContext；ctx.llm 须满足 LLMClient Protocol（async call）。

        Returns:
            含追加 dpo_pairs / lineage_ops / stats 的新 SilverRow 列表（长度 1）。
        """
        model_id: str = config.get("model_id", "fake-model")
        max_tokens: int = config.get("max_tokens", 512)
        prompt_template: str = config.get("prompt_template", _DEFAULT_PROMPT_TEMPLATE)
        chosen_instruction: str = config.get("chosen_instruction", _DEFAULT_CHOSEN_INSTRUCTION)
        rejected_instruction: str = config.get("rejected_instruction", _DEFAULT_REJECTED_INSTRUCTION)
        skip_if_text_chars_lt: int = config.get("skip_if_text_chars_lt", 50)

        # ------------------------------------------------------------------
        # 1. short text skip
        # ------------------------------------------------------------------
        if len(row.text) < skip_if_text_chars_lt:
            new_row = row.model_copy(
                update={
                    "stats": {**row.stats, "skipped": "short_text"},
                    "lineage_ops": [
                        *row.lineage_ops,
                        {"op": "dpo_pair_gen", "version": "1.0", "skipped": "short_text"},
                    ],
                }
            )
            return [new_row]

        # ------------------------------------------------------------------
        # 2. chosen 调用
        # ------------------------------------------------------------------
        lang = row.stats.get("lang") or getattr(row, "lang", None) or "unknown"
        chosen_prompt = prompt_template.format(
            text=row.text, lang=lang, instruction=chosen_instruction
        )
        rejected_prompt = prompt_template.format(
            text=row.text, lang=lang, instruction=rejected_instruction
        )

        pair_failed = False
        failure_reason: str = ""
        chosen_resp = None
        rejected_resp = None

        # chosen 调用
        try:
            req_chosen = LLMRequest(
                model_id=model_id,
                messages=[LLMMessage(role="user", content=chosen_prompt)],
                max_tokens=max_tokens,
            )
            chosen_resp = await ctx.llm.call(req_chosen)
            if chosen_resp.text == "":
                pair_failed = True
                failure_reason = "chosen_empty_response"
        except Exception as exc:  # noqa: BLE001
            pair_failed = True
            failure_reason = f"chosen_call_failed: {type(exc).__name__}"

        # ------------------------------------------------------------------
        # 3. rejected 调用（仅在 chosen 成功后进行）
        # ------------------------------------------------------------------
        if not pair_failed:
            try:
                req_rejected = LLMRequest(
                    model_id=model_id,
                    messages=[LLMMessage(role="user", content=rejected_prompt)],
                    max_tokens=max_tokens,
                )
                rejected_resp = await ctx.llm.call(req_rejected)
                if rejected_resp.text == "":
                    pair_failed = True
                    failure_reason = "rejected_empty_response"
            except Exception as exc:  # noqa: BLE001
                pair_failed = True
                failure_reason = f"rejected_call_failed: {type(exc).__name__}"

        # ------------------------------------------------------------------
        # 4 & 5. 写 stats / lineage
        # ------------------------------------------------------------------
        if pair_failed:
            new_failures = row.stats.get("dpo_pair_failures", 0) + 1
            new_stats = {
                **row.stats,
                "dpo_pair_failures": new_failures,
            }
            new_lineage = [
                *row.lineage_ops,
                {
                    "op": "dpo_pair_gen",
                    "version": "1.0",
                    "model_id": model_id,
                    "success": False,
                    "reason": failure_reason,
                },
            ]
        else:
            # 两次调用均成功（chosen_resp / rejected_resp 非 None）
            assert chosen_resp is not None and rejected_resp is not None  # mypy / type narrowing
            pair_entry = {
                "prompt": row.text[:200],
                "chosen": chosen_resp.text,
                "rejected": rejected_resp.text,
            }
            new_pairs = list(row.stats.get("dpo_pairs", [])) + [pair_entry]
            new_pair_count = row.stats.get("dpo_pair_count", 0) + 1
            new_stats = {
                **row.stats,
                "dpo_pairs": new_pairs,
                "dpo_pair_count": new_pair_count,
            }
            new_lineage = [
                *row.lineage_ops,
                {
                    "op": "dpo_pair_gen",
                    "version": "1.0",
                    "model_id": model_id,
                    "success": True,
                    "chosen_tokens": chosen_resp.output_tokens,
                    "rejected_tokens": rejected_resp.output_tokens,
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
# 模块末尾注册（与 W4-8 eval_gen 同模式）
# ---------------------------------------------------------------------------

from dataplat_core.operators.registry import OperatorRegistry  # noqa: E402

try:
    OperatorRegistry.register("dpo_pair_gen", DPOPairGenOperator)
except ValueError:
    pass  # 模块重复 import 场景
