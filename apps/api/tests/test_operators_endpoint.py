"""GET /operators endpoint 行为测试（web-recipe-structured-config-20260521 AC-2）。

无 DB 依赖：使用 dependency_overrides 覆盖 get_current_user；
OperatorRegistry 由 dataplat_api.main import 时自动完成注册。

验证：
1. GET /operators → 200 + ≥ 11 条 entry
2. 含 name="dedup" 的 entry，version 非空，config_schema.properties.key.enum == ["text", "source_blob"]
"""

from __future__ import annotations

import pytest
from dataplat_api.auth.deps import get_current_user
from dataplat_api.main import app
from dataplat_core.protocols.auth import AuthenticatedUser
from httpx import ASGITransport, AsyncClient


def _fake_user() -> AuthenticatedUser:
    return AuthenticatedUser(
        user_id="test-user-id",
        username="testuser",
        email=None,
        role="user",
        is_active=True,
    )


@pytest.mark.asyncio
async def test_get_operators_returns_entries_with_dedup_schema() -> None:
    """GET /operators → 200；≥ 11 entries；dedup schema 形状正确。"""
    # 覆盖 auth 依赖，避免 DB 依赖
    app.dependency_overrides[get_current_user] = _fake_user
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/operators")

        assert resp.status_code == 200, resp.text
        entries = resp.json()
        assert isinstance(entries, list), f"期望 list，得到 {type(entries)}"
        assert len(entries) >= 11, f"期望 ≥ 11 entries，实际 {len(entries)}"

        # 验证 dedup entry 的 schema 形状
        dedup = next((e for e in entries if e["name"] == "dedup"), None)
        assert dedup is not None, "缺 dedup entry"
        assert dedup["version"], "dedup.version 应非空"

        schema = dedup["config_schema"]
        assert "properties" in schema, f"dedup.config_schema 缺 properties：{schema}"
        key_prop = schema["properties"].get("key", {})
        assert "enum" in key_prop, f"dedup.config_schema.properties.key 缺 enum：{key_prop}"
        assert key_prop["enum"] == ["text", "source_blob"], (
            f"dedup key.enum 不匹配：{key_prop['enum']}"
        )
    finally:
        app.dependency_overrides.pop(get_current_user, None)
