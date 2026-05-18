"""Pipeline / Recipe schemas（spec pipeline-orchestrator-mvp-20260518 T-1）。

对齐 design.md §4.3 DSL：
- 节点 `processor` 形如 `<name>@<version>`；
- 节点 `inputs[*]` 形如 `@<node-id>`（链上上游节点）或 `<layer>/<owner>/<name>@<ref>`（既存 repo ref）；
- 节点 `output` 形如 `<layer>/<owner>/<name>@<ref>` 或 `<layer>/<owner>/<name>@auto`。

字段级 validator 在 schema 阶段早抛错（v2 SHOULD #4 反哺），避免 topo_sort 期才报错。
"""

from __future__ import annotations

import re
from typing import Any, Literal

import yaml  # type: ignore[import-untyped]
from pydantic import BaseModel, ConfigDict, Field, field_validator

# `<layer>/<owner>/<name>@<ref>`；layer/owner/name 允许 [a-zA-Z0-9_-]，ref 允许 [a-zA-Z0-9_.-]
_REPO_REF_PATTERN = re.compile(
    r"^(?P<layer>bronze|silver|gold)/(?P<owner>[A-Za-z0-9_-]+)/(?P<name>[A-Za-z0-9_-]+)@(?P<ref>[A-Za-z0-9_.-]+)$"
)
# `@<node-id>`；node-id 允许 [a-zA-Z0-9_-]
_NODE_REF_PATTERN = re.compile(r"^@(?P<node_id>[A-Za-z0-9_-]+)$")
# `<name>@<version>`；name [a-zA-Z0-9_-]，version [a-zA-Z0-9_.-]
_PROCESSOR_REF_PATTERN = re.compile(
    r"^(?P<name>[A-Za-z0-9_-]+)@(?P<version>[A-Za-z0-9_.-]+)$"
)


def parse_processor_ref(ref: str) -> tuple[str, str]:
    m = _PROCESSOR_REF_PATTERN.match(ref)
    if m is None:
        raise ValueError(
            f"非法 processor 引用 {ref!r}；期望形如 'name@version'"
        )
    return m.group("name"), m.group("version")


def parse_input_ref(
    ref: str,
) -> tuple[Literal["node", "repo"], dict[str, str]]:
    """返回 (kind, parts)；kind=='node' → parts={'node_id': ...}；
    kind=='repo' → parts={'layer','owner','name','ref'}。"""
    m_node = _NODE_REF_PATTERN.match(ref)
    if m_node is not None:
        return "node", {"node_id": m_node.group("node_id")}
    m_repo = _REPO_REF_PATTERN.match(ref)
    if m_repo is not None:
        return "repo", {
            "layer": m_repo.group("layer"),
            "owner": m_repo.group("owner"),
            "name": m_repo.group("name"),
            "ref": m_repo.group("ref"),
        }
    raise ValueError(
        f"非法 input 引用 {ref!r}；期望形如 '@<node-id>' 或 '<layer>/<owner>/<name>@<ref>'"
    )


def parse_output_ref(ref: str) -> dict[str, str]:
    """output 必须是 `<layer>/<owner>/<name>@<ref>` 形态（含 `@auto`）。"""
    m = _REPO_REF_PATTERN.match(ref)
    if m is None:
        raise ValueError(
            f"非法 output 引用 {ref!r}；期望形如 '<layer>/<owner>/<name>@<ref>' 或 '...@auto'"
        )
    return {
        "layer": m.group("layer"),
        "owner": m.group("owner"),
        "name": m.group("name"),
        "ref": m.group("ref"),
    }


class RecipeNode(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    processor: str
    # v2 SHOULD FIX #4：min_length=1 拦空 inputs；MVP single-input only 由 orchestrator
    # validate_recipe 再补一道（拦 len!=1）。
    inputs: list[str] = Field(min_length=1)
    config: dict[str, Any] = Field(default_factory=dict)
    output: str

    @field_validator("processor")
    @classmethod
    def _check_processor(cls, v: str) -> str:
        parse_processor_ref(v)
        return v

    @field_validator("inputs")
    @classmethod
    def _check_inputs(cls, v: list[str]) -> list[str]:
        for ref in v:
            parse_input_ref(ref)
        return v

    @field_validator("output")
    @classmethod
    def _check_output(cls, v: str) -> str:
        parse_output_ref(v)
        return v


class Recipe(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1)
    nodes: list[RecipeNode]


def load_recipe(data: str | dict[str, Any]) -> Recipe:
    """YAML 文本走 yaml.safe_load 解析；dict 直接 model_validate。"""
    if isinstance(data, str):
        parsed = yaml.safe_load(data)
        if not isinstance(parsed, dict):
            raise ValueError(
                f"recipe YAML 顶层必须是 mapping，实际 {type(parsed).__name__}"
            )
        return Recipe.model_validate(parsed)
    return Recipe.model_validate(data)


class RecipeCreateRequest(BaseModel):
    """POST /pipelines/runs JSON 入口 body（T-6a）。"""

    model_config = ConfigDict(extra="forbid")

    recipe: Recipe


class PipelineNodeRunResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    node_id: str
    processor_name: str
    processor_version: str
    config: dict[str, Any]
    status: str
    cache_hit: bool
    output_commit_hash: str | None = None
    # stage 4 SHOULD #1：error 兜底路径解析未完成时为 None
    input_commits: list[str] | None = None
    cache_key: str | None = None
    error: str | None = None


class PipelineRunResponse(BaseModel):
    """GET /pipelines/runs/{run_id} response（T-6a）。"""

    model_config = ConfigDict(extra="forbid")

    run_id: str
    recipe_name: str
    status: str
    error: str | None = None
    created_by: str
    node_runs: list[PipelineNodeRunResponse]


class PipelineRunCreatedResponse(BaseModel):
    """POST /pipelines/runs 202 response。"""

    model_config = ConfigDict(extra="forbid")

    run_id: str
    job_id: str
