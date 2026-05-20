"""JsonlImportAdapter：把已上传 .jsonl / .jsonl.gz 整文件 blob refs 校验并转成 IngestResult.files
（spec adapter-jsonl-import-20260520 AC-1~4）。

强制单文件（maxItems=1）；path 必须以 .jsonl 或 .jsonl.gz 结尾；
可选 line_count 透传到 IngestResult.notes（loader-jsonl W3-6 用得上）。

不写 workspace、不依赖 ctx；workspace/ctx 参数类型放宽到 `| None` 让单元
测试可直接传 None。其他 adapter 应按 SourceAdapter Protocol 严类型实现。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from dataplat_core.protocols.adapter import IngestFileRef, IngestResult
from dataplat_core.protocols.runcontext import RunContext
from pydantic import BaseModel, ConfigDict


class _JsonlImportFile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str
    sha256: str


class _JsonlImportSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    files: list[_JsonlImportFile]
    line_count: int | None = None


_INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "files": {
            "type": "array",
            "minItems": 1,
            "maxItems": 1,
            "items": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "minLength": 1},
                    "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                },
                "required": ["path", "sha256"],
                "additionalProperties": False,
            },
        },
        "line_count": {"type": "integer", "minimum": 0},
    },
    "required": ["files"],
    "additionalProperties": False,
}


class JsonlImportAdapter:
    """把单个 .jsonl / .jsonl.gz blob ref 转成 IngestResult.files。

    spec.files 校验失败（非单文件 / 非 .jsonl 后缀）→ raise ValueError，
    由 AdapterRunner 翻译为 HTTPException 400。

    line_count 若提供，透传到 IngestResult.notes = "line_count=N"。
    """

    name: str = "jsonl-import"
    version: str = "0.1"
    output_subtype: str = "jsonl"
    input_schema: dict[str, Any] = _INPUT_SCHEMA

    def ingest(
        self,
        spec: dict[str, Any],
        workspace: Path | None,  # 不使用；放宽便于单元测试
        ctx: RunContext | None,  # 不使用
    ) -> IngestResult:
        del workspace, ctx
        try:
            parsed = _JsonlImportSpec.model_validate(spec)
        except Exception as exc:  # noqa: BLE001
            raise ValueError(f"JsonlImport spec 非法：{exc}") from exc

        # 防御性 assert：即使 schema 已限 maxItems=1，实现也再做一次防 schema 漂移
        if len(parsed.files) != 1:
            raise ValueError(
                f"JsonlImport spec 非法：需恰好 1 个文件，实际 {len(parsed.files)} 个"
            )

        f = parsed.files[0]
        path = f.path

        # path 后缀校验
        if not path.lower().endswith((".jsonl", ".jsonl.gz")):
            raise ValueError(
                f"JsonlImport spec.files[0].path 必须以 .jsonl 或 .jsonl.gz 结尾: {path}"
            )

        notes: str | None = None
        if parsed.line_count is not None:
            notes = f"line_count={parsed.line_count}"

        return IngestResult(
            asset_count=0,
            file_count=1,
            files=[IngestFileRef(path=f.path, sha256=f.sha256)],
            notes=notes,
        )
