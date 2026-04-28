from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Any

from elecgenflow.engineering.ampacity_aea import AmpacityCatalog, AmpacityLookupKey
from elecgenflow.engineering.nominal_tables import NominalLookupError, NominalTables


@dataclass(frozen=True)
class SizingRow:
    from_board: str
    to: str
    wire: str

    downstream_kva: float
    voltage_ll_v: float
    ib_a: float

    # current wire evaluation
    current_section_mm2: float | None
    iz_a: float | None
    iz_source: str | None  # "nominal" | "aea" | None

    # suggested (auto-sizing suggested)
    suggested_section_mm2: float | None
    suggested_iz_a: float | None
    suggested_source: str | None  # "aea" | None

    status: str  # PASS | FAIL | UNKNOWN
    note: str = ""


def _f0(x: Any) -> float:
    try:
        return float(x)
    except Exception:
        return 0.0


def _calc_ib_3ph_from_kva(kva: float, v_ll: float) -> float:
    if v_ll <= 0:
        return 0.0
    return (kva * 1000.0) / (math.sqrt(3.0) * v_ll)


_SEC_RE = re.compile(r"(\d+(?:\.\d+)?)\s*$")


def _guess_section_from_wire_tag(wire: str) -> float | None:
    """
    Intenta extraer sección desde tags tipo:
      - CU-PVC-B2-3x-25  -> 25
      - W-TGBT-TSF-4x240 -> 240
      - ...-95           -> 95
    """
    if not wire:
        return None
    m = _SEC_RE.search(wire)
    if not m:
        return None
    try:
        return float(m.group(1))
    except Exception:
        return None


class CableSizingValidationService:
    @staticmethod
    def validate_feedrs(
        *,
        load_report: dict[str, Any],
        nominal: NominalTables,
        voltage_ll_v: float,
        ampacity: AmpacityCatalog | None = None,
        default_ampacity_key: AmpacityLookupKey | None = None,
    ) -> dict[str, Any]:
        """
        - Valida Ib vs Iz con Iz desde:
          1) nominal tables (cable tag exacto)
          2) ampacity AEA (si hay catálogo y se puede mapear)
        - Si FAIL/UNKNOWN y hay ampacity, sugiere sección mínima que cumpla (auto-sizing sugerido).
        """
        ins = load_report.get("in_service") or {}
        feeders = ins.get("feeders") or []

        rows: list[SizingRow] = []

        for f in feeders:
            from_board = str(f.get("from_board") or "")
            to = str(f.get("to") or "")
            wire = str(f.get("wire") or "")

            dt = f.get("downstream_total") or {}
            kva = _f0(dt.get("kVA"))
            ib = _calc_ib_3ph_from_kva(kva, voltage_ll_v)

            current_section = _guess_section_from_wire_tag(wire)

            iz: float | None = None
            iz_source: str | None = None
            note = ""

            # 1) try nominal tables by exact tag
            if wire:
                try:
                    cable = nominal.get_cable(wire)
                    iz = cable.ampacity_a
                    iz_source = "nominal"
                    if iz is None:
                        note = "Cable found in nominal but ampacity_a missing"
                except NominalLookupError:
                    pass
            else:
                note = "Wire tag missing"

            # 2) fallback: AEA ampacity table (if provided)
            aea_key: AmpacityLookupKey | None = None
            if ampacity is not None:
                aea_key = AmpacityCatalog.parse_wire_tag(wire) or default_ampacity_key

            if (
                iz is None
                and ampacity is not None
                and aea_key is not None
                and current_section is not None
            ):
                iz_aea = ampacity.get_ampacity(key=aea_key, seccion=current_section)
                if iz_aea is not None:
                    iz = float(iz_aea)
                    iz_source = "aea"
                    if not note:
                        note = "Iz from AEA table"

            status = "UNKNOWN"
            if iz is not None:
                status = "PASS" if ib <= iz else "FAIL"
            else:
                if not note:
                    note = "Iz not available (no nominal ampacity_a and no AEA match)"

            # Auto-sizing suggested: if FAIL or UNKNOWN, suggest section from AEA
            sugg_sec: float | None = None
            sugg_iz: float | None = None
            sugg_source: str | None = None

            if ampacity is not None and aea_key is not None and (status in {"FAIL", "UNKNOWN"}):
                sugg_sec = ampacity.suggest_section(key=aea_key, ib_a=ib)
                if sugg_sec is not None:
                    sugg_iz_val = ampacity.get_ampacity(key=aea_key, seccion=sugg_sec)
                    sugg_iz = float(sugg_iz_val) if sugg_iz_val is not None else None
                    sugg_source = "aea"
                    if status == "FAIL":
                        note = (note + " | " if note else "") + f"Suggested section {sugg_sec}mm2"
                    else:
                        note = (
                            note + " | " if note else ""
                        ) + f"Suggested section {sugg_sec}mm2 (no current Iz)"

            rows.append(
                SizingRow(
                    from_board=from_board,
                    to=to,
                    wire=wire,
                    downstream_kva=kva,
                    voltage_ll_v=voltage_ll_v,
                    ib_a=ib,
                    current_section_mm2=current_section,
                    iz_a=iz,
                    iz_source=iz_source,
                    suggested_section_mm2=sugg_sec,
                    suggested_iz_a=sugg_iz,
                    suggested_source=sugg_source,
                    status=status,
                    note=note,
                )
            )

        pass_n = sum(1 for r in rows if r.status == "PASS")
        fail_n = sum(1 for r in rows if r.status == "FAIL")
        unk_n = sum(1 for r in rows if r.status == "UNKNOWN")
        sugg_n = sum(1 for r in rows if r.suggested_section_mm2 is not None)

        return {
            "version": "0.2",
            "assumptions": {
                "model": "3ph",
                "voltage_ll_v": voltage_ll_v,
                "ib_formula": "Ib = kVA*1000 / (sqrt(3)*Vll)",
                "iz_sources": [
                    "NominalTables.cables[*].ampacity_a",
                    "AEA ampacity table (optional)",
                ],
                "auto_sizing": "suggested_only",
                "no_apply_changes": True,
            },
            "summary": {
                "total": len(rows),
                "pass": pass_n,
                "fail": fail_n,
                "unknown": unk_n,
                "suggested": sugg_n,
            },
            "rows": [
                {
                    "from": r.from_board,
                    "to": r.to,
                    "wire": r.wire,
                    "downstream_kva": round(r.downstream_kva, 6),
                    "voltage_ll_v": r.voltage_ll_v,
                    "ib_a": round(r.ib_a, 3),
                    "current_section_mm2": r.current_section_mm2,
                    "iz_a": (round(r.iz_a, 3) if r.iz_a is not None else None),
                    "iz_source": r.iz_source,
                    "suggested_section_mm2": r.suggested_section_mm2,
                    "suggested_iz_a": (
                        round(r.suggested_iz_a, 3) if r.suggested_iz_a is not None else None
                    ),
                    "suggested_source": r.suggested_source,
                    "status": r.status,
                    "note": r.note,
                }
                for r in rows
            ],
        }

    @staticmethod
    def to_markdown(sizing_report: dict[str, Any]) -> str:
        a = sizing_report.get("assumptions") or {}
        s = sizing_report.get("summary") or {}
        rows = sizing_report.get("rows") or []

        lines: list[str] = []
        lines.append("# Sizing Report (EPIC-04.04 — Suggested Auto-Sizing)")
        lines.append("")
        lines.append("## Assumptions")
        lines.append("")
        lines.append(f"- model: {a.get('model')}")
        lines.append(f"- voltage_ll_v: {a.get('voltage_ll_v')}")
        lines.append(f"- ib_formula: {a.get('ib_formula')}")
        lines.append(f"- iz_sources: {a.get('iz_sources')}")
        lines.append(f"- auto_sizing: {a.get('auto_sizing')}")
        lines.append(f"- no_apply_changes: {a.get('no_apply_changes')}")
        lines.append("")
        lines.append("## Summary")
        lines.append("")
        lines.append(f"- total: {s.get('total')}")
        lines.append(f"- pass: {s.get('pass')}")
        lines.append(f"- fail: {s.get('fail')}")
        lines.append(f"- unknown: {s.get('unknown')}")
        lines.append(f"- suggested: {s.get('suggested')}")
        lines.append("")
        lines.append("## Feeder Validation (Ib vs Iz) + Suggested Section")
        lines.append("")
        lines.append(
            "| From | To | Wire | kVA | Vll(V) | Ib(A) | Sec(mm²) | Iz(A) | Iz src | Suggested(mm²) | Sug Iz(A) | Status | Note |"
        )
        lines.append("|---|---|---|---:|---:|---:|---:|---:|---|---:|---:|---|---|")
        for r in rows:
            iz = r.get("iz_a")
            ssec = r.get("suggested_section_mm2")
            siz = r.get("suggested_iz_a")
            lines.append(
                f"| {r.get('from','')} | {r.get('to','')} | {r.get('wire','')} | "
                f"{r.get('downstream_kva',0):.3f} | {r.get('voltage_ll_v',0)} | {r.get('ib_a',0):.3f} | "
                f"{(r.get('current_section_mm2') if r.get('current_section_mm2') is not None else '')} | "
                f"{(iz if iz is not None else '')} | {r.get('iz_source','')} | "
                f"{(ssec if ssec is not None else '')} | {(siz if siz is not None else '')} | "
                f"{r.get('status','')} | {r.get('note','')} |"
            )
        lines.append("")
        return "\n".join(lines)
