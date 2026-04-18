from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ReportArtifact(BaseModel):
    kind: str = Field(description="Ej: markdown, json, csv, image")
    path: str | None = None
    content: str | None = None
    meta: dict[str, Any] = Field(default_factory=dict)


class ReportArtifacts(BaseModel):
    artifacts: list[ReportArtifact] = Field(default_factory=list)
