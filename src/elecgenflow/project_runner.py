from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, cast

from elecgenflow.core.config import load_config
from elecgenflow.core.engine import Engine
from elecgenflow.domain.contracts.problem import DesignProblem
from elecgenflow.ingest.dsl_adapter import build_elecboard_ir
from elecgenflow.ingest.import_utils import call_if_exists, import_module_from_path
from elecgenflow.ingest.network_compiler import compile_network
from elecgenflow.ingest.payload_models import NetworkLinkSnapshot
from elecgenflow.ingest.project_loader import load_project
from elecgenflow.ingest.registry_bootstrap import bootstrap_registry
from electro_core.network import Network

logger = logging.getLogger(__name__)


def _runtime_links_from_network_module(network_file: str) -> list[NetworkLinkSnapshot]:
    mod = import_module_from_path("plant_network_runtime", Path(network_file))

    build_fn = getattr(mod, "build", None)
    if callable(build_fn):
        net = Network()
        out = build_fn(net)
        if out is not None:
            net = cast(Network, out)

        links: list[NetworkLinkSnapshot] = []
        for lk in net.links:
            origin = lk.origin
            dest = lk.destination
            links.append(
                {
                    "origin": {
                        "board": cast(Any, origin.board),
                        "column": origin.column,
                        "protection": origin.protection,
                        "terminal": origin.terminal,
                    },
                    "destination": {
                        "board": cast(Any, dest.board),
                        "column": dest.column,
                        "protection": dest.protection,
                        "terminal": dest.terminal,
                        "load": dest.load,
                    },
                    "wire": lk.wire,
                    "meta": lk.meta,
                }
            )
        return links

    data = call_if_exists(mod, "build_network_snapshot")
    return cast(list[NetworkLinkSnapshot], data) if isinstance(data, list) else []


def run_project(
    project_path: str, *, out_dir: str = "out", config_path: str = "configs/default_ar.yaml"
) -> None:
    project_root = Path(project_path)
    cfg = load_config(Path(config_path))
    engine = Engine(cfg)

    snapshots = load_project(project_root)

    network_links: list[NetworkLinkSnapshot] = list(snapshots.network_links)
    if (not network_links) and snapshots.network_file:
        network_links = _runtime_links_from_network_module(snapshots.network_file)

    reg = bootstrap_registry(
        boards_by_name=snapshots.boards_by_name,
        assemblies=snapshots.assemblies,
        network_links=network_links,
    )

    _compiled_dev, report_dev = compile_network(network_links, reg, mode="dev")
    if report_dev.issues:
        logger.warning(
            "DEV CHECK: compile issues=%d compiled=%d skipped=%d",
            len(report_dev.issues),
            report_dev.compiled,
            report_dev.skipped,
        )

    compiled_links, report_rt = compile_network(network_links, reg, mode="runtime")
    if report_rt.issues:
        logger.warning(
            "RUNTIME: compile issues=%d compiled=%d skipped=%d",
            len(report_rt.issues),
            report_rt.compiled,
            report_rt.skipped,
        )

    elecboard_ir = build_elecboard_ir(snapshots.boards_by_name, reg, compiled_links)

    payload: dict[str, Any] = {
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
            "loads": sorted(reg.loads),
            "disabled": {
                "boards": sorted(reg.disabled_boards),
                "columns": sorted([f"{a}:{c}" for (a, c) in reg.disabled_columns]),
                "endpoints": sorted([f"{b}:{p}" for (b, p) in reg.disabled_endpoints]),
                "entrypoints": sorted([f"{b}:{p}" for (b, p) in reg.disabled_entrypoints]),
                "terminals": sorted([f"{b}:{t}" for (b, t) in reg.disabled_terminals]),
                "loads": sorted(reg.disabled_loads),
            },
        },
        "compile_report": {
            "dev": {
                "compiled": report_dev.compiled,
                "skipped": report_dev.skipped,
                "issues": [i.__dict__ for i in report_dev.issues],
            },
            "runtime": {
                "compiled": report_rt.compiled,
                "skipped": report_rt.skipped,
                "issues": [i.__dict__ for i in report_rt.issues],
            },
        },
        "logical_ir": elecboard_ir.to_logical_ir_dict(),
        "owner": snapshots.owner,
    }

    problem = DesignProblem(
        problem_id=f"PROJECT:{project_root.name}",
        name=project_root.name,
        description="Auto-loaded project (EPIC-04.00)",
        seed=12345,
        payload=payload,
    )

    engine.run(problem, out_dir=Path(out_dir))
