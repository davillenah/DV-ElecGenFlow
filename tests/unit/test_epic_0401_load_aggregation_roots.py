from __future__ import annotations

from elecgenflow.engineering.load_aggregation import LoadAggregationService


def test_root_totals_multiple_roots_sum_to_system_total() -> None:
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
        "X": {
            "name": "X",
            "buses": [
                {
                    "circuits": [
                        {"tag": "c1", "type": "generic", "load": {"value": 2.0, "unit": "kW"}}
                    ]
                }
            ],
        },
        "Y": {
            "name": "Y",
            "buses": [
                {
                    "circuits": [
                        {"tag": "c1", "type": "generic", "load": {"value": 3.0, "unit": "kW"}}
                    ]
                }
            ],
        },
    }

    compiled_links = [
        {
            "origin": {"board": "A", "protection": "Q1"},
            "destination": {"board": "B", "protection": "IG"},
            "wire": "W1",
            "meta": {},
        },
        {
            "origin": {"board": "X", "protection": "Q1"},
            "destination": {"board": "Y", "protection": "IG"},
            "wire": "W2",
            "meta": {},
        },
    ]

    report = LoadAggregationService.aggregate(
        boards_by_name=boards,
        compiled_links=compiled_links,
        in_service_boards={"A", "B", "X", "Y"},
        out_of_service_boards=set(),
        assembly_columns={},
        power_factor=0.85,
    )

    assert report["roots"] == ["A", "X"]

    rt = {x["root"]: x["total"] for x in report["root_totals"]}
    assert rt["A"]["kW"] == 15.0
    assert rt["X"]["kW"] == 5.0

    sys_total = report["system_total"]
    assert sys_total["kW"] == 20.0
