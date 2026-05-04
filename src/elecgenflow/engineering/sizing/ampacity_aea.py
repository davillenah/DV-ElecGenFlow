from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, ValidationError


class AmpacityRow(BaseModel):
    seccion: float = Field(gt=0)
    i_2x: float = Field(alias="2x", gt=0)
    i_3x: float = Field(alias="3x", gt=0)

    class Config:
        populate_by_name = True


class AmpacityConditions(BaseModel):
    temperatura_ambiente: float
    temperatura_terreno: float
    resistividad: float


MaterialKey = Literal["cobre", "aluminio"]
InsulationKey = Literal["PVC", "XLPE"]


class AmpacityAEA(BaseModel):
    descripcion: str
    condiciones: AmpacityConditions
    materiales: dict[str, Any]  # nested mapping, validated at lookup-time


@dataclass(frozen=True)
class AmpacityLookupKey:
    material: str  # cobre/aluminio
    insulation: str  # PVC/XLPE
    metodo: str  # B2/C/E/F/G/D1/D2
    arrangement: str  # "2x" | "3x"


class AmpacityCatalog:
    def __init__(self, model: AmpacityAEA) -> None:
        self.model = model

    @staticmethod
    def load(path: Path) -> AmpacityCatalog:
        data = json.loads(path.read_text(encoding="utf-8"))
        try:
            m = AmpacityAEA.model_validate(data)
        except ValidationError as exc:
            raise ValueError(f"Ampacity AEA inválido: {path}\n{exc}") from exc
        return AmpacityCatalog(m)

    def _get_rows(self, material: str, insulation: str, metodo: str) -> list[AmpacityRow]:
        mats = self.model.materiales
        if material not in mats:
            return []
        ins_map = mats.get(material) or {}
        if not isinstance(ins_map, dict):
            return []
        iso_map = ins_map.get(insulation) or {}
        if not isinstance(iso_map, dict):
            return []
        rows_raw = iso_map.get(metodo) or []
        if not isinstance(rows_raw, list):
            return []
        rows: list[AmpacityRow] = []
        for r in rows_raw:
            if isinstance(r, dict):
                try:
                    rows.append(AmpacityRow.model_validate(r))
                except ValidationError:
                    continue
        return sorted(rows, key=lambda x: x.seccion)

    def get_ampacity(self, *, key: AmpacityLookupKey, seccion: float) -> float | None:
        rows = self._get_rows(key.material, key.insulation, key.metodo)
        if not rows:
            return None
        # exact match by section
        for r in rows:
            if abs(r.seccion - seccion) < 1e-9:
                return r.i_2x if key.arrangement == "2x" else r.i_3x
        return None

    def suggest_section(self, *, key: AmpacityLookupKey, ib_a: float) -> float | None:
        rows = self._get_rows(key.material, key.insulation, key.metodo)
        if not rows:
            return None
        for r in rows:
            iz = r.i_2x if key.arrangement == "2x" else r.i_3x
            if iz >= ib_a:
                return r.seccion
        return None

    @staticmethod
    def parse_wire_tag(tag: str) -> AmpacityLookupKey | None:
        """
        Convención recomendada para poder auto-dimensionar sin DB extra:
        CU-PVC-B2-3x-25
        AL-XLPE-C-2x-50
        """
        parts = tag.strip().split("-")
        if len(parts) < 5:
            return None
        mat_raw, ins_raw, metodo, arrangement, _sec = (
            parts[0],
            parts[1],
            parts[2],
            parts[3],
            parts[4],
        )
        material = (
            "cobre"
            if mat_raw.upper() in {"CU", "COBRE"}
            else "aluminio" if mat_raw.upper() in {"AL", "ALUMINIO"} else ""
        )
        if not material:
            return None
        insulation = ins_raw.upper()
        if insulation not in {"PVC", "XLPE"}:
            return None
        if arrangement not in {"2x", "3x"}:
            return None
        return AmpacityLookupKey(
            material=material, insulation=insulation, metodo=metodo, arrangement=arrangement
        )
