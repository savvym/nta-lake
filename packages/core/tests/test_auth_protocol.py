"""AuthProvider Protocol + AuthenticatedUser 单元测试。"""

from __future__ import annotations

from typing import Protocol

import pytest
from dataplat_core.protocols.auth import AuthenticatedUser, AuthProvider
from pydantic import BaseModel, ValidationError


def test_auth_provider_is_runtime_checkable_protocol() -> None:
    assert issubclass(AuthProvider, Protocol)
    assert getattr(AuthProvider, "_is_runtime_protocol", False) is True


def test_authenticated_user_roundtrip() -> None:
    u = AuthenticatedUser(
        user_id="abc",
        username="alice",
        email="alice@example.com",
        role="admin",
        is_active=True,
    )
    j = u.model_dump_json()
    assert AuthenticatedUser.model_validate_json(j) == u
    assert issubclass(AuthenticatedUser, BaseModel)


def test_authenticated_user_allows_null_email() -> None:
    u = AuthenticatedUser(user_id="x", username="bob", role="user", is_active=True)
    assert u.email is None


def test_authenticated_user_rejects_extra_field() -> None:
    with pytest.raises(ValidationError):
        AuthenticatedUser(
            user_id="x",
            username="bob",
            role="user",
            is_active=True,
            bogus_extra="not allowed",
        )
