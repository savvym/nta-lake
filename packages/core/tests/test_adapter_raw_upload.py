from __future__ import annotations

import pytest

from dataplat_core.adapters import RawFileUploadAdapter, get_default
from dataplat_core.adapters.registry import AdapterRegistry
from dataplat_core.protocols.adapter import IngestResult


class _StubAdapter:
    name = "test-adapter-w3-1"
    version = "0.1"
    input_schema: dict = {"type": "object"}
    output_subtype = "test"

    def ingest(self, spec, workspace, ctx):
        del spec, workspace, ctx
        return IngestResult()


def test_adapter_registry_round_trip():
    """AC-1: register / get / duplicate raise / list_names contains."""
    reg = AdapterRegistry()
    stub = _StubAdapter()
    reg.register(stub)
    assert reg.get("test-adapter-w3-1") is stub
    with pytest.raises(ValueError, match="already registered"):
        reg.register(_StubAdapter())
    assert "test-adapter-w3-1" in reg.list_names()


def test_raw_upload_auto_registered():
    """AC-2: import dataplat_core.adapters → raw-file-upload 已注册."""
    reg = get_default()
    assert "raw-file-upload" in reg.list_names()
    adapter = reg.get("raw-file-upload")
    assert adapter.name == "raw-file-upload"


def test_raw_upload_ingest_happy():
    """AC-3: ingest happy path with 2 files + asset_id."""
    sha_a = "a" * 64
    sha_b = "b" * 64
    spec = {
        "files": [
            {"path": "doc.md", "sha256": sha_a},
            {"path": "img.png", "sha256": sha_b},
        ],
        "asset_id": "a1",
    }
    adapter = RawFileUploadAdapter()
    result = adapter.ingest(spec, None, None)
    assert result.file_count == 2
    assert result.asset_count == 1
    assert result.files[0].path == "doc.md"
    assert result.files[0].sha256 == sha_a
    assert result.files[1].path == "img.png"
    assert result.files[1].sha256 == sha_b


def test_raw_upload_ingest_duplicate_path_raises():
    """AC-4: duplicate path → ValueError 含 '重复 path'."""
    sha = "c" * 64
    spec = {
        "files": [
            {"path": "x.txt", "sha256": sha},
            {"path": "x.txt", "sha256": sha},
        ],
    }
    adapter = RawFileUploadAdapter()
    with pytest.raises(ValueError, match="重复 path"):
        adapter.ingest(spec, None, None)
