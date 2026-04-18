from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class MetricValue(BaseModel):
    name: str
    value: float
    unit: str | None = None
    meta: dict[str, Any] = Field(default_factory=dict)


class MetricsBundle(BaseModel):
    values: list[MetricValue] = Field(default_factory=list)

    def get(self, name: str) -> MetricValue | None:
        for m in self.values:
            if m.name == name:
                return m
        return None
