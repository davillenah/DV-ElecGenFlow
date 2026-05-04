# examples/Ford_BsAs_Pacheco/project_owner.py

from __future__ import annotations

OWNER = {
    "locale": {
        "country": "AR",
        "province": "BsAs",
        "city": "Grand Bourg",
    },
    "client": "Ford Argentina S.C.A.",
    "site": "Planta Pacheco",
    "project": {"name": "Fluent Demo - AutoSizing DSL"},
    "contacts": [{
        "name": "Daniel Villena",
        "role": "Engineering",
        "email": "ingenierovillena@gmail.com"
         },
    ],
    # Defaults “Argentina” (declarados). Se usarán después para derating real.
    "environment": {
        "ambient_air_c": 30,
        "soil_temp_c": 20,
    },
    # Resistividad típica (placeholder por localidad; después lo mapeás a tabla real)
    "soil": {
        "resistivity_km_w": 2.5,
    },
    "notes": (
        "Proyecto demo EPIC-04.00+:\n"
        "- DSL + Registry + Network (base)\n"
        "- EPIC-04.01: Load aggregation + artifacts (load_report.*)\n"
        "- EPIC-04.02: DAG dirigido + artifacts (dag_report.*)\n"
        "- EPIC-04.03: Tablas nominales v0 + overlays + artifacts (nominal_*.*)\n"
        "- EPIC-04.04: Auto-sizing sugerido (Ib vs Iz + sección sugerida) + artifacts (sizing_report.*)\n"
        "- EPIC-11 (precursor): PDF desde artifacts (engineering_report.pdf)\n"
    ),
}
