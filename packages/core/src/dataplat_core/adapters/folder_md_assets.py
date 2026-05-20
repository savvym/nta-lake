"""FolderMdAssetsAdapter：把已上传 markdown + 素材的 blob refs 校验并转成 IngestResult.files
（spec adapter-folder-md-assets-20260520 AC-1~4）。

结构有意义：至少 1 个 .md 文件；路径必须相对（拒绝 `..` / 绝对路径 / 空）；
asset_count = 非 .md 文件数。

不写 workspace、不依赖 ctx；workspace/ctx 参数类型放宽到 `| None` 让单元
测试可直接传 None。其他 adapter 应按 SourceAdapter Protocol 严类型实现。
"""

from __future__ import annotations

from pathlib import Path, PurePosixPath
from typing import Any

from dataplat_core.protocols.adapter import IngestFileRef, IngestResult
from dataplat_core.protocols.runcontext import RunContext
from pydantic import BaseModel, ConfigDict


class _FolderMdFile(BaseModel):
    model_config = ConfigDict(extra="forbid")

    path: str
    sha256: str


class _FolderMdSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    files: list[_FolderMdFile]
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


class FolderMdAssetsAdapter:
    """把 (path → blob sha256) refs 转成 IngestResult.files，要求至少 1 个 .md。

    spec.files 校验失败（path 安全检查 / path 重复 / 无 .md） → raise ValueError，
    由 AdapterRunner 翻译为 HTTPException 400。

    asset_count = 非 .md 文件数；file_count = len(files)。
    """

    name: str = "folder-md-assets"
    version: str = "0.1"
    output_subtype: str = "folder-md-assets"
    input_schema: dict[str, Any] = _INPUT_SCHEMA

    def ingest(
        self,
        spec: dict[str, Any],
        workspace: Path | None,  # 不使用；放宽便于单元测试
        ctx: RunContext | None,  # 不使用
    ) -> IngestResult:
        del workspace, ctx
        try:
            parsed = _FolderMdSpec.model_validate(spec)
        except Exception as exc:  # noqa: BLE001
            raise ValueError(f"FolderMdAssets spec 非法：{exc}") from exc

        files = parsed.files

        # 1. path safety（先遍历，按顺序抛第一个违规）
        for f in files:
            path = f.path
            if (
                path == ""
                or path.startswith("/")
                or ".." in PurePosixPath(path).parts
            ):
                raise ValueError(f"FolderMdAssets 非法相对路径: {path!r}")

        # 2. 重复 path
        seen: set[str] = set()
        for f in files:
            if f.path in seen:
                raise ValueError(f"FolderMdAssets spec.files 含重复 path: {f.path}")
            seen.add(f.path)

        # 3. 至少 1 个 .md
        md_count = sum(1 for f in files if f.path.lower().endswith(".md"))
        if md_count < 1:
            raise ValueError("FolderMdAssets spec.files 至少一个 .md 文件必需")

        refs = [IngestFileRef(path=f.path, sha256=f.sha256) for f in files]
        asset_count = len(files) - md_count
        return IngestResult(
            asset_count=asset_count,
            file_count=len(refs),
            files=refs,
        )
