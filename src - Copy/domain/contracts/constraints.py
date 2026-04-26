from __future__ import annotations

from pydantic import BaseModel, Field


class ConstraintSet(BaseModel):
    """Restricciones del problema.

    Defaults en None para evitar suposiciones técnicas.
    """

    max_voltage_drop_pct: float | None = Field(default=None, ge=0.0, le=100.0)
    max_line_loading_pct: float | None = Field(default=None, ge=0.0, le=300.0)
    max_transformer_loading_pct: float | None = Field(default=None, ge=0.0, le=300.0)
    max_thd_v_pct: float | None = Field(default=None, ge=0.0, le=100.0)
    min_power_factor: float | None = Field(default=None, ge=0.0, le=1.0)

    max_ground_resistance_ohm: float | None = Field(default=None, ge=0.0)

    notes: str | None = None
