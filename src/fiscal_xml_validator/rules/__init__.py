"""Mecanismo de execução e registro de regras de validação fiscal."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..catalog.rule_catalog import RuleCatalog
from ..models import Category, Diagnostic, Severity
from ..normalization.models import NormalizedDocument
from .arithmetic import (
    TaxCalcCOFINSRule,
    TaxCalcICMSRule,
    TaxCalcIPIRule,
    TaxCalcPISRule,
    TaxTotICMSRule,
    TaxTotNFRule,
    TaxTotProdRule,
)
from .base import BaseRule
from .referential import (
    FigCFOPNFCeRule,
    FigCFOPUFRule,
    FigChaveAcessoRule,
    FigCSTCRTRule,
    FigCSTIsencaoRule,
    FigNCMFormatRule,
)

# Instâncias ativas das regras
ACTIVE_RULES: List[BaseRule] = [
    TaxCalcICMSRule(),
    TaxCalcPISRule(),
    TaxCalcCOFINSRule(),
    TaxCalcIPIRule(),
    TaxTotProdRule(),
    TaxTotICMSRule(),
    TaxTotNFRule(),
    FigCFOPUFRule(),
    FigCFOPNFCeRule(),
    FigCSTCRTRule(),
    FigCSTIsencaoRule(),
    FigNCMFormatRule(),
    FigChaveAcessoRule(),
]


class RulesEngine:
    """Motor de execução de regras fiscais com agregação e deduplicação."""

    def __init__(self, rules: Optional[List[BaseRule]] = None):
        self.rules = rules if rules is not None else list(ACTIVE_RULES)

    def execute(
        self,
        doc: NormalizedDocument,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Diagnostic]:
        all_diagnostics: List[Diagnostic] = []
        seen_keys = set()

        for rule in self.rules:
            # Filtro por tipo de documento se especificado
            if (
                rule.metadata.document_types
                and doc.document_type
                and doc.document_type != "UNKNOWN"
                and doc.document_type not in rule.metadata.document_types
            ):
                continue

            try:
                results = rule.validate(doc, context)
                for diag in results:
                    dedup_key = (diag.rule_id, diag.xml_path, diag.tag, diag.found_value)
                    if dedup_key not in seen_keys:
                        seen_keys.add(dedup_key)
                        all_diagnostics.append(diag)
            except Exception as e:
                # Falhas isoladas em regras não devem derrubar toda a execução (Seção 7.3 AGENTS.md)
                all_diagnostics.append(
                    Diagnostic(
                        id=f"ERR-RULE-{rule.metadata.id}",
                        severity=Severity.WARNING,
                        category=Category.STRUCTURE,
                        rule_id=rule.metadata.id,
                        message=f"Falha técnica ao executar regra {rule.metadata.id}: {str(e)}",
                        document_type=doc.document_type,
                        layout_version=doc.layout_version,
                        xml_path="",
                        tag="",
                        rule_explanation="Ocorreu um erro interno durante a avaliação da regra.",
                        fiscal_impact="A verificação específica não pôde ser completada.",
                        suggested_fix="Revise o conteúdo da tag envolvida no XML.",
                        confidence=0.5,
                        limitations=[f"Exceção interna: {type(e).__name__}"],
                    )
                )

        return all_diagnostics

