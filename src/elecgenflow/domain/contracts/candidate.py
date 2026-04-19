from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from elecgenflow.domain.contracts.artifacts import ReportArtifacts
from elecgenflow.domain.contracts.common import TraceableModel
from elecgenflow.domain.contracts.metrics import MetricsBundle
from elecgenflow.domain.contracts.problem import DesignProblem
from elecgenflow.domain.contracts.rules import RuleResult

CandidateStatus = Literal["new", "rejected", "simulated", "evaluated", "ranked"]


class DesignCandidate(TraceableModel):
    candidate_id: str
    problem_id: str
    status: CandidateStatus = "new"

    logical_ir: dict[str, Any] = Field(default_factory=dict)
    electrical_ir: dict[str, Any] = Field(default_factory=dict)

    rule_results: list[RuleResult] = Field(default_factory=list)
    simulation: dict[str, Any] = Field(default_factory=dict)
    metrics: MetricsBundle = Field(default_factory=MetricsBundle)
    reports: ReportArtifacts = Field(default_factory=ReportArtifacts)

    @staticmethod
    def from_problem(problem: DesignProblem, candidate_id: str) -> DesignCandidate:
        return DesignCandidate(
            candidate_id=candidate_id,
            problem_id=problem.problem_id,
            status="new",
            logical_ir=problem.payload.get("logical_ir", {}),
            electrical_ir=problem.payload.get("electrical_ir", {}),
            tags={"problem_name": problem.name},
        )
