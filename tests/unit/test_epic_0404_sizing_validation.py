from __future__ import annotations

from elecgenflow.engineering.nominal_tables import (
    CableSpec,
    NominalTables,
)
from elecgenflow.engineering.sizing_validation import CableSizingValidationService


def test_sizing_validation_pass_fail_unknown() -> None:
    # minimal nominal tables
    nominal = NominalTables(
        version="v0",
        cables={
            "W1": CableSpec(
                tag="W1",
                manufacturer="GEN",
                family="CU-XLPE",
                material="CU",
                insulation="XLPE",
                jacket="PVC",
                cores=4,
                section_mm2=25,
                voltage_class="LV",
                ampacity_a=100,
                resistance_ohm_km_20c=0.7,
                meta={},
            )
        },
        protections={},
        install_methods={},
        overlays_applied=[],
    )

    load_report = {
        "in_service": {
            "feeders": [
                {"from_board": "A", "to": "B", "wire": "W1", "downstream_total": {"kVA": 50.0}},
                {
                    "from_board": "A",
                    "to": "C",
                    "wire": "W-NOT-FOUND",
                    "downstream_total": {"kVA": 10.0},
                },
                {"from_board": "A", "to": "D", "wire": "", "downstream_total": {"kVA": 10.0}},
            ]
        }
    }

    rep = CableSizingValidationService.validate_feedrs(
        load_report=load_report, nominal=nominal, voltage_ll_v=380.0
    )
    assert rep["summary"]["total"] == 3
    # W1 at 50 kVA, 380V 3ph => Ib ≈ 75.9A, Iz=100 => PASS
    assert rep["rows"][0]["status"] == "PASS"
    assert rep["rows"][1]["status"] == "UNKNOWN"
    assert rep["rows"][2]["status"] == "UNKNOWN"
