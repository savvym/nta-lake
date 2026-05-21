"""集成 smoke test（W4-6 integration-test-framework-20260520）。

目的：保证 integration_test.sh 真执行了一条 env-gated 测试，
      防止 script up 之后 pytest 命令空跑或路径错。

验收标准 AC-3：
  - env 就位（DATAPLAT_DATABASE_URL 已设）→ 1 passed
  - env 缺位 → 1 skipped（整个模块 pytestmark skipif）

测试内容：httpx ASGI transport → GET /healthz → 200 + body.status == "ok"。
"""

from __future__ import annotations

import os

import httpx
import pytest
from dataplat_api.main import app


def _database_url() -> str | None:
    return os.environ.get("DATAPLAT_DATABASE_URL")


pytestmark = pytest.mark.skipif(
    not _database_url(),
    reason="DATAPLAT_DATABASE_URL 未设置；integration smoke test 跳过",
)


@pytest.mark.anyio
async def test_health_ok() -> None:
    """GET /healthz → 200 + body.status == "ok"（ASGI transport，不需要真实网络）。"""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.get("/healthz")

    assert response.status_code == 200, f"期望 200，得到 {response.status_code}"
    body = response.json()
    assert body.get("status") == "ok", f"期望 status=ok，得到 {body}"
