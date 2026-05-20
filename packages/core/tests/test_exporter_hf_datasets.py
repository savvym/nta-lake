"""W3-7 HF datasets exporter 行为测试（AC-1..AC-4）。

- AC-1: happy roundtrip：3 行 silver JSONL → export → datasets.load_from_disk → len==3, "text" in column_names
- AC-2: HfDatasetExportResult 字段正确：row_count==3, dataset_info_path 存在, total_bytes > 0
- AC-3: 空 silver snapshot (b"") → export 成功, len(ds)==0, row_count==0, total_bytes > 0
- AC-4: 坏行（非 JSON）→ raise ValueError 含 "非法 JSON 行"

stub BlobStore 内联（inline，不污染任何生产注册表）。
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import datasets as hf_datasets
import pytest

from dataplat_core.exporters.hf_datasets import HfDatasetExportResult, export_to_hf_datasets


# ---------------------------------------------------------------------------
# Stub BlobStore（async get 最小子集，参考 W2-6 / W3-6 模式）
# ---------------------------------------------------------------------------


class _StubBlobStore:
    """内存 BlobStore stub：sha → bytes，只实现 get。"""

    def __init__(self, data: dict[str, bytes]) -> None:
        self._data = dict(data)

    async def get(self, sha: str) -> bytes:
        if sha not in self._data:
            raise KeyError(sha)
        return self._data[sha]


# ---------------------------------------------------------------------------
# 测试辅助：构造标准 silver JSONL 行
# ---------------------------------------------------------------------------

_BLOB_SHA = "a" * 64


def _make_silver_jsonl(texts: list[str]) -> bytes:
    """构造包含 N 行 silver JSONL 的 bytes（每行有 text/images/source_ref/stats/lineage_ops）。"""
    lines = []
    for i, text in enumerate(texts, start=1):
        row = {
            "text": text,
            "images": [],
            "source_ref": {
                "blob_sha": _BLOB_SHA,
                "loader": "jsonl",
                "loader_version": "0.1",
                "line_no": i,
            },
            "stats": {},
            "lineage_ops": [],
        }
        lines.append(json.dumps(row))
    return "\n".join(lines).encode("utf-8")


# ---------------------------------------------------------------------------
# AC-1: happy roundtrip
# ---------------------------------------------------------------------------


def test_export_hf_datasets_roundtrip_happy(tmp_path: Path) -> None:
    """AC-1: 3 行 silver JSONL → export → datasets.load_from_disk 可读；
    len(ds)==3, "text" in ds.column_names, ds[0]["text"]=="row0"。
    """
    blob = _make_silver_jsonl(["row0", "row1", "row2"])
    store = _StubBlobStore({_BLOB_SHA: blob})
    target = tmp_path / "hf_out"

    result = asyncio.run(export_to_hf_datasets(_BLOB_SHA, target, store))

    # target_path 目录含 dataset_info.json
    assert (Path(result.target_path) / "dataset_info.json").is_file()

    # datasets.load_from_disk 可加载
    ds = hf_datasets.load_from_disk(result.target_path)
    assert len(ds) == 3
    assert "text" in ds.column_names
    assert ds[0]["text"] == "row0"


# ---------------------------------------------------------------------------
# AC-2: HfDatasetExportResult 字段正确
# ---------------------------------------------------------------------------


def test_export_hf_datasets_result_fields(tmp_path: Path) -> None:
    """AC-2: 返回值字段：row_count==3, "text" in column_names,
    dataset_info_path 以 dataset_info.json 结尾且文件存在, total_bytes > 0。
    """
    blob = _make_silver_jsonl(["row0", "row1", "row2"])
    store = _StubBlobStore({_BLOB_SHA: blob})
    target = tmp_path / "hf_out"

    result = asyncio.run(export_to_hf_datasets(_BLOB_SHA, target, store))

    assert isinstance(result, HfDatasetExportResult)
    assert result.row_count == 3
    assert "text" in result.column_names
    assert result.dataset_info_path.endswith("dataset_info.json")
    assert Path(result.dataset_info_path).is_file()
    assert result.total_bytes > 0


# ---------------------------------------------------------------------------
# AC-3: 空 silver snapshot
# ---------------------------------------------------------------------------


def test_export_hf_datasets_empty(tmp_path: Path) -> None:
    """AC-3: 空 silver snapshot (b"") → export 成功；
    len(ds)==0, row_count==0, total_bytes > 0（dataset_info.json 自身有内容）。
    column_names==[] (HF 空 dataset 行为，datasets 3.6.0 验证通过)。
    """
    store = _StubBlobStore({_BLOB_SHA: b""})
    target = tmp_path / "hf_empty"

    result = asyncio.run(export_to_hf_datasets(_BLOB_SHA, target, store))

    assert result.row_count == 0
    assert result.column_names == []
    assert result.total_bytes > 0

    ds = hf_datasets.load_from_disk(result.target_path)
    assert len(ds) == 0


# ---------------------------------------------------------------------------
# AC-4: 坏行 → raise ValueError
# ---------------------------------------------------------------------------


def test_export_hf_datasets_rejects_malformed_jsonl(tmp_path: Path) -> None:
    """AC-4: 含非法 JSON 行 → raise ValueError 含 "非法 JSON 行" 子串；
    target_path 未被部分写入（save_to_disk 仅在全部解析成功后调用）。
    """
    malformed = b"not a json line\n"
    store = _StubBlobStore({_BLOB_SHA: malformed})
    target = tmp_path / "hf_bad"

    with pytest.raises(ValueError, match="非法 JSON 行"):
        asyncio.run(export_to_hf_datasets(_BLOB_SHA, target, store))
