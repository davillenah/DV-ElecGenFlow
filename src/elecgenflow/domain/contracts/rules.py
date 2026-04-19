from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Severity = Literal["info", "warning", "error"]


class RuleReference(BaseModel):
    code: str = Field(description="Referencia normativa o ID interno (ej. AEA90364-... )")
    url: str | None = None
    notes: str | None = None


class RuleResult(BaseModel):
    rule_id: str
    passed: bool
    severity: Severity = "error"
    message: str
    references: list[RuleReference] = Field(default_factory=list)
    context: dict[str, str] = Field(default_factory=dict)
