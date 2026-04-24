from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, cast

from elecgenflow.core.config import load_config
from elecgenflow.core.engine import Engine
from elecgenflow.domain.contracts.problem import DesignProblem
from elecgenflow.engineering.load_aggregation import LoadAggregationService
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
    compiled_links, report_rt = compile_network(network_links, reg, mode="runtime")

    elecboard_ir = build_elecboard_ir(snapshots.boards_by_name, reg, compiled_links)

    # EPIC-04.01-B: PF desde config
    load_report = LoadAggregationService.aggregate(
        boards_by_name=cast(dict[str, dict[str, Any]], snapshots.boards_by_name),
        compiled_links=cast(list[dict[str, Any]], compiled_links),
        in_service_boards=set(reg.in_service_boards),
        out_of_service_boards=set(reg.out_of_service_boards),
        assembly_columns=dict(reg.assembly_columns),
        power_factor=cfg.power_factor_default,
    )
    load_md = LoadAggregationService.to_markdown(load_report)

    out_path = Path(out_dir)
    artifacts_dir = out_path / cfg.artifacts_subdir
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    load_json_path = artifacts_dir / "load_report.json"
    load_md_path = artifacts_dir / "load_report.md"
    load_json_path.write_text(
        json.dumps(load_report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    load_md_path.write_text(load_md, encoding="utf-8")

    registry_snapshot = {
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
    }

    compile_report = {
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
    }

    payload: dict[str, Any] = {
        "logical_ir": elecboard_ir.to_logical_ir_dict(),
        "electrical_ir": {
            "load_report": load_report,
            "registry_snapshot": registry_snapshot,
            "compile_report": compile_report,
            "artifacts": {
                "load_report_json": str(load_json_path.as_posix()),
                "load_report_md": str(load_md_path.as_posix()),
            },
        },
        "owner": snapshots.owner,
    }

    problem = DesignProblem(
        problem_id=f"PROJECT:{project_root.name}",
        name=project_root.name,
        description="Auto-loaded project + EPIC-04.01 load aggregation",
        seed=cfg.default_seed,
        payload=payload,
    )

    engine.run(problem, out_dir=Path(out_dir))
