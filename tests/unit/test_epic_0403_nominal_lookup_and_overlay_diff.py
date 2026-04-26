from __future__ import annotations

import json
from pathlib import Path

import pytest

from elecgenflow.engineering.nominal_tables import (
    NominalLookupError,
    load_nominal_tables,
    nominal_overlay_diff,
)


def _write(p: Path, obj: dict) -> None:
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


def test_nominal_lookup_with_suggestions(tmp_path: Path) -> None:
    root = tmp_path / "data" / "nominal"
    (root / "v0").mkdir(parents=True)

    _write(
        root / "v0" / "cables.json",
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
        },
    )
    _write(
        root / "v0" / "protections.json",
        {
            "version": "v0",
            "kind": "protections",
            "items": [
                {"tag": "MCB-1P-16A-C", "kind": "MCB", "poles": 1, "rating_amps": 16, "curve": "C"}
            ],
        },
    )
    _write(
        root / "v0" / "install_methods.json",
        {
            "version": "v0",
            "kind": "install_methods",
            "items": [{"tag": "BANDEJA", "description": "Bandeja"}],
        },
    )

    tables = load_nominal_tables(root=root, version="v0", overlays=[])

    assert tables.get_cable("CU-XLPE-1C-25").section_mm2 == 25

    with pytest.raises(NominalLookupError) as exc:
        tables.get_cable("CU-XLPE-1C-")

    err = exc.value
    assert err.kind == "cables"
    assert err.suggestions


def test_overlay_diff_detects_changed_tag(tmp_path: Path) -> None:
    root = tmp_path / "data" / "nominal"
    (root / "v0").mkdir(parents=True)
    (root / "overlays" / "schneider").mkdir(parents=True)

    _write(root / "v0" / "cables.json", {"version": "v0", "kind": "cables", "items": []})
    _write(
        root / "v0" / "install_methods.json",
        {"version": "v0", "kind": "install_methods", "items": []},
    )
    _write(
        root / "v0" / "protections.json",
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
                }
            ],
        },
    )

    overlay_path = root / "overlays" / "schneider" / "protections.json"
    _write(
        overlay_path,
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
        },
    )

    diff = nominal_overlay_diff(root=root, version="v0", overlays=[overlay_path])
    changed = diff["protections"]["changed"]
    assert "MCCB-4P-250A-36kA" in changed
