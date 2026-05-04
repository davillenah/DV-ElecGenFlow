from __future__ import annotations

import json
from pathlib import Path

from elecgenflow.engineering.ampacity_aea import AmpacityCatalog, AmpacityLookupKey
from elecgenflow.engineering.cable_schedule import CableScheduleService


def test_cable_schedule_selects_section(tmp_path: Path) -> None:
    amp_path = tmp_path / "ampacity_aea.json"
    amp_path.write_text(
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
            }
        ),
        encoding="utf-8",
    )
    amp = AmpacityCatalog.load(amp_path)
    default_key = AmpacityLookupKey(
        material="cobre", insulation="PVC", metodo="B2", arrangement="3x"
    )

    load_report = {
        "in_service": {
            "feeders": [
                {"from_board": "A", "to": "B", "wire": "W378", "downstream_total": {"kVA": 50.0}},
            ]
        }
    }
    compiled_links = [
        {
            "wire": "W378",
            "wire_id": "W378",
            "wire_config": {
                "conductor": "CU",
                "insulation": "PVC",
                "install_method": "B2",
                "meta": {"arrangement": "3x"},
            },
        }
    ]

    sched = CableScheduleService.build(
        load_report=load_report,
        compiled_links=compiled_links,
        ampacity=amp,
        voltage_ll_v=380.0,
        default_key=default_key,
    )

    row = sched["rows"][0]
    assert row["selected_section_mm2"] == 35
    assert row["selected_iz_a"] == 86
