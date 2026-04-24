from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class LoadTotals:
    kw: float = 0.0
    kva: float = 0.0
    raw: int = 0


_NUM_UNIT_RE = re.compile(r"^\s*([0-9]+(?:\.[0-9]+)?)\s*([a-zA-Z]+)\s*$")


def _to_float_opt(x: Any) -> float | None:
    try:
        return float(x)
    except Exception:
        return None


def _parse_raw_string(raw: str) -> tuple[float, str] | None:
    m = _NUM_UNIT_RE.match(raw)
    if not m:
        return None
    val = float(m.group(1))
    unit = m.group(2).lower()
    return val, unit


def _convert_value_unit(value: float, unit: str, *, pf: float) -> LoadTotals:
    if unit == "va":
        kva = value / 1000.0
        return LoadTotals(kw=kva * pf, kva=kva)
    if unit == "kva":
        kva = value
        return LoadTotals(kw=kva * pf, kva=kva)
    if unit == "mva":
        kva = value * 1000.0
        return LoadTotals(kw=kva * pf, kva=kva)

    if unit == "w":
        kw = value / 1000.0
        return LoadTotals(kw=kw, kva=(kw / pf))
    if unit == "kw":
        kw = value
        return LoadTotals(kw=kw, kva=(kw / pf))
    if unit == "mw":
        kw = value * 1000.0
        return LoadTotals(kw=kw, kva=(kw / pf))

    if unit == "hp":
        kw = value * 0.746
        return LoadTotals(kw=kw, kva=(kw / pf))

    return LoadTotals(raw=1)


def _norm_load(load: Any, *, pf: float) -> LoadTotals:
    if pf <= 0 or pf > 1:
        pf = 0.85

    if isinstance(load, str):
        parsed = _parse_raw_string(load)
        if not parsed:
            return LoadTotals(raw=1)
        v, unit = parsed
        return _convert_value_unit(v, unit, pf=pf)

    if not isinstance(load, dict):
        return LoadTotals(raw=1)

    if "raw" in load and isinstance(load.get("raw"), str):
        parsed = _parse_raw_string(str(load["raw"]))
        if not parsed:
            return LoadTotals(raw=1)
        v, unit = parsed
        return _convert_value_unit(v, unit, pf=pf)

    v_opt = _to_float_opt(load.get("value"))
    u = load.get("unit")
    if v_opt is None or not isinstance(u, str):
        return LoadTotals(raw=1)

    return _convert_value_unit(v_opt, u.lower(), pf=pf)


def _add(a: LoadTotals, b: LoadTotals) -> LoadTotals:
    return LoadTotals(kw=a.kw + b.kw, kva=a.kva + b.kva, raw=a.raw + b.raw)


def _iter_circuit_loads(board_snap: dict[str, Any], *, pf: float) -> list[LoadTotals]:
    loads: list[LoadTotals] = []
    buses = board_snap.get("buses") or []
    for b in buses:
        for c in b.get("circuits") or []:
            loads.append(_norm_load(c.get("load"), pf=pf))
            for sc in c.get("subcircuits") or []:
                loads.append(_norm_load(sc.get("load"), pf=pf))
    return loads


def _board_local_totals(board_snap: dict[str, Any], *, pf: float) -> LoadTotals:
    total = LoadTotals()
    for lt in _iter_circuit_loads(board_snap, pf=pf):
        total = _add(total, lt)
    return total


def _virtual_load_board_name(load_tag: str) -> str:
    return f"LOAD:{load_tag}"


class LoadAggregationService:
    @staticmethod
    def aggregate(
        *,
        boards_by_name: dict[str, dict[str, Any]],
        compiled_links: list[dict[str, Any]],
        in_service_boards: set[str],
        out_of_service_boards: set[str],
        assembly_columns: dict[str, dict[str, str]] | None = None,
        power_factor: float = 0.85,
    ) -> dict[str, Any]:
        pf = power_factor if 0 < power_factor <= 1 else 0.85
        asm_cols = assembly_columns or {}

        graph: dict[str, list[str]] = {}
        feeders: list[dict[str, Any]] = []
        all_in_service: set[str] = set(in_service_boards)

        # assembly -> columns (roll-up macro)
        for asm, colmap in asm_cols.items():
            if asm not in in_service_boards:
                continue
            all_in_service.add(asm)
            for _col, board_tag in colmap.items():
                if board_tag in in_service_boards:
                    graph.setdefault(asm, []).append(board_tag)

        # network feeders
        for lk in compiled_links:
            o = lk.get("origin") or {}
            d = lk.get("destination") or {}

            ob = o.get("board")
            if not isinstance(ob, str) or not ob:
                continue
            if ob not in in_service_boards:
                continue

            load_tag = d.get("load")
            if isinstance(load_tag, str) and load_tag:
                db = _virtual_load_board_name(load_tag)
                all_in_service.add(db)
            else:
                db_any = d.get("board")
                db = str(db_any) if isinstance(db_any, str) and db_any else ""
                if not db:
                    continue
                if db in in_service_boards:
                    all_in_service.add(db)

            graph.setdefault(ob, []).append(db)

            feeders.append(
                {
                    "from_board": ob,
                    "to": db,
                    "wire": lk.get("wire"),
                    "meta": lk.get("meta") or {},
                }
            )

        # local loads
        local: dict[str, LoadTotals] = {}
        for b in all_in_service:
            if b.startswith("LOAD:"):
                local[b] = LoadTotals()
            else:
                local[b] = _board_local_totals(boards_by_name.get(b) or {}, pf=pf)

        # out_of_service locals (report only)
        local_oos: dict[str, LoadTotals] = {}
        for b in sorted(out_of_service_boards):
            local_oos[b] = _board_local_totals(boards_by_name.get(b) or {}, pf=pf)

        # totals DFS
        issues: list[dict[str, Any]] = []
        total: dict[str, LoadTotals] = {}

        def dfs(node: str, visiting: set[str]) -> LoadTotals:
            if node in total:
                return total[node]
            if node in visiting:
                issues.append({"code": "CYCLE_DETECTED", "node": node})
                total[node] = local.get(node, LoadTotals())
                return total[node]

            visiting.add(node)
            acc = local.get(node, LoadTotals())

            for child in graph.get(node, []):
                if child in out_of_service_boards:
                    continue
                acc = _add(acc, dfs(child, visiting))

            visiting.remove(node)
            total[node] = acc
            return acc

        for b in all_in_service:
            dfs(b, set())

        # feeder downstream totals
        feeder_reports: list[dict[str, Any]] = []
        for f in feeders:
            to_b = f["to"]
            tt = total.get(to_b, LoadTotals())
            feeder_reports.append(
                {
                    **f,
                    "downstream_total": {
                        "kW": round(tt.kw, 6),
                        "kVA": round(tt.kva, 6),
                        "raw": tt.raw,
                    },
                }
            )

        # roots (indegree 0) on all_in_service
        indeg: dict[str, int] = dict.fromkeys(all_in_service, 0)
        for u, children in graph.items():
            if u not in all_in_service:
                continue
            for v in children:
                if v in all_in_service:
                    indeg[v] = indeg.get(v, 0) + 1

        roots = sorted([b for b, deg in indeg.items() if deg == 0])

        # root totals (04.01-A)
        root_totals: list[dict[str, Any]] = []
        sys_kw = 0.0
        sys_kva = 0.0
        sys_raw = 0
        for r in roots:
            tt = total.get(r, LoadTotals())
            root_totals.append(
                {
                    "root": r,
                    "total": {"kW": round(tt.kw, 6), "kVA": round(tt.kva, 6), "raw": tt.raw},
                }
            )
            sys_kw += tt.kw
            sys_kva += tt.kva
            sys_raw += tt.raw

        # board reports
        in_service_reports: dict[str, Any] = {}
        for b in sorted(all_in_service):
            lt = local.get(b, LoadTotals())
            tt = total.get(b, LoadTotals())
            in_service_reports[b] = {
                "local": {"kW": round(lt.kw, 6), "kVA": round(lt.kva, 6), "raw": lt.raw},
                "total": {"kW": round(tt.kw, 6), "kVA": round(tt.kva, 6), "raw": tt.raw},
                "downstream": sorted(graph.get(b, [])),
            }

        out_service_reports: dict[str, Any] = {}
        for b in sorted(out_of_service_boards):
            lt = local_oos.get(b, LoadTotals())
            out_service_reports[b] = {
                "local": {"kW": round(lt.kw, 6), "kVA": round(lt.kva, 6), "raw": lt.raw},
                "note": "out_of_service (no propagation)",
            }

        return {
            "version": "0.4",
            "power_factor": pf,
            "roots": roots,
            "root_totals": root_totals,
            "system_total": {"kW": round(sys_kw, 6), "kVA": round(sys_kva, 6), "raw": sys_raw},
            "in_service": {"boards": in_service_reports, "feeders": feeder_reports},
            "out_of_service": {"boards": out_service_reports},
            "issues": issues,
            "notes": {
                "units_supported": ["VA", "kVA", "MVA", "W", "kW", "MW", "HP"],
                "pf_constant_for_now": True,
                "assembly_rollup_enabled": True,
            },
        }

    @staticmethod
    def to_markdown(load_report: dict[str, Any]) -> str:
        pf = load_report.get("power_factor", 0.85)
        roots = load_report.get("roots") or []
        sys_total = load_report.get("system_total") or {}
        root_totals = load_report.get("root_totals") or []

        lines: list[str] = []
        lines.append("# Load Report (EPIC-04.01)")
        lines.append("")
        lines.append(f"**PF (constante por ahora):** {pf}")
        lines.append("")
        lines.append(
            f"**Roots (in_service, indegree=0):** {', '.join(roots) if roots else '(none)'}"
        )
        lines.append(
            f"**TOTAL SISTEMA:** {sys_total.get('kW', 0):.3f} kW | {sys_total.get('kVA', 0):.3f} kVA | raw={sys_total.get('raw', 0)}"
        )
        lines.append("")

        if root_totals:
            lines.append("## Root Summary")
            lines.append("")
            lines.append("| Root | Total kW | Total kVA | Raw |")
            lines.append("|---|---:|---:|---:|")
            for rt in root_totals:
                root = rt.get("root", "")
                tot = rt.get("total") or {}
                lines.append(
                    f"| {root} | {tot.get('kW', 0):.3f} | {tot.get('kVA', 0):.3f} | {tot.get('raw', 0)} |"
                )
            lines.append("")

        ins = load_report.get("in_service") or {}
        ins_boards = ins.get("boards") or {}
        feeders = ins.get("feeders") or []

        oos = load_report.get("out_of_service") or {}
        oos_boards = oos.get("boards") or {}

        lines.append("## Board Summary (ALL)")
        lines.append("")
        lines.append(
            "| Board | Status | Local kW | Local kVA | Raw | Total kW | Total kVA | Raw | Downstream | Note |"
        )
        lines.append("|---|---|---:|---:|---:|---:|---:|---:|---|---|")

        for b, info in ins_boards.items():
            loc = info.get("local") or {}
            tot = info.get("total") or {}
            ds = info.get("downstream") or []
            lines.append(
                f"| {b} | in_service | {loc.get('kW', 0):.3f} | {loc.get('kVA', 0):.3f} | {loc.get('raw', 0)} | "
                f"{tot.get('kW', 0):.3f} | {tot.get('kVA', 0):.3f} | {tot.get('raw', 0)} | {', '.join(ds)} |  |"
            )

        for b, info in oos_boards.items():
            loc = info.get("local") or {}
            note = info.get("note", "out_of_service")
            lines.append(
                f"| {b} | out_of_service | {loc.get('kW', 0):.3f} | {loc.get('kVA', 0):.3f} | {loc.get('raw', 0)} | "
                f"{0.0:.3f} | {0.0:.3f} | {0} |  | {note} |"
            )

        lines.append("")
        lines.append("## Feeder Summary (In-Service)")
        lines.append("")
        lines.append("| From | To | Wire | Downstream kW | Downstream kVA | Raw |")
        lines.append("|---|---|---|---:|---:|---:|")
        for f in feeders:
            dt = f.get("downstream_total") or {}
            lines.append(
                f"| {f.get('from_board','')} | {f.get('to','')} | {f.get('wire','')} | "
                f"{dt.get('kW', 0):.3f} | {dt.get('kVA', 0):.3f} | {dt.get('raw', 0)} |"
            )

        issues = load_report.get("issues") or []
        if issues:
            lines.append("")
            lines.append("## Issues")
            lines.append("")
            for i in issues:
                lines.append(f"- {i}")

        return "\n".join(lines)
