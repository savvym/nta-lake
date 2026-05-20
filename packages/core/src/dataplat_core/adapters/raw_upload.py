"""RawFileUploadAdapter：把已上传的 blob refs 校验并转成 IngestResult.files
（spec adapter-framework-20260517 AC-5）。

不写 workspace、不依赖 ctx；workspace/ctx 参数类型放宽到 `| None` 让单元
测试可直接传 None。其他 adapter 应按 SourceAdapter Protocol 严类型实现。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from dataplat_core.protocols.adapter import IngestFileRef, IngestResult
from dataplat_core.protocols.runcontext import RunContext
from pydantic import BaseModel, ConfigDict


class _RawFile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str
    sha256: str


class _RawSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    files: list[_RawFile]
    asset_id: str | None = None


_INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "files": {
            "type": "array",
            "minItems": 1,
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
        "asset_id": {"type": "string"},
    },
    "required": ["files"],
    "additionalProperties": False,
}


class RawFileUploadAdapter:
    """把 (path → blob sha256) refs 转成 IngestResult.files。

    spec.files 校验失败（空 / path 重复 / sha256 非 hex） → raise ValueError，
    由 AdapterRunner 翻译为 HTTPException 400。
    """

    name: str = "raw-file-upload"
    version: str = "0.1"
    input_schema: dict[str, Any] = _INPUT_SCHEMA
    output_subtype: str = "generic"

    def ingest(
        self,
        spec: dict[str, Any],
        workspace: Path | None,  # 不使用；放宽便于单元测试
        ctx: RunContext | None,  # 不使用
    ) -> IngestResult:
        del workspace, ctx
        try:
            parsed = _RawSpec.model_validate(spec)
        except Exception as exc:  # noqa: BLE001
            raise ValueError(f"RawFileUpload spec 非法：{exc}") from exc

        if not parsed.files:
            raise ValueError("RawFileUpload spec.files 非空必需")

        seen: set[str] = set()
        for f in parsed.files:
            if f.path in seen:
                raise ValueError(f"RawFileUpload spec.files 含重复 path: {f.path}")
            seen.add(f.path)

        refs = [IngestFileRef(path=f.path, sha256=f.sha256) for f in parsed.files]
        return IngestResult(
            asset_count=1 if parsed.asset_id else 0,
            file_count=len(refs),
            files=refs,
        )
