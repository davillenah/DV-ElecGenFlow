from __future__ import annotations

import json
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


def _escape_html(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
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
            st = head_style if r_idx == 0 else body_style
            out_row.append(Paragraph(_escape_html(c), st))
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
            [Paragraph(_escape_html(k), label_style), Paragraph(_escape_html(v), value_style)]
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
    h1 = styles["EGF_H1"]
    h2 = styles["EGF_H2"]
    h3 = styles["EGF_H3"]
    body = styles["EGF_Body"]
    mono = styles["EGF_Mono"]

    flow: list[Any] = []
    flow.append(Paragraph(_escape_html(title), h1))
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
            code_buf.append(_escape_html(line))
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
            flow.append(Paragraph(_escape_html(s[2:]), h1))
            continue
        if s.startswith("## "):
            flow.append(Paragraph(_escape_html(s[3:]), h2))
            continue
        if s.startswith("### "):
            flow.append(Paragraph(_escape_html(s[4:]), h3))
            continue
        if s.startswith("- "):
            flow.append(Paragraph(f"• {_escape_html(s[2:])}", body))
            continue

        flow.append(Paragraph(_escape_html(s), body))

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

    pf = load_json.get("power_factor", "n/a")
    roots = load_json.get("roots") or []
    sys_total = load_json.get("system_total") or {}
    sys_kw = sys_total.get("kW")
    sys_kva = sys_total.get("kVA")

    ins = load_json.get("in_service") or {}
    top_feed = ins.get("feeders_top_kva") or []

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
    prot_diff = nominal_diff.get("protections") or {}
    prot_changed = (
        len((prot_diff.get("changed") or {}).keys())
        if isinstance(prot_diff.get("changed"), dict)
        else 0
    )
    prot_added = (
        len(prot_diff.get("added") or []) if isinstance(prot_diff.get("added"), list) else 0
    )
    prot_removed = (
        len(prot_diff.get("removed") or []) if isinstance(prot_diff.get("removed"), list) else 0
    )

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
        ["Total sistema", f"{_fmt_num(sys_kw)} kW | {_fmt_num(sys_kva)} kVA"],
        ["DAG roots", ", ".join(dag_roots) if dag_roots else "(none)"],
        ["DAG estado", f"nodes={len(dag_nodes)} edges={len(dag_edges)} cycle={dag_has_cycle}"],
        ["DAG unreachable", f"{len(dag_unreachable)}"],
        [
            "Nominal tables",
            f"cables={_fmt_int(cables_n)} protections={_fmt_int(prot_n)} methods={_fmt_int(meth_n)}",
        ],
        [
            "Overlays",
            f"{len(overlays) if isinstance(overlays, list) else 0} | prot +{prot_added} -{prot_removed} ~{prot_changed}",
        ],
    ]
    flow.append(_kpi_box(kpis, styles=styles))
    flow.append(Spacer(1, 0.35 * cm))

    if isinstance(top_feed, list) and top_feed:
        flow.append(Paragraph("Top Feeders (kVA) — vista rápida", h2))
        lines: list[str] = []
        lines.append("| From | To | Wire | kW | kVA |")
        lines.append("|---|---|---|---:|---:|")
        for f in top_feed[:5]:
            dt = f.get("downstream_total") or {}
            lines.append(
                f"| {f.get('from_board','')} | {f.get('to','')} | {f.get('wire','')} | "
                f"{_fmt_num(dt.get('kW'))} | {_fmt_num(dt.get('kVA'))} |"
            )
        flow.append(_table_from_markdown_lines(lines, styles=styles))

    return flow


def build_engineering_pdf(
    *,
    project_name: str,
    artifacts_dir: Path,
    out_pdf: Path,
) -> PdfBuildResult:
    styles = _theme_styles()

    md_sources = [
        ("Load Report (EPIC-04.01)", artifacts_dir / "load_report.md"),
        ("DAG Report (EPIC-04.02)", artifacts_dir / "dag_report.md"),
        ("Nominal Tables Snapshot (EPIC-04.03)", artifacts_dir / "nominal_snapshot.md"),
        ("Nominal Overlay Diff (EPIC-04.03)", artifacts_dir / "nominal_overlay_diff.md"),
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

    for section_title, md_path in md_sources:
        md_text = md_path.read_text(encoding="utf-8") if md_path.exists() else "(missing artifact)"
        story.extend(_parse_markdown_to_flowables(md_text, title=section_title, styles=styles))
        story.append(PageBreak())

    doc.build(
        story,
        onFirstPage=lambda c, d: _header_footer(c, d, project_name=project_name),
        onLaterPages=lambda c, d: _header_footer(c, d, project_name=project_name),
    )

    return PdfBuildResult(enabled=True, pdf_path=str(out_pdf))
