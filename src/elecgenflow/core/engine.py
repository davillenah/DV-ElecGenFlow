# src/elecgenflow/core/engine.py

from __future__ import annotations

import json
import logging
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict

from elecgenflow.core.catalog_provider import CatalogProvider
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
from elecgenflow.engineering.sizing.sizing_engine import SizingEngine
from elecgenflow.engineering.sizing.sizing_orchestrator import SizingOrchestrator
from elecgenflow.ingest.network_compiler import compile_network
from elecgenflow.ingest.project_loader import load_project
from elecgenflow.ingest.registry_bootstrap import bootstrap_registry

logger = logging.getLogger(__name__)


class EngineServices(BaseModel):
    """Inyección de dependencias (services) para DDD/MVP."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    generator: CandidateGenerator
    rule_engine: RuleEngine
    simulator: SimulationEngine
    evaluator: Evaluator
    optimizer: Optimizer


def _json_safe(obj: Any) -> Any:
    """
    Serializador robusto para resultados (dataclasses, enums, etc.).
    """
    if is_dataclass(obj):
        return {k: _json_safe(v) for k, v in asdict(obj).items()}
    if isinstance(obj, dict):
        return {str(k): _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [_json_safe(v) for v in obj]
    v = getattr(obj, "value", None)
    if v is not None and not isinstance(obj, (str, int, float, bool)):
        return _json_safe(v)
    return obj


def _infer_project_root(problem: DesignProblem) -> Path:
    """
    Best-effort: intenta obtener project root desde el problema.
    Orden:
      1) payload["project_root"] si existe
      2) attrs project_root/project_dir/project_path si existen
      3) fallback cwd
    """
    try:
        pr = problem.payload.get("project_root")
        if isinstance(pr, str) and pr:
            return Path(pr)
    except Exception:
        pass

    for attr in ("project_root", "project_dir", "project_path"):
        v = getattr(problem, attr, None)
        if isinstance(v, str) and v:
            return Path(v)

    cwd = Path.cwd()
    if (cwd / "Plant" / "Boards").exists():
        return cwd
    if (cwd / "Boards").exists():
        return cwd
    if (cwd / "MyProject" / "Plant" / "Boards").exists():
        return cwd / "MyProject"
    return cwd


class Engine:
    """Orquestador headless del motor (Presenter)."""

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
        """Ejecuta el pipeline del motor y deja artefactos en `out_dir`."""
        out_dir.mkdir(parents=True, exist_ok=True)

        artifacts_dir = out_dir / self.config.artifacts_subdir
        artifacts_dir.mkdir(parents=True, exist_ok=True)

        logger.info("Engine run started")
        logger.info(
            "Problem id=%s locale=%s standards=%s",
            problem.problem_id,
            problem.locale,
            problem.standards,
        )

        config_path = Path("configs/default_ar.yaml")
        config_text = config_path.read_text(encoding="utf-8") if config_path.exists() else ""
        problem_text = problem.model_dump_json(indent=2)

        seed = problem.seed if problem.seed is not None else self.config.default_seed
        manifest = RunManifest.create(seed=seed, config_text=config_text, problem_text=problem_text)
        manifest_path = artifacts_dir / "run_manifest.json"
        manifest.write(manifest_path)

        candidate = DesignCandidate.from_problem(problem, candidate_id="CAND-0001")

        artifacts: dict[str, Any] = {
            "run_manifest": str(manifest_path.as_posix()),
            "engine_result": str((artifacts_dir / "engine_result.json").as_posix()),
        }

        sizing_message = ""
        if self.config.sizing.enabled:
            try:
                project_root = _infer_project_root(problem)
                snapshots = load_project(project_root)

                reg = bootstrap_registry(
                    boards_by_name=snapshots.boards_by_name,
                    assemblies=snapshots.assemblies,
                    network_links=snapshots.network_links,
                )

                compiled_links, report = compile_network(
                    snapshots.network_links,
                    reg,
                    mode="dev",
                )

                catalog = CatalogProvider.from_engine_config(self.config).build()

                engine = SizingEngine(
                    catalog=catalog,
                    default_pf=self.config.sizing.power_factor_default,
                )
                orchestrator = SizingOrchestrator(
                    catalog=catalog,
                    power_factor_default=self.config.sizing.power_factor_default,
                    sizing_engine=engine,
                )

                sized = orchestrator.size_feeders(
                    boards_by_name=snapshots.boards_by_name,
                    compiled_links=compiled_links,
                    in_service_boards=reg.in_service_boards,
                    out_of_service_boards=reg.out_of_service_boards,
                    assembly_columns=reg.assembly_columns,
                )

                sizing_path = artifacts_dir / self.config.sizing.sizing_results_filename
                sizing_payload = {
                    "project_root": str(project_root.as_posix()),
                    "network_file": snapshots.network_file,
                    "compiled_links": report.compiled,
                    "skipped_links": report.skipped,
                    "issues": [_json_safe(asdict(i)) for i in report.issues],
                    "results": [_json_safe(r) for r in sized],
                }
                sizing_path.write_text(
                    json.dumps(sizing_payload, indent=2, ensure_ascii=False), encoding="utf-8"
                )
                artifacts["sizing_results"] = str(sizing_path.as_posix())

                sizing_message = f"Sizing: feeders={len(sized)} artifacts=sizing_results.json"
                logger.info(sizing_message)

            except Exception as exc:
                sizing_message = f"Sizing skipped: {exc}"
                logger.warning(sizing_message)

        result = EngineResult(
            problem_id=problem.problem_id,
            status="partial",
            message=(
                "EPIC-1: contratos y validación listos. "
                "Sizing automático (ampacidad+coordinación) ejecutado si está habilitado. "
                + (f" {sizing_message}" if sizing_message else "")
            ),
            candidates=[candidate],
            artifacts=artifacts,
        )

        (artifacts_dir / "engine_result.json").write_text(
            result.model_dump_json(indent=2),
            encoding="utf-8",
        )

        logger.info("Engine run completed (partial)")
        return result
