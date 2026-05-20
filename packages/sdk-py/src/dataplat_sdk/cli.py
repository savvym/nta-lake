"""dataplat CLI（Typer-based；design.md §7.3）。

子命令布局：
  dataplat login           # POST /auth/login
  dataplat repo create     # POST /repos
  dataplat repo get        # GET  /repos/{o}/{n}
  dataplat blob upload     # POST /repos/{o}/{n}/blobs
  dataplat snapshot create # POST /repos/{o}/{n}/snapshots
  dataplat ingest          # POST /jobs/ingest
  dataplat process         # POST /process
  dataplat jobs get        # GET  /jobs/{id}

全局参数：
  --url            dataplat API base URL（env DATAPLAT_URL；默认 http://localhost:8000）
  --username       登录用户名（env DATAPLAT_USERNAME）
  --password       登录密码（env DATAPLAT_PASSWORD；只用于 login 子命令）
  --token          复用已有 token（env DATAPLAT_TOKEN）

约束：每个子命令都用 `dataplat_sdk.cli.Client` 构造 client；测试时
monkeypatch 这个名字替换为 fake，CliRunner.invoke 就能拦截。

W1-1（api-snapshot-rename-20260520）：commit_app → snapshot_app，
dataplat commit create → dataplat snapshot create，--parents → --parent。
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Annotated, Any

import typer

from dataplat_sdk.client import Client

app = typer.Typer(name="dataplat", help="dataplat CLI", no_args_is_help=True)

repo_app = typer.Typer(help="Repository 操作", no_args_is_help=True)
blob_app = typer.Typer(help="Blob 上传", no_args_is_help=True)
snapshot_app = typer.Typer(help="Snapshot 操作", no_args_is_help=True)
jobs_app = typer.Typer(help="Job 查询", no_args_is_help=True)

app.add_typer(repo_app, name="repo")
app.add_typer(blob_app, name="blob")
app.add_typer(snapshot_app, name="snapshot")
app.add_typer(jobs_app, name="jobs")


def _make_client(url: str | None, token: str | None) -> Client:
    base = url or os.environ.get("DATAPLAT_URL", "http://localhost:8000")
    tok = token or os.environ.get("DATAPLAT_TOKEN")
    return Client(base_url=base, token=tok)


def _emit(obj: Any) -> None:
    typer.echo(json.dumps(obj, ensure_ascii=False, indent=2))


# ---------- login ----------


@app.command("login")
def login_cmd(
    username: Annotated[str, typer.Option(envvar="DATAPLAT_USERNAME", help="用户名")],
    password: Annotated[
        str, typer.Option(envvar="DATAPLAT_PASSWORD", help="密码")
    ],
    url: Annotated[
        str | None, typer.Option(envvar="DATAPLAT_URL", help="API base URL")
    ] = None,
) -> None:
    """登录 dataplat（POST /auth/login）。"""
    client = _make_client(url, None)
    client.login(username, password)
    typer.echo("login ok")


# ---------- repo ----------


@repo_app.command("create")
def repo_create_cmd(
    owner: str,
    name: str,
    layer: Annotated[str, typer.Option(help="bronze/silver/gold")] = "bronze",
    subtype: Annotated[str, typer.Option(help="repo subtype")] = "pdf",
    visibility: Annotated[str, typer.Option(help="public/private")] = "public",
    url: Annotated[
        str | None, typer.Option(envvar="DATAPLAT_URL")
    ] = None,
    token: Annotated[
        str | None, typer.Option(envvar="DATAPLAT_TOKEN")
    ] = None,
) -> None:
    client = _make_client(url, token)
    repo = client.create_repo(owner, name, layer, subtype, visibility)
    _emit(repo)


@repo_app.command("get")
def repo_get_cmd(
    owner: str,
    name: str,
    url: Annotated[str | None, typer.Option(envvar="DATAPLAT_URL")] = None,
    token: Annotated[str | None, typer.Option(envvar="DATAPLAT_TOKEN")] = None,
) -> None:
    client = _make_client(url, token)
    _emit(client.get_repo(owner, name))


# ---------- blob ----------


@blob_app.command("upload")
def blob_upload_cmd(
    owner: str,
    name: str,
    file: Annotated[Path, typer.Argument(help="本地文件路径")],
    url: Annotated[str | None, typer.Option(envvar="DATAPLAT_URL")] = None,
    token: Annotated[str | None, typer.Option(envvar="DATAPLAT_TOKEN")] = None,
) -> None:
    if not file.exists() or not file.is_file():
        typer.echo(f"file not found: {file}", err=True)
        raise typer.Exit(code=1)
    content = file.read_bytes()
    client = _make_client(url, token)
    sha = client.upload_blob(owner, name, content)
    typer.echo(sha)


# ---------- snapshot ----------


@snapshot_app.command("create")
def snapshot_create_cmd(
    owner: str,
    name: str,
    author_id: Annotated[str, typer.Option(help="snapshot author")],
    entries_json: Annotated[
        str,
        typer.Option(
            "--entries",
            help='JSON list: [{"name":"a.md","mode":33188,"entry_type":"blob","target_hash":"<sha>"}]',
        ),
    ],
    message: Annotated[str | None, typer.Option()] = None,
    ref: Annotated[str | None, typer.Option()] = None,
    parent: Annotated[
        str | None, typer.Option("--parent", help="parent snapshot sha256 (single)")
    ] = None,
    url: Annotated[str | None, typer.Option(envvar="DATAPLAT_URL")] = None,
    token: Annotated[str | None, typer.Option(envvar="DATAPLAT_TOKEN")] = None,
) -> None:
    entries = json.loads(entries_json)
    client = _make_client(url, token)
    snapshot = client.create_snapshot(
        owner, name, entries, author_id, parent, message, ref
    )
    _emit(snapshot)


# ---------- ingest ----------


@app.command("ingest")
def ingest_cmd(
    owner: str,
    name: str,
    adapter_name: Annotated[str, typer.Option()],
    adapter_version: Annotated[str, typer.Option()] = "0.1",
    spec_json: Annotated[str, typer.Option("--spec", help="JSON adapter spec")] = "{}",
    author_id: Annotated[str, typer.Option()] = "cli",
    ref: Annotated[str | None, typer.Option()] = None,
    message: Annotated[str | None, typer.Option()] = None,
    url: Annotated[str | None, typer.Option(envvar="DATAPLAT_URL")] = None,
    token: Annotated[str | None, typer.Option(envvar="DATAPLAT_TOKEN")] = None,
) -> None:
    spec = json.loads(spec_json)
    client = _make_client(url, token)
    job_id = client.enqueue_ingest(
        owner, name, adapter_name, adapter_version, spec, author_id, ref, message
    )
    typer.echo(job_id)


# ---------- process ----------


@app.command("process")
def process_cmd(
    source_owner: str,
    source_name: str,
    source_ref: str,
    target_owner: str,
    target_name: str,
    processor_name: Annotated[str, typer.Option()],
    processor_version: Annotated[str, typer.Option()] = "0.1",
    config_json: Annotated[
        str, typer.Option("--config", help="JSON processor config")
    ] = "{}",
    author_id: Annotated[str, typer.Option()] = "cli",
    ref: Annotated[str | None, typer.Option()] = None,
    message: Annotated[str | None, typer.Option()] = None,
    url: Annotated[str | None, typer.Option(envvar="DATAPLAT_URL")] = None,
    token: Annotated[str | None, typer.Option(envvar="DATAPLAT_TOKEN")] = None,
) -> None:
    config = json.loads(config_json)
    client = _make_client(url, token)
    job_id = client.enqueue_process(
        source_owner,
        source_name,
        source_ref,
        target_owner,
        target_name,
        processor_name,
        processor_version,
        config,
        author_id,
        ref,
        message,
    )
    typer.echo(job_id)


# ---------- jobs ----------


@jobs_app.command("get")
def jobs_get_cmd(
    job_id: str,
    url: Annotated[str | None, typer.Option(envvar="DATAPLAT_URL")] = None,
    token: Annotated[str | None, typer.Option(envvar="DATAPLAT_TOKEN")] = None,
) -> None:
    client = _make_client(url, token)
    _emit(client.get_job(job_id))


if __name__ == "__main__":
    sys.exit(app())
