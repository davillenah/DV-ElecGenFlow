from __future__ import annotations

from pathlib import Path

from elecgenflow.domain.contracts.problem import DesignProblem
from elecgenflow.domain.schemas.export import export_json_schema


def test_export_json_schema(tmp_path: Path) -> None:
    out = tmp_path / "DesignProblem.schema.json"
    export_json_schema(DesignProblem, out)
    text = out.read_text(encoding="utf-8")
    assert "problem_id" in text
