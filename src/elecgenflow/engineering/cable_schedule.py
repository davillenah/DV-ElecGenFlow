# src/elecgenflow/engineering/cable_schedule.py
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from elecgenflow.engineering.ampacity_aea import AmpacityCatalog, AmpacityLookupKey


def _f0(x: Any) -> float:
    try:
        return float(x)
    except Exception:
        return 0.0


def _calc_ib_3ph_from_kva(kva: float, v_ll: float) -> float:
    if v_ll <= 0:
        return 0.0
    return (kva * 1000.0) / (math.sqrt(3.0) * v_ll)


def _arrangement_from_config(wire_cfg: dict[str, Any]) -> str:
    meta = wire_cfg.get("meta") or {}
    if isinstance(meta, dict):
        arr = meta.get("arrangement")
        if arr in {"2x", "3x"}:
            return str(arr)
    return "3x"


def _key_from_wire_config(wire_cfg: dict[str, Any]) -> AmpacityLookupKey | None:
    conductor = wire_cfg.get("conductor")
    insulation = wire_cfg.get("insulation")
    method = wire_cfg.get("install_method")

    if conductor not in {"CU", "AL"}:
        return None
    if insulation not in {"PVC", "XLPE"}:
        return None
    if not isinstance(method, str) or not method:
        return None

    material = "cobre" if conductor == "CU" else "aluminio"
    arrangement = _arrangement_from_config(wire_cfg)

    return AmpacityLookupKey(
        material=material, insulation=insulation, metodo=method, arrangement=arrangement
    )


def _wire_config_from_links(compiled_links: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for lk in compiled_links:
        wire_id = str(lk.get("wire_id") or lk.get("wire") or "").strip()
        wc = lk.get("wire_config") or {}
        if wire_id and isinstance(wc, dict):
            out[wire_id] = wc
    return out


@dataclass(frozen=True)
class CableScheduleRow:
    from_board: str
    to: str
    wire_id: str
    kva: float
    vll: float

    ib_a: float
    ib_design_a: float

    conductor: str | None
    insulation: str | None
    method: str | None
    arrangement: str | None

    selected_section_mm2: float | None
    selected_iz_a: float | None

    note: str = ""


class CableScheduleService:
    @staticmethod
    def build(
        *,
        load_report: dict[str, Any],
        compiled_links: list[dict[str, Any]],
        ampacity: AmpacityCatalog,
        voltage_ll_v: float,
        default_key: AmpacityLookupKey,
        cable_reserve_pct: float = 0.0,
    ) -> dict[str, Any]:
        wc_map = _wire_config_from_links(compiled_links)

        ins = load_report.get("in_service") or {}
        feeders = ins.get("feeders") or []

        rows: list[CableScheduleRow] = []
        for f in feeders:
            from_board = str(f.get("from_board") or "")
            to = str(f.get("to") or "")
            wire_id = str(f.get("wire") or "")

            dt = f.get("downstream_total") or {}
            kva = _f0(dt.get("kVA"))

            ib = _calc_ib_3ph_from_kva(kva, voltage_ll_v)
            ib_design = ib * (1.0 + (cable_reserve_pct / 100.0))

            wire_cfg = wc_map.get(wire_id) or {}
            key = _key_from_wire_config(wire_cfg) or default_key

            selected_section = ampacity.suggest_section(key=key, ib_a=ib_design)
            selected_iz = (
                ampacity.get_ampacity(key=key, seccion=selected_section)
                if selected_section
                else None
            )

            note = ""
            if not wc_map.get(wire_id):
                note = "wire_config missing -> default key applied"
            if selected_section is None:
                note = (note + " | " if note else "") + "no section found"

            rows.append(
                CableScheduleRow(
                    from_board=from_board,
                    to=to,
                    wire_id=wire_id,
                    kva=kva,
                    vll=voltage_ll_v,
                    ib_a=ib,
                    ib_design_a=ib_design,
                    conductor=wire_cfg.get("conductor") if isinstance(wire_cfg, dict) else None,
                    insulation=wire_cfg.get("insulation") if isinstance(wire_cfg, dict) else None,
                    method=wire_cfg.get("install_method") if isinstance(wire_cfg, dict) else None,
                    arrangement=(
                        _arrangement_from_config(wire_cfg) if isinstance(wire_cfg, dict) else None
                    ),
                    selected_section_mm2=selected_section,
                    selected_iz_a=float(selected_iz) if selected_iz is not None else None,
                    note=note,
                )
            )

        return {
            "version": "0.1",
            "assumptions": {
                "selection": "minimum section that satisfies Iz >= Ib_design",
                "ib_formula": "Ib = kVA*1000 / (sqrt(3)*Vll)",
                "ib_design": "Ib_design = Ib * (1 + cable_reserve_pct/100)",
                "cable_reserve_pct": cable_reserve_pct,
                "voltage_ll_v": voltage_ll_v,
                "ampacity_source": "AEA ampacity catalog",
                "default_key": {
                    "material": default_key.material,
                    "insulation": default_key.insulation,
                    "metodo": default_key.metodo,
                    "arrangement": default_key.arrangement,
                },
            },
            "rows": [
                {
                    "from": r.from_board,
                    "to": r.to,
                    "wire_id": r.wire_id,
                    "kva": round(r.kva, 6),
                    "vll": r.vll,
                    "ib_a": round(r.ib_a, 3),
                    "ib_design_a": round(r.ib_design_a, 3),
                    "conductor": r.conductor,
                    "insulation": r.insulation,
                    "method": r.method,
                    "arrangement": r.arrangement,
                    "selected_section_mm2": r.selected_section_mm2,
                    "selected_iz_a": (
                        round(r.selected_iz_a, 3) if r.selected_iz_a is not None else None
                    ),
                    "note": r.note,
                }
                for r in rows
            ],
        }

    @staticmethod
    def to_markdown(schedule: dict[str, Any]) -> str:
        a = schedule.get("assumptions") or {}
        rows = schedule.get("rows") or []

        lines: list[str] = []
        lines.append("# Cable Schedule (Auto-Sizing) — EPIC-04.04")
        lines.append("")
        lines.append("## Assumptions")
        lines.append("")
        lines.append(f"- selection: {a.get('selection')}")
        lines.append(f"- ib_formula: {a.get('ib_formula')}")
        lines.append(f"- ib_design: {a.get('ib_design')}")
        lines.append(f"- cable_reserve_pct: {a.get('cable_reserve_pct')}")
        lines.append(f"- voltage_ll_v: {a.get('voltage_ll_v')}")
        lines.append(f"- ampacity_source: {a.get('ampacity_source')}")
        lines.append(f"- default_key: {a.get('default_key')}")
        lines.append("")
        lines.append("## Cables")
        lines.append("")
        lines.append(
            "| From | To | WireID | kVA | Vll(V) | Ib(A) | Ib*(1+R) | Cond | Selected (mm²) | Iz(A) | Note |"
        )
        lines.append("|---|---|---|---:|---:|---:|---:|---|---:|---:|---|")

        for r in rows:
            cond = f"{r.get('conductor', '?')}/{r.get('insulation', '?')}/{r.get('method', '?')}/{r.get('arrangement', '?')}"
            lines.append(
                f"| {r.get('from', '')} | {r.get('to', '')} | {r.get('wire_id', '')} | "
                f"{r.get('kva', 0):.3f} | {r.get('vll', 0)} | {r.get('ib_a', 0):.3f} | {r.get('ib_design_a', 0):.3f} | "
                f"{cond} | {r.get('selected_section_mm2') if r.get('selected_section_mm2') is not None else ''} | "
                f"{r.get('selected_iz_a') if r.get('selected_iz_a') is not None else ''} | {r.get('note', '')} |"
            )

        lines.append("")
        return "\n".join(lines)
