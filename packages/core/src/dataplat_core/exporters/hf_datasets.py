"""HF datasets exporter（W3-7）：把 W2-6 silver JSONL blob 反序列化 →
HuggingFace datasets 兼容目录（dataset_info.json + Arrow shards），
供训练侧 datasets.load_from_disk(path) 直接消费。
"""

from __future__ import annotations

import json
from pathlib import Path

import datasets as hf_datasets
import pyarrow as pa
from datasets import DatasetInfo, Features
from pydantic import BaseModel, ConfigDict, Field

from dataplat_core.domain.types import SHA256
from dataplat_core.protocols.storage import BlobStore


class HfDatasetExportResult(BaseModel):
    """export_to_hf_datasets 返回值。"""

    model_config = ConfigDict(extra="forbid")

    target_path: str
    row_count: int = Field(ge=0)
    column_names: list[str]
    dataset_info_path: str
    total_bytes: int = Field(ge=0)


def _write_empty_dataset_dir(target: Path) -> None:
    """为空 silver snapshot 写出 HF datasets 兼容目录。

    datasets.save_to_disk 在 rows=0 时抛 SchemaInferenceError（需要至少一行或显式 features）。
    针对空快照的特殊处理：用 pyarrow IPC stream 写空 Arrow 文件 + 手写 state.json +
    DatasetInfo.write_to_directory 写 dataset_info.json，使得 load_from_disk 可正常加载
    0 行、0 列的 Dataset（AC-3 验证）。
    """
    # 1. 写空 Arrow IPC Stream 文件（schema=空；datasets 用 open_stream 读取）
    arrow_file = target / "data-00000-of-00001.arrow"
    schema = pa.schema([])
    with pa.ipc.new_stream(str(arrow_file), schema):
        pass  # 无 batch 写入

    # 2. 写 dataset_info.json（空 features）
    DatasetInfo(features=Features({})).write_to_directory(str(target))

    # 3. 写 state.json（datasets 加载时必须的状态文件）
    state = {
        "_data_files": [{"filename": "data-00000-of-00001.arrow"}],
        "_fingerprint": "empty_silver_snapshot",
        "_format_columns": None,
        "_format_kwargs": {},
        "_format_type": None,
        "_output_all_columns": False,
        "_split": None,
    }
    (target / "state.json").write_text(json.dumps(state))


async def export_to_hf_datasets(
    silver_blob_sha: SHA256,
    target_path: Path | str,
    store: BlobStore,
    *,
    split: str = "train",
) -> HfDatasetExportResult:
    """从 silver snapshot blob → HF datasets 目录。

    严格步骤：get blob → decode utf-8 errors=replace → splitlines() →
    每行 json.loads（坏行 fail-fast 抛 ValueError）→ Dataset.from_list →
    save_to_disk → 收集 metadata 返回。

    空 snapshot（rows==0）特殊路径：datasets.save_to_disk 在无 schema 时抛
    SchemaInferenceError；改用 _write_empty_dataset_dir 手写 HF 兼容目录结构。
    load_from_disk 仍可正常加载 0 行 Dataset（见 design.md 风险 3 + AC-3）。

    `split` 参数当前作占位，未来扩展 multi-split 时使用。
    """
    # 1. 读 blob
    data = await store.get(silver_blob_sha)
    if not isinstance(data, bytes):
        chunks: list[bytes] = []
        async for chunk in data:
            chunks.append(chunk)
        data = b"".join(chunks)

    # 2. 解码 + 按行解析
    text = data.decode("utf-8", errors="replace")
    rows: list[dict] = []
    for idx, raw_line in enumerate(text.splitlines(), start=1):
        if not raw_line.strip():
            continue
        try:
            obj = json.loads(raw_line)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"silver snapshot 含非法 JSON 行 (line={idx}): {exc}"
            ) from exc
        if not isinstance(obj, dict):
            raise ValueError(
                f"silver snapshot 含非 dict 行 (line={idx})"
            )
        rows.append(obj)

    # 3. 解析 target 路径
    target = Path(target_path).expanduser().resolve()
    target.mkdir(parents=True, exist_ok=True)

    if rows:
        # 4a. 非空：Dataset.from_list + save_to_disk（标准路径）
        dataset = hf_datasets.Dataset.from_list(rows)
        dataset.save_to_disk(str(target))
        column_names = list(dataset.column_names)
    else:
        # 4b. 空快照特殊路径（datasets 3.x SchemaInferenceError workaround）
        _write_empty_dataset_dir(target)
        column_names = []

    # 5. dataset_info.json 必须存在（防御 datasets 库行为漂移）
    info_path = target / "dataset_info.json"
    if not info_path.is_file():
        raise ValueError(
            f"datasets 目录写入后未生成 dataset_info.json (path={info_path})"
        )

    # 6. 汇总 total_bytes
    total_bytes = sum(
        f.stat().st_size for f in target.rglob("*") if f.is_file()
    )

    return HfDatasetExportResult(
        target_path=str(target),
        row_count=len(rows),
        column_names=column_names,
        dataset_info_path=str(info_path),
        total_bytes=total_bytes,
    )
