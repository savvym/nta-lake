"""dataset export engine（W2-6）：把 SilverRow 列表序列化为 JSONL 字节并写入 BlobStore（CAS），
返回 SnapshotExportResult 元数据，是 in-memory recipe 结果 → 持久化 Silver snapshot 的原语。
"""

from __future__ import annotations

import io

from pydantic import BaseModel, ConfigDict, Field

from dataplat_core.domain.types import SHA256
from dataplat_core.protocols.loader import SilverRow
from dataplat_core.protocols.storage import BlobStore


class SnapshotExportResult(BaseModel):
    """export_silver_snapshot 的返回值，包含 snapshot 的 CAS 元数据。"""

    model_config = ConfigDict(extra="forbid")

    sha256: SHA256
    size_bytes: int = Field(ge=0)
    row_count: int = Field(ge=0)
    dataset_name: str = Field(min_length=1)
    deduplicated: bool
    notes: str | None = None


def serialize_rows_to_jsonl(rows: list[SilverRow]) -> bytes:
    """将 SilverRow 列表序列化为 JSONL 字节。

    - 空 list → b""
    - 非空：每行 model_dump_json() + "\\n"，全部 join 后 encode("utf-8")
    - 确定性：pydantic v2 model_dump_json 按字段声明顺序稳定输出
    """
    if not rows:
        return b""
    return "".join(row.model_dump_json() + "\n" for row in rows).encode("utf-8")


async def export_silver_snapshot(
    rows: list[SilverRow],
    dataset_name: str,
    store: BlobStore,
    *,
    notes: str | None = None,
) -> SnapshotExportResult:
    """把 SilverRow 列表序列化为 JSONL 并写入 BlobStore，返回 snapshot 元数据。

    严格 4 步：serialize → BytesIO → store.put → 构造 SnapshotExportResult。
    """
    # 1. 序列化
    payload = serialize_rows_to_jsonl(rows)
    # 2. 包装为 BinaryIO
    stream = io.BytesIO(payload)
    # 3. 写入 CAS
    put_result = await store.put(stream, declared_size=len(payload))
    # 4. 构造返回值
    return SnapshotExportResult(
        sha256=put_result.sha256,
        size_bytes=put_result.size,
        row_count=len(rows),
        dataset_name=dataset_name,
        deduplicated=put_result.deduplicated,
        notes=notes,
    )
