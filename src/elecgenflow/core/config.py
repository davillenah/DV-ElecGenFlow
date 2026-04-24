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

    # EPIC-04.01-B
    power_factor_default: float = Field(default=0.85, ge=0.0, le=1.0)


def load_config(path: Path) -> EngineConfig:
    if not path.exists():
        raise FileNotFoundError(f"Config no encontrada: {path}")

    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    try:
        return EngineConfig.model_validate(data)
    except ValidationError as exc:
        raise ValueError(f"Config inválida: {exc}") from exc
