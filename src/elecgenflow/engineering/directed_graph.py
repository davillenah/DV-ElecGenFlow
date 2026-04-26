from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class DirectedGraphReport:
    version: str
    roots: list[str]
    nodes: list[str]
    edges: list[dict[str, Any]]
    reachable: list[str]
    unreachable: list[str]
    has_cycle: bool
    cycles: list[list[str]]


def _edge_dst(lk: dict[str, Any]) -> str:
    d = lk.get("destination") or {}
    load_tag = d.get("load")
    if isinstance(load_tag, str) and load_tag:
        return f"LOAD:{load_tag}"
    db = d.get("board")
    return db if isinstance(db, str) else ""


def _edge_src(lk: dict[str, Any]) -> str:
    o = lk.get("origin") or {}
    ob = o.get("board")
    return ob if isinstance(ob, str) else ""


class DirectedElectricalGraphService:
    """
    EPIC-04.02:
    - Construye grafo dirigido desde compiled_links (runtime output del compiler).
    - Incluye nodos in_service aunque no tengan aristas (para detectar desconectados).
    - Roots = indegree 0 con outdegree > 0 (fuentes reales de alimentación).
    - Alcanzabilidad desde roots.
    - Ciclos dirigidos (DFS).
    """

    @staticmethod
    def build_report(
        *,
        compiled_links: list[dict[str, Any]],
        in_service_boards: set[str],
        out_of_service_boards: set[str],
        assembly_columns: dict[str, dict[str, str]] | None = None,
        include_assembly_edges: bool = True,
    ) -> dict[str, Any]:
        asm_cols = assembly_columns or {}

        adj: dict[str, list[str]] = {}
        edges: list[dict[str, Any]] = []

        # ✅ incluir todos los boards in_service como nodos (aunque estén aislados)
        nodes: set[str] = set(in_service_boards)

        # assembly -> column edges (opcional)
        if include_assembly_edges:
            for asm, colmap in asm_cols.items():
                if asm not in in_service_boards:
                    continue
                nodes.add(asm)
                for col, board_tag in colmap.items():
                    if board_tag in in_service_boards:
                        adj.setdefault(asm, []).append(board_tag)
                        edges.append(
                            {
                                "from": asm,
                                "to": board_tag,
                                "kind": "assembly_column",
                                "wire": "",
                                "meta": {"column": col, "board": board_tag},
                            }
                        )
                        nodes.add(board_tag)

        # network edges (feeders)
        for lk in compiled_links:
            src = _edge_src(lk)
            dst = _edge_dst(lk)
            if not src or not dst:
                continue
            if src in out_of_service_boards:
                continue

            # dst puede ser LOAD:* o board (in_service u out_of_service); lo incluimos igual como nodo
            nodes.add(src)
            nodes.add(dst)

            adj.setdefault(src, []).append(dst)
            edges.append(
                {
                    "from": src,
                    "to": dst,
                    "kind": "feeder",
                    "wire": lk.get("wire"),
                    "meta": lk.get("meta") or {},
                }
            )

        # indegree / outdegree
        indeg: dict[str, int] = dict.fromkeys(nodes, 0)
        outdeg: dict[str, int] = dict.fromkeys(nodes, 0)

        for _u, vs in adj.items():  # ✅ ruff B007 fix
            outdeg[_u] = outdeg.get(_u, 0) + len(vs)
            for v in vs:
                indeg[v] = indeg.get(v, 0) + 1

        # ✅ roots = indegree 0 AND outdegree > 0 (fuentes reales)
        roots = sorted([n for n in nodes if indeg.get(n, 0) == 0 and outdeg.get(n, 0) > 0])

        # reachable desde roots
        reachable_set: set[str] = set()
        q: deque[str] = deque(roots)
        while q:
            u = q.popleft()
            if u in reachable_set:
                continue
            reachable_set.add(u)
            for v in adj.get(u, []):
                if v not in reachable_set:
                    q.append(v)

        reachable = sorted(reachable_set)
        unreachable = sorted(nodes - reachable_set)

        # ciclos dirigidos
        colour: dict[str, int] = dict.fromkeys(nodes, 0)  # 0 unvisited, 1 visiting, 2 done
        parent: dict[str, str] = {}
        cycles: list[list[str]] = []

        def record_cycle(start: str, end: str) -> None:
            path: list[str] = [end]
            cur = end
            while cur != start and cur in parent:
                cur = parent[cur]
                path.append(cur)
            path.reverse()
            cycles.append(path)

        def dfs(u: str) -> None:
            colour[u] = 1
            for v in adj.get(u, []):
                if v not in colour:
                    colour[v] = 0
                if colour[v] == 0:
                    parent[v] = u
                    dfs(v)
                elif colour[v] == 1:
                    record_cycle(v, u)
            colour[u] = 2

        for n in nodes:
            if colour[n] == 0:
                dfs(n)

        # dedup cycles
        def canon(c: list[str]) -> tuple[str, ...]:
            if not c:
                return ()  # ✅ ruff C408 fix
            m = min(c)
            i = c.index(m)
            rot = c[i:] + c[:i]
            return tuple(rot)

        uniq: dict[tuple[str, ...], list[str]] = {}
        for c in cycles:
            k = canon(c)
            if k and k not in uniq:
                uniq[k] = c

        cycles_out = list(uniq.values())
        has_cycle = len(cycles_out) > 0

        report = DirectedGraphReport(
            version="0.2",
            roots=roots,
            nodes=sorted(nodes),
            edges=edges,
            reachable=reachable,
            unreachable=unreachable,
            has_cycle=has_cycle,
            cycles=cycles_out,
        )

        return {
            "version": report.version,
            "roots": report.roots,
            "nodes": report.nodes,
            "edges": report.edges,
            "reachable": report.reachable,
            "unreachable": report.unreachable,
            "has_cycle": report.has_cycle,
            "cycles": report.cycles,
            "notes": {
                "include_assembly_edges": include_assembly_edges,
                "root_definition": "indegree==0 and outdegree>0",
            },
        }

    @staticmethod
    def to_markdown(dag_report: dict[str, Any]) -> str:
        lines: list[str] = []
        lines.append("# DAG Report (EPIC-04.02)")
        lines.append("")
        lines.append(f"**Roots:** {', '.join(dag_report.get('roots') or [])}")
        lines.append(f"**Nodes:** {len(dag_report.get('nodes') or [])}")
        lines.append(f"**Edges:** {len(dag_report.get('edges') or [])}")
        lines.append(f"**Has cycle:** {dag_report.get('has_cycle')}")
        lines.append("")

        unreachable = dag_report.get("unreachable") or []
        if unreachable:
            lines.append("## Unreachable nodes")
            lines.append("")
            for n in unreachable:
                lines.append(f"- {n}")
            lines.append("")

        cycles = dag_report.get("cycles") or []
        if cycles:
            lines.append("## Cycles")
            lines.append("")
            for i, c in enumerate(cycles, start=1):
                lines.append(f"- Cycle {i}: {' -> '.join(c)}")
            lines.append("")

        lines.append("## Edges")
        lines.append("")
        lines.append("| From | To | Kind | Wire |")
        lines.append("|---|---|---|---|")
        for e in dag_report.get("edges") or []:
            lines.append(
                f"| {e.get('from','')} | {e.get('to','')} | {e.get('kind','')} | {e.get('wire','')} |"
            )

        return "\n".join(lines)
