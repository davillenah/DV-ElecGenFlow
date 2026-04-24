from __future__ import annotations

from elecgenflow.engineering.load_aggregation import LoadAggregationService


def test_load_aggregation_virtual_load_board_exists_and_is_zero_local() -> None:
    boards = {
        "SRC": {
            "name": "SRC",
            "buses": [
                {
                    "circuits": [
                        {"tag": "c1", "type": "generic", "load": {"value": 2.0, "unit": "kW"}}
                    ]
                }
            ],
        }
    }

    compiled_links = [
        {
            "origin": {"board": "SRC", "protection": "Q1"},
            "destination": {"load": "MOTOR-01"},
            "wire": "W2",
            "meta": {},
        }
    ]

    report = LoadAggregationService.aggregate(
        boards_by_name=boards,
        compiled_links=compiled_links,
        in_service_boards={"SRC"},
        out_of_service_boards=set(),
    )

    assert "LOAD:MOTOR-01" in report["in_service"]["boards"]
    assert report["in_service"]["boards"]["LOAD:MOTOR-01"]["local"]["kW"] == 0.0
    assert report["in_service"]["boards"]["SRC"]["total"]["kW"] == 2.0
