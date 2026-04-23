from __future__ import annotations

from elecgenflow.ingest.network_compiler import compile_network
from elecgenflow.ingest.registry_bootstrap import ENTRYPOINT_TAG, bootstrap_registry


def test_network_compiler_maps_assembly_column_to_real_board() -> None:
    boards = {
        "TS-FUERZA": {"name": "TS-FUERZA", "main_protection": {"kind": "MCCB"}, "buses": []},
        "COL-03-BOARD": {
            "name": "COL-03-BOARD",
            "main_protection": {"kind": "MCCB"},
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
            "destination": {"board": "TS-FUERZA", "protection": ENTRYPOINT_TAG},
            "wire": "W123",
            "meta": {},
        }
    ]

    reg = bootstrap_registry(boards, assemblies=assemblies, network_links=links)
    compiled, report = compile_network(links, reg, mode="dev")

    assert report.has_errors() is False
    assert report.compiled == 1
    assert report.skipped == 0
    assert compiled[0]["origin"]["board"] == "COL-03-BOARD"
    assert compiled[0]["meta"]["origin_assembly"] == "CCM 48"


def test_network_compiler_skips_invalid_link_in_runtime_mode() -> None:
    boards = {
        "TS-FUERZA": {"name": "TS-FUERZA", "main_protection": {"kind": "MCCB"}, "buses": []},
        "COL-03-BOARD": {
            "name": "COL-03-BOARD",
            "main_protection": {"kind": "MCCB"},
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
            "origin": {
                "board": "CCM 48",
                "column": "COL-99",
                "protection": "Q59",
            },  # columna inexistente
            "destination": {"board": "TS-FUERZA", "protection": ENTRYPOINT_TAG},
            "wire": "W123",
            "meta": {},
        }
    ]

    reg = bootstrap_registry(boards, assemblies=assemblies, network_links=links)
    compiled, report = compile_network(links, reg, mode="runtime")

    assert len(compiled) == 0
    assert report.compiled == 0
    assert report.skipped == 1
    assert report.issues
    assert any(i.code == "ORIGIN_COLUMN_MISSING" for i in report.issues)
