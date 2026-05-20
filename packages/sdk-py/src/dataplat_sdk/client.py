"""dataplat 同步 HTTP Client（design.md §7.2）。

用 httpx.Client 持有 cookie session；MVP 覆盖 8 个方法：login / create_repo
/ get_repo / upload_blob / create_snapshot / enqueue_ingest / enqueue_process
/ get_job。所有方法是同步的；用户在脚本 / Jupyter 里直接调。

token 字段保留接口为未来 SSO/PAT 预留，MVP 仅走 cookie。

W1-1（api-snapshot-rename-20260520）：create_commit → create_snapshot，
parents: list → parent: str | None，POST 目标 /snapshots。
"""

from __future__ import annotations

from typing import Any

import httpx


class Client:
    """dataplat 同步 HTTP 客户端。"""

    def __init__(
        self,
        base_url: str,
        token: str | None = None,
        timeout: float = 30.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._token = token
        headers = {}
        if token:
            headers["Authorization"] = f"Bearer {token}"
        kwargs: dict[str, Any] = {
            "base_url": self._base_url,
            "timeout": timeout,
            "headers": headers,
            "cookies": httpx.Cookies(),
        }
        if transport is not None:
            kwargs["transport"] = transport
        self._http: httpx.Client = httpx.Client(**kwargs)

    # ---------- lifecycle ----------

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> Client:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    # ---------- auth ----------

    def login(self, username: str, password: str) -> None:
        """POST /auth/login；cookie 自动存到 _http.cookies。"""
        resp = self._http.post(
            "/auth/login", json={"username": username, "password": password}
        )
        resp.raise_for_status()

    # ---------- repo ----------

    def create_repo(
        self,
        owner: str,
        name: str,
        layer: str = "bronze",
        subtype: str = "pdf",
        visibility: str = "public",
    ) -> dict[str, Any]:
        resp = self._http.post(
            "/repos",
            json={
                "owner": owner,
                "name": name,
                "layer": layer,
                "subtype": subtype,
                "visibility": visibility,
            },
        )
        resp.raise_for_status()
        return dict(resp.json())

    def get_repo(self, owner: str, name: str) -> dict[str, Any]:
        resp = self._http.get(f"/repos/{owner}/{name}")
        resp.raise_for_status()
        return dict(resp.json())

    # ---------- blob ----------

    def upload_blob(self, owner: str, name: str, content: bytes) -> str:
        """POST /repos/{owner}/{name}/blobs；返 sha256。"""
        resp = self._http.post(
            f"/repos/{owner}/{name}/blobs",
            content=content,
            headers={"content-type": "application/octet-stream"},
        )
        resp.raise_for_status()
        sha: str = resp.json()["sha256"]
        return sha

    # ---------- snapshot ----------

    def create_snapshot(
        self,
        owner: str,
        name: str,
        entries: list[dict[str, Any]],
        author_id: str,
        parent: str | None = None,
        message: str | None = None,
        ref: str | None = None,
    ) -> dict[str, Any]:
        """POST /repos/{owner}/{name}/snapshots。entries 元素形态：
        {name, mode, entry_type, target_hash}。

        W1-1：前称 create_commit；parents list 退化为 parent 单值（str | None）。
        """
        payload: dict[str, Any] = {
            "tree": {"entries": entries},
            "author_id": author_id,
        }
        if parent is not None:
            payload["parent"] = parent
        if message is not None:
            payload["message"] = message
        if ref is not None:
            payload["ref"] = ref
        resp = self._http.post(f"/repos/{owner}/{name}/snapshots", json=payload)
        resp.raise_for_status()
        return dict(resp.json())

    # ---------- jobs ----------

    def enqueue_ingest(
        self,
        owner: str,
        name: str,
        adapter_name: str,
        adapter_version: str,
        spec: dict[str, Any],
        author_id: str,
        ref: str | None = None,
        message: str | None = None,
    ) -> str:
        """POST /jobs/ingest；返 job_id。"""
        request: dict[str, Any] = {
            "adapter_name": adapter_name,
            "adapter_version": adapter_version,
            "spec": spec,
            "author_id": author_id,
        }
        if ref is not None:
            request["ref"] = ref
        if message is not None:
            request["message"] = message
        resp = self._http.post(
            "/jobs/ingest",
            json={"owner": owner, "name": name, "request": request},
        )
        resp.raise_for_status()
        job_id: str = resp.json()["id"]
        return job_id

    def enqueue_process(
        self,
        source_owner: str,
        source_name: str,
        source_ref: str,
        target_owner: str,
        target_name: str,
        processor_name: str,
        processor_version: str,
        config: dict[str, Any],
        author_id: str,
        ref: str | None = None,
        message: str | None = None,
    ) -> str:
        """POST /process；返 job_id。"""
        payload: dict[str, Any] = {
            "source_owner": source_owner,
            "source_name": source_name,
            "source_ref": source_ref,
            "target_owner": target_owner,
            "target_name": target_name,
            "processor_name": processor_name,
            "processor_version": processor_version,
            "config": config,
            "author_id": author_id,
        }
        if ref is not None:
            payload["ref"] = ref
        if message is not None:
            payload["message"] = message
        resp = self._http.post("/process", json=payload)
        resp.raise_for_status()
        job_id: str = resp.json()["id"]
        return job_id

    def get_job(self, job_id: str) -> dict[str, Any]:
        resp = self._http.get(f"/jobs/{job_id}")
        resp.raise_for_status()
        return dict(resp.json())
