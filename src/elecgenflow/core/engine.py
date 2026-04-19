from __future__ import annotations

import logging
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from elecgenflow.core.config import EngineConfig
from elecgenflow.core.logging import configure_logging
from elecgenflow.core.manifest import RunManifest
from elecgenflow.domain.contracts.candidate import DesignCandidate
from elecgenflow.domain.contracts.problem import DesignProblem
from elecgenflow.domain.contracts.results import EngineResult
from elecgenflow.domain.services.contracts import (
    CandidateGenerator,
    Evaluator,
    Optimizer,
    RuleEngine,
    SimulationEngine,
)

logger = logging.getLogger(__name__)


class EngineServices(BaseModel):
    """Inyección de dependencias (services) para DDD/MVP.

    EPIC-1 provee implementaciones stub.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    generator: CandidateGenerator
    rule_engine: RuleEngine
    simulator: SimulationEngine
    evaluator: Evaluator
    optimizer: Optimizer


class Engine:
    """Orquestador headless del motor (Presenter).

    En EPIC-1 el pipeline es stub y se centra en contratos + trazabilidad.
    """

    def __init__(self, config: EngineConfig, services: EngineServices | None = None) -> None:
        self.config = config
        configure_logging()
        self.services = services or EngineServices(
            generator=CandidateGenerator.stub(),
            rule_engine=RuleEngine.stub(),
            simulator=SimulationEngine.stub(),
            evaluator=Evaluator.stub(),
            optimizer=Optimizer.stub(),
        )

    def run(self, problem: DesignProblem, out_dir: Path) -> EngineResult:
        out_dir.mkdir(parents=True, exist_ok=True)
        artifacts_dir = out_dir / self.config.artifacts_subdir
        artifacts_dir.mkdir(parents=True, exist_ok=True)

        logger.info("Engine run started")
        logger.info(
            f"Problem id={problem.problem_id} locale={problem.locale} standards={problem.standards}"
        )

        config_path = Path("configs/default_ar.yaml")
        config_text = config_path.read_text(encoding="utf-8") if config_path.exists() else ""
        problem_text = problem.model_dump_json(indent=2)

        seed = problem.seed if problem.seed is not None else self.config.default_seed
        manifest = RunManifest.create(seed=seed, config_text=config_text, problem_text=problem_text)
        manifest.write(artifacts_dir / "run_manifest.json")

        candidate = DesignCandidate.from_problem(problem, candidate_id="CAND-0001")

        result = EngineResult(
            problem_id=problem.problem_id,
            status="partial",
            message=(
                "EPIC-1: contratos y validación listos. "
                "Pipeline generativo/simulación/reglas se implementa en EPIC-2..EPIC-8."
            ),
            candidates=[candidate],
            artifacts={
                "run_manifest": str((artifacts_dir / "run_manifest.json").as_posix()),
                "engine_result": str((artifacts_dir / "engine_result.json").as_posix()),
            },
        )

        (artifacts_dir / "engine_result.json").write_text(
            result.model_dump_json(indent=2), encoding="utf-8"
        )
        logger.info("Engine run completed (partial)")
        return result
