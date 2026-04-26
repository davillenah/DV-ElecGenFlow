from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from reportlab.lib.pagesizes import A4  # type: ignore[import-untyped]
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet  # type: ignore[import-untyped]
from reportlab.lib.units import cm  # type: ignore[import-untyped]
from reportlab.platypus import (  # type: ignore[import-untyped]
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
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
    # Escape básico para reportlab Paragraph (NO double-escape)
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _is_table_line(line: str) -> bool:
    # Heurística simple: tablas Markdown suelen contener pipes
    return "|" in line and not line.lstrip().startswith("```")


def _parse_markdown_to_flowables(md: str, *, title: str) -> list[Any]:
    """
    Renderer MD mínimo (suficiente para artifacts):
    - Headings (#, ##, ###)
    - Bullets (- )
    - Tablas y code blocks como Preformatted monospace
    - Párrafos simples
    """
    styles = getSampleStyleSheet()

    h1 = ParagraphStyle("EGF_H1", parent=styles["Heading1"], spaceAfter=10)
    h2 = ParagraphStyle("EGF_H2", parent=styles["Heading2"], spaceAfter=8)
    h3 = ParagraphStyle("EGF_H3", parent=styles["Heading3"], spaceAfter=6)
    body = ParagraphStyle("EGF_BODY", parent=styles["BodyText"], leading=12, spaceAfter=6)
    mono = ParagraphStyle("EGF_MONO", parent=styles["Code"], leading=10, spaceAfter=6)

    flow: list[Any] = []
    flow.append(Paragraph(_escape_html(title), h1))
    flow.append(Spacer(1, 0.25 * cm))

    in_code = False
    code_buf: list[str] = []

    table_buf: list[str] = []
    in_table = False

    def flush_code() -> None:
        nonlocal code_buf
        if code_buf:
            flow.append(Preformatted("\n".join(code_buf), mono))
            code_buf = []

    def flush_table() -> None:
        nonlocal table_buf
        if table_buf:
            flow.append(Preformatted("\n".join(table_buf), mono))
            table_buf = []

    for raw in _iter_md_lines(md):
        line = raw

        # fenced code blocks
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

        # tables (contiguous)
        if _is_table_line(line):
            in_table = True
            table_buf.append(_escape_html(line))
            continue

        if in_table and not line.strip():
            in_table = False
            flush_table()
            flow.append(Spacer(1, 0.15 * cm))
            continue

        if in_table and not _is_table_line(line):
            in_table = False
            flush_table()
            # sigue procesando line normalmente

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


def build_engineering_pdf(
    *,
    project_name: str,
    artifacts_dir: Path,
    out_pdf: Path,
) -> PdfBuildResult:
    md_sources = [
        ("Load Report (EPIC-04.01)", artifacts_dir / "load_report.md"),
        ("DAG Report (EPIC-04.02)", artifacts_dir / "dag_report.md"),
        ("Nominal Tables Snapshot (EPIC-04.03)", artifacts_dir / "nominal_snapshot.md"),
        ("Nominal Overlay Diff (EPIC-04.03)", artifacts_dir / "nominal_overlay_diff.md"),
    ]

    styles = getSampleStyleSheet()
    cover_title = ParagraphStyle("EGF_COVER", parent=styles["Title"], spaceAfter=18)
    cover_body = ParagraphStyle(
        "EGF_COVER_BODY", parent=styles["BodyText"], leading=14, spaceAfter=10
    )

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
    story.append(Paragraph("ElecGenFlow — Engineering Report", cover_title))
    story.append(Paragraph(f"Proyecto: {project_name}", cover_body))
    story.append(Paragraph(f"Generado: {_now_iso()}", cover_body))
    story.append(Paragraph(f"Artifacts: {artifacts_dir.as_posix()}", cover_body))
    story.append(PageBreak())

    for section_title, md_path in md_sources:
        md_text = md_path.read_text(encoding="utf-8") if md_path.exists() else "(missing artifact)"
        story.extend(_parse_markdown_to_flowables(md_text, title=section_title))
        story.append(PageBreak())

    doc.build(story)
    return PdfBuildResult(enabled=True, pdf_path=str(out_pdf))
