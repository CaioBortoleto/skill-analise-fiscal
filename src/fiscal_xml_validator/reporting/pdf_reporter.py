"""Gerador de relatórios executivos em PDF com apresentação visual profissional.

Em estrita conformidade com a seção 12.4 do AGENTS.md.
Apresenta todas as informações que precisam ser corrigidas e o MOTIVO detalhado.
"""

from __future__ import annotations

import datetime
from pathlib import Path
from typing import List, Optional

from ..models import Severity, ValidationReport

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.platypus import (
        HRFlowable,
        KeepTogether,
        PageBreak,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


class PDFReporter:
    """Gera relatório de auditoria fiscal em formato PDF executivo e apresentável."""

    @classmethod
    def generate_pdf(cls, report: ValidationReport, output_path: str | Path) -> str:
        if not REPORTLAB_AVAILABLE:
            raise ImportError(
                "A biblioteca 'reportlab' é necessária para gerar relatórios em PDF. "
                "Instale-a via: pip install reportlab"
            )

        out_file = str(Path(output_path).resolve())
        doc = SimpleDocTemplate(
            out_file,
            pagesize=A4,
            leftMargin=36,
            rightMargin=36,
            topMargin=36,
            bottomMargin=36,
        )

        styles = getSampleStyleSheet()

        # Cores corporativas elegantes
        color_primary = colors.HexColor("#1A365D")   # Azul executivo escuro
        color_secondary = colors.HexColor("#2B6CB0") # Azul médio
        color_danger = colors.HexColor("#9B2C2C")    # Vinho/Vermelho auditoria
        color_warning = colors.HexColor("#C05621")   # Laranja alerta
        color_success = colors.HexColor("#22543D")   # Verde conformidade
        color_bg_light = colors.HexColor("#F7FAFC")  # Fundo cinza suave
        color_motive_bg = colors.HexColor("#FFF5F5") # Fundo suave para o MOTIVO
        color_border = colors.HexColor("#E2E8F0")    # Borda sutil
        color_text_dark = colors.HexColor("#2D3748") # Texto principal

        # Estilos tipográficos
        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=22,
            textColor=color_primary,
        )
        subtitle_style = ParagraphStyle(
            "DocSubtitle",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#4A5568"),
        )
        sec_heading = ParagraphStyle(
            "SecHeading",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=16,
            textColor=color_primary,
            spaceAfter=6,
        )
        body_style = ParagraphStyle(
            "BodyDark",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=12,
            textColor=color_text_dark,
        )
        body_bold = ParagraphStyle(
            "BodyDarkBold",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=8.5,
            leading=12,
            textColor=color_text_dark,
        )
        motive_text = ParagraphStyle(
            "MotiveText",
            parent=styles["Normal"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=12,
            textColor=colors.HexColor("#742A2A"),
        )
        motive_title = ParagraphStyle(
            "MotiveTitle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=13,
            textColor=color_danger,
        )
        tag_badge = ParagraphStyle(
            "TagBadge",
            parent=styles["Normal"],
            fontName="Courier-Bold",
            fontSize=8.5,
            leading=11,
            textColor=color_primary,
        )
        code_style = ParagraphStyle(
            "CodeBlock",
            parent=styles["Normal"],
            fontName="Courier",
            fontSize=7.5,
            leading=10,
            textColor=colors.HexColor("#1A202C"),
        )

        story = []

        # 1. Cabeçalho Principal
        story.append(Paragraph("RELATÓRIO DE AUDITORIA E CORREÇÃO FISCAL", title_style))
        story.append(
            Paragraph(
                "Diagnóstico Explicável de Figuras Fiscais em Documentos Eletrônicos (DF-e)",
                subtitle_style,
            )
        )
        story.append(Spacer(1, 10))
        story.append(HRFlowable(width="100%", thickness=2, color=color_secondary, spaceAfter=12))

        # 2. Metadados do Documento
        doc_info = report.document
        sum_info = report.summary
        now_str = datetime.datetime.now().strftime("%d/%m/%Y às %H:%M:%S")

        doc_table_data = [
            [
                Paragraph("<b>Tipo de Documento:</b>", body_style),
                Paragraph(f"{doc_info.get('type', 'N/D')} (Modelo {doc_info.get('model', 'N/D')})", body_style),
                Paragraph("<b>Data da Auditoria:</b>", body_style),
                Paragraph(now_str, body_style),
            ],
            [
                Paragraph("<b>Versão do Layout:</b>", body_style),
                Paragraph(str(doc_info.get("layout_version", "4.00")), body_style),
                Paragraph("<b>Origem dos Dados:</b>", body_style),
                Paragraph(doc_info.get("origin", {}).get("label", "Arquivo fornecido"), body_style),
            ],
            [
                Paragraph("<b>Chave de Acesso:</b>", body_style),
                Paragraph(f"<code>{doc_info.get('access_key_masked') or 'Não informada'}</code>", body_style),
                Paragraph("<b>Arquivo Analisado:</b>", body_style),
                Paragraph(Path(doc_info.get("file_path", "XML em memória")).name, body_style),
            ],
        ]

        t_meta = Table(doc_table_data, colWidths=[110, 150, 110, 150])
        t_meta.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), color_bg_light),
                ("BOX", (0, 0), (-1, -1), 0.5, color_border),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, color_border),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ])
        )
        story.append(t_meta)
        story.append(Spacer(1, 12))

        # 3. Sumário Executivo
        status_color = color_success if sum_info.errors == 0 and sum_info.critical == 0 else color_danger
        status_label = "CONFORME (Nenhuma divergência crítica)" if sum_info.errors == 0 and sum_info.critical == 0 else "INCONSISTÊNCIAS IDENTIFICADAS (Ajustes Necessários)"

        status_style = ParagraphStyle(
            "StatusStyle",
            parent=styles["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=13,
            textColor=status_color,
        )

        sum_table_data = [
            [
                Paragraph(f"<b>STATUS GERAL:</b> {status_label}", status_style),
                Paragraph(f"<b>Erros Críticos:</b> {sum_info.critical}", body_style),
                Paragraph(f"<b>Erros Fiscais:</b> {sum_info.errors}", body_style),
                Paragraph(f"<b>Avisos:</b> {sum_info.warnings}", body_style),
            ]
        ]
        t_sum = Table(sum_table_data, colWidths=[240, 90, 95, 95])
        t_sum.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EDF2F7")),
                ("BOX", (0, 0), (-1, -1), 1, status_color),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ])
        )
        story.append(t_sum)
        story.append(Spacer(1, 16))

        # 4. Caso não haja erros
        if not report.diagnostics:
            story.append(
                Paragraph(
                    "<b>✅ Nenhuma inconsistência foi identificada nas regras fiscais executadas.</b>",
                    ParagraphStyle("OkStyle", parent=body_style, fontSize=11, textColor=color_success),
                )
            )
            story.append(Spacer(1, 6))
            story.append(
                Paragraph(
                    "Nota técnica: Este resultado atesta a conformidade com o conjunto de regras ativas no catálogo do validador. Ele não substitui a validação fiscal integral pelo contador responsável.",
                    subtitle_style,
                )
            )
            doc.build(story)
            return out_file

        # 5. Seção de Detalhamento: O que precisa ser corrigido e o MOTIVO
        story.append(Paragraph("DETALHAMENTO DAS FIGURAS FISCAIS QUE EXIGEM CORREÇÃO", sec_heading))
        story.append(
            Paragraph(
                "Abaixo estão detalhados os campos inconsistentes, seus valores atuais e o <b>MOTIVO FISCAL E NORMATIVO</b> de cada correção exigida:",
                body_style,
            )
        )
        story.append(Spacer(1, 8))

        for idx, diag in enumerate(report.diagnostics, start=1):
            sev_badge_color = color_danger if diag.severity.value in ["critical", "error"] else color_warning
            sev_title_style = ParagraphStyle(
                f"SevTitle_{idx}",
                parent=styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=10,
                leading=13,
                textColor=colors.white,
            )

            # Cabeçalho do Card
            card_header = [
                [
                    Paragraph(
                        f"OCORRÊNCIA #{idx} — [{diag.severity.value.upper()}] {diag.rule_id}: {diag.message}",
                        sev_title_style,
                    )
                ]
            ]
            t_card_header = Table(card_header, colWidths=[520])
            t_card_header.setStyle(
                TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), sev_badge_color),
                    ("TOPPADDING", (0, 0), (-1, -1), 5),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ])
            )

            # Bloco A: O que precisa ser corrigido
            what_data = [
                [
                    Paragraph("<b>Campo / Tag:</b>", body_style),
                    Paragraph(f"<code>&lt;{diag.tag}&gt;</code>", tag_badge),
                    Paragraph("<b>Caminho XML:</b>", body_style),
                    Paragraph(f"<code>{diag.xml_path}</code>", code_style),
                ],
                [
                    Paragraph("<b>Valor Encontrado:</b>", body_style),
                    Paragraph(f"<b><font color='#C53030'>{diag.found_value or 'N/A'}</font></b>", body_style),
                    Paragraph("<b>Valor Correto / Esperado:</b>", body_style),
                    Paragraph(f"<b><font color='#22543D'>{diag.expected_value or 'Ajuste contextual'}</font></b>", body_style),
                ],
            ]
            t_what = Table(what_data, colWidths=[100, 160, 110, 150])
            t_what.setStyle(
                TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), color_bg_light),
                    ("INNERGRID", (0, 0), (-1, -1), 0.5, color_border),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ])
            )

            # Bloco B: O MOTIVO DE PRECISAR SER CORRIGIDO (Destaque Principal)
            src_ref = diag.source.get("reference") or diag.source.get("type", "Regra Tributária Oficial")
            why_data = [
                [
                    Paragraph("MOTIVO DA CORREÇÃO (EMBASAMENTO FISCAL & RISCO):", motive_title),
                ],
                [
                    Paragraph(
                        f"• <b>Por que corrigir:</b> {diag.rule_explanation}<br/>"
                        f"• <b>Base Legal / Fonte Normativa:</b> <u>{src_ref}</u><br/>"
                        f"• <b>Impacto Fiscal & SEFAZ:</b> {diag.fiscal_impact}<br/>"
                        f"• <b>Ação Recomendada:</b> {diag.suggested_fix}",
                        motive_text,
                    ),
                ],
            ]
            t_why = Table(why_data, colWidths=[520])
            t_why.setStyle(
                TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), color_motive_bg),
                    ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#FEB2B2")),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ])
            )

            # Empacota cada ocorrência para evitar quebra no meio da página
            story.append(KeepTogether([t_card_header, t_what, t_why, Spacer(1, 10)]))

        # 6. Seção de Proposta Experimental de Correção (Diff)
        if report.fix_result and report.fix_result.has_changes:
            story.append(Spacer(1, 8))
            story.append(Paragraph("PROPOSTA DE CORREÇÃO EM FORMATO DIFF UNIFICADO", sec_heading))
            story.append(
                Paragraph(
                    "As alterações sugeridas abaixo corrigem os campos divergentes identificados. "
                    "<b>Atenção:</b> Esta proposta é puramente técnica e analítica; não substitua XMLs oficiais sem validação humana.",
                    subtitle_style,
                )
            )
            story.append(Spacer(1, 6))

            # Converte as linhas do diff para parágrafos formatados
            diff_lines = report.fix_result.diff.splitlines()
            diff_p_list = []
            for d_line in diff_lines[:40]:  # Limita a 40 linhas no PDF para manter clareza
                escaped = d_line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace(" ", "&nbsp;")
                if d_line.startswith("+"):
                    line_style = ParagraphStyle("DiffAdd", parent=code_style, textColor=colors.HexColor("#22543D"))
                elif d_line.startswith("-"):
                    line_style = ParagraphStyle("DiffSub", parent=code_style, textColor=colors.HexColor("#9B2C2C"))
                elif d_line.startswith("@"):
                    line_style = ParagraphStyle("DiffHdr", parent=code_style, textColor=colors.HexColor("#2B6CB0"))
                else:
                    line_style = code_style
                diff_p_list.append(Paragraph(escaped, line_style))

            t_diff = Table([[p] for p in diff_p_list], colWidths=[520])
            t_diff.setStyle(
                TableStyle([
                    ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F7FAFC")),
                    ("BOX", (0, 0), (-1, -1), 0.5, color_border),
                    ("TOPPADDING", (0, 0), (-1, -1), 1),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
                    ("LEFTPADDING", (0, 0), (-1, -1), 6),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ])
            )
            story.append(KeepTogether([t_diff, Spacer(1, 10)]))

        # 7. Rodapé informativo
        story.append(Spacer(1, 10))
        story.append(HRFlowable(width="100%", thickness=0.5, color=color_border, spaceAfter=8))
        story.append(
            Paragraph(
                "Documento gerado pelo <b>fiscal-xml-validator</b>. Sistema em conformidade com o Manual de Orientação do Contribuinte da SEFAZ e normas do SPED.",
                subtitle_style,
            )
        )

        doc.build(story)
        return out_file

