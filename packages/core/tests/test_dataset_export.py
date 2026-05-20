"""dataset export engine 行为测试（W2-6，AC-1..AC-4）。

- AC-1: serialize_rows_to_jsonl 空列表 → b""；3 行 → 3 行 JSONL；每行 json.loads 字段一致；确定性
- AC-2: export_silver_snapshot end-to-end：InMemoryBlobStore stub + 3 行 → SnapshotExportResult 正确
- AC-3: export_silver_snapshot 一致性自检：sha256 / size_bytes 与本地计算结果严格一致
- AC-4: export_silver_snapshot 空 rows：sha256 == sha256(b"")，store.put 仍被调

InMemoryBlobStore 在本文件 inline 定义，不污染任何生产注册表。
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import AsyncIterator
from typing import BinaryIO

from dataplat_core.dataset import SnapshotExportResult, export_silver_snapshot, serialize_rows_to_jsonl
from dataplat_core.protocols.loader import SilverRow
from dataplat_core.protocols.storage import BlobPutResult, BlobStore


# ---------------------------------------------------------------------------
# InMemoryBlobStore stub（test inline）
# ---------------------------------------------------------------------------


class InMemoryBlobStore:
    """实现 BlobStore Protocol 的内存 stub，用于测试。"""

    def __init__(self) -> None:
        self._blobs: dict[str, bytes] = {}

    async def put(self, stream: BinaryIO, *, declared_size: int | None = None) -> BlobPutResult:
        data = stream.read()
        sha = hashlib.sha256(data).hexdigest()
        deduplicated = sha in self._blobs
        if not deduplicated:
            self._blobs[sha] = data
        return BlobPutResult(
            sha256=sha,
            size=len(data),
            storage_key=f"blobs/{sha[:2]}/{sha}",
            deduplicated=deduplicated,
        )

    async def get(self, sha256: str) -> AsyncIterator[bytes]:
        if sha256 not in self._blobs:
            raise KeyError(sha256)
        yield self._blobs[sha256]

    async def exists(self, sha256: str) -> bool:
        return sha256 in self._blobs

    async def get_size(self, sha256: str) -> int | None:
        if sha256 not in self._blobs:
            return None
        return len(self._blobs[sha256])

    async def delete(self, sha256: str) -> bool:
        return self._blobs.pop(sha256, None) is not None


# 验证 stub 满足 BlobStore Protocol（runtime_checkable）
assert isinstance(InMemoryBlobStore(), BlobStore), "InMemoryBlobStore 必须满足 BlobStore Protocol"


# ---------------------------------------------------------------------------
# 测试辅助：构造标准 SilverRow
# ---------------------------------------------------------------------------


def _make_row(text: str, path: str = "test.txt") -> SilverRow:
    return SilverRow(
        text=text,
        source_ref={"blob_sha": "test-blob", "path": path},
        images=[],
        stats={},
        lineage_ops=[],
    )


# ---------------------------------------------------------------------------
# AC-1：serialize_rows_to_jsonl
# ---------------------------------------------------------------------------


def test_serialize_rows_to_jsonl() -> None:
    """AC-1：序列化行为 + 确定性。"""
    # 空 list → b""
    assert serialize_rows_to_jsonl([]) == b""

    # 3 行 → 3 行 JSONL，末尾有 trailing newline（split 后 4 元素，最后空串）
    rows = [_make_row(f"row{i}") for i in range(3)]
    result = serialize_rows_to_jsonl(rows)
    parts = result.decode("utf-8").split("\n")
    non_empty = [p for p in parts if p]
    assert len(non_empty) == 3, f"期望 3 个非空行，得到 {len(non_empty)}"
    # 最后一个元素应为空串（trailing newline）
    assert parts[-1] == "", "末尾应有 trailing newline"

    # 每行 json.loads 字段与 row.model_dump() 一致
    for line, row in zip(non_empty, rows):
        parsed = json.loads(line)
        assert parsed == row.model_dump(), f"行内容不一致：{parsed} != {row.model_dump()}"

    # 确定性：同输入两次调用 bytes 严格相等
    assert serialize_rows_to_jsonl(rows) == serialize_rows_to_jsonl(rows)


# ---------------------------------------------------------------------------
# AC-2：export_silver_snapshot end-to-end
# ---------------------------------------------------------------------------


async def test_export_silver_snapshot_writes_blob() -> None:
    """AC-2：end-to-end 写入 BlobStore，返回字段正确。"""
    store = InMemoryBlobStore()
    rows = [_make_row(f"text-{i}") for i in range(3)]

    result = await export_silver_snapshot(rows, "silver-test", store)

    assert isinstance(result, SnapshotExportResult)
    assert len(result.sha256) == 64, "sha256 应为 64 字符 hex"
    assert all(c in "0123456789abcdef" for c in result.sha256), "sha256 应为小写 hex"
    assert result.size_bytes > 0
    assert result.row_count == 3
    assert result.dataset_name == "silver-test"
    assert result.deduplicated is False
    # blob 确实写入了 store
    assert await store.exists(result.sha256) is True


# ---------------------------------------------------------------------------
# AC-3：sha256 / size_bytes 一致性自检
# ---------------------------------------------------------------------------


async def test_export_silver_snapshot_sha256_matches() -> None:
    """AC-3：返回的 sha256 与本地计算一致；size_bytes == len(serialized_bytes)。"""
    store = InMemoryBlobStore()
    rows = [_make_row("hello"), _make_row("world")]

    result = await export_silver_snapshot(rows, "consistency-check", store)

    serialized = serialize_rows_to_jsonl(rows)
    expected_sha256 = hashlib.sha256(serialized).hexdigest()
    assert result.sha256 == expected_sha256
    assert result.size_bytes == len(serialized)


# ---------------------------------------------------------------------------
# AC-4：空 rows
# ---------------------------------------------------------------------------


async def test_export_silver_snapshot_empty() -> None:
    """AC-4：空 rows → sha256(b"")，size_bytes==0，row_count==0，store.put 仍被调。"""
    store = InMemoryBlobStore()
    result = await export_silver_snapshot([], "empty-dataset", store)

    sha256_empty = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    assert result.sha256 == sha256_empty
    assert result.size_bytes == 0
    assert result.row_count == 0
    # store.put 仍被调，空 blob 写入
    assert await store.exists(result.sha256) is True
