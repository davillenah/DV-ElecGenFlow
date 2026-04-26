from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class LocaleSpec(BaseModel):
    """Locale de proyecto (por defecto AR)."""

    country: Literal["AR"] = "AR"
    frequency_hz: int = Field(default=50, ge=1, le=100)
    voltage_mv_options_v: list[int] = Field(default_factory=lambda: [13200, 33000])
    voltage_lv_options_v: list[int] = Field(default_factory=lambda: [380, 220])
