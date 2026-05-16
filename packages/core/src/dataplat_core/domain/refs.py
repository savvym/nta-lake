"""Ref：可变指针，指向某个 Commit。

类 Git ref：`main` / `dev` / `v1.0` / `pr-7` 等均落到 refs 表的一行。
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from dataplat_core.domain.types import SHA256


class Ref(BaseModel):
    model_config = ConfigDict(frozen=False, extra="forbid")

    repo_id: str
    name: str = Field(min_length=1, pattern=r"^[A-Za-z0-9][\w./-]*$")
    commit_hash: SHA256
