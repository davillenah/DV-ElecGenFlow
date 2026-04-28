from __future__ import annotations

from pathlib import Path

from elecgenflow.engineering.ampacity_aea import AmpacityCatalog, AmpacityLookupKey


def test_ampacity_lookup_and_suggest(tmp_path: Path) -> None:
    # tiny sample file
    p = tmp_path / "amp.json"
    p.write_text(
        """
{
  "descripcion": "test",
  "condiciones": { "temperatura_ambiente": 40, "temperatura_terreno": 25, "resistividad": 1 },
  "materiales": {
    "cobre": { "PVC": { "B2": [ { "seccion": 25, "2x": 78, "3x": 70 }, { "seccion": 35, "2x": 97, "3x": 86 } ] } }
  }
}
""".strip(),
        encoding="utf-8",
    )

    cat = AmpacityCatalog.load(p)
    key = AmpacityLookupKey(material="cobre", insulation="PVC", metodo="B2", arrangement="3x")

    assert cat.get_ampacity(key=key, seccion=25) == 70
    assert cat.suggest_section(key=key, ib_a=80) == 35
