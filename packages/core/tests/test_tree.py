"""Tree / TreeEntry round-trip + entry_type Literal 校验。"""

from __future__ import annotations

import pytest
from dataplat_core.domain.tree import Tree, TreeEntry
from pydantic import ValidationError


def test_tree_roundtrip_with_entries() -> None:
    e1 = TreeEntry(name="ch01.md", mode=33188, entry_type="blob", target_hash="a" * 64)
    e2 = TreeEntry(name="ch02.md", mode=33188, entry_type="blob", target_hash="b" * 64)
    t = Tree(hash="c" * 64, entries=[e1, e2])
    assert Tree.model_validate_json(t.model_dump_json()) == t
    assert len(t.entries) == 2


def test_tree_empty_entries_allowed() -> None:
    t = Tree(hash="d" * 64, entries=[])
    assert t.entries == []


def test_tree_entry_rejects_invalid_entry_type() -> None:
    with pytest.raises(ValidationError):
        TreeEntry(
            name="bad",
            mode=33188,
            entry_type="commit",  # 应仅 blob/tree
            target_hash="e" * 64,
        )
