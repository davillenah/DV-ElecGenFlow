# src/elecgenflow/engineering/catalog/ampacity_aea_catalog.py

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar  # ✅ ClassVar agregado

from .methods import CableForm, InstallationRefMethod, PhaseSystem


@dataclass(frozen=True)
class AmpacityConditions:
    ambient_temp_c: float | None = None
    ground_temp_c: float | None = None
    soil_resistivity: float | None = None


@dataclass(frozen=True)
class AmpacityKey:
    method: InstallationRefMethod
    material: str
    insulation: str
    phase_system: PhaseSystem
    section_mm2: float
    cable_form: CableForm = CableForm.MULTIPOLAR


class AmpacityAEACatalog:
    """
    Catálogo Itab a partir de data/nominal/v0/ampacity_aea.json.

    Nota:
      - "2x" = monofásico
      - "3x" = trifásico
    """

    # ✅ FIX RUF012: indicar que es un atributo de clase intencional (compartido)
    _MATERIAL_MAP: ClassVar[dict[str, str]] = {
        "cobre": "CU",
        "cu": "CU",
        "copper": "CU",
        "aluminio": "AL",
        "al": "AL",
        "aluminum": "AL",
    }

    def __init__(self, *, conditions: AmpacityConditions, index: dict[AmpacityKey, float]):
        self.conditions = conditions
        self._index = index

    @staticmethod
    def _norm_insulation(x: str) -> str:
        return x.strip().upper()

    @classmethod
    def _norm_material(cls, x: str) -> str:
        k = x.strip().lower()
        return cls._MATERIAL_MAP.get(k, x.strip().upper())

    @staticmethod
    def _norm_cable_form(x: CableForm | str) -> CableForm:
        if isinstance(x, CableForm):
            return x
        s = str(x).strip().upper()
        if s in ("UNIPOLAR", "UNI", "1C", "SINGLE"):
            return CableForm.UNIPOLAR
        if s in ("MULTIPOLAR", "MULTI", "MULTICORE", "2C", "3C", "4C", "5C"):
            return CableForm.MULTIPOLAR
        return CableForm.MULTIPOLAR

    @classmethod
    def from_json(cls, path: str | Path) -> AmpacityAEACatalog:
        p = Path(path)
        raw = json.loads(p.read_text(encoding="utf-8"))

        cond = raw.get("condiciones", {}) or {}
        conditions = AmpacityConditions(
            ambient_temp_c=cond.get("temperatura_ambiente"),
            ground_temp_c=cond.get("temperatura_terreno"),
            soil_resistivity=cond.get("resistividad"),
        )

        materiales = raw.get("materiales", {})
        if not isinstance(materiales, dict) or not materiales:
            raise ValueError("ampacity_aea.json: falta 'materiales' o está vacío.")

        index: dict[AmpacityKey, float] = {}

        for mat_name, mat_block in materiales.items():
            material = cls._norm_material(mat_name)
            if not isinstance(mat_block, dict):
                continue

            for ins_name, ins_block in mat_block.items():
                insulation = cls._norm_insulation(ins_name)
                if not isinstance(ins_block, dict):
                    continue

                for method_name, rows in ins_block.items():
                    method = InstallationRefMethod(method_name.strip().upper())
                    if not isinstance(rows, list):
                        continue

                    for row in rows:
                        if "seccion" not in row:
                            continue
                        section = float(row["seccion"])

                        if "2x" in row and row["2x"] is not None:
                            key_mono = AmpacityKey(
                                method=method,
                                material=material,
                                insulation=insulation,
                                phase_system=PhaseSystem.SINGLE_PHASE,
                                section_mm2=section,
                                cable_form=CableForm.MULTIPOLAR,
                            )
                            index[key_mono] = float(row["2x"])

                        if "3x" in row and row["3x"] is not None:
                            key_tri = AmpacityKey(
                                method=method,
                                material=material,
                                insulation=insulation,
                                phase_system=PhaseSystem.THREE_PHASE,
                                section_mm2=section,
                                cable_form=CableForm.MULTIPOLAR,
                            )
                            index[key_tri] = float(row["3x"])

        if not index:
            raise ValueError(
                "ampacity_aea.json: no se indexó ningún valor Itab. Revisar estructura/contenido."
            )

        return cls(conditions=conditions, index=index)

    def itab_a(
        self,
        *,
        method: InstallationRefMethod,
        material: str,
        insulation: str,
        phase_system: PhaseSystem,
        section_mm2: float,
        cable_form: CableForm | str = CableForm.MULTIPOLAR,
    ) -> float:
        key = AmpacityKey(
            method=method,
            material=self._norm_material(material),
            insulation=self._norm_insulation(insulation),
            phase_system=phase_system,
            section_mm2=float(section_mm2),
            cable_form=self._norm_cable_form(cable_form),
        )

        if key in self._index:
            return self._index[key]

        fallback = AmpacityKey(
            method=key.method,
            material=key.material,
            insulation=key.insulation,
            phase_system=key.phase_system,
            section_mm2=key.section_mm2,
            cable_form=CableForm.MULTIPOLAR,
        )
        if fallback in self._index:
            return self._index[fallback]

        raise KeyError(
            f"No hay Itab para material={key.material}, insulation={key.insulation}, "
            f"method={key.method.value}, system={key.phase_system.value}, section={key.section_mm2}mm²."
        )
