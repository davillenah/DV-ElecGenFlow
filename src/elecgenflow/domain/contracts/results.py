from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from elecgenflow.domain.contracts.candidate import DesignCandidate


EngineStatus = Literal["ok", "partial", "failed"]


class EngineResult(BaseModel):
    problem_id: str
    status: EngineStatus
    message: str
    candidates: list[DesignCandidate] = Field(default_factory=list)
    artifacts: dict[str, Any] = Field(default_factory=dict)
