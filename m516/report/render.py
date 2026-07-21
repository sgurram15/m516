"""Render a `ReportData` (see `m516/report/template.py`) to an audit-ready PDF (FR-4.2), via reportlab
(pure-Python, no system PDF toolchain — same "verify it actually installs/works before building on it"
discipline as every provider/library choice in this project).

Layout only — no content decisions live here. Nothing in this module may reference a specific
framework/country/sector name (golden rule); severity and compliance-status labels come from the data.
"""

from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from m516.compliance.mapper import UNMAPPED
from m516.report.template import ComplianceGap, ReportData

_SEVERITY_COLORS = {
    "critical": colors.HexColor("#c0392b"),
    "high": colors.HexColor("#e67e22"),
    "medium": colors.HexColor("#f1c40f"),
    "low": colors.HexColor("#27ae60"),
}
_STATUS_COLORS = {
    "compliant": colors.HexColor("#27ae60"),
    "partial": colors.HexColor("#f1c40f"),
    "non-compliant": colors.HexColor("#c0392b"),
    UNMAPPED: colors.HexColor("#95a5a6"),
}
_HEADER_BG = colors.HexColor("#2c3e50")
_TABLE_GRID = colors.HexColor("#bdc3c7")


def render_pdf(report: ReportData, output_path: str | Path) -> Path:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    styles = getSampleStyleSheet()
    cell_style = ParagraphStyle("Cell", parent=styles["Normal"], fontSize=8, leading=10)
    disclaimer_style = ParagraphStyle(
        "Disclaimer", parent=styles["Italic"], fontSize=8, textColor=colors.grey
    )

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        leftMargin=1.5 * cm,
        rightMargin=1.5 * cm,
    )

    story: list = []
    story.extend(_title_section(report, styles, disclaimer_style))
    story.append(PageBreak())
    story.extend(_executive_summary_section(report, styles))
    story.extend(_asset_inventory_section(report, styles, cell_style))
    story.extend(_findings_section(report, styles, cell_style))
    story.extend(_compliance_section(report, styles, cell_style))
    story.extend(_remediation_section(report, styles))
    story.append(PageBreak())
    story.extend(_appendix_section(report, styles, cell_style))

    doc.build(story)
    return output_path


def _title_section(report: ReportData, styles, disclaimer_style) -> list:
    subtitle = report.domain
    if report.pack_display_name:
        subtitle = f"{subtitle} — {report.pack_display_name}"

    section = [
        Paragraph(report.report_title, styles["Title"]),
        Paragraph(subtitle, styles["Heading2"]),
        Paragraph(f"Generated: {report.generated_at.strftime('%Y-%m-%d %H:%M UTC')}", styles["Normal"]),
    ]
    if report.primary_regulator:
        section.append(Paragraph(f"Addressed to: {report.primary_regulator}", styles["Normal"]))
    section.append(Spacer(1, 0.8 * cm))
    section.append(Paragraph(report.disclaimer, disclaimer_style))
    return section


def _executive_summary_section(report: ReportData, styles) -> list:
    return [
        Paragraph("Executive Summary", styles["Heading1"]),
        Paragraph(report.executive_summary, styles["Normal"]),
        Spacer(1, 0.6 * cm),
    ]


def _asset_inventory_section(report: ReportData, styles, cell_style) -> list:
    header = ["IP", "Hostname", "Country", "WAF/CDN", "Services", "Cert status", "Sources"]
    rows = [header]
    for asset in report.assets:
        rows.append(
            [
                asset.ip or "—",
                asset.hostname or asset.domain or "—",
                asset.country or "—",
                "Yes" if asset.is_behind_waf else "No",
                str(asset.service_count),
                asset.cert_detection_level or "n/a",
                ", ".join(asset.sources) or "—",
            ]
        )

    table = Table(rows, repeatRows=1, hAlign="LEFT")
    table.setStyle(_base_table_style())
    return [Paragraph("Asset Inventory", styles["Heading1"]), table, Spacer(1, 0.6 * cm)]


def _findings_section(report: ReportData, styles, cell_style) -> list:
    if not report.findings:
        return [
            Paragraph("Ranked Findings", styles["Heading1"]),
            Paragraph("No CVE-eligible findings were produced.", styles["Normal"]),
            Spacer(1, 0.6 * cm),
        ]

    header = ["Severity", "Service", "CVE(s)", "CVSS", "Confidence", "Explanation"]
    rows = [header]
    for finding in report.findings:
        rows.append(
            [
                finding.severity.upper(),
                f"{finding.service.product or finding.service.name or 'unidentified'}:"
                f"{finding.service.port}/{finding.service.protocol}",
                ", ".join(finding.cve_ids) or "—",
                str(finding.cvss),
                finding.match_confidence,
                Paragraph(finding.explanation, cell_style),
            ]
        )

    table = Table(rows, repeatRows=1, hAlign="LEFT", colWidths=[2 * cm, 3.5 * cm, 3 * cm, 1.5 * cm, 2 * cm, 6 * cm])
    style = _base_table_style()
    for row_index, finding in enumerate(report.findings, start=1):
        color = _SEVERITY_COLORS.get(finding.severity)
        if color:
            style.add("TEXTCOLOR", (0, row_index), (0, row_index), color)
    table.setStyle(style)
    return [Paragraph("Ranked Findings", styles["Heading1"]), table, Spacer(1, 0.6 * cm)]


def _compliance_section(report: ReportData, styles, cell_style) -> list:
    section = [Paragraph("Compliance Gap Analysis", styles["Heading1"])]
    if not report.compliance_gaps:
        section.append(Paragraph("No compliance clauses were retrieved for this scan.", styles["Normal"]))
        section.append(Spacer(1, 0.6 * cm))
        return section

    header = ["Framework", "Clause", "Status", "Related finding(s)", "Remediation"]
    rows = [header]
    gap: ComplianceGap
    for gap in report.compliance_gaps:
        rows.append(
            [
                gap.framework,
                Paragraph(f"{gap.clause} — {gap.clause_title}", cell_style),
                gap.status,
                Paragraph("; ".join(gap.finding_refs), cell_style),
                Paragraph(gap.remediation or "—", cell_style),
            ]
        )

    table = Table(rows, repeatRows=1, hAlign="LEFT", colWidths=[2 * cm, 5 * cm, 2.5 * cm, 4 * cm, 4.5 * cm])
    style = _base_table_style()
    for row_index, gap in enumerate(report.compliance_gaps, start=1):
        color = _STATUS_COLORS.get(gap.status)
        if color:
            style.add("TEXTCOLOR", (2, row_index), (2, row_index), color)
    table.setStyle(style)
    section.append(table)
    section.append(Spacer(1, 0.6 * cm))
    return section


def _remediation_section(report: ReportData, styles) -> list:
    section = [Paragraph("Remediation Roadmap", styles["Heading1"])]
    if not report.remediation_roadmap:
        section.append(Paragraph("No remediation actions identified.", styles["Normal"]))
        return section

    items = [ListItem(Paragraph(item, styles["Normal"])) for item in report.remediation_roadmap]
    section.append(ListFlowable(items, bulletType="1"))
    return section


def _appendix_section(report: ReportData, styles, cell_style) -> list:
    section = [Paragraph("Technical Appendix", styles["Heading1"])]
    if not report.findings:
        section.append(Paragraph("No findings to detail.", styles["Normal"]))
        return section

    header = ["Asset", "Port/Proto", "Product/Version", "CPE", "Exploitability", "Impact"]
    rows = [header]
    for finding in report.findings:
        service = finding.service
        rows.append(
            [
                finding.asset.ip or finding.asset.hostname or "—",
                f"{service.port}/{service.protocol}",
                service.version_string or service.product or "—",
                Paragraph(service.cpe or "—", cell_style),
                str(finding.exploitability_score) if finding.exploitability_score is not None else "—",
                str(finding.impact_score) if finding.impact_score is not None else "—",
            ]
        )

    table = Table(rows, repeatRows=1, hAlign="LEFT")
    table.setStyle(_base_table_style())
    section.append(table)
    return section


def _base_table_style() -> TableStyle:
    return TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), _HEADER_BG),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.5, _TABLE_GRID),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f6f7")]),
        ]
    )
