from __future__ import annotations

from elecgenflow.engineering.directed_graph import DirectedElectricalGraphService


def test_dag_roots_and_reachability_simple_chain() -> None:
    compiled_links = [
        {"origin": {"board": "A"}, "destination": {"board": "B"}, "wire": "W1", "meta": {}},
        {"origin": {"board": "B"}, "destination": {"board": "C"}, "wire": "W2", "meta": {}},
    ]
    rep = DirectedElectricalGraphService.build_report(
        compiled_links=compiled_links,
        in_service_boards={"A", "B", "C"},
        out_of_service_boards=set(),
        assembly_columns={},
        include_assembly_edges=False,
    )
    assert rep["roots"] == ["A"]
    assert rep["has_cycle"] is False
    assert rep["unreachable"] == []


def test_dag_cycle_detected() -> None:
    compiled_links = [
        {"origin": {"board": "A"}, "destination": {"board": "B"}, "wire": "W1", "meta": {}},
        {"origin": {"board": "B"}, "destination": {"board": "A"}, "wire": "W2", "meta": {}},
    ]
    rep = DirectedElectricalGraphService.build_report(
        compiled_links=compiled_links,
        in_service_boards={"A", "B"},
        out_of_service_boards=set(),
        assembly_columns={},
        include_assembly_edges=False,
    )
    assert rep["has_cycle"] is True
    assert rep["cycles"]


def test_dag_unreachable_isolated_node() -> None:
    # C no tiene aristas -> no es root (outdegree=0) y queda unreachable
    compiled_links = [
        {"origin": {"board": "A"}, "destination": {"board": "B"}, "wire": "W1", "meta": {}},
    ]
    rep = DirectedElectricalGraphService.build_report(
        compiled_links=compiled_links,
        in_service_boards={"A", "B", "C"},
        out_of_service_boards=set(),
        assembly_columns={},
        include_assembly_edges=False,
    )
    assert rep["roots"] == ["A"]
    assert rep["unreachable"] == ["C"]
