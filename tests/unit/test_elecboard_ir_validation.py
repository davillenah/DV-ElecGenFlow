from __future__ import annotations

import json
from pathlib import Path

import pytest

from elecgenflow.elecboard.ir import Board, Branch, ElecboardIR, Load, Node, Source
from elecgenflow.elecboard.types import (
    BoardLevel,
    BranchKind,
    LoadKind,
    NodeKind,
    Phase,
    SourceKind,
    TopologyKind,
)


def make_minimal_ok_ir() -> ElecboardIR:
    board = Board(
        board_id="B1",
        name="Main LV Board",
        level=BoardLevel.LV,
        phases=[Phase.L1, Phase.L2, Phase.L3, Phase.N, Phase.PE],
        node_ids=["N1", "N2"],
        meta={"tag": "demo-board"},
    )
    n1 = Node(
        node_id="N1",
        board_id="B1",
        kind=NodeKind.BUS,
        phases=[Phase.L1, Phase.L2, Phase.L3, Phase.N, Phase.PE],
    )
    n2 = Node(
        node_id="N2",
        board_id="B1",
        kind=NodeKind.TERMINAL,
        phases=[Phase.L1, Phase.L2, Phase.L3, Phase.N, Phase.PE],
    )

    br = Branch(
        branch_id="BR1",
        from_node="N1",
        to_node="N2",
        kind=BranchKind.FEEDER,
        phases=[Phase.L1, Phase.L2, Phase.L3, Phase.N],
    )

    src = Source(
        source_id="S1",
        node_id="N1",
        kind=SourceKind.UTILITY,
        phases=[Phase.L1, Phase.L2, Phase.L3, Phase.N],
    )
    ld = Load(
        load_id="L1",
        node_id="N2",
        kind=LoadKind.GENERIC,
        phases=[Phase.L1, Phase.L2, Phase.L3, Phase.N],
    )

    return ElecboardIR(
        boards=[board],
        nodes=[n1, n2],
        branches=[br],
        sources=[src],
        loads=[ld],
        topology=TopologyKind.RADIAL,
        allow_islands=False,
        meta={"spec": "EPIC-3 test"},
    )


def test_minimal_ir_is_valid_and_roundtrips() -> None:
    ir = make_minimal_ok_ir()
    d = ir.to_logical_ir_dict()
    ir2 = ElecboardIR.from_logical_ir_dict(d)
    assert ir2.model_dump() == ir.model_dump()


def test_orphan_node_rejected_when_unattached() -> None:
    board = Board(
        board_id="B1", name="Main", level=BoardLevel.LV, phases=[Phase.L1, Phase.N], node_ids=["N1"]
    )
    n1 = Node(node_id="N1", board_id="B1", kind=NodeKind.JUNCTION, phases=[Phase.L1, Phase.N])
    # No branches, loads, or sources -> orphan node
    with pytest.raises(ValueError):
        ElecboardIR(boards=[board], nodes=[n1])


def test_missing_branch_endpoint_rejected() -> None:
    ir = make_minimal_ok_ir()
    ir.branches = [
        Branch(
            branch_id="BRX",
            from_node="N1",
            to_node="N999",  # missing
            kind=BranchKind.FEEDER,
            phases=[Phase.L1, Phase.N],
        )
    ]
    with pytest.raises(ValueError):
        ElecboardIR.model_validate(ir.model_dump())


def test_branch_phase_incompatible_rejected() -> None:
    # Make N2 only L1+N but branch uses L1+L2+L3+N
    ir = make_minimal_ok_ir()
    ir.nodes = [
        ir.nodes[0],
        Node(node_id="N2", board_id="B1", kind=NodeKind.TERMINAL, phases=[Phase.L1, Phase.N]),
    ]
    with pytest.raises(ValueError):
        ElecboardIR.model_validate(ir.model_dump())


def test_disconnected_from_sources_rejected_when_allow_islands_false() -> None:
    # Two components, but only one source => nodes in the other component are unreachable.
    b = Board(
        board_id="B1",
        name="Main",
        level=BoardLevel.LV,
        phases=[Phase.L1, Phase.N],
        node_ids=["A1", "A2", "B1", "B2"],
    )
    nodes = [
        Node(node_id="A1", board_id="B1", phases=[Phase.L1, Phase.N], kind=NodeKind.BUS),
        Node(node_id="A2", board_id="B1", phases=[Phase.L1, Phase.N], kind=NodeKind.TERMINAL),
        Node(node_id="B1", board_id="B1", phases=[Phase.L1, Phase.N], kind=NodeKind.BUS),
        Node(node_id="B2", board_id="B1", phases=[Phase.L1, Phase.N], kind=NodeKind.TERMINAL),
    ]
    branches = [
        Branch(
            branch_id="A12",
            from_node="A1",
            to_node="A2",
            phases=[Phase.L1, Phase.N],
            kind=BranchKind.FEEDER,
        ),
        Branch(
            branch_id="B12",
            from_node="B1",
            to_node="B2",
            phases=[Phase.L1, Phase.N],
            kind=BranchKind.FEEDER,
        ),
    ]
    sources = [
        Source(source_id="SA", node_id="A1", phases=[Phase.L1, Phase.N], kind=SourceKind.UTILITY),
    ]
    loads = [
        Load(load_id="LA", node_id="A2", phases=[Phase.L1, Phase.N], kind=LoadKind.GENERIC),
        Load(load_id="LB", node_id="B2", phases=[Phase.L1, Phase.N], kind=LoadKind.GENERIC),
    ]

    with pytest.raises(ValueError):
        ElecboardIR(
            boards=[b],
            nodes=nodes,
            branches=branches,
            sources=sources,
            loads=loads,
            topology=TopologyKind.UNKNOWN,
            allow_islands=False,
        )


def test_allow_islands_allows_disconnected_components() -> None:
    # Two separate components, each with a source. allow_islands=True should accept.
    b = Board(
        board_id="B1",
        name="Main",
        level=BoardLevel.LV,
        phases=[Phase.L1, Phase.N],
        node_ids=["A1", "A2", "B1", "B2"],
    )
    nodes = [
        Node(node_id="A1", board_id="B1", phases=[Phase.L1, Phase.N], kind=NodeKind.BUS),
        Node(node_id="A2", board_id="B1", phases=[Phase.L1, Phase.N], kind=NodeKind.TERMINAL),
        Node(node_id="B1", board_id="B1", phases=[Phase.L1, Phase.N], kind=NodeKind.BUS),
        Node(node_id="B2", board_id="B1", phases=[Phase.L1, Phase.N], kind=NodeKind.TERMINAL),
    ]
    branches = [
        Branch(
            branch_id="A12",
            from_node="A1",
            to_node="A2",
            phases=[Phase.L1, Phase.N],
            kind=BranchKind.FEEDER,
        ),
        Branch(
            branch_id="B12",
            from_node="B1",
            to_node="B2",
            phases=[Phase.L1, Phase.N],
            kind=BranchKind.FEEDER,
        ),
    ]
    sources = [
        Source(source_id="SA", node_id="A1", phases=[Phase.L1, Phase.N], kind=SourceKind.UTILITY),
        Source(source_id="SB", node_id="B1", phases=[Phase.L1, Phase.N], kind=SourceKind.GENERATOR),
    ]
    loads = [
        Load(load_id="LA", node_id="A2", phases=[Phase.L1, Phase.N], kind=LoadKind.GENERIC),
        Load(load_id="LB", node_id="B2", phases=[Phase.L1, Phase.N], kind=LoadKind.GENERIC),
    ]

    ir = ElecboardIR(
        boards=[b],
        nodes=nodes,
        branches=branches,
        sources=sources,
        loads=loads,
        topology=TopologyKind.UNKNOWN,
        allow_islands=True,
    )
    assert ir.allow_islands is True


def test_radial_cycle_rejected() -> None:
    # Triangle cycle N1-N2-N3-N1
    board = Board(
        board_id="B1",
        name="Main",
        level=BoardLevel.LV,
        phases=[Phase.L1, Phase.L2, Phase.L3, Phase.N],
        node_ids=["N1", "N2", "N3"],
    )
    nodes = [
        Node(
            node_id="N1",
            board_id="B1",
            kind=NodeKind.BUS,
            phases=[Phase.L1, Phase.L2, Phase.L3, Phase.N],
        ),
        Node(
            node_id="N2",
            board_id="B1",
            kind=NodeKind.JUNCTION,
            phases=[Phase.L1, Phase.L2, Phase.L3, Phase.N],
        ),
        Node(
            node_id="N3",
            board_id="B1",
            kind=NodeKind.JUNCTION,
            phases=[Phase.L1, Phase.L2, Phase.L3, Phase.N],
        ),
    ]
    branches = [
        Branch(
            branch_id="BR12",
            from_node="N1",
            to_node="N2",
            kind=BranchKind.FEEDER,
            phases=[Phase.L1, Phase.N],
        ),
        Branch(
            branch_id="BR23",
            from_node="N2",
            to_node="N3",
            kind=BranchKind.FEEDER,
            phases=[Phase.L1, Phase.N],
        ),
        Branch(
            branch_id="BR31",
            from_node="N3",
            to_node="N1",
            kind=BranchKind.TIE,
            phases=[Phase.L1, Phase.N],
        ),
    ]
    src = Source(source_id="S1", node_id="N1", kind=SourceKind.UTILITY, phases=[Phase.L1, Phase.N])

    with pytest.raises(ValueError):
        ElecboardIR(
            boards=[board],
            nodes=nodes,
            branches=branches,
            sources=[src],
            topology=TopologyKind.RADIAL,
            allow_islands=False,
        )


def test_example_json_file_validates() -> None:
    # Requires examples/elecboard_ir_minimal.json to exist
    path = Path("examples/elecboard_ir_minimal.json")
    if not path.exists():
        pytest.skip("examples/elecboard_ir_minimal.json not found")
    data = json.loads(path.read_text(encoding="utf-8"))
    ElecboardIR.model_validate(data)
