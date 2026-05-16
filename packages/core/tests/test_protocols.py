"""8 个 Protocol / 数据类 import 齐全（spec AC-8）。"""

from __future__ import annotations


def test_protocols_full_import_set() -> None:
    from dataplat_core.protocols.adapter import IngestResult, SourceAdapter
    from dataplat_core.protocols.processor import (
        Processor,
        ProcessResult,
        RepoSelector,
        RepoSpec,
        RepoView,
    )
    from dataplat_core.protocols.runcontext import RunContext

    # 实际类型存在 + 不为 None
    assert SourceAdapter is not None
    assert IngestResult is not None
    assert Processor is not None
    assert ProcessResult is not None
    assert RepoView is not None
    assert RepoSelector is not None
    assert RepoSpec is not None
    assert RunContext is not None


def test_repospec_pydantic_validates() -> None:
    from dataplat_core.protocols.processor import RepoSpec

    s = RepoSpec(layer="silver", subtype="text-corpus")
    assert s.layer == "silver"
    assert s.subtype == "text-corpus"
