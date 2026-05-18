"""ProcessorRunner.run 加 lineage 参数后既有 POST /process 路径回归
（spec pipeline-orchestrator-mvp-20260518 T-7a / R-1 缓解 / AC-5）。

只验证签名兼容（不传 lineage 时默认 None）+ 既有 routers/process.py 调用路径不需要改。
"""

from __future__ import annotations

import inspect

from dataplat_api.runner.processor_runner import ProcessorRunner


def test_processor_runner_smoke_lineage_optional() -> None:
    """lineage 参数必须有默认值 None（向后兼容）。"""
    sig = inspect.signature(ProcessorRunner.run)
    assert "lineage" in sig.parameters
    p = sig.parameters["lineage"]
    assert p.default is None


def test_processor_runner_lineage_after_existing_required_params() -> None:
    """lineage 参数必须放在 既有 required 参数之后（不破坏既有 positional 调用）。"""
    sig = inspect.signature(ProcessorRunner.run)
    params = list(sig.parameters.values())
    # 找 lineage 索引
    names = [p.name for p in params]
    li = names.index("lineage")
    # required 参数（无 default）必须都在 lineage 前面
    for p in params[:li]:
        assert p.default is not inspect.Parameter.empty or p.name in {
            "session",
            "store",
            "source_repo_id",
            "source_commit_hash",
            "target_repo_id",
            "processor_name",
            "processor_version",
            "config",
            "author_id",
        }
