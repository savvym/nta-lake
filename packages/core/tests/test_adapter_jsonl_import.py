"""JsonlImportAdapter behavioral tests (adapter-jsonl-import-20260520 AC-1~4)."""

import pytest

import dataplat_core.adapters  # noqa: F401 — side-effect: auto-register
from dataplat_core.adapters import JsonlImportAdapter, get_default


def test_jsonl_import_auto_registered() -> None:
    """AC-1: import dataplat_core.adapters 后 get_default().list_names() 含 "jsonl-import"."""
    assert "jsonl-import" in get_default().list_names()


def test_jsonl_import_ingest_happy() -> None:
    """AC-2: happy path 含 line_count，返回正确 IngestResult。"""
    spec = {
        "files": [{"path": "data.jsonl", "sha256": "a" * 64}],
        "line_count": 1000,
    }
    result = JsonlImportAdapter().ingest(spec, None, None)
    assert result.file_count == 1
    assert result.asset_count == 0
    assert result.files[0].path == "data.jsonl"
    assert result.files[0].sha256 == "a" * 64
    assert result.notes == "line_count=1000"


def test_jsonl_import_rejects_non_jsonl() -> None:
    """AC-3: 非 .jsonl 后缀 → ValueError 含 ".jsonl 或 .jsonl.gz"。"""
    spec = {"files": [{"path": "data.csv", "sha256": "a" * 64}]}
    with pytest.raises(ValueError, match=r"\.jsonl 或 \.jsonl\.gz"):
        JsonlImportAdapter().ingest(spec, None, None)


def test_jsonl_import_rejects_multi_files() -> None:
    """AC-4: files 数量 != 1（空 list 或 2 个）→ ValueError 含 "JsonlImport spec 非法"。"""
    # 子用例 1：空 list（违反 pydantic minItems=1）
    with pytest.raises(ValueError, match="JsonlImport spec 非法"):
        JsonlImportAdapter().ingest({"files": []}, None, None)

    # 子用例 2：2 个文件（违反 pydantic maxItems=1）
    two_files = [
        {"path": "a.jsonl", "sha256": "a" * 64},
        {"path": "b.jsonl", "sha256": "b" * 64},
    ]
    with pytest.raises(ValueError, match="JsonlImport spec 非法"):
        JsonlImportAdapter().ingest({"files": two_files}, None, None)
