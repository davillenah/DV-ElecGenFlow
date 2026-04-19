from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

ObjectiveName = Literal[
    "min_cost",
    "min_voltage_drop",
    "min_losses",
    "min_thd",
    "max_protection_margin",
    "min_device_count",
]


class ObjectiveSpec(BaseModel):
    name: ObjectiveName
    weight: float = Field(default=1.0, ge=0.0)
    enabled: bool = True
