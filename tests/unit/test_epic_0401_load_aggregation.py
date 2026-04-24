from __future__ import annotations

import math

from elecgenflow.engineering.load_aggregation import LoadAggregationService


def test_load_aggregation_simple_chain_no_duplication() -> None:
    boards = {
        "A": {
            "name": "A",
            "buses": [
                {
                    "circuits": [
                        {"tag": "c1", "type": "generic", "load": {"value": 10.0, "unit": "kW"}}
                    ]
                }
            ],
        },
        "B": {
            "name": "B",
            "buses": [
                {
                    "circuits": [
                        {"tag": "c1", "type": "generic", "load": {"value": 5.0, "unit": "kW"}}
                    ]
                }
            ],
        },
        "SPARE": {
            "name": "SPARE",
            "buses": [
                {
                    "circuits": [
                        {"tag": "x", "type": "generic", "load": {"value": 99.0, "unit": "kW"}}
                    ]
                }
            ],
        },
    }

    compiled_links = [
        {
            "origin": {"board": "A", "protection": "X"},
            "destination": {"board": "B", "protection": "IG"},
            "wire": "W1",
            "meta": {},
        }
    ]

    report = LoadAggregationService.aggregate(
        boards_by_name=boards,
        compiled_links=compiled_links,
        in_service_boards={"A", "B"},
        out_of_service_boards={"SPARE"},
        assembly_columns={},
        power_factor=0.85,
    )

    ins = report["in_service"]["boards"]
    oos = report["out_of_service"]["boards"]

    assert "SPARE" not in ins
    assert "SPARE" in oos

    assert ins["B"]["local"]["kW"] == 5.0
    assert ins["B"]["total"]["kW"] == 5.0
    assert math.isclose(ins["B"]["total"]["kVA"], 5.0 / 0.85, rel_tol=1e-6)

    assert ins["A"]["local"]["kW"] == 10.0
    assert ins["A"]["total"]["kW"] == 15.0
    assert math.isclose(ins["A"]["total"]["kVA"], 15.0 / 0.85, rel_tol=1e-6)
