"""Gerador de PDF do relatorio de compliance LGPD.

Usa reportlab pra render direto pra bytes — sem template HTML, sem dep de
sistema. Output: PDF formatado com metricas do periodo, pronto pra enviar
ao DPO (LGPD Art. 37).
"""

from __future__ import annotations

import datetime as dt
import io

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.schemas.compliance import ComplianceReport


def _fmt_dt(d: dt.datetime) -> str:
    return d.strftime("%d/%m/%Y %H:%M")


def _fmt_secs(secs: float | None) -> str:
    if secs is None:
        return "—"
    if secs < 60:
        return f"{secs:.0f}s"
    if secs < 3600:
        return f"{secs / 60:.1f}min"
    return f"{secs / 3600:.1f}h"


def render(report: ComplianceReport, org_name: str = "Organização") -> bytes:
    """Renderiza ComplianceReport como PDF. Retorna bytes prontos pra HTTP response."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        title="Relatorio de Compliance LGPD",
        author="SentinelBR",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "TitleSB",
        parent=styles["Title"],
        textColor=colors.HexColor("#059669"),  # emerald-600 (cor da marca)
        spaceAfter=14,
    )
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], spaceBefore=12, spaceAfter=6)
    body = styles["BodyText"]
    small = ParagraphStyle("Small", parent=body, fontSize=9, textColor=colors.grey)

    story: list = []

    # Header
    story.append(Paragraph("Relatorio de Compliance LGPD", title_style))
    story.append(
        Paragraph(
            f"<b>Organizacao:</b> {org_name}<br/>"
            f"<b>Periodo:</b> {_fmt_dt(report.period_start)} -> {_fmt_dt(report.period_end)} "
            f"({report.period_days} dias)<br/>"
            f"<b>Gerado em:</b> {_fmt_dt(dt.datetime.now(dt.UTC))}<br/>"
            f"<b>Base legal:</b> LGPD Art. 37 (registro de operacoes de tratamento) "
            f"e Art. 16 (retencao de logs).",
            body,
        )
    )

    # Section 1 - Autenticacao
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph("1. Autenticacao e Acesso", h2))
    story.append(_make_table([
        ["Metrica", "Valor"],
        ["Tentativas totais de login", str(report.total_logins)],
        ["Logins falhados", str(report.failed_logins)],
        ["Usuarios unicos que logaram", str(report.distinct_users_logged_in)],
    ]))

    # Section 2 - Hosts
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph("2. Hosts Monitorados", h2))
    story.append(_make_table([
        ["Metrica", "Valor"],
        ["Hosts cadastrados (total)", str(report.hosts_total)],
        ["Hosts ativos (heartbeat recente)", str(report.hosts_active)],
        ["Criados no periodo", str(report.hosts_created_in_period)],
        ["Removidos no periodo", str(report.hosts_deleted_in_period)],
    ]))

    # Section 3 - Deteccao e Resposta
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph("3. Deteccao e Resposta a Incidentes", h2))
    story.append(_make_table([
        ["Metrica", "Valor"],
        ["Alertas gerados no periodo", str(report.alerts_created_in_period)],
        ["Alertas abertos (atual)", str(report.alerts_open)],
        ["Alertas reconhecidos", str(report.alerts_acknowledged_in_period)],
        ["Alertas resolvidos", str(report.alerts_resolved_in_period)],
        ["Acoes executadas (auto-block, quarantine)", str(report.actions_executed_in_period)],
        ["MTTR (tempo medio de resposta)", _fmt_secs(report.mttr_seconds)],
    ]))

    # Section 4 - Audit log
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph("4. Audit Log (Art. 37 LGPD)", h2))
    story.append(_make_table([
        ["Metrica", "Valor"],
        ["Entradas no periodo", str(report.audit_log_entries_in_period)],
        ["Retencao configurada", f"{report.audit_retention_days} dias"],
    ]))

    # Footer
    story.append(Spacer(1, 1 * cm))
    story.append(Paragraph(
        "<b>Notas:</b><br/>"
        "- Audit logs cobrem login, criacao/exclusao de hosts, ack/resolve de alertas, "
        "reverter acoes, e geracao de relatorios.<br/>"
        "- MTTR = tempo entre criacao do alerta e execucao da resposta (auto-block ou "
        "quarantine).<br/>"
        "- Retencao de audit log: ao expirar, registros sao purgados automaticamente "
        "(LGPD Art. 16). Configuravel via env SENTINELBR_AUDIT_RETENTION_DAYS.<br/>"
        "- Gerado pelo SentinelBR - plataforma open-source AGPL-3.0.",
        small,
    ))

    doc.build(story)
    return buf.getvalue()


def _make_table(rows: list[list[str]]) -> Table:
    """Cria tabela 2 colunas (label, valor) com estilo consistente."""
    table = Table(rows, colWidths=[10 * cm, 4 * cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f4f4f5")),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#e4e4e7")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fafafa")]),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
    ]))
    return table
