# src/elecgenflow/project_runner.py
from __future__ import annotations

from pathlib import Path

from elecgenflow.core.config import load_config
from elecgenflow.core.engine import Engine
from elecgenflow.domain.contracts.problem import DesignProblem
from elecgenflow.ingest.dsl_adapter import build_elecboard_ir
from elecgenflow.ingest.network_compiler import compile_network
from elecgenflow.ingest.project_loader import load_project
from elecgenflow.ingest.registry_bootstrap import bootstrap_registry


def run_project(
    project_path: str,
    *,
    out_dir: str = "out",
    config_path: str = "configs/default_ar.yaml",
) -> None:
    project_root = Path(project_path)
    cfg = load_config(Path(config_path))
    engine = Engine(cfg)

    snapshots = load_project(project_root)

    # 1) bootstrap registry desde boards + assemblies + network links
    reg = bootstrap_registry(
        boards_by_name=snapshots.boards_by_name,
        assemblies=snapshots.assemblies,
        network_links=snapshots.network_links,
    )

    # 2) compile/validate network (incluye mapping assembly column -> board real)
    compiled_links = compile_network(snapshots.network_links, reg)

    # 3) Adapter DSL -> ElecboardIR (EPIC-03 intacto)
    elecboard_ir = build_elecboard_ir(snapshots.boards_by_name, reg, compiled_links)

    payload = {
        "dsl": {
            "boards": list(snapshots.boards_by_name.values()),
            "network": compiled_links,
            "assemblies": snapshots.assemblies,
        },
        "registry_snapshot": {
            "boards": sorted(reg.boards),
            "columns": sorted([f"{b}:{c}" for (b, c) in reg.columns]),
            "protections_entry": sorted([f"{b}:{t}" for (b, t) in reg.protections_entry]),
            "protections_end": sorted([f"{b}:{t}" for (b, t) in reg.protections_end]),
            "out_of_service": sorted(reg.out_of_service_boards),
            "in_service": sorted(reg.in_service_boards),
        },
        "logical_ir": elecboard_ir.to_logical_ir_dict(),
        "owner": snapshots.owner,
        "project_meta": {
            "project_root": str(project_root),
            "note": "EPIC-04.00 auto-loaded project. locale/standards stay in contracts defaults.",
        },
    }

    # IMPORTANT: NO pasar locale/standards como strings/lista (contrato usa objects)
    problem = DesignProblem(
        problem_id=f"PROJECT:{project_root.name}",
        name=project_root.name,
        description="Auto-loaded project (EPIC-04.00)",
        seed=12345,
        payload=payload,
    )

    engine.run(problem, out_dir=Path(out_dir))
