from __future__ import annotations

import json
from pathlib import Path

from elecgenflow.engineering.ampacity_aea import AmpacityCatalog, AmpacityLookupKey
from elecgenflow.engineering.nominal_tables import NominalTables
from elecgenflow.engineering.sizing_validation import CableSizingValidationService


def test_sizing_suggests_section_when_fail(tmp_path: Path) -> None:
    # Build a tiny AEA ampacity file
    p = tmp_path / "ampacity_aea.json"
    p.write_text(
        json.dumps(
            {
                "descripcion": "test",
                "condiciones": {
                    "temperatura_ambiente": 40,
                    "temperatura_terreno": 25,
                    "resistividad": 1,
                },
                "materiales": {
                    "cobre": {
                        "PVC": {
                            "B2": [
                                {"seccion": 25, "2x": 78, "3x": 70},
                                {"seccion": 35, "2x": 97, "3x": 86},
                            ]
                        }
                    }
                },
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    amp = AmpacityCatalog.load(p)

    default_key = AmpacityLookupKey(
        material="cobre", insulation="PVC", metodo="B2", arrangement="3x"
    )

    # minimal nominal tables (empty, to force AEA usage)
    nominal = NominalTables(
        version="v0", cables={}, protections={}, install_methods={}, overlays_applied=[]
    )

    # 50 kVA @ 380V 3ph => ~75.9 A -> should suggest 35 (since 25 is 70A for 3x)
    load_report = {
        "in_service": {
            "feeders": [
                {
                    "from_board": "A",
                    "to": "B",
                    "wire": "W-TAG-4x25",
                    "downstream_total": {"kVA": 50.0},
                },
            ]
        }
    }

    rep = CableSizingValidationService.validate_feedrs(
        load_report=load_report,
        nominal=nominal,
        voltage_ll_v=380.0,
        ampacity=amp,
        default_ampacity_key=default_key,
    )

    row = rep["rows"][0]
    assert row["status"] in {"FAIL", "UNKNOWN"}
    assert row["suggested_section_mm2"] == 35
    assert row["suggested_iz_a"] == 86
