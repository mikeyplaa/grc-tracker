from datetime import date

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from fpdf import FPDF
from sqlalchemy.orm import Session

from app.db import get_db
from app.frameworks import framework_from_slug
from app.reporting import ReportData, build_report

router = APIRouter(prefix="/export", tags=["export"])


def _render_markdown(report: ReportData) -> str:
    lines = [
        f"# GRC Tracker — {report.framework_label} Compliance Summary",
        "",
        f"Generated: {report.generated_at:%Y-%m-%d %H:%M} UTC",
        "",
        f"## Overall score: {report.overall * 100:.0f}%",
        "",
        "## Score by theme",
        "",
        "| Theme | Score |",
        "| --- | --- |",
    ]
    for theme, score in report.theme_scores.items():
        lines.append(f"| {theme} | {score * 100:.0f}% |")

    lines += ["", f"## Gaps ({len(report.gaps)})", ""]
    if report.gaps:
        for control in report.gaps:
            lines.append(
                f"- **{control.id}** {control.title} — "
                f"{control.status.value} ({control.theme})"
            )
    else:
        lines.append("No gaps — every control is Implemented or Evidenced.")

    lines += ["", f"## Stale evidence ({len(report.stale_items)})", ""]
    if report.stale_items:
        for item in report.stale_items:
            lines.append(f"- **{item.control_id}**: {item.title} (review was due {item.review_due})")
    else:
        lines.append("No stale evidence.")

    return "\n".join(lines) + "\n"


def _render_pdf(report: ReportData) -> bytes:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(
        0, 10, f"GRC Tracker - {report.framework_label} Compliance Summary",
        new_x="LMARGIN", new_y="NEXT",
    )
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 6, f"Generated: {report.generated_at:%Y-%m-%d %H:%M} UTC", new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 8, f"Overall score: {report.overall * 100:.0f}%", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Score by theme", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    for theme, score in report.theme_scores.items():
        pdf.cell(0, 6, f"  {theme}: {score * 100:.0f}%", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, f"Gaps ({len(report.gaps)})", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    if report.gaps:
        for control in report.gaps:
            pdf.multi_cell(
                0, 5.5,
                f"  {control.id} {control.title} - {control.status.value} ({control.theme})",
                new_x="LMARGIN", new_y="NEXT",
            )
    else:
        pdf.cell(0, 6, "  No gaps.", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, f"Stale evidence ({len(report.stale_items)})", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    if report.stale_items:
        for item in report.stale_items:
            pdf.multi_cell(
                0, 5.5,
                f"  {item.control_id}: {item.title} (review was due {item.review_due})",
                new_x="LMARGIN", new_y="NEXT",
            )
    else:
        pdf.cell(0, 6, "  No stale evidence.", new_x="LMARGIN", new_y="NEXT")

    return bytes(pdf.output())


@router.get("/markdown")
def export_markdown(framework: str = "iso27001", db: Session = Depends(get_db)) -> Response:
    report = build_report(db, framework_from_slug(framework))
    filename = f"grc-summary-{framework}-{date.today():%Y%m%d}.md"
    return Response(
        content=_render_markdown(report),
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/pdf")
def export_pdf(framework: str = "iso27001", db: Session = Depends(get_db)) -> Response:
    report = build_report(db, framework_from_slug(framework))
    filename = f"grc-summary-{framework}-{date.today():%Y%m%d}.pdf"
    return Response(
        content=_render_pdf(report),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
