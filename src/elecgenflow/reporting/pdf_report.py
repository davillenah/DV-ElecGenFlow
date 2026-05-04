# src/elecgenflow/reporting/pdf_report.py

from __future__ import annotations

import json
import os
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from reportlab.lib import colors  # type: ignore[import-untyped]
from reportlab.lib.pagesizes import A4  # type: ignore[import-untyped]
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet  # type: ignore[import-untyped]
from reportlab.lib.units import cm  # type: ignore[import-untyped]
from reportlab.platypus import (  # type: ignore[import-untyped]
    KeepTogether,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


@dataclass(frozen=True)
class PdfBuildResult:
    enabled: bool
    pdf_path: str
    reason: str | None = None


def _now_iso() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%SZ")


def _iter_md_lines(md: str) -> Iterable[str]:
    for line in md.splitlines():
        yield line.rstrip("\n")


def _escape_html_safe(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _unescape_html_entities(s: str) -> str:
    """
    Algunos artifacts Markdown pueden venir con entidades (&gt;=, &amp; etc).
    Para renderizar bien en PDF:
      1) des-escapamos entidades comunes a caracteres reales
      2) luego volvemos a escapar de forma segura para Paragraph.
    """
    return (
        s.replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&#39;", "'")
        .replace("&quot;", '"')
    )


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def _read_json_any(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _fmt_num(x: Any, nd: int = 3) -> str:
    try:
        return f"{float(x):.{nd}f}"
    except Exception:
        return "n/a"


def _fmt_int(x: Any) -> str:
    try:
        return str(int(x))
    except Exception:
        return "n/a"


def _is_table_line(line: str) -> bool:
    return "|" in line and not line.lstrip().startswith("```")


def _is_separator_row(cells: list[str]) -> bool:
    for c in cells:
        t = c.replace(":", "").replace("-", "").strip()
        if t != "":
            return False
    return True


def _theme_styles() -> Any:
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="EGF_Title",
            parent=styles["Title"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=26,
            textColor=colors.HexColor("#111827"),
            spaceAfter=14,
        )
    )
    styles.add(
        ParagraphStyle(
            name="EGF_H1",
            parent=styles["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            textColor=colors.HexColor("#0F172A"),
            spaceBefore=10,
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="EGF_H2",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            textColor=colors.HexColor("#0F172A"),
            spaceBefore=8,
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="EGF_H3",
            parent=styles["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#0F172A"),
            spaceBefore=6,
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle(
            name="EGF_Body",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=10,
            leading=13,
            textColor=colors.HexColor("#111827"),
            spaceAfter=4,
        )
    )
    styles.add(
        ParagraphStyle(
            name="EGF_Mono",
            parent=styles["Code"],
            fontName="Courier",
            fontSize=8.5,
            leading=10,
            textColor=colors.HexColor("#111827"),
            spaceAfter=6,
        )
    )
    styles.add(
        ParagraphStyle(
            name="EGF_Small",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9,
            leading=11,
            textColor=colors.HexColor("#374151"),
            spaceAfter=3,
        )
    )
    return styles


def _header_footer(canvas: Any, doc: Any, *, project_name: str) -> None:
    canvas.saveState()
    w, h = A4

    canvas.setStrokeColor(colors.lightgrey)
    canvas.setLineWidth(0.5)
    canvas.line(2.0 * cm, h - 1.6 * cm, w - 2.0 * cm, h - 1.6 * cm)
    canvas.line(2.0 * cm, 1.4 * cm, w - 2.0 * cm, 1.4 * cm)

    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(colors.grey)
    canvas.drawString(2.0 * cm, h - 1.35 * cm, f"ElecGenFlow — {project_name}")
    canvas.drawRightString(w - 2.0 * cm, 1.15 * cm, f"Página {doc.page}")
    canvas.restoreState()


def _table_from_markdown_lines(table_lines: list[str], *, styles: Any) -> Table:
    rows: list[list[str]] = []
    for ln in table_lines:
        parts = [p.strip() for p in ln.strip().strip("|").split("|")]
        rows.append(parts)

    if len(rows) >= 2 and _is_separator_row(rows[1]):
        rows.pop(1)

    if not rows:
        return Table([["(empty table)"]])

    body_style = styles["EGF_Body"]
    head_style = ParagraphStyle(
        "EGF_TableHead",
        parent=styles["EGF_Body"],
        fontName="Helvetica-Bold",
        textColor=colors.white,
    )

    formatted: list[list[Any]] = []
    for r_idx, row in enumerate(rows):
        out_row: list[Any] = []
        for c in row:
            c2 = _escape_html_safe(_unescape_html_entities(c))
            st = head_style if r_idx == 0 else body_style
            out_row.append(Paragraph(c2, st))
        formatted.append(out_row)

    cols = max(len(r) for r in formatted)
    usable_w = A4[0] - 4.0 * cm
    col_w = usable_w / max(cols, 1)
    col_widths = [col_w] * cols

    tbl = Table(formatted, colWidths=col_widths, repeatRows=1, hAlign="LEFT")
    tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#CBD5E1")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    return tbl


def _kpi_box(kpis: list[list[str]], *, styles: Any) -> Table:
    label_style = ParagraphStyle(
        "EGF_KPI_Label",
        parent=styles["EGF_Body"],
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#0F172A"),
    )
    value_style = styles["EGF_Body"]

    formatted: list[list[Any]] = []
    for k, v in kpis:
        formatted.append(
            [
                Paragraph(_escape_html_safe(_unescape_html_entities(k)), label_style),
                Paragraph(_escape_html_safe(_unescape_html_entities(v)), value_style),
            ]
        )

    t = Table(formatted, colWidths=[6.0 * cm, A4[0] - 4.0 * cm - 6.0 * cm])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#CBD5E1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#E2E8F0")),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    return t


def _parse_markdown_to_flowables(md: str, *, title: str, styles: Any) -> list[Any]:
    """
    Legacy: render de artifacts .md. Se mantiene para modo EGF_PDF_MODE=full.
    """
    h1 = styles["EGF_H1"]
    h2 = styles["EGF_H2"]
    h3 = styles["EGF_H3"]
    body = styles["EGF_Body"]
    mono = styles["EGF_Mono"]

    flow: list[Any] = []
    flow.append(Paragraph(_escape_html_safe(title), h1))
    flow.append(Spacer(1, 0.25 * cm))

    in_code = False
    code_buf: list[str] = []
    in_table = False
    table_buf: list[str] = []

    def flush_code() -> None:
        nonlocal code_buf
        if code_buf:
            flow.append(Preformatted("\n".join(code_buf), mono))
            code_buf = []

    def flush_table() -> None:
        nonlocal table_buf
        if table_buf:
            flow.append(_table_from_markdown_lines(table_buf, styles=styles))
            table_buf = []

    for raw in _iter_md_lines(md):
        line = raw

        if line.strip().startswith("```"):
            if in_code:
                in_code = False
                flush_code()
            else:
                in_code = True
            continue

        if in_code:
            code_buf.append(_escape_html_safe(_unescape_html_entities(line)))
            continue

        if _is_table_line(line):
            in_table = True
            table_buf.append(line)
            continue

        if in_table and not line.strip():
            in_table = False
            flush_table()
            flow.append(Spacer(1, 0.15 * cm))
            continue

        if in_table and not _is_table_line(line):
            in_table = False
            flush_table()

        s = line.strip()
        if not s:
            flow.append(Spacer(1, 0.15 * cm))
            continue

        if s.startswith("# "):
            flow.append(Paragraph(_escape_html_safe(_unescape_html_entities(s[2:])), h1))
            continue
        if s.startswith("## "):
            flow.append(Paragraph(_escape_html_safe(_unescape_html_entities(s[3:])), h2))
            continue
        if s.startswith("### "):
            flow.append(Paragraph(_escape_html_safe(_unescape_html_entities(s[4:])), h3))
            continue
        if s.startswith("- "):
            flow.append(Paragraph(f"• {_escape_html_safe(_unescape_html_entities(s[2:]))}", body))
            continue

        flow.append(Paragraph(_escape_html_safe(_unescape_html_entities(s)), body))

    if in_table:
        flush_table()
    if in_code:
        flush_code()

    return flow


def _kpi_cover_flowables(*, project_name: str, artifacts_dir: Path, styles: Any) -> list[Any]:
    title = styles["EGF_Title"]
    h2 = styles["EGF_H2"]
    small = styles["EGF_Small"]

    load_json = _read_json(artifacts_dir / "load_report.json") or {}
    dag_json = _read_json(artifacts_dir / "dag_report.json") or {}
    nominal_snap = _read_json(artifacts_dir / "nominal_snapshot.json") or {}
    nominal_diff = _read_json(artifacts_dir / "nominal_overlay_diff.json") or {}
    sizing = _read_json(artifacts_dir / "sizing_report.json") or {}
    cable_schedule = _read_json(artifacts_dir / "cable_schedule.json") or {}
    selected_wires = _read_json(artifacts_dir / "selected_wires.json") or {}

    pf = load_json.get("power_factor", "n/a")
    roots = load_json.get("roots") or []
    sys_total = load_json.get("system_total") or {}
    sys_kva = sys_total.get("kVA")
    sys_va: float | None = None
    try:
        if sys_kva is not None:
            sys_va = float(sys_kva) * 1000.0
    except Exception:
        sys_va = None

    dag_roots = dag_json.get("roots") or []
    dag_nodes = dag_json.get("nodes") or []
    dag_edges = dag_json.get("edges") or []
    dag_has_cycle = dag_json.get("has_cycle", False)
    dag_unreachable = dag_json.get("unreachable") or []

    counts = nominal_snap.get("counts") or {}
    cables_n = counts.get("cables")
    prot_n = counts.get("protections")
    meth_n = counts.get("install_methods")

    overlays = nominal_diff.get("overlays") or []

    sizing_sum = sizing.get("summary") or {}
    suggested_n = sizing_sum.get("suggested")

    reserve_pct = (
        selected_wires.get("cable_reserve_pct") if isinstance(selected_wires, dict) else None
    )
    if reserve_pct is None:
        reserve_pct = sizing.get("assumptions", {}).get("cable_reserve_pct")

    schedule_rows = cable_schedule.get("rows") if isinstance(cable_schedule, dict) else None
    schedule_count = len(schedule_rows) if isinstance(schedule_rows, list) else None

    flow: list[Any] = []
    flow.append(Paragraph("ElecGenFlow — Engineering Report", title))
    flow.append(Paragraph(f"Proyecto: {project_name}", small))
    flow.append(Paragraph(f"Generado: {_now_iso()}", small))
    flow.append(Paragraph(f"Artifacts: {artifacts_dir.as_posix()}", small))
    flow.append(Spacer(1, 0.35 * cm))

    flow.append(Paragraph("Resumen Ejecutivo (KPIs)", h2))
    flow.append(Spacer(1, 0.15 * cm))

    kpis = [
        ["PF usado", _fmt_num(pf, 3) if pf != "n/a" else "n/a"],
        ["Roots (Load)", ", ".join(roots) if roots else "(none)"],
        ["Total sistema (kVA)", _fmt_num(sys_kva, 3) if sys_kva is not None else "n/a"],
        ["Total sistema (VA)", _fmt_num(sys_va, 0) if sys_va is not None else "n/a"],
        ["DAG roots", ", ".join(dag_roots) if dag_roots else "(none)"],
        ["DAG estado", f"nodes={len(dag_nodes)} edges={len(dag_edges)} cycle={dag_has_cycle}"],
        ["DAG unreachable", f"{len(dag_unreachable)}"],
        [
            "Nominal tables",
            f"cables={_fmt_int(cables_n)} protections={_fmt_int(prot_n)} methods={_fmt_int(meth_n)}",
        ],
        ["Overlays aplicados", f"{len(overlays) if isinstance(overlays, list) else 0}"],
        ["Sizing sugerencias", _fmt_int(suggested_n)],
        ["Reserva cable (%)", _fmt_num(reserve_pct, 1) if reserve_pct is not None else "n/a"],
        ["Cables en schedule", _fmt_int(schedule_count)],
    ]
    flow.append(_kpi_box(kpis, styles=styles))
    flow.append(Spacer(1, 0.35 * cm))

    return flow


def _cond_str(r: dict[str, Any]) -> str:
    conductor = str(r.get("conductor") or "")
    insulation = str(r.get("insulation") or "")
    method = str(r.get("method") or r.get("install_method") or "")
    arrangement = str(r.get("arrangement") or (r.get("meta") or {}).get("arrangement") or "")
    if arrangement:
        return f"{conductor}/{insulation}/{method}/{arrangement}"
    return f"{conductor}/{insulation}/{method}".strip("/")


def _build_minimal_report_flowables(
    *, project_name: str, artifacts_dir: Path, styles: Any
) -> list[Any]:
    """
    Minimal report:
      - Ensambles: cargas + cable seleccionado (si aplica)
      - Tableros: cargas + cable(s) entrante(s) seleccionado(s)
    """
    h1 = styles["EGF_H1"]
    h2 = styles["EGF_H2"]
    h3 = styles["EGF_H3"]
    body = styles["EGF_Body"]
    mono = styles["EGF_Mono"]
    small = styles["EGF_Small"]

    load = _read_json_any(artifacts_dir / "load_report.json") or {}
    cable = _read_json_any(artifacts_dir / "cable_schedule.json") or {}
    selected = _read_json_any(artifacts_dir / "selected_wires.json") or {}

    pf = load.get("power_factor", "n/a") if isinstance(load, dict) else "n/a"

    reserve_pct = None
    vll = None
    if isinstance(selected, dict):
        reserve_pct = selected.get("cable_reserve_pct")
        vll = selected.get("voltage_ll_v")
    if reserve_pct is None and isinstance(cable, dict):
        reserve_pct = (cable.get("assumptions") or {}).get("cable_reserve_pct")
    if vll is None and isinstance(cable, dict):
        vll = (cable.get("assumptions") or {}).get("voltage_ll_v")

    rows = cable.get("rows", []) if isinstance(cable, dict) else []
    if not isinstance(rows, list):
        rows = []

    rows_by_to: dict[str, list[dict[str, Any]]] = {}
    for r in rows:
        to = str(r.get("to") or "")
        rows_by_to.setdefault(to, []).append(r)

    row_by_wire: dict[str, dict[str, Any]] = {}
    for r in rows:
        wid = str(r.get("wire_id") or "")
        if wid:
            row_by_wire[wid] = r

    flow: list[Any] = []
    flow.append(Paragraph("Memoria Técnica (MINIMAL) — Cargas + Cables", h1))
    flow.append(Paragraph(f"Proyecto: {project_name}", body))
    flow.append(Paragraph(f"PF: {pf} | VLL: {vll} V | Reserva: {reserve_pct} %", small))
    flow.append(Spacer(1, 0.35 * cm))

    # Ensambles
    flow.append(Paragraph("1) Ensambles — cargas y cables", h2))
    ins = load.get("in_service", {}) if isinstance(load, dict) else {}
    feeders_collapsed = ins.get("feeders_assembly_view_collapsed") or []
    feeders_asm = ins.get("feeders_assembly_view") or []

    feeders_src = (
        feeders_collapsed
        if isinstance(feeders_collapsed, list) and feeders_collapsed
        else feeders_asm
    )
    if not isinstance(feeders_src, list):
        feeders_src = []

    if feeders_src:
        md = [
            "| Ensamble | To | Wire | Downstream kW | Downstream kVA | mm² | Iz(A) | Cond | Note |",
            "|---|---|---|---:|---:|---:|---:|---|---|",
        ]
        for f in feeders_src:
            fa = str(f.get("from_assembly") or "")
            to = str(f.get("to") or "")
            wire = str(f.get("wire") or "")
            dt = f.get("downstream_total") or {}
            kw = dt.get("kW", 0.0)
            kva = dt.get("kVA", 0.0)

            r = row_by_wire.get(wire, {})
            md.append(
                "| "
                + " | ".join(
                    [
                        fa,
                        to,
                        wire,
                        _fmt_num(kw, 3),
                        _fmt_num(kva, 3),
                        str(r.get("selected_section_mm2") or ""),
                        str(r.get("selected_iz_a") or ""),
                        _cond_str(r) if r else "",
                        str(r.get("note") or ""),
                    ]
                )
                + " |"
            )
        flow.append(_table_from_markdown_lines(md, styles=styles))
    else:
        flow.append(Paragraph("No se encontró vista por ensamble en load_report.json.", body))

    flow.append(PageBreak())

    # Tableros
    flow.append(Paragraph("2) Tableros — cargas y cable(s) seleccionado(s)", h2))
    boards = ins.get("boards") or {}
    if not isinstance(boards, dict):
        boards = {}

    board_names = sorted(boards.keys(), key=lambda x: (str(x).startswith("LOAD:"), str(x)))

    for bname in board_names:
        info = boards.get(bname) or {}
        loc = info.get("local") or {}
        tot = info.get("total") or {}

        flow.append(Paragraph(f"Tablero: {bname}", h3))
        flow.append(
            Paragraph(
                f"Carga local: {_fmt_num(loc.get('kW'),3)} kW | {_fmt_num(loc.get('kVA'),3)} kVA "
                f"— Total downstream: {_fmt_num(tot.get('kW'),3)} kW | {_fmt_num(tot.get('kVA'),3)} kVA",
                body,
            )
        )

        feeders_in = rows_by_to.get(str(bname), [])
        if feeders_in:
            md = [
                "| From | WireID | kVA | Ib | Ib*(1+R) | parallel | grouped | Ib/cable | Cond | mm² | Iz(A) | Note |",
                "|---|---|---:|---:|---:|---:|---:|---:|---|---:|---:|---|",
            ]
            for r in feeders_in:
                md.append(
                    "| "
                    + " | ".join(
                        [
                            str(r.get("from") or ""),
                            str(r.get("wire_id") or ""),
                            _fmt_num(r.get("kva"), 3),
                            _fmt_num(r.get("ib_a"), 3),
                            _fmt_num(r.get("ib_design_a"), 3),
                            str(r.get("parallel") or ""),
                            str(r.get("grouped") or ""),
                            _fmt_num(r.get("ib_per_cable_a"), 3),
                            _cond_str(r),
                            str(r.get("selected_section_mm2") or ""),
                            str(r.get("selected_iz_a") or ""),
                            str(r.get("note") or ""),
                        ]
                    )
                    + " |"
                )
            flow.append(_table_from_markdown_lines(md, styles=styles))
        else:
            flow.append(
                Paragraph(
                    "Sin feeder entrante registrado en cable_schedule.json para este tablero.",
                    small,
                )
            )

        flow.append(Spacer(1, 0.25 * cm))

    flow.append(PageBreak())

    # Fórmulas
    flow.append(Paragraph("Anexo — Fórmulas (resumen)", h2))
    formulas = """
Ib (3φ) = (kVA * 1000) / (sqrt(3) * VLL)
Ib_design = Ib * (1 + reserve_pct/100)
Ib_per_cable = Ib_design / parallel
Selección sugerida: mínima sección tal que Iz >= Ib_per_cable
"""
    flow.append(Preformatted(formulas.strip(), mono))
    return flow


def build_engineering_pdf(
    *, project_name: str, artifacts_dir: Path, out_pdf: Path
) -> PdfBuildResult:
    styles = _theme_styles()

    md_sources = [
        ("Load Report (EPIC-04.01)", artifacts_dir / "load_report.md"),
        ("DAG Report (EPIC-04.02)", artifacts_dir / "dag_report.md"),
        ("Nominal Tables Snapshot (EPIC-04.03)", artifacts_dir / "nominal_snapshot.md"),
        ("Nominal Overlay Diff (EPIC-04.03)", artifacts_dir / "nominal_overlay_diff.md"),
        ("Sizing Report (EPIC-04.04)", artifacts_dir / "sizing_report.md"),
        ("Cable Schedule (EPIC-04.04)", artifacts_dir / "cable_schedule.md"),
    ]

    doc = SimpleDocTemplate(
        str(out_pdf),
        pagesize=A4,
        leftMargin=2.0 * cm,
        rightMargin=2.0 * cm,
        topMargin=2.0 * cm,
        bottomMargin=2.0 * cm,
        title=f"ElecGenFlow Engineering Report - {project_name}",
        author="elecgenflow",
    )

    story: list[Any] = []
    story.append(
        KeepTogether(
            _kpi_cover_flowables(
                project_name=project_name, artifacts_dir=artifacts_dir, styles=styles
            )
        )
    )
    story.append(PageBreak())

    mode = os.getenv("EGF_PDF_MODE", "minimal").lower().strip()

    if mode == "full":
        for section_title, md_path in md_sources:
            md_text = (
                md_path.read_text(encoding="utf-8") if md_path.exists() else "(missing artifact)"
            )
            story.extend(_parse_markdown_to_flowables(md_text, title=section_title, styles=styles))
            story.append(PageBreak())
    else:
        story.extend(
            _build_minimal_report_flowables(
                project_name=project_name, artifacts_dir=artifacts_dir, styles=styles
            )
        )

    doc.build(
        story,
        onFirstPage=lambda c, d: _header_footer(c, d, project_name=project_name),
        onLaterPages=lambda c, d: _header_footer(c, d, project_name=project_name),
    )

    return PdfBuildResult(enabled=True, pdf_path=str(out_pdf))
