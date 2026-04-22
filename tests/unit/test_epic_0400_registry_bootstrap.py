from __future__ import annotations

from elecgenflow.ingest.registry_bootstrap import bootstrap_registry


def test_registry_bootstrap_exposes_entry_and_endpoints_with_variable_entrypoint_tag() -> None:
    boards = {
        "TS-FUERZA": {
            "name": "TS-FUERZA",
            "main_protection": {"kind": "MCCB", "amps": 250, "tag": "MAIN-IN"},
            "buses": [
                {
                    "circuits": [
                        {"tag": "dos", "type": "lite", "protection": "MCB"},
                        {
                            "tag": "G1",
                            "type": "hvac",
                            "protection": "RCCB",
                            "subcircuits": [
                                {"tag": "C1", "protection": "MCB"},
                                {"tag": "C2", "protection": "MCB"},
                            ],
                        },
                    ]
                }
            ],
        }
    }

    reg = bootstrap_registry(boards, assemblies=[], network_links=[])

    assert ("TS-FUERZA", "MAIN-IN") in reg.protections_entry
    assert ("TS-FUERZA", "dos") in reg.protections_end
    assert ("TS-FUERZA", "G1:C1") in reg.protections_end
    assert ("TS-FUERZA", "G1:C2") in reg.protections_end
