"""MinerUClient：薄 HTTP 客户端，封装 MinerU v3 异步 job 接口。

按 spec processor-pdf-mineru-live-fix-20260519。四方法：
- submit(pdf_bytes, filename, parse_method, backend) → task_id
  POST <base>/tasks（multipart，字段名 `files` 数组，状态码 200 或 202）
- poll(task_id) → dict{state, ...}（GET <base>/tasks/{id}，仅取状态）
- fetch_result(task_id) → str（GET <base>/tasks/{id}/result，从响应提 markdown 文本）
- fetch_markdown(task_id, poll_interval, poll_timeout) → str
  循环 poll 到终态；succeeded → fetch_result；failed/超时 → ValueError

鉴权：X-API-Key 头（与 MinerU 3.1.x 部署对齐）。

JSON 解析集中在 _parse_submit_response / _parse_poll_status / _parse_result_payload；
MinerU 真服务字段名若有变体，仅改这三处。fetch_result 的 markdown 提取支持多
layout：顶层 `markdown` / `md_content` / `results[0].markdown` 三种 fallback。
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

import httpx

_logger = logging.getLogger("dataplat.processor.mineru")

_DEFAULT_TIMEOUT = 60.0
_TERMINAL_OK = {"succeeded", "success", "done", "completed", "finished"}
_TERMINAL_FAIL = {"failed", "error", "errored"}


class MinerUClient:
    """无 state；每次 submit / poll / fetch_result 用 httpx.AsyncClient 一次性请求。"""

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
            return {"X-API-Key": self._token}
        return {}

    async def submit(
        self,
        pdf_bytes: bytes,
        filename: str,
        parse_method: str = "auto",
        backend: str = "hybrid-auto-engine",
    ) -> str:
        url = f"{self._base_url}/tasks"
        files = [("files", (filename, pdf_bytes, "application/pdf"))]
        data = {"parse_method": parse_method, "backend": backend}
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.post(
                url, files=files, data=data, headers=self._headers()
            )
        if resp.status_code not in (200, 202):
            raise ValueError(
                f"MinerU submit 非 200/202：status={resp.status_code} url={url}"
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
        return _parse_poll_status(resp.json())

    async def fetch_result(self, task_id: str) -> str:
        url = f"{self._base_url}/tasks/{task_id}/result"
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            resp = await client.get(url, headers=self._headers())
        if resp.status_code != 200:
            raise ValueError(
                f"MinerU fetch_result 非 200：status={resp.status_code} task_id={task_id}"
            )
        return _parse_result_payload(resp.json(), task_id)

    async def fetch_markdown(
        self,
        task_id: str,
        poll_interval: float = 5.0,
        poll_timeout: float = 600.0,
    ) -> str:
        deadline = time.monotonic() + poll_timeout
        while True:
            data = await self.poll(task_id)
            status = _extract_status_string(data)
            if status in _TERMINAL_OK:
                return await self.fetch_result(task_id)
            if status in _TERMINAL_FAIL:
                err = data.get("error") or data.get("message") or "(no error message)"
                raise ValueError(
                    f"MinerU task {task_id} failed: {err}"
                )
            if time.monotonic() >= deadline:
                raise ValueError(
                    f"MinerU task {task_id} 轮询超时：> {poll_timeout}s"
                )
            _logger.debug(
                "MinerU task %s status=%s, sleeping %.1fs",
                task_id,
                status,
                poll_interval,
            )
            await asyncio.sleep(poll_interval)


def _parse_submit_response(payload: dict[str, Any]) -> str:
    task_id = (
        payload.get("task_id")
        or payload.get("id")
        or payload.get("taskId")
    )
    if not isinstance(task_id, str) or not task_id:
        raise ValueError(
            f"MinerU submit 响应无 task_id / id / taskId 字段：keys={list(payload.keys())}"
        )
    return task_id


def _parse_poll_status(payload: dict[str, Any]) -> dict[str, Any]:
    if _extract_status_string(payload) == "":
        raise ValueError(
            f"MinerU poll 响应缺 status / state 字段：keys={list(payload.keys())}"
        )
    return payload


def _extract_status_string(payload: dict[str, Any]) -> str:
    """兼容 status / state 两种命名（MinerU 不同版本变体）。"""
    for key in ("status", "state"):
        val = payload.get(key)
        if isinstance(val, str) and val:
            return val.lower()
    return ""


def _parse_result_payload(payload: dict[str, Any], task_id: str) -> str:
    """MinerU /result 响应提 markdown 文本。

    多 layout fallback：
    1) 顶层 `markdown`：MVP 假设
    2) 顶层 `md_content`：mineru-cli 风格
    3) `results[0].markdown` / `results[0].md_content`：批处理风格
    4) 顶层 `data.markdown` / `data.md_content`：包了一层 data 的风格

    全失败 → 抛 ValueError 列出 keys，便于联调时定位真实 layout。
    """
    md = payload.get("markdown") or payload.get("md_content")
    if isinstance(md, str) and md:
        return md
    data = payload.get("data")
    if isinstance(data, dict):
        md = data.get("markdown") or data.get("md_content")
        if isinstance(md, str) and md:
            return md
    results = payload.get("results")
    if isinstance(results, list) and results and isinstance(results[0], dict):
        md = results[0].get("markdown") or results[0].get("md_content")
        if isinstance(md, str) and md:
            return md
    raise ValueError(
        f"MinerU task {task_id} /result 无 markdown 字段；"
        f"已尝试 markdown / md_content / data.* / results[0].* 全 miss；"
        f"top-level keys={list(payload.keys())}"
    )
