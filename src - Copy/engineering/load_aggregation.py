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


def _s(x: Any) -> str:
    """Safe string cast for dict.get() values (prevents Optional[str] mypy issues)."""
    return x if isinstance(x, str) else ""


def _f0(x: Any) -> float:
    """Safe float cast: None/invalid -> 0.0 (prevents mypy arg-type issues)."""
    try:
        if x is None:
            return 0.0
        return float(x)
    except Exception:
        return 0.0


def _i0(x: Any) -> int:
    """Safe int cast: None/invalid -> 0."""
    try:
        if x is None:
            return 0
        return int(x)
    except Exception:
        return 0


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
    # VA-family -> derive kW
    if unit == "va":
        kva = value / 1000.0
        return LoadTotals(kw=kva * pf, kva=kva)
    if unit == "kva":
        kva = value
        return LoadTotals(kw=kva * pf, kva=kva)
    if unit == "mva":
        kva = value * 1000.0
        return LoadTotals(kw=kva * pf, kva=kva)

    # W-family -> derive kVA
    if unit == "w":
        kw = value / 1000.0
        return LoadTotals(kw=kw, kva=(kw / pf))
    if unit == "kw":
        kw = value
        return LoadTotals(kw=kw, kva=(kw / pf))
    if unit == "mw":
        kw = value * 1000.0
        return LoadTotals(kw=kw, kva=(kw / pf))

    # HP -> kW -> kVA
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

    raw_val = load.get("raw")
    if isinstance(raw_val, str):
        parsed = _parse_raw_string(raw_val)
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


def _kva_of_feeder(f: dict[str, Any]) -> float:
    dt = f.get("downstream_total") or {}
    return _f0(dt.get("kVA"))


def _top_n_feeders_by_kva(feeders: list[dict[str, Any]], n: int = 5) -> list[dict[str, Any]]:
    return sorted(feeders, key=_kva_of_feeder, reverse=True)[: max(0, int(n))]


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

        # board -> owning assembly (para feeder view)
        board_to_assembly: dict[str, str] = {}

        # assembly -> columns edges (roll-up macro) + map board->assembly
        for asm, colmap in asm_cols.items():
            if asm not in in_service_boards:
                continue
            all_in_service.add(asm)
            for _col, board_tag in colmap.items():
                board_to_assembly[board_tag] = asm
                if board_tag in in_service_boards:
                    graph.setdefault(asm, []).append(board_tag)

        # network feeders
        for lk in compiled_links:
            o = lk.get("origin") or {}
            d = lk.get("destination") or {}

            ob_any = o.get("board")
            if not isinstance(ob_any, str) or not ob_any:
                continue
            if ob_any not in in_service_boards:
                continue
            ob = ob_any

            load_tag = d.get("load")
            if isinstance(load_tag, str) and load_tag:
                db = _virtual_load_board_name(load_tag)
                all_in_service.add(db)
            else:
                db = _s(d.get("board"))
                if not db:
                    continue
                if db in in_service_boards:
                    all_in_service.add(db)

            graph.setdefault(ob, []).append(db)

            feeders.append(
                {
                    "from_board": ob,
                    "to": db,
                    "wire": _s(lk.get("wire")),
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

        # feeder downstream totals (board-level)
        feeder_reports: list[dict[str, Any]] = []
        for f in feeders:
            to_board = _s(f.get("to"))
            tt = total.get(to_board, LoadTotals())
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

        # Top feeders by kVA
        feeders_top_kva = _top_n_feeders_by_kva(feeder_reports, n=5)

        # feeder view by assembly (per-row)
        feeders_assembly_view: list[dict[str, Any]] = []
        for f in feeder_reports:
            fb = _s(f.get("from_board"))
            asm = board_to_assembly.get(fb) or ""
            if asm:
                feeders_assembly_view.append(
                    {
                        "from_assembly": asm,
                        "from_board": fb,
                        "to": _s(f.get("to")),
                        "wire": _s(f.get("wire")),
                        "downstream_total": f.get("downstream_total") or {},
                        "meta": f.get("meta") or {},
                    }
                )

        # Collapsed assembly view (group+sum)
        agg: dict[tuple[str, str, str], dict[str, Any]] = {}
        for f in feeders_assembly_view:
            fa = _s(f.get("from_assembly"))
            to_b = _s(f.get("to"))
            wire = _s(f.get("wire"))
            key = (fa, to_b, wire)

            dt = f.get("downstream_total") or {}
            kw = _f0(dt.get("kW"))
            kva = _f0(dt.get("kVA"))
            raw = _i0(dt.get("raw"))

            slot = agg.get(key)
            if slot is None:
                slot = {
                    "from_assembly": fa,
                    "to": to_b,
                    "wire": wire,
                    "from_boards": set(),  # set[str]
                    "downstream_total": {"kW": 0.0, "kVA": 0.0, "raw": 0},
                }
                agg[key] = slot

            from_boards_set = slot["from_boards"]
            from_boards_set.add(_s(f.get("from_board")))

            slot_dt = slot["downstream_total"]
            slot_dt["kW"] = _f0(slot_dt.get("kW")) + kw
            slot_dt["kVA"] = _f0(slot_dt.get("kVA")) + kva
            slot_dt["raw"] = _i0(slot_dt.get("raw")) + raw

        feeders_assembly_view_collapsed: list[dict[str, Any]] = []
        for (_fa, _to, _wire), slot in agg.items():
            from_boards_set = slot.pop("from_boards")
            from_boards = sorted(from_boards_set)  # ✅ ruff C414: no list()
            dt = slot.get("downstream_total") or {}
            feeders_assembly_view_collapsed.append(
                {
                    "from_assembly": _s(slot.get("from_assembly")),
                    "to": _s(slot.get("to")),
                    "wire": _s(slot.get("wire")),
                    "from_boards": from_boards,
                    "downstream_total": {
                        "kW": round(_f0(dt.get("kW")), 6),
                        "kVA": round(_f0(dt.get("kVA")), 6),
                        "raw": _i0(dt.get("raw")),
                    },
                }
            )

        feeders_assembly_view_collapsed.sort(
            key=lambda x: _f0((x.get("downstream_total") or {}).get("kVA")),
            reverse=True,
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

        # root totals + system total
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
            "version": "0.6",
            "power_factor": pf,
            "roots": roots,
            "root_totals": root_totals,
            "system_total": {"kW": round(sys_kw, 6), "kVA": round(sys_kva, 6), "raw": sys_raw},
            "in_service": {
                "boards": in_service_reports,
                "feeders": feeder_reports,
                "feeders_top_kva": feeders_top_kva,
                "feeders_assembly_view": feeders_assembly_view,
                "feeders_assembly_view_collapsed": feeders_assembly_view_collapsed,
            },
            "out_of_service": {"boards": out_service_reports},
            "issues": issues,
            "notes": {
                "units_supported": ["VA", "kVA", "MVA", "W", "kW", "MW", "HP"],
                "pf_constant_for_now": True,
                "assembly_rollup_enabled": True,
                "feeders_assembly_view_enabled": True,
                "feeders_assembly_view_collapsed_enabled": True,
                "feeders_top_kva_enabled": True,
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
                root = _s(rt.get("root"))
                tot = rt.get("total") or {}
                lines.append(
                    f"| {root} | {tot.get('kW', 0):.3f} | {tot.get('kVA', 0):.3f} | {tot.get('raw', 0)} |"
                )
            lines.append("")

        ins = load_report.get("in_service") or {}
        ins_boards = ins.get("boards") or {}
        feeders = ins.get("feeders") or []
        feeders_top = ins.get("feeders_top_kva") or []
        feeders_asm = ins.get("feeders_assembly_view") or []
        feeders_asm_collapsed = ins.get("feeders_assembly_view_collapsed") or []

        oos = load_report.get("out_of_service") or {}
        oos_boards = oos.get("boards") or {}

        if feeders_top:
            lines.append("## Top Feeders (kVA)")
            lines.append("")
            lines.append("| From | To | Wire | Downstream kW | Downstream kVA | Raw |")
            lines.append("|---|---|---|---:|---:|---:|")
            for f in feeders_top:
                dt = f.get("downstream_total") or {}
                lines.append(
                    f"| {_s(f.get('from_board'))} | {_s(f.get('to'))} | {_s(f.get('wire'))} | "
                    f"{_f0(dt.get('kW')):.3f} | {_f0(dt.get('kVA')):.3f} | {_i0(dt.get('raw'))} |"
                )
            lines.append("")

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
            note = _s(info.get("note")) or "out_of_service"
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
                f"| {_s(f.get('from_board'))} | {_s(f.get('to'))} | {_s(f.get('wire'))} | "
                f"{_f0(dt.get('kW')):.3f} | {_f0(dt.get('kVA')):.3f} | {_i0(dt.get('raw'))} |"
            )

        if feeders_asm:
            lines.append("")
            lines.append("## Feeder Summary (Assembly View)")
            lines.append("")
            lines.append(
                "| From Assembly | From Board | To | Wire | Downstream kW | Downstream kVA | Raw |"
            )
            lines.append("|---|---|---|---|---:|---:|---:|")
            for f in feeders_asm:
                dt = f.get("downstream_total") or {}
                lines.append(
                    f"| {_s(f.get('from_assembly'))} | {_s(f.get('from_board'))} | {_s(f.get('to'))} | {_s(f.get('wire'))} | "
                    f"{_f0(dt.get('kW')):.3f} | {_f0(dt.get('kVA')):.3f} | {_i0(dt.get('raw'))} |"
                )

        if feeders_asm_collapsed:
            lines.append("")
            lines.append("## Feeder Summary (Assembly View — Collapsed)")
            lines.append("")
            lines.append(
                "| From Assembly | To | Wire | From Boards | Downstream kW | Downstream kVA | Raw |"
            )
            lines.append("|---|---|---|---|---:|---:|---:|")
            for f in feeders_asm_collapsed:
                dt = f.get("downstream_total") or {}
                from_boards = f.get("from_boards") or []
                fb_txt = ", ".join(from_boards) if isinstance(from_boards, list) else ""
                lines.append(
                    f"| {_s(f.get('from_assembly'))} | {_s(f.get('to'))} | {_s(f.get('wire'))} | {fb_txt} | "
                    f"{_f0(dt.get('kW')):.3f} | {_f0(dt.get('kVA')):.3f} | {_i0(dt.get('raw'))} |"
                )

        issues = load_report.get("issues") or []
        if issues:
            lines.append("")
            lines.append("## Issues")
            lines.append("")
            for i in issues:
                lines.append(f"- {i}")

        return "\n".join(lines)
