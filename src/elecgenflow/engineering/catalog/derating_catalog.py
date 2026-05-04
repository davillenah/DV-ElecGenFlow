# src/elecgenflow/engineering/catalog/derating_catalog.py

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .methods import InstallationRefMethod


@dataclass(frozen=True)
class DeratingBreakdown:
    kt: float = 1.0
    kg: float = 1.0
    ksoil: float = 1.0
    kdepth: float = 1.0
    kother: float = 1.0

    @property
    def total(self) -> float:
        # En IEC la metodología usa factores multiplicativos (no aditivos). [1](https://aionlinecalculator.com/cable-sizing-guide.html)[2](https://www.linkedin.com/feed/update/urn:li:activity:7376840200469073920/)
        return self.kt * self.kg * self.ksoil * self.kdepth * self.kother


class DeratingCatalog:
    """
    Lee factores desde JSON editable.
    Si no encuentra coincidencia, devuelve 1.0 (fallback seguro).

    Estructura propuesta en JSON:
      {
        "Kt": { "AIR": { "PVC": {"30": 1.0, "40": 1.0}, "XLPE": {...} },
                "GROUND": {...} },
        "Kg": { "B2": {"1": 1.0, "2": 1.0}, "E": {...}, ... },
        "Ksoil": { "1.0": 1.0, "2.5": 1.0 },
        "Kdepth": { "0.7": 1.0, "1.0": 1.0 }
      }
    """

    def __init__(self, cfg: dict[str, Any]):
        self.cfg = cfg or {}

    @classmethod
    def from_json(cls, path: str | Path) -> DeratingCatalog:
        p = Path(path)
        return cls(json.loads(p.read_text(encoding="utf-8")))

    def _lookup(self, table: dict[str, Any], key: str, default: float = 1.0) -> float:
        try:
            v = table.get(key, default)
            return float(v)
        except Exception:
            return float(default)

    def kt(self, *, insulation: str, ambient_c: float, environment: str = "AIR") -> float:
        env = environment.strip().upper()
        ins = insulation.strip().upper()
        kt_table = (self.cfg.get("Kt", {}) or {}).get(env, {}) or {}
        ins_table = kt_table.get(ins, {}) or {}
        # ✅ FIX RUF046: round() ya devuelve int cuando ndigits=None, no hace falta int(...)
        return self._lookup(ins_table, str(round(ambient_c)), 1.0)

    def kg(self, *, method: InstallationRefMethod, grouped_circuits: int) -> float:
        kg_table = self.cfg.get("Kg", {}) or {}
        m_table = kg_table.get(method.value, {}) or {}
        return self._lookup(m_table, str(int(grouped_circuits)), 1.0)

    def ksoil(self, *, soil_resistivity: float | None) -> float:
        # clave por resistividad (ej "1.0", "2.5", etc.)
        ks_table = self.cfg.get("Ksoil", {}) or {}
        if soil_resistivity is None:
            return 1.0
        return self._lookup(ks_table, str(float(soil_resistivity)), 1.0)

    def kdepth(self, *, burial_depth_m: float | None) -> float:
        kd_table = self.cfg.get("Kdepth", {}) or {}
        if burial_depth_m is None:
            return 1.0
        return self._lookup(kd_table, str(float(burial_depth_m)), 1.0)

    def breakdown(
        self,
        *,
        method: InstallationRefMethod,
        insulation: str,
        ambient_air_c: float,
        grouped_circuits: int,
        soil_resistivity: float | None = None,
        burial_depth_m: float | None = None,
        environment: str = "AIR",
        kother: float = 1.0,
    ) -> DeratingBreakdown:
        return DeratingBreakdown(
            kt=self.kt(insulation=insulation, ambient_c=ambient_air_c, environment=environment),
            kg=self.kg(method=method, grouped_circuits=grouped_circuits),
            ksoil=self.ksoil(soil_resistivity=soil_resistivity),
            kdepth=self.kdepth(burial_depth_m=burial_depth_m),
            kother=float(kother),
        )
