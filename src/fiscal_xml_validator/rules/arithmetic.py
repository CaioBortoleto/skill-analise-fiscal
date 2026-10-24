"""Regras de consistência aritmética para bases de cálculo, alíquotas e totais.

Conforme seções 2.2, 2.3 e 2.4 do AGENTS.md.
"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Any, Dict, List, Optional

from ..catalog.rule_catalog import RuleMetadata
from ..models import Category, Diagnostic, Severity
from ..normalization.models import NormalizedDocument
from .base import BaseRule


def _round_currency(val: Decimal) -> Decimal:
    """Arredonda para 2 casas decimais conforme padrão fiscal brasileiro (ABNT NBR 5891)."""
    return val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class TaxCalcICMSRule(BaseRule):
    """TAX-CALC-001: Consistência aritmética do valor do ICMS."""

    metadata = RuleMetadata(
        id="TAX-CALC-001",
        title="Consistência aritmética do valor do ICMS próprio",
        category=Category.ARITHMETIC,
        severity=Severity.ERROR,
        document_types=["NFE", "NFCE"],
        description="Verifica se vICMS é igual ao produto da Base de Cálculo (vBC) pela Alíquota (pICMS).",
        source_type="manual_sefaz",
        source_reference="Manual de Orientação do Contribuinte (MOC) - Anexo I - Regra de Validação N12-20",
    )

    def validate(self, doc: NormalizedDocument, context: Optional[Dict[str, Any]] = None) -> List[Diagnostic]:
        diagnostics = []
        for item in doc.itens:
            icms = item.icms
            if icms is None or icms.vBC is None or icms.pICMS is None or icms.vICMS is None:
                continue

            # Apenas grupos tributados integralmente ou com redução de base onde vICMS é explicitado
            if icms.CST in ["00", "10", "20", "70", "90"] or icms.CSOSN in ["900"]:
                calculated = _round_currency(icms.vBC * (icms.pICMS / Decimal("100")))
                diff = abs(icms.vICMS - calculated)
                # Tolera até R$ 0.01 por questão de arredondamento de casas intermediárias
                if diff > Decimal("0.01"):
                    xml_path = f"{icms.xml_subpath}/vICMS"
                    diag = Diagnostic(
                        id=f"TAX-CALC-001-item-{item.nItem}",
                        severity=Severity.ERROR,
                        category=Category.ARITHMETIC,
                        rule_id=self.metadata.id,
                        message=f"Divergência no cálculo do ICMS do item {item.nItem}: informado {icms.vICMS:.2f}, calculado {calculated:.2f}.",
                        document_type=doc.document_type,
                        layout_version=doc.layout_version,
                        xml_path=xml_path,
                        tag="vICMS",
                        found_value=f"{icms.vICMS:.2f}",
                        expected_value=f"{calculated:.2f}",
                        rule_explanation="O valor do ICMS (vICMS) deve corresponder à multiplicação da Base de Cálculo (vBC) pela alíquota (pICMS/100).",
                        source={
                            "type": self.metadata.source_type,
                            "reference": self.metadata.source_reference,
                        },
                        fiscal_impact="Rejeição pela SEFAZ por erro de cálculo ou divergência na apuração do imposto.",
                        suggested_fix=f"Ajuste vICMS para {calculated:.2f} ou retifique a base de cálculo (vBC) e a alíquota (pICMS).",
                        confidence=1.0,
                        limitations=[],
                    )
                    diagnostics.append(diag)
        return diagnostics


class TaxCalcPISRule(BaseRule):
    """TAX-CALC-003: Consistência aritmética do PIS."""

    metadata = RuleMetadata(
        id="TAX-CALC-003",
        title="Consistência aritmética do valor do PIS",
        category=Category.ARITHMETIC,
        severity=Severity.ERROR,
        document_types=["NFE", "NFCE"],
        description="Verifica se vPIS é igual a vBC * pPIS / 100 para operações tributadas por alíquota percentual.",
        source_type="manual_sefaz",
        source_reference="MOC Anexo I - Regra de Validação Q07-10",
    )

    def validate(self, doc: NormalizedDocument, context: Optional[Dict[str, Any]] = None) -> List[Diagnostic]:
        diagnostics = []
        for item in doc.itens:
            pis = item.pis
            if pis is None or pis.vBC is None or pis.pPIS is None or pis.vPIS is None:
                continue

            calculated = _round_currency(pis.vBC * (pis.pPIS / Decimal("100")))
            if abs(pis.vPIS - calculated) > Decimal("0.01"):
                xml_path = f"{pis.xml_subpath}/vPIS"
                diagnostics.append(
                    Diagnostic(
                        id=f"TAX-CALC-003-item-{item.nItem}",
                        severity=Severity.ERROR,
                        category=Category.ARITHMETIC,
                        rule_id=self.metadata.id,
                        message=f"Divergência no cálculo do PIS do item {item.nItem}: informado {pis.vPIS:.2f}, calculado {calculated:.2f}.",
                        document_type=doc.document_type,
                        layout_version=doc.layout_version,
                        xml_path=xml_path,
                        tag="vPIS",
                        found_value=f"{pis.vPIS:.2f}",
                        expected_value=f"{calculated:.2f}",
                        rule_explanation="O valor do PIS (vPIS) deve ser coerente com a multiplicação de vBC por pPIS.",
                        source={
                            "type": self.metadata.source_type,
                            "reference": self.metadata.source_reference,
                        },
                        fiscal_impact="Risco de escrituração incorreta na EFD-Contribuições e rejeição de autorização.",
                        suggested_fix=f"Retifique vPIS para {calculated:.2f} ou confira a base e a alíquota aplicadas.",
                        confidence=1.0,
                    )
                )
        return diagnostics


class TaxCalcCOFINSRule(BaseRule):
    """TAX-CALC-004: Consistência aritmética da COFINS."""

    metadata = RuleMetadata(
        id="TAX-CALC-004",
        title="Consistência aritmética do valor da COFINS",
        category=Category.ARITHMETIC,
        severity=Severity.ERROR,
        document_types=["NFE", "NFCE"],
        description="Verifica se vCOFINS é igual a vBC * pCOFINS / 100 para operações tributadas por alíquota percentual.",
        source_type="manual_sefaz",
        source_reference="MOC Anexo I - Regra de Validação S07-10",
    )

    def validate(self, doc: NormalizedDocument, context: Optional[Dict[str, Any]] = None) -> List[Diagnostic]:
        diagnostics = []
        for item in doc.itens:
            cofins = item.cofins
            if cofins is None or cofins.vBC is None or cofins.pCOFINS is None or cofins.vCOFINS is None:
                continue

            calculated = _round_currency(cofins.vBC * (cofins.pCOFINS / Decimal("100")))
            if abs(cofins.vCOFINS - calculated) > Decimal("0.01"):
                xml_path = f"{cofins.xml_subpath}/vCOFINS"
                diagnostics.append(
                    Diagnostic(
                        id=f"TAX-CALC-004-item-{item.nItem}",
                        severity=Severity.ERROR,
                        category=Category.ARITHMETIC,
                        rule_id=self.metadata.id,
                        message=f"Divergência no cálculo da COFINS do item {item.nItem}: informado {cofins.vCOFINS:.2f}, calculado {calculated:.2f}.",
                        document_type=doc.document_type,
                        layout_version=doc.layout_version,
                        xml_path=xml_path,
                        tag="vCOFINS",
                        found_value=f"{cofins.vCOFINS:.2f}",
                        expected_value=f"{calculated:.2f}",
                        rule_explanation="O valor da COFINS (vCOFINS) deve ser coerente com a multiplicação de vBC por pCOFINS.",
                        source={
                            "type": self.metadata.source_type,
                            "reference": self.metadata.source_reference,
                        },
                        fiscal_impact="Inconsistência na EFD-Contribuições e eventual rejeição fiscal.",
                        suggested_fix=f"Retifique vCOFINS para {calculated:.2f}.",
                        confidence=1.0,
                    )
                )
        return diagnostics


class TaxCalcIPIRule(BaseRule):
    """TAX-CALC-005: Consistência aritmética do IPI."""

    metadata = RuleMetadata(
        id="TAX-CALC-005",
        title="Consistência aritmética do valor do IPI",
        category=Category.ARITHMETIC,
        severity=Severity.ERROR,
        document_types=["NFE"],
        description="Verifica se vIPI é igual a vBC * pIPI / 100 para itens com IPITrib.",
        source_type="manual_sefaz",
        source_reference="MOC Anexo I - Regra de Validação O14-10",
    )

    def validate(self, doc: NormalizedDocument, context: Optional[Dict[str, Any]] = None) -> List[Diagnostic]:
        diagnostics = []
        for item in doc.itens:
            ipi = item.ipi
            if ipi is None or ipi.vBC is None or ipi.pIPI is None or ipi.vIPI is None:
                continue

            calculated = _round_currency(ipi.vBC * (ipi.pIPI / Decimal("100")))
            if abs(ipi.vIPI - calculated) > Decimal("0.01"):
                xml_path = f"{ipi.xml_subpath}/vIPI"
                diagnostics.append(
                    Diagnostic(
                        id=f"TAX-CALC-005-item-{item.nItem}",
                        severity=Severity.ERROR,
                        category=Category.ARITHMETIC,
                        rule_id=self.metadata.id,
                        message=f"Divergência no cálculo do IPI do item {item.nItem}: informado {ipi.vIPI:.2f}, calculado {calculated:.2f}.",
                        document_type=doc.document_type,
                        layout_version=doc.layout_version,
                        xml_path=xml_path,
                        tag="vIPI",
                        found_value=f"{ipi.vIPI:.2f}",
                        expected_value=f"{calculated:.2f}",
                        rule_explanation="O valor do IPI (vIPI) deve corresponder à Base de Cálculo (vBC) multiplicada pela alíquota (pIPI).",
                        source={
                            "type": self.metadata.source_type,
                            "reference": self.metadata.source_reference,
                        },
                        fiscal_impact="Erro na escrituração do IPI e divergência em relação à tabela TIPI.",
                        suggested_fix=f"Retifique vIPI para {calculated:.2f}.",
                        confidence=1.0,
                    )
                )
        return diagnostics


class TaxTotProdRule(BaseRule):
    """TAX-TOT-001: Somatório do valor dos produtos."""

    metadata = RuleMetadata(
        id="TAX-TOT-001",
        title="Somatório do valor total dos produtos (vProd)",
        category=Category.ARITHMETIC,
        severity=Severity.ERROR,
        document_types=["NFE", "NFCE"],
        description="Compara o somatório de vProd de todos os itens com ICMSTot.vProd.",
        source_type="manual_sefaz",
        source_reference="MOC Anexo I - Regra de Validação W07-10",
    )

    def validate(self, doc: NormalizedDocument, context: Optional[Dict[str, Any]] = None) -> List[Diagnostic]:
        if doc.total is None:
            return []

        sum_prod = _round_currency(sum((item.vProd for item in doc.itens), Decimal("0.00")))
        tot_prod = doc.total.vProd

        if abs(tot_prod - sum_prod) > Decimal("0.01"):
            return [
                Diagnostic(
                    id="TAX-TOT-001-vProd",
                    severity=Severity.ERROR,
                    category=Category.ARITHMETIC,
                    rule_id=self.metadata.id,
                    message=f"Somatório de vProd dos itens ({sum_prod:.2f}) diverge do total informado em ICMSTot ({tot_prod:.2f}).",
                    document_type=doc.document_type,
                    layout_version=doc.layout_version,
                    xml_path=f"{doc.total.xml_path}/vProd",
                    tag="vProd",
                    found_value=f"{tot_prod:.2f}",
                    expected_value=f"{sum_prod:.2f}",
                    rule_explanation="O campo total/ICMSTot/vProd deve ser exatamente a soma de det/prod/vProd de cada item.",
                    source={
                        "type": self.metadata.source_type,
                        "reference": self.metadata.source_reference,
                    },
                    fiscal_impact="Rejeição SEFAZ 531: Total do Valor dos Produtos difere do somatório dos itens.",
                    suggested_fix=f"Ajuste ICMSTot/vProd para {sum_prod:.2f} ou confira os valores unitários e produtos individuais.",
                    confidence=1.0,
                )
            ]
        return []


class TaxTotICMSRule(BaseRule):
    """TAX-TOT-002: Somatório do valor do ICMS."""

    metadata = RuleMetadata(
        id="TAX-TOT-002",
        title="Somatório do valor do ICMS total (vICMS)",
        category=Category.ARITHMETIC,
        severity=Severity.ERROR,
        document_types=["NFE", "NFCE"],
        description="Compara o somatório de vICMS dos itens com ICMSTot.vICMS.",
        source_type="manual_sefaz",
        source_reference="MOC Anexo I - Regra de Validação W04-10",
    )

    def validate(self, doc: NormalizedDocument, context: Optional[Dict[str, Any]] = None) -> List[Diagnostic]:
        if doc.total is None:
            return []

        sum_icms = Decimal("0.00")
        for item in doc.itens:
            if item.icms and item.icms.vICMS:
                sum_icms += item.icms.vICMS
        sum_icms = _round_currency(sum_icms)

        tot_icms = doc.total.vICMS
        if abs(tot_icms - sum_icms) > Decimal("0.01"):
            return [
                Diagnostic(
                    id="TAX-TOT-002-vICMS",
                    severity=Severity.ERROR,
                    category=Category.ARITHMETIC,
                    rule_id=self.metadata.id,
                    message=f"Somatório de vICMS dos itens ({sum_icms:.2f}) diverge do total informado em ICMSTot ({tot_icms:.2f}).",
                    document_type=doc.document_type,
                    layout_version=doc.layout_version,
                    xml_path=f"{doc.total.xml_path}/vICMS",
                    tag="vICMS",
                    found_value=f"{tot_icms:.2f}",
                    expected_value=f"{sum_icms:.2f}",
                    rule_explanation="O campo total/ICMSTot/vICMS deve corresponder à soma dos valores de vICMS dos itens.",
                    source={
                        "type": self.metadata.source_type,
                        "reference": self.metadata.source_reference,
                    },
                    fiscal_impact="Rejeição SEFAZ 532: Total do ICMS difere do somatório dos itens.",
                    suggested_fix=f"Atualize ICMSTot/vICMS para {sum_icms:.2f}.",
                    confidence=1.0,
                )
            ]
        return []


class TaxTotNFRule(BaseRule):
    """TAX-TOT-003: Validação da equação do Valor Total da NF-e (vNF)."""

    metadata = RuleMetadata(
        id="TAX-TOT-003",
        title="Equação do Valor Total da Nota Fiscal (vNF)",
        category=Category.ARITHMETIC,
        severity=Severity.ERROR,
        document_types=["NFE", "NFCE"],
        description="Verifica se vNF = vProd - vDesc - vICMSDeson + vST + vFCPST + vFrete + vSeg + vOutro + vII + vIPI + vIPIDevol.",
        source_type="manual_sefaz",
        source_reference="MOC Anexo I - Regra de Validação W16-10",
    )

    def validate(self, doc: NormalizedDocument, context: Optional[Dict[str, Any]] = None) -> List[Diagnostic]:
        if doc.total is None:
            return []

        tot = doc.total
        # vNF = vProd - vDesc - vICMSDeson + vST + vFCPST + vFrete + vSeg + vOutro + vII + vIPI + vIPIDevol
        expected_vnf = (
            tot.vProd
            - tot.vDesc
            - tot.vICMSDeson
            + tot.vST
            + tot.vFCPST
            + tot.vFrete
            + tot.vSeg
            + tot.vOutro
            + tot.vII
            + tot.vIPI
            + tot.vIPIDevol
        )
        expected_vnf = _round_currency(expected_vnf)

        if abs(tot.vNF - expected_vnf) > Decimal("0.01"):
            return [
                Diagnostic(
                    id="TAX-TOT-003-vNF",
                    severity=Severity.ERROR,
                    category=Category.ARITHMETIC,
                    rule_id=self.metadata.id,
                    message=f"Valor total da NF (vNF={tot.vNF:.2f}) diverge da equação legal dos componentes ({expected_vnf:.2f}).",
                    document_type=doc.document_type,
                    layout_version=doc.layout_version,
                    xml_path=f"{tot.xml_path}/vNF",
                    tag="vNF",
                    found_value=f"{tot.vNF:.2f}",
                    expected_value=f"{expected_vnf:.2f}",
                    rule_explanation="vNF deve ser a soma de produtos, tributos agregados (ST, IPI, II), frete, seguro e despesas, deduzidos descontos e desonerações.",
                    source={
                        "type": self.metadata.source_type,
                        "reference": self.metadata.source_reference,
                    },
                    fiscal_impact="Rejeição SEFAZ 535: Total da NF difere do somatório dos valores que compõem o valor total.",
                    suggested_fix=f"Retifique ICMSTot/vNF para {expected_vnf:.2f}.",
                    confidence=1.0,
                )
            ]
        return []

