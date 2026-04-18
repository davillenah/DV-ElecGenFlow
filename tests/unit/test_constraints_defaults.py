from __future__ import annotations

from elecgenflow.domain.contracts.constraints import ConstraintSet


def test_constraints_defaults_are_none_to_avoid_assumptions() -> None:
    c = ConstraintSet()
    assert c.max_voltage_drop_pct is None
    assert c.max_line_loading_pct is None
    assert c.min_power_factor is None
