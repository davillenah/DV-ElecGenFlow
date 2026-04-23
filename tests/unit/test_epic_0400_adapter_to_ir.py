from __future__ import annotations

from elecgenflow.elecboard.ir import ElecboardIR
from elecgenflow.ingest.dsl_adapter import build_elecboard_ir
from elecgenflow.ingest.network_compiler import compile_network
from elecgenflow.ingest.registry_bootstrap import bootstrap_registry


def test_ends_at_load_creates_virtual_load_board_in_ir() -> None:
    boards = {
        "TGBT-COL-03": {
            "name": "TGBT-COL-03",
            "main_protection": {"kind": "MCCB"},
            "buses": [{"circuits": [{"tag": "Q59", "type": "generic", "protection": "MCCB"}]}],
        },
    }
    assemblies = []
    links = [
        {
            "origin": {"board": "TGBT-COL-03", "protection": "Q59"},
            "destination": {"load": "MOTOR-BOMBA-01"},
            "wire": "4x10mm2",
            "meta": {},
        }
    ]

    reg = bootstrap_registry(boards, assemblies=assemblies, network_links=links)
    compiled, _ = compile_network(links, reg, mode="runtime")

    ir = build_elecboard_ir(boards, reg, compiled)
    assert isinstance(ir, ElecboardIR)

    # existe un board virtual LOAD:MOTOR-BOMBA-01
    names = [b.name for b in ir.boards]
    assert "LOAD:MOTOR-BOMBA-01" in names
