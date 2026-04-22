from __future__ import annotations

from elecgenflow.elecboard.ir import ElecboardIR
from elecgenflow.ingest.dsl_adapter import build_elecboard_ir
from elecgenflow.ingest.network_compiler import compile_network
from elecgenflow.ingest.registry_bootstrap import bootstrap_registry


def test_adapter_builds_valid_elecboard_ir_with_variable_entrypoint() -> None:
    entry_tag = "MAIN-IN"

    boards = {
        "TS-FUERZA": {
            "name": "TS-FUERZA",
            "main_protection": {"kind": "MCCB", "amps": 250, "tag": entry_tag},
            "buses": [{"circuits": [{"tag": "dos", "type": "lite", "protection": "MCB"}]}],
        },
        "COL-03-BOARD": {
            "name": "COL-03-BOARD",
            "main_protection": {"kind": "MCCB", "amps": 160, "tag": "IG"},
            "buses": [{"circuits": [{"tag": "Q59", "type": "generic", "protection": "MCCB"}]}],
        },
    }

    assemblies = [
        {
            "name": "CCM 48",
            "kind": "CCM",
            "columns": [{"index": 3, "board": "COL-03-BOARD"}],
            "meta": {},
        }
    ]

    links = [
        {
            "origin": {"board": "CCM 48", "column": "COL-03", "protection": "Q59"},
            "destination": {"board": "TS-FUERZA", "protection": entry_tag},
            "wire": "W123",
            "meta": {},
        }
    ]

    reg = bootstrap_registry(boards, assemblies=assemblies, network_links=links)
    compiled = compile_network(links, reg)
    ir = build_elecboard_ir(boards, reg, compiled)

    assert isinstance(ir, ElecboardIR)
    ElecboardIR.from_logical_ir_dict(ir.to_logical_ir_dict())
