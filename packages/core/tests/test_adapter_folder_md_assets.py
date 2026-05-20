"""FolderMdAssetsAdapter behavioral tests（AC-1 ~ AC-4）。"""

from __future__ import annotations

import pytest

import dataplat_core.adapters  # noqa: F401  触发 auto-register 副作用
from dataplat_core.adapters import FolderMdAssetsAdapter, get_default


def test_folder_md_assets_auto_registered() -> None:
    """AC-1：import 后 get_default().list_names() 含 "folder-md-assets"。"""
    names = get_default().list_names()
    assert "folder-md-assets" in names


def test_folder_md_assets_ingest_happy() -> None:
    """AC-2：happy path，doc.md + assets/img.png → file_count==2, asset_count==1。"""
    spec = {
        "files": [
            {"path": "doc.md", "sha256": "a" * 64},
            {"path": "assets/img.png", "sha256": "b" * 64},
        ]
    }
    result = FolderMdAssetsAdapter().ingest(spec, None, None)
    assert result.file_count == 2
    assert result.asset_count == 1
    assert result.files[0].path == "doc.md"
    assert result.files[1].path == "assets/img.png"
    assert result.files[1].sha256 == "b" * 64


def test_folder_md_assets_rejects_unsafe_paths() -> None:
    """AC-3：绝对路径、.. 穿越、空 path 均 raise ValueError 含 "非法相对路径"。"""
    adapter = FolderMdAssetsAdapter()

    # 绝对路径（"/abs.md" 含 .md，path safety 先生效）
    with pytest.raises(ValueError, match="非法相对路径"):
        adapter.ingest(
            {"files": [{"path": "/abs.md", "sha256": "a" * 64}]},
            None,
            None,
        )

    # .. 穿越（"../escape.md" 含 .md，path safety 先生效）
    with pytest.raises(ValueError, match="非法相对路径"):
        adapter.ingest(
            {"files": [{"path": "../escape.md", "sha256": "a" * 64}]},
            None,
            None,
        )

    # 空 path（代码层 path=="" 检查，pydantic 模型不限制空串）
    with pytest.raises(ValueError, match="非法相对路径"):
        adapter.ingest(
            {"files": [{"path": "", "sha256": "a" * 64}]},
            None,
            None,
        )


def test_folder_md_assets_requires_md() -> None:
    """AC-4：无 .md 文件 → raise ValueError 含 "至少一个 .md"。"""
    spec = {"files": [{"path": "assets/img.png", "sha256": "a" * 64}]}
    with pytest.raises(ValueError, match="至少一个 .md"):
        FolderMdAssetsAdapter().ingest(spec, None, None)
