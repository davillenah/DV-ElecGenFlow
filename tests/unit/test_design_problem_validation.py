from __future__ import annotations

import pytest

from elecgenflow.domain.contracts.objectives import ObjectiveSpec
from elecgenflow.domain.contracts.problem import DesignProblem


def test_design_problem_minimal_ok() -> None:
    p = DesignProblem(problem_id="P-001", name="Demo")
    assert p.problem_id == "P-001"
    assert p.locale.country == "AR"
    assert p.standards.aea_90364 is True


def test_design_problem_objectives_all_disabled_invalid() -> None:
    with pytest.raises(ValueError):
        DesignProblem(
            problem_id="P-002",
            name="Demo",
            objectives=[
                ObjectiveSpec(name="min_cost", weight=0.0, enabled=True),
                ObjectiveSpec(name="min_voltage_drop", weight=1.0, enabled=False),
            ],
        )


def test_design_problem_objectives_enabled_ok() -> None:
    p = DesignProblem(
        problem_id="P-003",
        name="Demo",
        objectives=[ObjectiveSpec(name="min_cost", weight=1.0, enabled=True)],
    )
    assert len(p.objectives) == 1
