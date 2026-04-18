from __future__ import annotations

from pydantic import BaseModel, Field


class StandardsRef(BaseModel):
    """Referencia normativa declarativa (no implica cumplimiento automático)."""

    aea_90364: bool = True
    aea_95403: bool = True
    iec_backup: bool = True
    notes: str | None = Field(default=None, description="Notas sobre alcance normativo aplicable")
