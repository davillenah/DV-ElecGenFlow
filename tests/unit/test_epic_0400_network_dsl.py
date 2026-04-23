from __future__ import annotations

from elecgenflow.ingest.network_compiler import compile_network
from elecgenflow.ingest.registry_bootstrap import ENTRYPOINT_TAG, bootstrap_registry


def test_network_compiler_reports_missing_tag_in_dev_mode() -> None:
    boards = {
        "CCM 48": {"name": "CCM 48", "buses": []},  # placeholder (sin endpoints)
        "TS-FUERZA": {"name": "TS-FUERZA", "main_protection": {"kind": "MCCB"}, "buses": []},
    }

    reg = bootstrap_registry(boards, assemblies=[], network_links=[])

    links = [
        {
            "origin": {"board": "CCM 48", "protection": "Q59"},
            "destination": {"board": "TS-FUERZA", "protection": ENTRYPOINT_TAG},
            "wire": "W123",
            "meta": {},
        }
    ]

    compiled, report = compile_network(links, reg, mode="dev")

    assert len(compiled) == 0
    assert report.compiled == 0
    assert report.skipped == 1
    assert report.issues
    assert report.has_errors() is True
    assert any(i.code == "ORIGIN_ENDPOINT_UNKNOWN" for i in report.issues)
