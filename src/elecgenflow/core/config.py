# src/elecgenflow/core/config.py

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, ValidationError


class StandardsConfig(BaseModel):
    aea_90364: bool = True
    aea_95403: bool = True
    iec_backup: bool = True


class VoltageConfig(BaseModel):
    lv: list[int] = Field(default_factory=lambda: [380, 220])
    mv: list[int] = Field(default_factory=lambda: [13200, 33000])


class SizingConfig(BaseModel):
    """
    Configuración para dimensionamiento automático.
    Mantiene rutas a tablas nominales y algunos defaults operativos.
    """

    enabled: bool = True

    # PF por defecto (solo si una carga viene en kW sin kVA)
    power_factor_default: float = Field(default=0.85, ge=0.0, le=1.0)

    # Tablas nominales
    nominal_tables_root: str = "data/nominal"
    nominal_tables_version: str = "v0"
    nominal_overlays: list[str] = Field(default_factory=list)

    # Nombres de archivos nominales
    ampacity_filename: str = "ampacity_aea.json"
    derating_filename: str = "derating_defaults.json"

    # Artefacto de salida del sizing
    sizing_results_filename: str = "sizing_results.json"


class EngineConfig(BaseModel):
    """Configuración global del motor (defaults AR + flags).

    Nota: no reemplaza datos eléctricos de proyecto.
    """

    country: Literal["AR"] = "AR"
    frequency_hz: int = 50
    voltages: VoltageConfig = Field(default_factory=VoltageConfig)
    standards: StandardsConfig = Field(default_factory=StandardsConfig)

    default_seed: int = 12345
    deterministic: bool = True

    artifacts_subdir: str = "artifacts"

    # Defaults históricos (se mantienen para compatibilidad con configs viejas)
    power_factor_default: float = Field(default=0.85, ge=0.0, le=1.0)
    nominal_tables_root: str = "data/nominal"
    nominal_tables_version: str = "v0"
    nominal_overlays: list[str] = Field(default_factory=list)

    # Config preferida para sizing (se puede sobreescribir desde YAML)
    sizing: SizingConfig = Field(default_factory=SizingConfig)


def load_config(path: Path) -> EngineConfig:
    if not path.exists():
        raise FileNotFoundError(f"Config no encontrada: {path}")

    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    try:
        return EngineConfig.model_validate(data)
    except ValidationError as exc:
        raise ValueError(f"Config inválida: {exc}") from exc
