"""DAG 拓扑排序 + 环检测（spec pipeline-orchestrator-mvp-20260518 T-3，AC-2）。

无副作用纯函数；供 PipelineOrchestrator 入口校验 + 节点遍历顺序使用。
"""

from __future__ import annotations

from collections import deque
from typing import Any

from dataplat_api.schemas.pipeline import Recipe, parse_input_ref


def topo_sort(nodes: list[dict[str, Any]]) -> list[str]:
    """Kahn 算法拓扑排序。

    Args:
        nodes: 每元素 ``{"id": str, "deps": list[str]}``；deps 是 id 的列表。

    Returns:
        排序后的 id 列表（同层稳定按输入顺序）。

    Raises:
        ValueError: 含环 / deps 引用了不存在的 id / id 重复。
    """
    ids: list[str] = []
    deps_map: dict[str, list[str]] = {}
    for n in nodes:
        nid = n["id"]
        if nid in deps_map:
            raise ValueError(f"重复 node id: {nid}")
        ids.append(nid)
        deps_map[nid] = list(n.get("deps", []))

    valid = set(deps_map)
    for nid, deps in deps_map.items():
        unknown = [d for d in deps if d not in valid]
        if unknown:
            raise ValueError(
                f"node {nid!r} 引用未知 deps: {unknown}"
            )

    indegree: dict[str, int] = {nid: len(deps_map[nid]) for nid in ids}
    children: dict[str, list[str]] = {nid: [] for nid in ids}
    for nid in ids:
        for d in deps_map[nid]:
            children[d].append(nid)

    # 稳定 BFS：按输入顺序入队
    queue: deque[str] = deque(nid for nid in ids if indegree[nid] == 0)
    ordered: list[str] = []
    while queue:
        cur = queue.popleft()
        ordered.append(cur)
        for nxt in children[cur]:
            indegree[nxt] -= 1
            if indegree[nxt] == 0:
                queue.append(nxt)

    if len(ordered) != len(ids):
        remaining = [nid for nid in ids if indegree[nid] > 0]
        raise ValueError(f"cycle detected involving: {remaining}")

    return ordered


def build_node_deps(recipe: Recipe) -> list[dict[str, Any]]:
    """把 Recipe.nodes[].inputs 中 `@<node-id>` 形式抽出为 deps；
    `<layer>/<owner>/<name>@<ref>` 形式不入 deps（外部 ref 输入）。

    返回 ``[{"id": str, "deps": list[str]}]``，可直接喂 ``topo_sort``。
    """
    out: list[dict[str, Any]] = []
    for node in recipe.nodes:
        deps: list[str] = []
        for ref in node.inputs:
            kind, parts = parse_input_ref(ref)
            if kind == "node":
                deps.append(parts["node_id"])
        out.append({"id": node.id, "deps": deps})
    return out
