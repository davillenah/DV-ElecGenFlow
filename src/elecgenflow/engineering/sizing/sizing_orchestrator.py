# src/elecgenflow/engineering/sizing/sizing_orchestrator.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from elecgenflow.engineering.catalog.composite_catalog import CableQuery, CompositeCatalog
from elecgenflow.engineering.catalog.methods import CableForm, InstallationRefMethod, PhaseSystem
from elecgenflow.engineering.sizing.load_aggregation import LoadAggregationService
from elecgenflow.engineering.sizing.protection_policy import ProtectionSpec
from elecgenflow.engineering.sizing.sizing_engine import Result, SizingEngine


@dataclass(frozen=True)
class FeederSizingInput:
    """Feeder resuelto desde snapshots."""

    from_board: str
    to_board: str
    circuit_tag: str
    wire_id: str

    load_kw: float
    load_kva: float

    phase_system: PhaseSystem
    cable_form: CableForm
    conductor: str
    insulation: str
    method: InstallationRefMethod

    ambient_air_c: float = 40.0
    grouped_circuits: int = 1
    soil_resistivity: float | None = None
    burial_depth_m: float | None = None

    voltage_ll_v: float = 380.0
    voltage_ln_v: float = 220.0


@dataclass(frozen=True)
class FeederSizingPrepared:
    """Paquete liviano para trazabilidad (probe + Itab/Iz)."""

    inp: FeederSizingInput
    cable_query: CableQuery
    itab_a: float
    iz_eff_a: float


@dataclass(frozen=True)
class FeederSized:
    """Resultado final por feeder (input + resultado del motor)."""

    inp: FeederSizingInput
    result: Result


def _s(x: Any) -> str:
    return x if isinstance(x, str) else ""


def _f0(x: Any) -> float:
    try:
        if x is None:
            return 0.0
        return float(x)
    except Exception:
        return 0.0


def _infer_phase_system_from_board(board_snap: dict[str, Any]) -> PhaseSystem:
    sys_raw = (
        board_snap.get("system")
        or board_snap.get("configured_as")
        or board_snap.get("phase_system")
        or ""
    )
    ssys = _s(sys_raw).upper()
    if "TRI" in ssys:
        return PhaseSystem.THREE_PHASE
    if "MONO" in ssys or "SINGLE" in ssys:
        return PhaseSystem.SINGLE_PHASE
    return PhaseSystem.THREE_PHASE


def _infer_voltage_from_board(board_snap: dict[str, Any]) -> tuple[float, float]:
    vraw = board_snap.get("voltage") or board_snap.get("voltage_v") or ""
    vtxt = _s(vraw).upper().replace("V", "").strip()
    if "/" in vtxt:
        a, b = vtxt.split("/", 1)
        return _f0(a), _f0(b)

    vll = _f0(vtxt)
    if vll > 0:
        return vll, 220.0
    return 380.0, 220.0


def _wire_cfg_from_meta(meta: dict[str, Any]) -> dict[str, Any]:
    """
    Entrada preferida: meta["wire_config"] (dict).
    Fallback: meta completo (compatibilidad con snapshots viejos).
    """
    wc = meta.get("wire_config")
    if isinstance(wc, dict):
        return wc
    return meta


def _infer_cable_form(cfg: dict[str, Any]) -> CableForm:
    if cfg.get("multipolar") is True:
        return CableForm.MULTIPOLAR
    if cfg.get("unipolar") is True:
        return CableForm.UNIPOLAR

    sform = _s(cfg.get("form") or cfg.get("cable_form")).upper()
    if "UNI" in sform:
        return CableForm.UNIPOLAR
    if "MULTI" in sform:
        return CableForm.MULTIPOLAR
    return CableForm.MULTIPOLAR


def _norm_conductor(x: Any) -> str:
    s = _s(x).upper()
    if s in ("AL", "ALUMINIO", "ALUMINUM"):
        return "AL"
    if s in ("CU", "COBRE", "COPPER"):
        return "CU"
    return s or "CU"


def _norm_insulation(x: Any) -> str:
    s = _s(x).upper()
    return s or "PVC"


def _norm_method(x: Any) -> InstallationRefMethod:
    s = _s(x).upper()
    try:
        return InstallationRefMethod(s)
    except Exception:
        return InstallationRefMethod.E


def _protection_spec_from_cfg(cfg: dict[str, Any]) -> ProtectionSpec:
    dev = _s(cfg.get("protection_type") or cfg.get("device_type") or "MCB")
    in_a = cfg.get("protection_in_a")
    i2_a = cfg.get("protection_i2_a")
    return ProtectionSpec(
        device_type=dev,
        in_a=float(in_a) if in_a is not None else None,
        i2_a=float(i2_a) if i2_a is not None else None,
    )


class SizingOrchestrator:
    """Construye inputs desde snapshots y ejecuta el motor."""

    def __init__(
        self,
        *,
        catalog: CompositeCatalog,
        power_factor_default: float = 0.85,
        sizing_engine: SizingEngine | None = None,
    ) -> None:
        self.catalog = catalog
        self.pf_default = power_factor_default
        self.sizing_engine = sizing_engine or SizingEngine(
            catalog=catalog,
            default_pf=power_factor_default,
        )

    def _load_report(
        self,
        *,
        boards_by_name: dict[str, dict[str, Any]],
        compiled_links: list[dict[str, Any]],
        in_service_boards: set[str],
        out_of_service_boards: set[str],
        assembly_columns: dict[str, dict[str, str]] | None,
    ) -> dict[str, Any]:
        return LoadAggregationService.aggregate(
            boards_by_name=boards_by_name,
            compiled_links=compiled_links,
            in_service_boards=in_service_boards,
            out_of_service_boards=out_of_service_boards,
            assembly_columns=assembly_columns,
            power_factor=self.pf_default,
        )

    def _iter_feeder_inputs(
        self,
        *,
        boards_by_name: dict[str, dict[str, Any]],
        feeders: list[dict[str, Any]],
    ) -> list[FeederSizingInput]:
        out: list[FeederSizingInput] = []

        for f in feeders:
            from_board = _s(f.get("from_board"))
            to_node = _s(f.get("to"))
            wire_id = _s(f.get("wire"))

            meta = f.get("meta") or {}
            if not isinstance(meta, dict):
                meta = {}

            if not from_board or not to_node or not wire_id:
                continue
            if to_node.startswith("LOAD:"):
                continue

            from_snap = boards_by_name.get(from_board) or {}

            phase_system = _infer_phase_system_from_board(from_snap)
            vll, vln = _infer_voltage_from_board(from_snap)

            dt = f.get("downstream_total") or {}
            load_kw = _f0(dt.get("kW"))
            load_kva = _f0(dt.get("kVA"))

            cfg = _wire_cfg_from_meta(meta)

            conductor = _norm_conductor(cfg.get("conductor"))
            insulation = _norm_insulation(cfg.get("insulation"))
            method = _norm_method(cfg.get("installed_in") or cfg.get("method"))
            cable_form = _infer_cable_form(cfg)

            ambient_air_c = _f0(cfg.get("ambient_air_c")) or 40.0
            grouped = int(cfg.get("grouped_circuits") or 1)
            soil = cfg.get("soil_resistivity")
            depth = cfg.get("burial_depth_m")
            circuit_tag = _s(cfg.get("circuit_tag") or cfg.get("tag") or "")

            out.append(
                FeederSizingInput(
                    from_board=from_board,
                    to_board=to_node,
                    circuit_tag=circuit_tag,
                    wire_id=wire_id,
                    load_kw=load_kw,
                    load_kva=load_kva,
                    phase_system=phase_system,
                    cable_form=cable_form,
                    conductor=conductor,
                    insulation=insulation,
                    method=method,
                    ambient_air_c=ambient_air_c,
                    grouped_circuits=grouped,
                    soil_resistivity=float(soil) if soil is not None else None,
                    burial_depth_m=float(depth) if depth is not None else None,
                    voltage_ll_v=vll or 380.0,
                    voltage_ln_v=vln or 220.0,
                )
            )

        return out

    def prepare_feeders(
        self,
        *,
        boards_by_name: dict[str, dict[str, Any]],
        compiled_links: list[dict[str, Any]],
        in_service_boards: set[str],
        out_of_service_boards: set[str],
        assembly_columns: dict[str, dict[str, str]] | None = None,
    ) -> list[FeederSizingPrepared]:
        load_report = self._load_report(
            boards_by_name=boards_by_name,
            compiled_links=compiled_links,
            in_service_boards=in_service_boards,
            out_of_service_boards=out_of_service_boards,
            assembly_columns=assembly_columns,
        )
        feeders = (load_report.get("in_service") or {}).get("feeders") or []

        prepared: list[FeederSizingPrepared] = []
        inputs = self._iter_feeder_inputs(boards_by_name=boards_by_name, feeders=feeders)

        for inp in inputs:
            conductor_temp_c = 70.0 if inp.insulation.upper() == "PVC" else 90.0

            q = CableQuery(
                method=inp.method,
                material=inp.conductor,
                insulation=inp.insulation,
                phase_system=inp.phase_system,
                cable_form=inp.cable_form,
                section_mm2=2.5,
                ambient_air_c=inp.ambient_air_c,
                grouped_circuits=inp.grouped_circuits,
                soil_resistivity=inp.soil_resistivity,
                burial_depth_m=inp.burial_depth_m,
                conductor_temp_c=conductor_temp_c,
            )

            try:
                itab, _d, iz = self.catalog.itab_and_iz(q)
            except Exception:
                continue

            prepared.append(FeederSizingPrepared(inp=inp, cable_query=q, itab_a=itab, iz_eff_a=iz))

        return prepared

    def size_feeders(
        self,
        *,
        boards_by_name: dict[str, dict[str, Any]],
        compiled_links: list[dict[str, Any]],
        in_service_boards: set[str],
        out_of_service_boards: set[str],
        assembly_columns: dict[str, dict[str, str]] | None = None,
    ) -> list[FeederSized]:
        load_report = self._load_report(
            boards_by_name=boards_by_name,
            compiled_links=compiled_links,
            in_service_boards=in_service_boards,
            out_of_service_boards=out_of_service_boards,
            assembly_columns=assembly_columns,
        )
        feeders = (load_report.get("in_service") or {}).get("feeders") or []

        sized: list[FeederSized] = []
        inputs = self._iter_feeder_inputs(boards_by_name=boards_by_name, feeders=feeders)

        # Map rápido: wire_id -> meta (para hints de protección y otros)
        meta_by_wire: dict[str, dict[str, Any]] = {}
        for f in feeders:
            w = _s(f.get("wire"))
            m = f.get("meta")
            if w and isinstance(m, dict):
                meta_by_wire[w] = m

        for inp in inputs:
            meta = meta_by_wire.get(inp.wire_id, {})
            cfg = _wire_cfg_from_meta(meta) if isinstance(meta, dict) else {}
            prot = _protection_spec_from_cfg(cfg)

            res = self.sizing_engine.size_feeder_ampacity_only(
                from_board=inp.from_board,
                to_board=inp.to_board,
                wire_id=inp.wire_id,
                method=inp.method,
                cable_form=inp.cable_form,
                conductor=inp.conductor,
                insulation=inp.insulation,
                phase_system=inp.phase_system,
                load_kva=inp.load_kva,
                load_kw=inp.load_kw,
                voltage_ll_v=inp.voltage_ll_v,
                voltage_ln_v=inp.voltage_ln_v,
                ambient_air_c=inp.ambient_air_c,
                grouped_circuits=inp.grouped_circuits,
                soil_resistivity=inp.soil_resistivity,
                burial_depth_m=inp.burial_depth_m,
                protection=prot,
            )

            sized.append(FeederSized(inp=inp, result=res))

        return sized
