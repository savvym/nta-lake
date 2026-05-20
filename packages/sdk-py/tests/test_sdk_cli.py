"""CLI Typer 集成测试（spec sdk-cli-mvp-20260518 AC-10 部分）。

用 typer.testing.CliRunner 调 app；monkeypatch dataplat_sdk.cli.Client 替换
为 fake 类，拦截方法调用。
"""

from __future__ import annotations

import json
from typing import Any

import pytest
from dataplat_sdk import cli as cli_mod
from dataplat_sdk.cli import app
from typer.testing import CliRunner


class _FakeClient:
    """记录每次方法调用 + 返预设响应。"""

    def __init__(self, base_url: str, token: str | None = None, **_kwargs: Any) -> None:
        self.base_url = base_url
        self.token = token
        self.calls: list[tuple[str, dict[str, Any]]] = []

    # methods 用 _record + 返 stub
    def login(self, username: str, password: str) -> None:
        self.calls.append(("login", {"username": username, "password": password}))

    def create_repo(
        self,
        owner: str,
        name: str,
        layer: str = "bronze",
        subtype: str = "pdf",
        visibility: str = "public",
    ) -> dict[str, Any]:
        self.calls.append(
            (
                "create_repo",
                {"owner": owner, "name": name, "layer": layer, "subtype": subtype},
            )
        )
        return {"id": "r1", "owner": owner, "name": name, "layer": layer}

    def get_repo(self, owner: str, name: str) -> dict[str, Any]:
        self.calls.append(("get_repo", {"owner": owner, "name": name}))
        return {"id": "r1", "owner": owner, "name": name}

    def upload_blob(self, owner: str, name: str, content: bytes) -> str:
        self.calls.append(
            ("upload_blob", {"owner": owner, "name": name, "size": len(content)})
        )
        return "a" * 64

    def create_snapshot(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("create_snapshot", {"args": args, "kwargs": kwargs}))
        return {"hash": "b" * 64}

    def enqueue_ingest(self, *args: Any, **kwargs: Any) -> str:
        self.calls.append(("enqueue_ingest", {"args": args, "kwargs": kwargs}))
        return "job-ing-1"

    def enqueue_process(self, *args: Any, **kwargs: Any) -> str:
        self.calls.append(("enqueue_process", {"args": args, "kwargs": kwargs}))
        return "job-proc-1"

    def get_job(self, job_id: str) -> dict[str, Any]:
        self.calls.append(("get_job", {"job_id": job_id}))
        return {"id": job_id, "status": "succeeded"}


@pytest.fixture
def fake_client_holder(monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """monkeypatch cli.Client 为 _FakeClient；返回 holder dict 让测试拿到实例。"""
    holder: dict[str, Any] = {"last": None}

    def factory(*args: Any, **kwargs: Any) -> _FakeClient:
        inst = _FakeClient(*args, **kwargs)
        holder["last"] = inst
        return inst

    monkeypatch.setattr(cli_mod, "Client", factory)
    return holder


def test_a_cli_help_lists_subcommands() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    out = result.stdout
    for sub in ["login", "repo", "blob", "snapshot", "ingest", "process", "jobs"]:
        assert sub in out, f"subcommand {sub} missing from help: {out}"


def test_b_cli_login_calls_client_login(fake_client_holder: dict[str, Any]) -> None:
    runner = CliRunner()
    result = runner.invoke(
        app,
        ["login", "--username", "alice", "--password", "pw", "--url", "https://x"],
    )
    assert result.exit_code == 0, result.stdout
    fake: _FakeClient = fake_client_holder["last"]
    assert ("login", {"username": "alice", "password": "pw"}) in fake.calls
    assert "login ok" in result.stdout


def test_c_cli_repo_create_outputs_json(fake_client_holder: dict[str, Any]) -> None:
    runner = CliRunner()
    result = runner.invoke(
        app,
        ["repo", "create", "myorg", "myrepo", "--layer", "bronze", "--subtype", "pdf"],
    )
    assert result.exit_code == 0, result.stdout
    body = json.loads(result.stdout)
    assert body["owner"] == "myorg" and body["name"] == "myrepo"
    fake: _FakeClient = fake_client_holder["last"]
    create_call = [c for c in fake.calls if c[0] == "create_repo"]
    assert create_call and create_call[0][1]["owner"] == "myorg"


def test_d_cli_blob_upload_reads_file_and_returns_sha(
    fake_client_holder: dict[str, Any], tmp_path: Any
) -> None:
    f = tmp_path / "doc.md"
    f.write_bytes(b"hello content")
    runner = CliRunner()
    result = runner.invoke(app, ["blob", "upload", "o", "n", str(f)])
    assert result.exit_code == 0, result.stdout
    assert "a" * 64 in result.stdout
    fake: _FakeClient = fake_client_holder["last"]
    up = [c for c in fake.calls if c[0] == "upload_blob"]
    assert up and up[0][1]["size"] == len(b"hello content")


def test_e_cli_ingest_emits_job_id(fake_client_holder: dict[str, Any]) -> None:
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "ingest",
            "o",
            "n",
            "--adapter-name",
            "raw-file-upload",
            "--adapter-version",
            "0.1",
            "--spec",
            "{}",
            "--author-id",
            "cli",
            "--ref",
            "main",
        ],
    )
    assert result.exit_code == 0, result.stdout
    assert "job-ing-1" in result.stdout
    fake: _FakeClient = fake_client_holder["last"]
    assert any(c[0] == "enqueue_ingest" for c in fake.calls)


def test_f_cli_jobs_get_outputs_json(fake_client_holder: dict[str, Any]) -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["jobs", "get", "xyz"])
    assert result.exit_code == 0, result.stdout
    body = json.loads(result.stdout)
    assert body["id"] == "xyz" and body["status"] == "succeeded"
