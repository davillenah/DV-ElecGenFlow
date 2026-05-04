# src/elecgenflow/engineering/catalog/composite_catalog.py

from __future__ import annotations

from dataclasses import dataclass

from .ampacity_aea_catalog import AmpacityAEACatalog
from .derating_catalog import DeratingBreakdown, DeratingCatalog
from .impedance_catalog import Impedance, StandardImpedanceCatalog
from .methods import CableForm, InstallationRefMethod, PhaseSystem


@dataclass(frozen=True)
class CableQuery:
    method: InstallationRefMethod
    material: str  # "CU"/"AL"
    insulation: str  # "PVC"/"XLPE"
    phase_system: PhaseSystem  # MONO/TRI -> mapea "2x"/"3x"
    cable_form: CableForm  # UNIPOLAR/MULTIPOLAR
    section_mm2: float
    ambient_air_c: float
    grouped_circuits: int
    soil_resistivity: float | None
    burial_depth_m: float | None
    conductor_temp_c: float  # 70/90 definido por tu network (.with_insulation)


class CompositeCatalog:
    def __init__(
        self,
        *,
        ampacity: AmpacityAEACatalog,
        impedance: StandardImpedanceCatalog,
        derating: DeratingCatalog,
        frequency_hz: float = 50.0,
    ):
        self.ampacity = ampacity
        self.impedance = impedance
        self.derating = derating
        self.frequency_hz = float(frequency_hz)

    def itab_and_iz(self, q: CableQuery) -> tuple[float, DeratingBreakdown, float]:
        itab = self.ampacity.itab_a(
            method=q.method,
            material=q.material,
            insulation=q.insulation,
            phase_system=q.phase_system,
            section_mm2=q.section_mm2,
            cable_form=q.cable_form,
        )
        d = self.derating.breakdown(
            method=q.method,
            insulation=q.insulation,
            ambient_air_c=q.ambient_air_c,
            grouped_circuits=q.grouped_circuits,
            soil_resistivity=q.soil_resistivity,
            burial_depth_m=q.burial_depth_m,
            environment="AIR",
            kother=1.0,
        )
        iz_eff = itab * d.total
        return itab, d, iz_eff

    def rx(self, q: CableQuery) -> Impedance:
        return self.impedance.impedance(
            material=q.material,
            section_mm2=q.section_mm2,
            conductor_temp_c=q.conductor_temp_c,
            frequency_hz=self.frequency_hz,
        )
