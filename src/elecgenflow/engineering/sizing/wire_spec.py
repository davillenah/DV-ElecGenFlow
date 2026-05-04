# src/elecgenflow/engineering/sizing/wire_spec.py

from __future__ import annotations

from dataclasses import dataclass

from elecgenflow.engineering.catalog.methods import CableForm, InstallationRefMethod, PhaseSystem


@dataclass(frozen=True)
class WireSpec:
    """
    Especificación declarativa del cable tal como viene desde la Network DSL.

    Importante: acá NO hay sección. La sección la decide el dimensionamiento.
    """

    wire_id: str
    phase_system: PhaseSystem  # MONO/TRI (inferido desde Board o link)
    cable_form: CableForm  # UNIPOLAR/MULTIPOLAR
    conductor: str  # "CU"/"AL" (tu DSL: .with_conductor("AL"))
    insulation: str  # "PVC"/"XLPE" (tu DSL: .with_insulation("PVC"))
    method: InstallationRefMethod  # A1..G (tu DSL: .installed_in("E"))
    include_protection_cable: bool = False  # .with_protection_cable_included()

    # opcionales para factores futuros
    ambient_air_c: float = 40.0
    grouped_circuits: int = 1
    soil_resistivity: float | None = None
    burial_depth_m: float | None = None
