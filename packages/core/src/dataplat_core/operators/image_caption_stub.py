"""ImageCaptionStubOperator：将 images 元数据（filename + blob_sha）拼占位符注入 text。

演示"image metadata → 文本注入"算子模式：
- images=[] 时 1→1 no-op（仅追加 lineage_ops，不改 text）
- images 非空时：对每张图片拼 template 占位符，用 separator 连接后追加到 text 末尾

LLM 真实 caption / OCR 留 operator-image-caption-llm-* / operator-image-ocr-* follow-up。
"""

from __future__ import annotations

from typing import Any

from dataplat_core.protocols.loader import SilverRow
from dataplat_core.protocols.operator import OperatorSpec
from dataplat_core.protocols.runcontext import RunContext

_DEFAULT_TEMPLATE = "[image: {filename} ({blob_sha_short})]"
_DEFAULT_SEPARATOR = "\n\n"


class ImageCaptionStubOperator:
    """图片占位符注入算子。run() 将 images 元数据拼占位符追加到 text；输入 row 不被 mutate。

    config 可选项：
    - template: 占位符模板（默认 "[image: {filename} ({blob_sha_short})]"）
      可用变量：{filename}、{blob_sha_short}（blob_sha 前 8 位）、{blob_sha}（完整）
    - separator: 连接多个 caption marker 及追加到 text 的分隔符（默认 "\\n\\n"）
    """

    name: str = "image_caption_stub"
    version: str = "1.0"
    spec: OperatorSpec = OperatorSpec(
        name="image_caption_stub",
        version="1.0",
        config_schema={
            "type": "object",
            "properties": {
                "template": {"type": "string"},
                "separator": {"type": "string"},
            },
            "additionalProperties": False,
        },
    )

    def run(
        self,
        row: SilverRow,
        config: dict[str, Any],
        ctx: RunContext,
    ) -> list[SilverRow]:
        """对 images 列表拼占位符后追加到 text；images=[] 时 no-op 仅追加 lineage_ops。

        使用 model_copy(update=...) + dict/list literal 保证不共享 stats / lineage_ops 引用。
        images 字段保留原列表（strip 是另一个 Operator 的职责）。
        """
        template = config.get("template", _DEFAULT_TEMPLATE)
        separator = config.get("separator", _DEFAULT_SEPARATOR)

        if not row.images:
            # no-op 分支：仅追加 lineage_ops，不改 text / stats / images
            new_row = row.model_copy(
                update={
                    "lineage_ops": [
                        *row.lineage_ops,
                        {"op": "image_caption_stub", "version": "1.0", "image_count": 0},
                    ],
                }
            )
            return [new_row]

        # 对每张图拼占位符（image dict 必须含 filename + blob_sha；缺失 → KeyError，v1 不兜底）
        markers = [
            template.format(
                filename=img["filename"],
                blob_sha_short=img["blob_sha"][:8],
                blob_sha=img["blob_sha"],
            )
            for img in row.images
        ]
        captions_joined = separator.join(markers)
        new_text = row.text + separator + captions_joined

        new_row = row.model_copy(
            update={
                "text": new_text,
                "stats": {**row.stats, "image_captions_added": len(row.images)},
                "lineage_ops": [
                    *row.lineage_ops,
                    {
                        "op": "image_caption_stub",
                        "version": "1.0",
                        "image_count": len(row.images),
                    },
                ],
                # images 不动：保留原列表，strip 是另一个 Operator 的职责
            }
        )
        return [new_row]
