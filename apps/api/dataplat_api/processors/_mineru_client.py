"""MinerUClient：薄 HTTP 客户端，封装 MinerU 异步 job 接口。

按 spec.md AC-4。三方法：
- submit(pdf_bytes, filename, parse_method) → task_id（POST <base>/tasks，multipart）
- poll(task_id) → dict{status, markdown?}（GET <base>/tasks/{id}）
- fetch_markdown(task_id, poll_interval, poll_timeout) → str（循环 poll 直到 succeeded / failed / 超时）

JSON 解析集中在 _parse_submit_response / _parse_poll_response 两个函数；MinerU
真服务字段名若与假设有差异，仅改这两处。假设：
- submit 响应：{"task_id": "..."} 或 {"id": "..."}
- poll 响应：{"status": "running"|"succeeded"|"failed", "markdown": "..."?, "error": "..."?}
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

import httpx

_logger = logging.getLogger("dataplat.processor.mineru")

_DEFAULT_TIMEOUT = 60.0
_TERMINAL_OK = {"succeeded", "success", "done", "completed"}
_TERMINAL_FAIL = {"failed", "error"}


class MinerUClient:
    """无 state；每次 submit / poll 用 httpx.AsyncClient 一次性请求。"""

    def __init__(
        self,
        base_url: str,
        token: str | None = None,
        request_timeout_seconds: float = _DEFAULT_TIMEOUT,
    ) -> None:
        if not base_url:
            raise ValueError("MinerUClient.base_url 不能为空")
        self._base_url = base_url.rstrip("/")
        self._token = token or None
        self._timeout = request_timeout_seconds

    def _headers(self) -> dict[str, str]:
        if self._token:
            return {"Authorization": f"Bearer {self._token}"}
        return {}

    async def submit(
        self,
        pdf_bytes: bytes,
        filename: str,
        parse_method: str = "auto",
    ) -> str:
        url = f"{self._base_url}/tasks"
        files = {"file": (filename, pdf_bytes, "application/pdf")}
        data = {"parse_method": parse_method}
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(
                url, files=files, data=data, headers=self._headers()
            )
        if resp.status_code != 200:
            raise ValueError(
                f"MinerU submit 非 200：status={resp.status_code} url={url}"
            )
        return _parse_submit_response(resp.json())

    async def poll(self, task_id: str) -> dict[str, Any]:
        url = f"{self._base_url}/tasks/{task_id}"
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.get(url, headers=self._headers())
        if resp.status_code != 200:
            raise ValueError(
                f"MinerU poll 非 200：status={resp.status_code} task_id={task_id}"
            )
        return _parse_poll_response(resp.json())

    async def fetch_markdown(
        self,
        task_id: str,
        poll_interval: float = 5.0,
        poll_timeout: float = 600.0,
    ) -> str:
        deadline = time.monotonic() + poll_timeout
        while True:
            data = await self.poll(task_id)
            status = data.get("status", "")
            if status in _TERMINAL_OK:
                md = data.get("markdown")
                if not isinstance(md, str) or not md:
                    raise ValueError(
                        f"MinerU task {task_id} succeeded 但 markdown 字段缺失或为空"
                    )
                return md
            if status in _TERMINAL_FAIL:
                err = data.get("error") or "(no error message)"
                raise ValueError(
                    f"MinerU task {task_id} failed: {err}"
                )
            if time.monotonic() >= deadline:
                raise ValueError(
                    f"MinerU task {task_id} 轮询超时：> {poll_timeout}s"
                )
            _logger.debug("MinerU task %s status=%s, sleeping %.1fs", task_id, status, poll_interval)
            await asyncio.sleep(poll_interval)


def _parse_submit_response(payload: dict[str, Any]) -> str:
    task_id = payload.get("task_id") or payload.get("id")
    if not isinstance(task_id, str) or not task_id:
        raise ValueError(
            f"MinerU submit 响应无 task_id / id 字段：{payload!r}"
        )
    return task_id


def _parse_poll_response(payload: dict[str, Any]) -> dict[str, Any]:
    status = payload.get("status")
    if not isinstance(status, str):
        raise ValueError(
            f"MinerU poll 响应缺 status 字段或类型错误：{payload!r}"
        )
    return payload
