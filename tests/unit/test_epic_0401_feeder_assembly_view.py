from __future__ import annotations

from elecgenflow.engineering.load_aggregation import LoadAggregationService


def test_feeder_assembly_view_maps_column_board_to_assembly() -> None:
    boards = {
        "TGBT-GENERAL": {"name": "TGBT-GENERAL", "buses": []},
        "TGBT-COL-03": {"name": "TGBT-COL-03", "buses": []},
        "TS-FUERZA": {
            "name": "TS-FUERZA",
            "buses": [
                {
                    "circuits": [
                        {"tag": "x", "type": "generic", "load": {"value": 10.0, "unit": "kW"}}
                    ]
                }
            ],
        },
    }

    compiled_links = [
        {
            "origin": {"board": "TGBT-COL-03", "protection": "Q59"},
            "destination": {"board": "TS-FUERZA", "protection": "IG"},
            "wire": "W1",
            "meta": {"origin_assembly": "TGBT-GENERAL", "origin_column_board": "TGBT-COL-03"},
        }
    ]

    report = LoadAggregationService.aggregate(
        boards_by_name=boards,
        compiled_links=compiled_links,
        in_service_boards={"TGBT-GENERAL", "TGBT-COL-03", "TS-FUERZA"},
        out_of_service_boards=set(),
        assembly_columns={"TGBT-GENERAL": {"COL-03": "TGBT-COL-03"}},
        power_factor=0.85,
    )

    asm_view = report["in_service"]["feeders_assembly_view"]
    assert len(asm_view) == 1
    assert asm_view[0]["from_assembly"] == "TGBT-GENERAL"
    assert asm_view[0]["from_board"] == "TGBT-COL-03"
    assert asm_view[0]["to"] == "TS-FUERZA"
