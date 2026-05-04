# src/elecgenflow/engineering/catalog/impedance_catalog.py

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar  # ✅ ClassVar


@dataclass(frozen=True)
class Impedance:
    r_ohm_km: float
    x_ohm_km: float
    notes: str = ""


class StandardImpedanceCatalog:
    """
    Modelo estándar de impedancia cuando no hay tabla de fabricante.

    Defaults (IEC Annex G extract, en ausencia de datos precisos):
      - rho1 (ohm*mm^2/m): Cu 0.0225, Al 0.036
      - X (ohm/km): 0.08 (equivalente 0.08 mOhm/m)

    R(ohm/km) = (rho1 / S(mm^2)) * 1000
    """

    # ✅ FIX RUF012: ClassVar para dict constante de clase
    RHO1: ClassVar[dict[str, float]] = {"CU": 0.0225, "AL": 0.0360}

    def __init__(self, *, default_x_ohm_km: float = 0.08):
        self.default_x_ohm_km = float(default_x_ohm_km)

    @staticmethod
    def _norm_material(x: str) -> str:
        x = x.strip().upper()
        if x in ("COBRE", "COPPER", "CU"):
            return "CU"
        if x in ("ALUMINIO", "ALUMINUM", "AL"):
            return "AL"
        return x

    def impedance(
        self,
        *,
        material: str,
        section_mm2: float,
        conductor_temp_c: float,
        frequency_hz: float = 50.0,
        x_override_ohm_km: float | None = None,
    ) -> Impedance:
        mat = self._norm_material(material)
        if mat not in self.RHO1:
            raise ValueError(f"Material no soportado para impedancia estándar: {material}")
        if section_mm2 <= 0:
            raise ValueError("section_mm2 debe ser > 0")

        rho1 = self.RHO1[mat]
        r = (rho1 / float(section_mm2)) * 1000.0
        x = float(x_override_ohm_km) if x_override_ohm_km is not None else self.default_x_ohm_km

        # ✅ FIX RUF001: evitar caracter confusable 'rho' en string
        return Impedance(
            r_ohm_km=r,
            x_ohm_km=x,
            notes=(
                f"Std IEC Annex G: rho1={rho1} ohm*mm^2/m, X={x} ohm/km, "
                f"Tcond={conductor_temp_c}C, f={frequency_hz}Hz"
            ),
        )
