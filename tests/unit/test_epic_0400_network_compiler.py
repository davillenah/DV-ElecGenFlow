from __future__ import annotations

import pytest

from elecgenflow.ingest.errors import MissingTagError
from elecgenflow.ingest.network_compiler import compile_network
from elecgenflow.ingest.registry_bootstrap import bootstrap_registry


def test_network_compiler_maps_assembly_column_to_real_board_and_accepts_variable_entrypoint() -> (
    None
):
    entry_tag = "MAIN-IN"

    boards = {
        "TS-FUERZA": {
            "name": "TS-FUERZA",
            "main_protection": {"kind": "MCCB", "tag": entry_tag},
            "buses": [],
        },
        "COL-03-BOARD": {
            "name": "COL-03-BOARD",
            "main_protection": {"kind": "MCCB", "tag": "IG"},
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

    assert compiled[0]["origin"]["board"] == "COL-03-BOARD"
    assert compiled[0]["meta"]["origin_assembly"] == "CCM 48"


def test_network_compiler_raises_on_missing_tag() -> None:
    boards = {
        "CCM 48": {"name": "CCM 48", "buses": []},
        "TS-FUERZA": {
            "name": "TS-FUERZA",
            "main_protection": {"kind": "MCCB", "tag": "IG"},
            "buses": [],
        },
    }

    reg = bootstrap_registry(boards, assemblies=[], network_links=[])

    links = [
        {
            "origin": {"board": "CCM 48", "protection": "Q59"},
            "destination": {"board": "TS-FUERZA", "protection": "IG"},
            "wire": "W123",
            "meta": {},
        }
    ]

    with pytest.raises(MissingTagError):
        compile_network(links, reg)
