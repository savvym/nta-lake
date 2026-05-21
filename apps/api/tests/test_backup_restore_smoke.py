"""backup/restore smoke test（W4-10 backup-restore-20260520）。

目的：验证 backup_bronze.sh + restore_bronze.sh 的端到端 round-trip。

验收标准 AC-4：
  - env 就位（DATAPLAT_MINIO_ENDPOINT 已设）→ 1 passed
  - env 缺位 → 1 skipped（整个模块 pytestmark skipif）

测试内容：
  1. boto3 put 3 fake blob 到测试 bucket dataplat-blobs-test-backup
  2. subprocess 跑 backup_bronze.sh → 断言 BACKUP_OK + tarball 存在 + tar -tzf 列 3 个文件
  3. subprocess 跑 restore_bronze.sh --force → 断言 RESTORE_OK 3
  4. boto3 list_objects_v2 在 restore bucket 验 3 个 key
  5. try/finally 清理 2 个 bucket + tarball
"""

from __future__ import annotations

import os
import subprocess
import tarfile
from pathlib import Path

import boto3
import pytest

_MINIO_ENDPOINT = os.environ.get("DATAPLAT_MINIO_ENDPOINT", "")

pytestmark = pytest.mark.skipif(
    not _MINIO_ENDPOINT,
    reason="DATAPLAT_MINIO_ENDPOINT 未设置；backup/restore smoke test 跳过",
)

# ---------------------------------------------------------------------------
# 测试常量
# ---------------------------------------------------------------------------
_BACKUP_BUCKET = "dataplat-blobs-test-backup"
_RESTORE_BUCKET = "dataplat-blobs-test-restore"
_FAKE_BLOBS: list[tuple[str, bytes]] = [
    ("sha256/aa/bb/aabbcc1111111111111111111111111111111111111111111111111111111111", b"fake-blob-1"),
    ("sha256/dd/ee/ddeeff2222222222222222222222222222222222222222222222222222222222", b"fake-blob-2"),
    ("sha256/ff/00/ff003333333333333333333333333333333333333333333333333333333333", b"fake-blob-3"),
]


def _make_s3_client() -> boto3.client:
    return boto3.client(
        "s3",
        endpoint_url=_MINIO_ENDPOINT,
        aws_access_key_id=os.environ.get("DATAPLAT_MINIO_ACCESS_KEY", "dataplat"),
        aws_secret_access_key=os.environ.get("DATAPLAT_MINIO_SECRET_KEY", "dataplat-dev-secret"),
        region_name="us-east-1",
    )


def _delete_bucket_objects(s3: boto3.client, bucket: str) -> None:
    try:
        resp = s3.list_objects_v2(Bucket=bucket)
        objects = resp.get("Contents", [])
        if objects:
            s3.delete_objects(
                Bucket=bucket,
                Delete={"Objects": [{"Key": obj["Key"]} for obj in objects]},
            )
        s3.delete_bucket(Bucket=bucket)
    except Exception:
        pass


def test_backup_restore_roundtrip(tmp_path: Path) -> None:
    """put 3 blob → backup → restore → verify 3 blob 在新 bucket。"""
    s3 = _make_s3_client()

    # -----------------------------------------------------------------------
    # setUp：创建 backup bucket + put 3 fake blobs
    # -----------------------------------------------------------------------
    s3.create_bucket(Bucket=_BACKUP_BUCKET)
    for key, data in _FAKE_BLOBS:
        s3.put_object(Bucket=_BACKUP_BUCKET, Key=key, Body=data)

    repo_root = Path(__file__).parent.parent.parent.parent

    try:
        # -------------------------------------------------------------------
        # backup
        # -------------------------------------------------------------------
        backup_result = subprocess.run(
            ["bash", str(repo_root / "scripts" / "backup_bronze.sh"), str(tmp_path),
             "--bucket", _BACKUP_BUCKET],
            capture_output=True,
            text=True,
        )
        assert backup_result.returncode == 0, (
            f"backup 退码 {backup_result.returncode}\n"
            f"stdout: {backup_result.stdout}\n"
            f"stderr: {backup_result.stderr}"
        )
        assert "BACKUP_OK" in backup_result.stdout, (
            f"BACKUP_OK 未出现在 stdout: {backup_result.stdout!r}"
        )

        # 从 BACKUP_OK <path> <size> <count> 解析 tarball 路径
        ok_line = next(
            line for line in backup_result.stdout.splitlines() if line.startswith("BACKUP_OK")
        )
        parts = ok_line.split()
        assert len(parts) >= 2, f"BACKUP_OK 行格式异常：{ok_line!r}"
        tarball_path = Path(parts[1])
        assert tarball_path.exists(), f"tarball 不存在：{tarball_path}"

        # tar -tzf 列出应含 3 个文件
        with tarfile.open(str(tarball_path), "r:gz") as tf:
            members = [m for m in tf.getmembers() if m.isfile()]
        assert len(members) >= 3, f"tarball 内文件数期望 >= 3，实际 {len(members)}"

        # -------------------------------------------------------------------
        # restore
        # -------------------------------------------------------------------
        restore_result = subprocess.run(
            ["bash", str(repo_root / "scripts" / "restore_bronze.sh"), str(tarball_path),
             "--bucket", _RESTORE_BUCKET, "--force"],
            capture_output=True,
            text=True,
        )
        assert restore_result.returncode == 0, (
            f"restore 退码 {restore_result.returncode}\n"
            f"stdout: {restore_result.stdout}\n"
            f"stderr: {restore_result.stderr}"
        )
        assert "RESTORE_OK" in restore_result.stdout, (
            f"RESTORE_OK 未出现在 stdout: {restore_result.stdout!r}"
        )
        assert "3" in restore_result.stdout, (
            f"RESTORE_OK 应含计数 3，实际：{restore_result.stdout!r}"
        )

        # -------------------------------------------------------------------
        # 验证 restore bucket 内有 3 个 key
        # -------------------------------------------------------------------
        list_resp = s3.list_objects_v2(Bucket=_RESTORE_BUCKET)
        restored_keys = [obj["Key"] for obj in list_resp.get("Contents", [])]
        assert len(restored_keys) >= 3, (
            f"restore bucket 内对象数期望 >= 3，实际 {len(restored_keys)}: {restored_keys}"
        )
        backup_keys = {key for key, _ in _FAKE_BLOBS}
        for key in backup_keys:
            assert key in restored_keys, f"key {key!r} 未在 restore bucket 找到"

    finally:
        # -------------------------------------------------------------------
        # tearDown：删 2 个 bucket
        # -------------------------------------------------------------------
        _delete_bucket_objects(s3, _BACKUP_BUCKET)
        _delete_bucket_objects(s3, _RESTORE_BUCKET)
