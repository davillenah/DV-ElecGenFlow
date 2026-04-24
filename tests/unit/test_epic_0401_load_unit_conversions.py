from __future__ import annotations

import math

from elecgenflow.engineering.load_aggregation import LoadAggregationService


def test_load_conversion_hp_to_kw_and_kva() -> None:
    # 10 HP = 7.46 kW ; kVA = kW / PF
    pf = 0.85
    boards = {
        "MOTOR-HP": {
            "name": "MOTOR-HP",
            "buses": [{"circuits": [{"tag": "m1", "type": "motor", "load": "10HP"}]}],
        }
    }

    report = LoadAggregationService.aggregate(
        boards_by_name=boards,
        compiled_links=[],
        in_service_boards={"MOTOR-HP"},
        out_of_service_boards=set(),
        assembly_columns={},
        power_factor=pf,
    )

    b = report["in_service"]["boards"]["MOTOR-HP"]
    kw = b["local"]["kW"]
    kva = b["local"]["kVA"]

    expected_kw = 10.0 * 0.746
    expected_kva = expected_kw / pf

    assert math.isclose(kw, expected_kw, rel_tol=1e-6)
    assert math.isclose(kva, expected_kva, rel_tol=1e-6)
    assert b["total"]["kW"] == b["local"]["kW"]
    assert b["total"]["kVA"] == b["local"]["kVA"]


def test_load_conversion_mva_to_kva_and_kw() -> None:
    # 0.1 MVA = 100 kVA ; kW = kVA * PF
    pf = 0.85
    boards = {
        "TRAFO-MVA": {
            "name": "TRAFO-MVA",
            "buses": [{"circuits": [{"tag": "t1", "type": "generic", "load": "0.1MVA"}]}],
        }
    }

    report = LoadAggregationService.aggregate(
        boards_by_name=boards,
        compiled_links=[],
        in_service_boards={"TRAFO-MVA"},
        out_of_service_boards=set(),
        assembly_columns={},
        power_factor=pf,
    )

    b = report["in_service"]["boards"]["TRAFO-MVA"]
    kw = b["local"]["kW"]
    kva = b["local"]["kVA"]

    expected_kva = 0.1 * 1000.0
    expected_kw = expected_kva * pf

    assert math.isclose(kva, expected_kva, rel_tol=1e-6)
    assert math.isclose(kw, expected_kw, rel_tol=1e-6)
    assert b["total"]["kW"] == b["local"]["kW"]
    assert b["total"]["kVA"] == b["local"]["kVA"]


def test_load_conversion_mw_to_kw_and_kva() -> None:
    # 2 MW = 2000 kW ; kVA = kW / PF
    pf = 0.85
    boards = {
        "PLANTA-MW": {
            "name": "PLANTA-MW",
            "buses": [{"circuits": [{"tag": "p1", "type": "generic", "load": "2MW"}]}],
        }
    }

    report = LoadAggregationService.aggregate(
        boards_by_name=boards,
        compiled_links=[],
        in_service_boards={"PLANTA-MW"},
        out_of_service_boards=set(),
        assembly_columns={},
        power_factor=pf,
    )

    b = report["in_service"]["boards"]["PLANTA-MW"]
    kw = b["local"]["kW"]
    kva = b["local"]["kVA"]

    expected_kw = 2.0 * 1000.0
    expected_kva = expected_kw / pf

    assert math.isclose(kw, expected_kw, rel_tol=1e-6)
    assert math.isclose(kva, expected_kva, rel_tol=1e-6)
    assert b["total"]["kW"] == b["local"]["kW"]
    assert b["total"]["kVA"] == b["local"]["kVA"]
