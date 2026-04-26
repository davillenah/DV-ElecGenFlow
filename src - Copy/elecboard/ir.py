from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from pydantic import BaseModel, Field, field_serializer, field_validator, model_validator

from elecgenflow.elecboard.types import (
    BoardLevel,
    BranchKind,
    LoadKind,
    NodeKind,
    Phase,
    SourceKind,
    TopologyKind,
)
from elecgenflow.elecboard.validators import (
    ValidationIssue,
    build_adjacency,
    connected_components,
    connected_from_sources,
    has_cycle_undirected,
    validate_unique_ids,
)


def _as_sorted_list(phases: Iterable[Phase]) -> list[str]:
    return [p.value for p in sorted(set(phases), key=lambda x: x.value)]


def _parse_phases(value: Any) -> set[Phase]:
    if value is None:
        return set()

    raw = list(value) if isinstance(value, (list, tuple, set, frozenset)) else [value]

    parsed: set[Phase] = set()
    for v in raw:
        if isinstance(v, Phase):
            parsed.add(v)
        else:
            parsed.add(Phase(str(v)))
    return parsed


class Board(BaseModel):
    board_id: str
    name: str
    level: BoardLevel
    phases: set[Phase] = Field(default_factory=set)
    node_ids: list[str] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=dict)

    @field_validator("phases", mode="before")
    @classmethod
    def _val_phases(cls, v: Any) -> set[Phase]:
        return _parse_phases(v)

    @field_serializer("phases")
    def _ser_phases(self, v: set[Phase]) -> list[str]:
        return _as_sorted_list(v)


class Node(BaseModel):
    node_id: str
    board_id: str
    phases: set[Phase] = Field(default_factory=set)
    kind: NodeKind = NodeKind.JUNCTION
    meta: dict[str, Any] = Field(default_factory=dict)

    @field_validator("phases", mode="before")
    @classmethod
    def _val_phases(cls, v: Any) -> set[Phase]:
        return _parse_phases(v)

    @field_serializer("phases")
    def _ser_phases(self, v: set[Phase]) -> list[str]:
        return _as_sorted_list(v)


class Branch(BaseModel):
    branch_id: str
    from_node: str
    to_node: str
    kind: BranchKind = BranchKind.FEEDER
    phases: set[Phase] = Field(default_factory=set)
    meta: dict[str, Any] = Field(default_factory=dict)

    @field_validator("phases", mode="before")
    @classmethod
    def _val_phases(cls, v: Any) -> set[Phase]:
        return _parse_phases(v)

    @field_serializer("phases")
    def _ser_phases(self, v: set[Phase]) -> list[str]:
        return _as_sorted_list(v)


class Load(BaseModel):
    load_id: str
    node_id: str
    kind: LoadKind = LoadKind.GENERIC
    phases: set[Phase] = Field(default_factory=set)
    meta: dict[str, Any] = Field(default_factory=dict)

    @field_validator("phases", mode="before")
    @classmethod
    def _val_phases(cls, v: Any) -> set[Phase]:
        return _parse_phases(v)

    @field_serializer("phases")
    def _ser_phases(self, v: set[Phase]) -> list[str]:
        return _as_sorted_list(v)


class Source(BaseModel):
    source_id: str
    node_id: str
    kind: SourceKind = SourceKind.UTILITY
    phases: set[Phase] = Field(default_factory=set)
    meta: dict[str, Any] = Field(default_factory=dict)

    @field_validator("phases", mode="before")
    @classmethod
    def _val_phases(cls, v: Any) -> set[Phase]:
        return _parse_phases(v)

    @field_serializer("phases")
    def _ser_phases(self, v: set[Phase]) -> list[str]:
        return _as_sorted_list(v)


class ElecboardIR(BaseModel):
    """Elecboard IR v1 (Logical Model).

    Structural and explicit model. It excludes electrical magnitudes and simulation engines.
    """

    boards: list[Board] = Field(default_factory=list)
    nodes: list[Node] = Field(default_factory=list)
    branches: list[Branch] = Field(default_factory=list)
    loads: list[Load] = Field(default_factory=list)
    sources: list[Source] = Field(default_factory=list)

    topology: TopologyKind = TopologyKind.UNKNOWN
    allow_islands: bool = False

    meta: dict[str, Any] = Field(default_factory=dict)

    def diagnostics(self) -> list[ValidationIssue]:
        """Return structured issues without raising (useful for reports)."""
        issues: list[ValidationIssue] = []

        board_ids = [b.board_id for b in self.boards]
        node_ids = [n.node_id for n in self.nodes]
        branch_ids = [br.branch_id for br in self.branches]
        load_ids = [load.load_id for load in self.loads]
        source_ids = [s.source_id for s in self.sources]

        issues.extend(
            validate_unique_ids(
                boards=board_ids,
                nodes=node_ids,
                branches=branch_ids,
                loads=load_ids,
                sources=source_ids,
            )
        )

        nodes_by_id: dict[str, Node] = {n.node_id: n for n in self.nodes}
        boards_by_id: dict[str, Board] = {b.board_id: b for b in self.boards}

        # Board references & consistency
        for b in self.boards:
            for nid in b.node_ids:
                if nid not in nodes_by_id:
                    issues.append(
                        ValidationIssue(
                            code="BOARD_NODE_MISSING",
                            message=f"Board '{b.board_id}' references missing node '{nid}'",
                            context={"board_id": b.board_id, "node_id": nid},
                        )
                    )
                else:
                    if nodes_by_id[nid].board_id != b.board_id:
                        issues.append(
                            ValidationIssue(
                                code="BOARD_NODE_MISMATCH",
                                message=(
                                    f"Node '{nid}' belongs to board '{nodes_by_id[nid].board_id}' "
                                    f"but is listed in board '{b.board_id}'"
                                ),
                                context={
                                    "board_id": b.board_id,
                                    "node_id": nid,
                                    "node_board_id": nodes_by_id[nid].board_id,
                                },
                            )
                        )

        # Node -> board existence
        for n in self.nodes:
            if n.board_id not in boards_by_id:
                issues.append(
                    ValidationIssue(
                        code="NODE_BOARD_MISSING",
                        message=f"Node '{n.node_id}' references missing board '{n.board_id}'",
                        context={"node_id": n.node_id, "board_id": n.board_id},
                    )
                )

        # Branch references & phase compatibility
        edges: list[tuple[str, str]] = []
        for br in self.branches:
            if br.from_node not in nodes_by_id:
                issues.append(
                    ValidationIssue(
                        code="BRANCH_FROM_MISSING",
                        message=f"Branch '{br.branch_id}' references missing from_node '{br.from_node}'",
                        context={"branch_id": br.branch_id, "from_node": br.from_node},
                    )
                )
                continue
            if br.to_node not in nodes_by_id:
                issues.append(
                    ValidationIssue(
                        code="BRANCH_TO_MISSING",
                        message=f"Branch '{br.branch_id}' references missing to_node '{br.to_node}'",
                        context={"branch_id": br.branch_id, "to_node": br.to_node},
                    )
                )
                continue

            edges.append((br.from_node, br.to_node))

            fn = nodes_by_id[br.from_node]
            tn = nodes_by_id[br.to_node]
            if br.phases and not (br.phases.issubset(fn.phases) and br.phases.issubset(tn.phases)):
                issues.append(
                    ValidationIssue(
                        code="PHASES_INCOMPATIBLE_BRANCH",
                        message=(
                            f"Branch '{br.branch_id}' phases {sorted([p.value for p in br.phases])} "
                            f"not compatible with nodes '{fn.node_id}' phases {sorted([p.value for p in fn.phases])} "
                            f"and '{tn.node_id}' phases {sorted([p.value for p in tn.phases])}"
                        ),
                        context={
                            "branch_id": br.branch_id,
                            "from_node": br.from_node,
                            "to_node": br.to_node,
                        },
                    )
                )

        # Load references & phase compatibility
        for ld in self.loads:
            if ld.node_id not in nodes_by_id:
                issues.append(
                    ValidationIssue(
                        code="LOAD_NODE_MISSING",
                        message=f"Load '{ld.load_id}' references missing node '{ld.node_id}'",
                        context={"load_id": ld.load_id, "node_id": ld.node_id},
                    )
                )
                continue
            n = nodes_by_id[ld.node_id]
            if ld.phases and not ld.phases.issubset(n.phases):
                issues.append(
                    ValidationIssue(
                        code="PHASES_INCOMPATIBLE_LOAD",
                        message=(
                            f"Load '{ld.load_id}' phases {sorted([p.value for p in ld.phases])} "
                            f"not subset of node '{n.node_id}' phases {sorted([p.value for p in n.phases])}"
                        ),
                        context={"load_id": ld.load_id, "node_id": ld.node_id},
                    )
                )

        # Source references & phase compatibility
        for sc in self.sources:
            if sc.node_id not in nodes_by_id:
                issues.append(
                    ValidationIssue(
                        code="SOURCE_NODE_MISSING",
                        message=f"Source '{sc.source_id}' references missing node '{sc.node_id}'",
                        context={"source_id": sc.source_id, "node_id": sc.node_id},
                    )
                )
                continue
            n = nodes_by_id[sc.node_id]
            if sc.phases and not sc.phases.issubset(n.phases):
                issues.append(
                    ValidationIssue(
                        code="PHASES_INCOMPATIBLE_SOURCE",
                        message=(
                            f"Source '{sc.source_id}' phases {sorted([p.value for p in sc.phases])} "
                            f"not subset of node '{n.node_id}' phases {sorted([p.value for p in n.phases])}"
                        ),
                        context={"source_id": sc.source_id, "node_id": sc.node_id},
                    )
                )

        adjacency = build_adjacency(edges)

        # Orphan nodes: no branch degree and no load/source attached.
        attached_nodes = {load.node_id for load in self.loads if load.node_id in nodes_by_id} | {
            s.node_id for s in self.sources if s.node_id in nodes_by_id
        }
        for n in self.nodes:
            deg = len(adjacency.get(n.node_id, set()))
            if deg == 0 and n.node_id not in attached_nodes:
                issues.append(
                    ValidationIssue(
                        code="ORPHAN_NODE",
                        message=f"Node '{n.node_id}' is orphan (no branch, load, or source attached).",
                        context={"node_id": n.node_id},
                    )
                )

        # Connectivity / islands
        node_id_list = [n.node_id for n in self.nodes]
        source_nodes = {s.node_id for s in self.sources if s.node_id in nodes_by_id}
        if not self.allow_islands:
            if source_nodes:
                reachable = connected_from_sources(node_id_list, adjacency, source_nodes)
                missing = sorted(set(node_id_list) - reachable)
                if missing:
                    issues.append(
                        ValidationIssue(
                            code="DISCONNECTED_FROM_SOURCES",
                            message=f"Nodes not reachable from any source: {missing}",
                            context={"missing_nodes": ",".join(missing)},
                        )
                    )
            else:
                comps = connected_components(node_id_list, adjacency)
                if len(comps) > 1:
                    issues.append(
                        ValidationIssue(
                            code="DISCONNECTED_GRAPH",
                            message=f"Graph has multiple connected components (allow_islands=False): {len(comps)}",
                            context={"components": str([sorted(c) for c in comps])},
                        )
                    )

        # Topology constraint: radial => no cycles

        if self.topology == TopologyKind.RADIAL and has_cycle_undirected(node_id_list, edges):
            issues.append(
                ValidationIssue(
                    code="TOPOLOGY_CYCLE",
                    message="Topology declared as radial but branch graph contains a cycle.",
                    context={"topology": self.topology.value},
                )
            )
        return issues

    @model_validator(mode="after")
    def _validate_ir(self) -> ElecboardIR:
        issues = self.diagnostics()
        if issues:
            lines = [f"{i.code}: {i.message}" for i in issues]
            raise ValueError("ElecboardIR validation failed:\n" + "\n".join(lines))
        return self

    def to_logical_ir_dict(self) -> dict[str, Any]:
        """Serialise to a plain dict suitable for DesignCandidate.logical_ir."""
        return self.model_dump(mode="json")

    @staticmethod
    def from_logical_ir_dict(data: dict[str, Any]) -> ElecboardIR:
        """Parse + validate from a dict (e.g., DesignCandidate.logical_ir)."""
        return ElecboardIR.model_validate(data)
