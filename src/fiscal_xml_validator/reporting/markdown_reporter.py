"""Gerador de relatórios Markdown para documentação, auditoria e GitHub Actions."""

from __future__ import annotations

from typing import List
from ..models import ValidationReport


class MarkdownReporter:
    """Exporta o relatório em GitHub Flavored Markdown."""

    @classmethod
    def format_report(cls, report: ValidationReport) -> str:
        lines: List[str] = []
        doc_info = report.document
        sum_info = report.summary

        lines.append("# Relatório de Auditoria e Validação Fiscal de XML")
        lines.append("")
        lines.append("## Metadados do Documento")
        lines.append("")
        lines.append(f"- **Origem:** `{doc_info.get('origin', {}).get('type')}` ({doc_info.get('origin', {}).get('label')})")
        lines.append(f"- **Tipo:** `{doc_info.get('type')}` (Modelo `{doc_info.get('model', 'N/D')}`)")
        lines.append(f"- **Versão do Layout:** `{doc_info.get('layout_version', 'N/D')}`")
        if doc_info.get("access_key_masked"):
            lines.append(f"- **Chave de Acesso:** `{doc_info.get('access_key_masked')}`")
        lines.append("")
        lines.append("## Sumário Executivo")
        lines.append("")
        lines.append("| Status | Erros Críticos | Erros | Avisos | Informativos |")
        lines.append("|---|---|---|---|---|")
        lines.append(f"| **{sum_info.status.upper()}** | {sum_info.critical} | {sum_info.errors} | {sum_info.warnings} | {sum_info.infos} |")
        lines.append("")

        if not report.diagnostics:
            lines.append("> [!NOTE]")
            lines.append("> Nenhuma inconsistência foi encontrada nas verificações executadas.")
            lines.append("> Isso não garante a conformidade fiscal integral do documento.")
            return "\n".join(lines)

        lines.append("## Diagnósticos Detalhados")
        lines.append("")

        for diag in report.diagnostics:
            badge = "🚨" if diag.severity.value in ["critical", "error"] else "⚠️"
            lines.append(f"### {badge} [{diag.severity.value.upper()}] `{diag.rule_id}` — {diag.message}")
            lines.append("")
            lines.append(f"- **Caminho XML:** `{diag.xml_path}`")
            lines.append(f"- **Tag:** `<{diag.tag}>`")
            lines.append(f"- **Valor Encontrado:** `{diag.found_value}`")
            lines.append(f"- **Valor Esperado:** `{diag.expected_value}`")
            lines.append(f"- **Regra:** {diag.rule_explanation}")
            lines.append(f"- **Fonte Normativa:** `{diag.source.get('reference') or diag.source.get('type')}`")
            lines.append(f"- **Impacto Fiscal:** {diag.fiscal_impact}")
            lines.append(f"- **Sugestão de Ação:** {diag.suggested_fix}")
            lines.append("")

        if report.fix_result and report.fix_result.has_changes:
            lines.append("## Proposta Experimental de Correção")
            lines.append("")
            lines.append("> [!WARNING]")
            lines.append("> Proposta gerada automaticamente para revisão humana. Não substitua documentos fiscais oficiais sem validação prévia.")
            lines.append("")
            lines.append("```diff")
            lines.append(report.fix_result.diff)
            lines.append("```")
            lines.append("")

        return "\n".join(lines)

