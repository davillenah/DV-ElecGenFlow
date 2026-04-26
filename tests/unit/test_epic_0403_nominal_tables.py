from __future__ import annotations

import json
from pathlib import Path

from elecgenflow.engineering.nominal_tables import load_nominal_tables


def test_nominal_tables_load_base_ok(tmp_path: Path) -> None:
    root = tmp_path / "data" / "nominal"
    (root / "v0").mkdir(parents=True)

    (root / "v0" / "cables.json").write_text(
        json.dumps(
            {
                "version": "v0",
                "kind": "cables",
                "items": [
                    {
                        "tag": "CU-XLPE-1C-25",
                        "manufacturer": "GENERIC",
                        "family": "CU-XLPE",
                        "material": "CU",
                        "insulation": "XLPE",
                        "cores": 1,
                        "section_mm2": 25,
                        "voltage_class": "LV",
                        "ampacity_a": 100,
                        "meta": {},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    (root / "v0" / "protections.json").write_text(
        json.dumps(
            {
                "version": "v0",
                "kind": "protections",
                "items": [
                    {
                        "tag": "MCB-1P-16A-C",
                        "kind": "MCB",
                        "poles": 1,
                        "rating_amps": 16,
                        "curve": "C",
                        "meta": {},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    (root / "v0" / "install_methods.json").write_text(
        json.dumps(
            {
                "version": "v0",
                "kind": "install_methods",
                "items": [{"tag": "BANDEJA", "description": "Bandeja", "meta": {}}],
            }
        ),
        encoding="utf-8",
    )

    tables = load_nominal_tables(root=root, version="v0", overlays=[])
    assert "CU-XLPE-1C-25" in tables.cables
    assert "MCB-1P-16A-C" in tables.protections
    assert "BANDEJA" in tables.install_methods


def test_nominal_tables_overlay_overrides_by_tag(tmp_path: Path) -> None:
    root = tmp_path / "data" / "nominal"
    (root / "v0").mkdir(parents=True)
    (root / "overlays" / "schneider").mkdir(parents=True)

    (root / "v0" / "cables.json").write_text(
        json.dumps({"version": "v0", "kind": "cables", "items": []}),
        encoding="utf-8",
    )
    (root / "v0" / "install_methods.json").write_text(
        json.dumps({"version": "v0", "kind": "install_methods", "items": []}),
        encoding="utf-8",
    )
    (root / "v0" / "protections.json").write_text(
        json.dumps(
            {
                "version": "v0",
                "kind": "protections",
                "items": [
                    {
                        "tag": "MCCB-4P-250A-36kA",
                        "manufacturer": "GENERIC",
                        "kind": "MCCB",
                        "poles": 4,
                        "rating_amps": 250,
                        "breaking_capacity_ka": 36,
                        "meta": {},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    overlay_path = root / "overlays" / "schneider" / "protections.json"
    overlay_path.write_text(
        json.dumps(
            {
                "version": "v0",
                "kind": "protections",
                "overlay": True,
                "manufacturer": "SCHNEIDER",
                "items": [
                    {
                        "tag": "MCCB-4P-250A-36kA",
                        "manufacturer": "SCHNEIDER",
                        "kind": "MCCB",
                        "poles": 4,
                        "rating_amps": 250,
                        "breaking_capacity_ka": 36,
                        "meta": {"series": "NSX"},
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    tables = load_nominal_tables(root=root, version="v0", overlays=[overlay_path])
    assert tables.protections["MCCB-4P-250A-36kA"].manufacturer == "SCHNEIDER"
