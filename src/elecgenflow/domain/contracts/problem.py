from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, model_validator

from elecgenflow.domain.contracts.constraints import ConstraintSet
from elecgenflow.domain.contracts.objectives import ObjectiveSpec
from elecgenflow.domain.value_objects.locale import LocaleSpec
from elecgenflow.domain.value_objects.standards import StandardsRef


class DesignProblem(BaseModel):
    """Entrada principal del motor (EPIC-1).

    Regla estricta: no asumir datos eléctricos críticos.
    Los detalles técnicos entran vía payload o modelos de EPIC-2/3+.
    """

    problem_id: str = Field(description="ID único del problema")
    name: str
    description: str | None = None

    locale: LocaleSpec = Field(default_factory=LocaleSpec)
    standards: StandardsRef = Field(default_factory=StandardsRef)

    seed: int | None = Field(default=None, ge=0, description="Seed para reproducibilidad")

    objectives: list[ObjectiveSpec] = Field(default_factory=list)
    constraints: ConstraintSet = Field(default_factory=ConstraintSet)

    payload: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _validate_objectives(self) -> DesignProblem:
        if self.objectives:
            enabled = [o for o in self.objectives if o.enabled and o.weight > 0]
            if not enabled:
                raise ValueError(
                    "Si objectives se proveen, al menos uno debe estar enabled con weight>0."
                )
        return self
