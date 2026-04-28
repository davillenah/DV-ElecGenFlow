from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, cast

from elecgenflow.core.config import load_config
from elecgenflow.core.engine import Engine
from elecgenflow.domain.contracts.problem import DesignProblem
from elecgenflow.engineering.ampacity_aea import AmpacityCatalog, AmpacityLookupKey
from elecgenflow.engineering.directed_graph import DirectedElectricalGraphService
from elecgenflow.engineering.load_aggregation import LoadAggregationService
from elecgenflow.engineering.nominal_tables import (
    load_nominal_tables,
    nominal_overlay_diff,
    nominal_overlay_diff_md,
    nominal_snapshot,
    nominal_snapshot_md,
)
from elecgenflow.engineering.sizing_validation import CableSizingValidationService
from elecgenflow.ingest.dsl_adapter import build_elecboard_ir
from elecgenflow.ingest.import_utils import call_if_exists, import_module_from_path
from elecgenflow.ingest.network_compiler import compile_network
from elecgenflow.ingest.payload_models import NetworkLinkSnapshot
from elecgenflow.ingest.project_loader import load_project
from elecgenflow.ingest.registry_bootstrap import bootstrap_registry
from elecgenflow.reporting.pdf_report import build_engineering_pdf
from electro_core.network import Network

logger = logging.getLogger(__name__)


def _runtime_links_from_network_module(network_file: str) -> list[NetworkLinkSnapshot]:
    """
    Runtime loader para Network DSL.
    Preferencia:
      1) build(network) -> Network (fluent)
      2) build_network_snapshot() -> list[NetworkLinkSnapshot] (fallback)
    """
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


def _get_default_lv_vll(cfg: Any) -> float:
    """
    Usa cfg.voltages.lv[0] si existe (ej: voltages.lv: [380, 220]).
    Fallback: 380.
    """
    try:
        volts = getattr(cfg, "voltages", None)
        if volts is not None:
            lv = getattr(volts, "lv", None)
            if isinstance(lv, list) and lv:
                return float(lv[0])
    except Exception:
        pass
    return 380.0


def _filter_valid_overlays(candidates: list[Path]) -> list[Path]:
    """
    Ignora overlays sin overlay=true (no bloqueante).
    Solo se aplican overlays con {"overlay": true}.
    """
    overlays: list[Path] = []
    for p in candidates:
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(data, dict) and data.get("overlay") is True:
                overlays.append(p)
            else:
                logger.warning("Ignoring nominal overlay (missing overlay=true): %s", p)
        except Exception:
            logger.warning("Ignoring nominal overlay (invalid json): %s", p)
    return overlays


def run_project(
    project_path: str,
    *,
    out_dir: str = "out",
    config_path: str = "configs/default_ar.yaml",
) -> None:
    project_root = Path(project_path)
    cfg = load_config(Path(config_path))
    engine = Engine(cfg)

    # ------------------------------------------------------------------
    # Artifacts dir (shared)
    # ------------------------------------------------------------------
    out_path = Path(out_dir)
    artifacts_dir = out_path / cfg.artifacts_subdir
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Load project + network
    # ------------------------------------------------------------------
    snapshots = load_project(project_root)

    network_links: list[NetworkLinkSnapshot] = list(snapshots.network_links)
    if not network_links and snapshots.network_file:
        network_links = _runtime_links_from_network_module(snapshots.network_file)

    reg = bootstrap_registry(
        boards_by_name=snapshots.boards_by_name,
        assemblies=snapshots.assemblies,
        network_links=network_links,
    )

    _compiled_dev, report_dev = compile_network(network_links, reg, mode="dev")
    compiled_links, report_rt = compile_network(network_links, reg, mode="runtime")

    elecboard_ir = build_elecboard_ir(
        snapshots.boards_by_name,
        reg,
        compiled_links,
    )

    # ------------------------------------------------------------------
    # EPIC-04.01 — Load aggregation
    # ------------------------------------------------------------------
    load_report = LoadAggregationService.aggregate(
        boards_by_name=cast(dict[str, dict[str, Any]], snapshots.boards_by_name),
        compiled_links=cast(list[dict[str, Any]], compiled_links),
        in_service_boards=set(reg.in_service_boards),
        out_of_service_boards=set(reg.out_of_service_boards),
        assembly_columns=dict(reg.assembly_columns),
        power_factor=cfg.power_factor_default,
    )
    load_md = LoadAggregationService.to_markdown(load_report)

    load_json_path = artifacts_dir / "load_report.json"
    load_md_path = artifacts_dir / "load_report.md"
    load_json_path.write_text(
        json.dumps(load_report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    load_md_path.write_text(load_md, encoding="utf-8")

    # ------------------------------------------------------------------
    # EPIC-04.02 — DAG report
    # ------------------------------------------------------------------
    dag_report = DirectedElectricalGraphService.build_report(
        compiled_links=cast(list[dict[str, Any]], compiled_links),
        in_service_boards=set(reg.in_service_boards),
        out_of_service_boards=set(reg.out_of_service_boards),
        assembly_columns=dict(reg.assembly_columns),
        include_assembly_edges=True,
    )
    dag_md = DirectedElectricalGraphService.to_markdown(dag_report)

    dag_json_path = artifacts_dir / "dag_report.json"
    dag_md_path = artifacts_dir / "dag_report.md"
    dag_json_path.write_text(json.dumps(dag_report, indent=2, ensure_ascii=False), encoding="utf-8")
    dag_md_path.write_text(dag_md, encoding="utf-8")

    # ------------------------------------------------------------------
    # EPIC-04.03 — Nominal tables + overlay diff (AUTO overlays, non-blocking)
    # ------------------------------------------------------------------
    root_nominal = Path(cfg.nominal_tables_root)

    if cfg.nominal_overlays:
        candidates = [Path(x) for x in cfg.nominal_overlays]
    else:
        found = list(root_nominal.glob("overlays/**/*.json"))
        candidates = sorted(found, key=lambda p: (len(p.parts), str(p)))

    overlays = _filter_valid_overlays(candidates)

    nominal_tables = load_nominal_tables(
        root=root_nominal,
        version=str(cfg.nominal_tables_version),
        overlays=overlays,
    )

    nominal_json = nominal_snapshot(nominal_tables)
    nominal_md = nominal_snapshot_md(nominal_tables)

    nominal_json_path = artifacts_dir / "nominal_snapshot.json"
    nominal_md_path = artifacts_dir / "nominal_snapshot.md"
    nominal_json_path.write_text(
        json.dumps(nominal_json, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    nominal_md_path.write_text(nominal_md, encoding="utf-8")

    overlay_diff = nominal_overlay_diff(
        root=root_nominal,
        version=str(cfg.nominal_tables_version),
        overlays=overlays,
    )
    overlay_diff_md = nominal_overlay_diff_md(overlay_diff)

    overlay_json_path = artifacts_dir / "nominal_overlay_diff.json"
    overlay_md_path = artifacts_dir / "nominal_overlay_diff.md"
    overlay_json_path.write_text(
        json.dumps(overlay_diff, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    overlay_md_path.write_text(overlay_diff_md, encoding="utf-8")

    # ------------------------------------------------------------------
    # EPIC-04.04 — Auto-sizing sugerido (Ib vs Iz + suggested section)
    # ------------------------------------------------------------------
    vll = _get_default_lv_vll(cfg)

    ampacity_path = root_nominal / str(cfg.nominal_tables_version) / "ampacity_aea.json"
    ampacity = AmpacityCatalog.load(ampacity_path) if ampacity_path.exists() else None

    # Default mapping if wire tag cannot be parsed (safe defaults)
    default_key = AmpacityLookupKey(
        material="cobre", insulation="PVC", metodo="B2", arrangement="3x"
    )

    sizing_report = CableSizingValidationService.validate_feedrs(
        load_report=load_report,
        nominal=nominal_tables,
        voltage_ll_v=float(vll),
        ampacity=ampacity,
        default_ampacity_key=default_key,
    )
    sizing_md = CableSizingValidationService.to_markdown(sizing_report)

    sizing_json_path = artifacts_dir / "sizing_report.json"
    sizing_md_path = artifacts_dir / "sizing_report.md"
    sizing_json_path.write_text(
        json.dumps(sizing_report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    sizing_md_path.write_text(sizing_md, encoding="utf-8")

    # ------------------------------------------------------------------
    # EPIC-11 precursor — PDF consolidated from artifacts
    # ------------------------------------------------------------------
    pdf_path = artifacts_dir / "engineering_report.pdf"
    pdf_res = build_engineering_pdf(
        project_name=project_root.name,
        artifacts_dir=artifacts_dir,
        out_pdf=pdf_path,
    )

    # ------------------------------------------------------------------
    # Registry snapshot + compile report
    # ------------------------------------------------------------------
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

    # ------------------------------------------------------------------
    # Payload final
    # ------------------------------------------------------------------
    payload: dict[str, Any] = {
        "logical_ir": elecboard_ir.to_logical_ir_dict(),
        "electrical_ir": {
            "load_report": load_report,
            "dag_report": dag_report,
            "nominal_tables": nominal_json,
            "nominal_overlay_diff": overlay_diff,
            "sizing_report": sizing_report,
            "registry_snapshot": registry_snapshot,
            "compile_report": compile_report,
            "pdf_build": {
                "enabled": pdf_res.enabled,
                "pdf_path": pdf_res.pdf_path,
                "reason": pdf_res.reason,
            },
            "artifacts": {
                "load_report_json": str(load_json_path.as_posix()),
                "load_report_md": str(load_md_path.as_posix()),
                "dag_report_json": str(dag_json_path.as_posix()),
                "dag_report_md": str(dag_md_path.as_posix()),
                "nominal_snapshot_json": str(nominal_json_path.as_posix()),
                "nominal_snapshot_md": str(nominal_md_path.as_posix()),
                "nominal_overlay_diff_json": str(overlay_json_path.as_posix()),
                "nominal_overlay_diff_md": str(overlay_md_path.as_posix()),
                "sizing_report_json": str(sizing_json_path.as_posix()),
                "sizing_report_md": str(sizing_md_path.as_posix()),
                "engineering_report_pdf": str(pdf_path.as_posix()),
            },
        },
        "owner": snapshots.owner,
    }

    problem = DesignProblem(
        problem_id=f"PROJECT:{project_root.name}",
        name=project_root.name,
        description="Auto-loaded project + EPIC-04.01/04.02/04.03 + EPIC-04.04 suggested sizing + PDF",
        seed=cfg.default_seed,
        payload=payload,
    )

    engine.run(problem, out_dir=out_path)
