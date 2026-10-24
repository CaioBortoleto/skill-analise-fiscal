"""Gerador de relatórios legíveis para console/terminal.

Conforme seções 2.4 e 12.1 do AGENTS.md.
"""

from __future__ import annotations

from typing import List
from ..models import Diagnostic, Severity, ValidationReport


class ConsoleReporter:
    """Formata os diagnósticos em texto estruturado respondendo às 6 perguntas essenciais."""

    @classmethod
    def format_report(cls, report: ValidationReport, show_diff: bool = True) -> str:
        lines: List[str] = []
        sep = "=" * 78
        subsep = "-" * 78

        lines.append(sep)
        lines.append("  RELATÓRIO DE AUDITORIA FISCAL DE XML")
        lines.append(sep)

        # Metadados do documento
        doc_info = report.document
        lines.append(f"Origem do Documento: {doc_info.get('origin', {}).get('label', 'Desconhecida')}")
        lines.append(f"Tipo de Documento:   {doc_info.get('type', 'N/D')} (Modelo {doc_info.get('model', 'N/D')})")
        lines.append(f"Versão do Layout:    {doc_info.get('layout_version', 'N/D')}")
        if doc_info.get("access_key_masked"):
            lines.append(f"Chave de Acesso:     {doc_info.get('access_key_masked')}")
        lines.append(subsep)

        # Sumário
        sum_info = report.summary
        lines.append(
            f"Status: {sum_info.status.upper()} | "
            f"Erros: {sum_info.errors} | Avisos: {sum_info.warnings} | Informativos: {sum_info.infos}"
        )
        lines.append(sep)
        lines.append("")

        if not report.diagnostics:
            lines.append("✅ Nenhuma inconsistência foi encontrada nas verificações executadas.")
            lines.append("   Nota: Isso não garante a conformidade fiscal integral do documento.")
            lines.append("   Consulte as limitações, regras ativas e referências normativas.")
            lines.append("")
            return "\n".join(lines)

        # Detalhamento de cada diagnóstico
        lines.append(f"FORAM IDENTIFICADAS {len(report.diagnostics)} OCORRÊNCIA(S):")
        lines.append("")

        for i, diag in enumerate(report.diagnostics, start=1):
            sev_tag = f"[{diag.severity.value.upper()}]"
            lines.append(f"{sev_tag} {diag.rule_id} — {diag.message}")
            lines.append(f"  1. Localização:  Tag <{diag.tag}> em {diag.xml_path}")
            lines.append(f"  2. Encontrado:   {diag.found_value if diag.found_value is not None else 'N/A'}")
            lines.append(f"  3. Esperado:     {diag.expected_value if diag.expected_value is not None else 'Condição não satisfeita'}")
            lines.append(f"  4. Regra:        {diag.rule_explanation}")
            lines.append(f"     Fonte:        {diag.source.get('reference') or diag.source.get('type', 'Regra interna')}")
            lines.append(f"  5. Impacto:      {diag.fiscal_impact}")
            lines.append(f"  6. Sugestão:     {diag.suggested_fix}")
            if diag.limitations:
                lines.append(f"     Limitações:   {'; '.join(diag.limitations)}")
            lines.append(subsep)

        # Proposta de correção experimental (Diff)
        if show_diff and report.fix_result and report.fix_result.has_changes:
            lines.append("")
            lines.append("PROPOSTA EXPERIMENTAL DE CORREÇÃO (DIFF UNIFICADO):")
            lines.append("Atenção: Valide previamente as alterações com um responsável fiscal.")
            lines.append(subsep)
            lines.append(report.fix_result.diff)
            lines.append(subsep)

        return "\n".join(lines)

