from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from elecgenflow.engineering.nominal_tables import NominalLookupError, NominalTables


@dataclass(frozen=True)
class SizingRow:
    from_board: str
    to: str
    wire: str
    downstream_kva: float
    voltage_ll_v: float
    ib_a: float
    iz_a: float | None
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


class CableSizingValidationService:
    @staticmethod
    def validate_feedrs(
        *,
        load_report: dict[str, Any],
        nominal: NominalTables,
        voltage_ll_v: float,
    ) -> dict[str, Any]:
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

            iz: float | None = None
            status = "UNKNOWN"
            note = ""

            if wire:
                try:
                    cable = nominal.get_cable(wire)
                    iz = cable.ampacity_a
                    if iz is None:
                        status = "UNKNOWN"
                        note = "Cable found but ampacity_a missing"
                    else:
                        status = "PASS" if ib <= iz else "FAIL"
                except NominalLookupError as exc:
                    status = "UNKNOWN"
                    note = f"{exc}"
            else:
                note = "Wire tag missing"

            rows.append(
                SizingRow(
                    from_board=from_board,
                    to=to,
                    wire=wire,
                    downstream_kva=kva,
                    voltage_ll_v=voltage_ll_v,
                    ib_a=ib,
                    iz_a=iz,
                    status=status,
                    note=note,
                )
            )

        # summary
        pass_n = sum(1 for r in rows if r.status == "PASS")
        fail_n = sum(1 for r in rows if r.status == "FAIL")
        unk_n = sum(1 for r in rows if r.status == "UNKNOWN")

        return {
            "version": "0.1",
            "assumptions": {
                "model": "3ph",
                "voltage_ll_v": voltage_ll_v,
                "ib_formula": "Ib = kVA*1000 / (sqrt(3)*Vll)",
                "iz_source": "NominalTables.cables[*].ampacity_a",
                "no_auto_sizing": True,
            },
            "summary": {"total": len(rows), "pass": pass_n, "fail": fail_n, "unknown": unk_n},
            "rows": [
                {
                    "from": r.from_board,
                    "to": r.to,
                    "wire": r.wire,
                    "downstream_kva": round(r.downstream_kva, 6),
                    "voltage_ll_v": r.voltage_ll_v,
                    "ib_a": round(r.ib_a, 3),
                    "iz_a": (round(r.iz_a, 3) if r.iz_a is not None else None),
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
        lines.append("# Sizing Report (EPIC-04.04 — Validation Starter)")
        lines.append("")
        lines.append("## Assumptions")
        lines.append("")
        lines.append(f"- model: {a.get('model')}")
        lines.append(f"- voltage_ll_v: {a.get('voltage_ll_v')}")
        lines.append(f"- ib_formula: {a.get('ib_formula')}")
        lines.append(f"- iz_source: {a.get('iz_source')}")
        lines.append(f"- no_auto_sizing: {a.get('no_auto_sizing')}")
        lines.append("")
        lines.append("## Summary")
        lines.append("")
        lines.append(f"- total: {s.get('total')}")
        lines.append(f"- pass: {s.get('pass')}")
        lines.append(f"- fail: {s.get('fail')}")
        lines.append(f"- unknown: {s.get('unknown')}")
        lines.append("")
        lines.append("## Feeder Validation (Ib vs Iz)")
        lines.append("")
        lines.append("| From | To | Wire | kVA | Vll(V) | Ib(A) | Iz(A) | Status | Note |")
        lines.append("|---|---|---|---:|---:|---:|---:|---|---|")
        for r in rows:
            lines.append(
                f"| {r.get('from','')} | {r.get('to','')} | {r.get('wire','')} | "
                f"{r.get('downstream_kva',0):.3f} | {r.get('voltage_ll_v',0)} | {r.get('ib_a',0):.3f} | "
                f"{(r.get('iz_a') if r.get('iz_a') is not None else '')} | {r.get('status','')} | {r.get('note','')} |"
            )
        lines.append("")
        return "\n".join(lines)
