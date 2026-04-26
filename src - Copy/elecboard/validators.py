from __future__ import annotations

from collections import defaultdict, deque
from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str
    context: dict[str, str]


def _dedup_ids(ids: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    dup: set[str] = set()
    for i in ids:
        if i in seen:
            dup.add(i)
        seen.add(i)
    return sorted(dup)


def validate_unique_ids(
    *,
    boards: list[str],
    nodes: list[str],
    branches: list[str],
    loads: list[str],
    sources: list[str],
) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    for label, ids in [
        ("board_id", boards),
        ("node_id", nodes),
        ("branch_id", branches),
        ("load_id", loads),
        ("source_id", sources),
    ]:
        dups = _dedup_ids(ids)
        for d in dups:
            issues.append(
                ValidationIssue(
                    code="DUPLICATE_ID",
                    message=f"Duplicate {label}: '{d}'",
                    context={"id": d, "field": label},
                )
            )
    return issues


def build_adjacency(branch_edges: list[tuple[str, str]]) -> dict[str, set[str]]:
    adj: dict[str, set[str]] = defaultdict(set)
    for a, b in branch_edges:
        adj[a].add(b)
        adj[b].add(a)
    return dict(adj)


def connected_from_sources(
    node_ids: list[str],
    adjacency: dict[str, set[str]],
    source_nodes: set[str],
) -> set[str]:
    """Return nodes reachable from at least one source node via branches."""
    if not source_nodes:
        return set()

    node_set = set(node_ids)
    visited: set[str] = set()
    q: deque[str] = deque()

    for s in source_nodes:
        if s in node_set:
            visited.add(s)
            q.append(s)

    while q:
        u = q.popleft()
        for v in adjacency.get(u, set()):
            if v not in visited:
                visited.add(v)
                q.append(v)

    return visited


def connected_components(node_ids: list[str], adjacency: dict[str, set[str]]) -> list[set[str]]:
    """Connected components over the branch graph (undirected)."""
    remaining = set(node_ids)
    comps: list[set[str]] = []
    while remaining:
        start = next(iter(remaining))
        comp: set[str] = set()
        q: deque[str] = deque([start])
        remaining.remove(start)
        comp.add(start)

        while q:
            u = q.popleft()
            for v in adjacency.get(u, set()):
                if v in remaining:
                    remaining.remove(v)
                    comp.add(v)
                    q.append(v)

        comps.append(comp)

    return comps


def has_cycle_undirected(node_ids: list[str], edges: list[tuple[str, str]]) -> bool:
    """Detect cycles in an undirected graph via Union-Find."""
    parent: dict[str, str] = {n: n for n in node_ids}
    rank: dict[str, int] = dict.fromkeys(node_ids, 0)

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a: str, b: str) -> bool:
        ra, rb = find(a), find(b)
        if ra == rb:
            return True  # cycle detected
        if rank[ra] < rank[rb]:
            parent[ra] = rb
        elif rank[ra] > rank[rb]:
            parent[rb] = ra
        else:
            parent[rb] = ra
            rank[ra] += 1
        return False

    for a, b in edges:
        if a not in parent or b not in parent:
            continue
        if union(a, b):
            return True

    return False
