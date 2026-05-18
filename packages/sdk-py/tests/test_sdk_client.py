"""SDK Client 单元测试（spec sdk-cli-mvp-20260518 AC-10 部分）。

用 httpx.MockTransport 拦截 HTTP 请求；不依赖真后端。
"""

from __future__ import annotations

import json
from typing import Any

import httpx
from dataplat_sdk import Client


def _make_mock(handler: Any) -> httpx.MockTransport:
    return httpx.MockTransport(handler)


def test_a_client_login_persists_cookie() -> None:
    """login 后 cookie 自动保存到 client._http.cookies。"""
    captured: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["json"] = json.loads(request.content.decode("utf-8"))
        return httpx.Response(
            200,
            headers={"set-cookie": "access_token=fake-jwt; Path=/"},
            json={"ok": True},
        )

    c = Client(base_url="https://test", transport=_make_mock(handler))
    c.login("alice", "pw")
    assert captured["url"].endswith("/auth/login")
    assert captured["json"] == {"username": "alice", "password": "pw"}
    assert "access_token" in {ck.name for ck in c._http.cookies.jar}
    c.close()


def test_b_client_create_and_get_repo_roundtrip() -> None:
    """create_repo + get_repo 走对应路由。"""
    routes: dict[str, tuple[int, dict]] = {
        "POST /repos": (
            201,
            {"id": "r1", "owner": "o", "name": "n", "layer": "bronze"},
        ),
        "GET /repos/o/n": (
            200,
            {"id": "r1", "owner": "o", "name": "n", "layer": "bronze"},
        ),
    }

    def handler(request: httpx.Request) -> httpx.Response:
        key = f"{request.method} {request.url.path}"
        status, body = routes.get(key, (404, {"detail": f"no route {key}"}))
        return httpx.Response(status, json=body)

    c = Client(base_url="https://test", transport=_make_mock(handler))
    r1 = c.create_repo("o", "n")
    assert r1["owner"] == "o" and r1["name"] == "n"
    r2 = c.get_repo("o", "n")
    assert r2["id"] == r1["id"]
    c.close()


def test_c_client_upload_blob_returns_sha() -> None:
    """upload_blob 把 bytes 发到 /repos/.../blobs，从响应解 sha。"""
    sent: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        sent["path"] = request.url.path
        sent["body"] = request.content
        return httpx.Response(201, json={"sha256": "a" * 64, "size": len(request.content)})

    c = Client(base_url="https://test", transport=_make_mock(handler))
    sha = c.upload_blob("o", "n", b"hello world")
    assert sent["path"] == "/repos/o/n/blobs"
    assert sent["body"] == b"hello world"
    assert sha == "a" * 64
    c.close()


def test_d_client_create_commit_payload_shape() -> None:
    """create_commit 把 entries 包成 tree.entries 形态，含 parents/author_id/ref。"""
    sent: dict[str, Any] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        sent["path"] = request.url.path
        sent["json"] = json.loads(request.content.decode("utf-8"))
        return httpx.Response(200, json={"hash": "b" * 64, "dedup": False})

    c = Client(base_url="https://test", transport=_make_mock(handler))
    out = c.create_commit(
        "o",
        "n",
        entries=[{"name": "a.md", "mode": 33188, "entry_type": "blob", "target_hash": "c" * 64}],
        author_id="u1",
        message="init",
        ref="main",
    )
    assert sent["path"] == "/repos/o/n/commits"
    assert sent["json"]["tree"]["entries"][0]["name"] == "a.md"
    assert sent["json"]["author_id"] == "u1"
    assert sent["json"]["ref"] == "main"
    assert out["hash"] == "b" * 64
    c.close()


def test_e_client_enqueue_ingest_and_process_return_job_id() -> None:
    """enqueue_ingest / enqueue_process 路由对 + 返 id。"""

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/jobs/ingest":
            payload = json.loads(request.content.decode("utf-8"))
            assert "request" in payload and payload["owner"] == "o"
            return httpx.Response(201, json={"id": "job-ing-1", "status": "queued"})
        if request.url.path == "/process":
            payload = json.loads(request.content.decode("utf-8"))
            assert payload["processor_name"] == "llm-qa-gen"
            return httpx.Response(201, json={"id": "job-proc-1", "status": "queued"})
        return httpx.Response(404)

    c = Client(base_url="https://test", transport=_make_mock(handler))
    ingest_id = c.enqueue_ingest(
        "o", "n", "raw-file-upload", "0.1", {"files": []}, "u1", ref="main"
    )
    assert ingest_id == "job-ing-1"
    process_id = c.enqueue_process(
        "so",
        "sn",
        "main",
        "to",
        "tn",
        "llm-qa-gen",
        "0.1",
        {"records_per_doc": 1},
        "u1",
        ref="main",
    )
    assert process_id == "job-proc-1"
    c.close()


def test_f_client_get_job_returns_dict() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/jobs/xyz"
        return httpx.Response(200, json={"id": "xyz", "status": "succeeded", "result": {}})

    c = Client(base_url="https://test", transport=_make_mock(handler))
    job = c.get_job("xyz")
    assert job["status"] == "succeeded"
    c.close()
