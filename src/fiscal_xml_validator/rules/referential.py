"""Regras de consistência referencial de figuras fiscais (CFOP, CST, CSOSN, NCM, CEST).

Conforme seções 2.2, 2.3, 2.4 e 7.2 do AGENTS.md.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from ..catalog.rule_catalog import RuleMetadata
from ..ingestion import AccessKeyValidator
from ..models import Category, Diagnostic, Severity
from ..normalization.models import NormalizedDocument
from .base import BaseRule


class FigCFOPUFRule(BaseRule):
    """FIG-CFOP-001: Compatibilidade do CFOP com os estados de origem e destino."""

    metadata = RuleMetadata(
        id="FIG-CFOP-001",
        title="Compatibilidade do CFOP com UF do Emitente e Destinatário",
        category=Category.REFERENCE,
        severity=Severity.ERROR,
        document_types=["NFE", "NFCE"],
        description="Verifica se o primeiro dígito do CFOP corresponde à abrangência geográfica da operação (interna, interestadual ou exterior).",
        source_type="ajuste_sinief",
        source_reference="Convênio S/Nº de 1970 (Tabela CFOP) e MOC Anexo I - Regra I08-10",
    )

    def validate(self, doc: NormalizedDocument, context: Optional[Dict[str, Any]] = None) -> List[Diagnostic]:
        diagnostics = []
        emit_uf = doc.emit.UF.strip().upper() if doc.emit and doc.emit.UF else None
        dest_uf = doc.dest.UF.strip().upper() if doc.dest and doc.dest.UF else None
        is_saida = doc.ide.tpNF == "1"

        # Se não há destinatário ou emitente com UF, não é possível avaliar com segurança
        if not emit_uf:
            return []

        for item in doc.itens:
            cfop = item.CFOP.strip()
            if not cfop or len(cfop) != 4 or not cfop.isdigit():
                continue

            first_digit = cfop[0]

            # 1. Operação com Exterior
            if doc.ide.idDest == "3" or dest_uf == "EX" or (doc.dest and doc.dest.idEstrangeiro):
                expected_first = "7" if is_saida else "3"
                if first_digit != expected_first:
                    diagnostics.append(
                        Diagnostic(
                            id=f"FIG-CFOP-001-item-{item.nItem}",
                            severity=Severity.ERROR,
                            category=Category.REFERENCE,
                            rule_id=self.metadata.id,
                            message=f"Item {item.nItem}: CFOP '{cfop}' incompatível com operação de comércio exterior.",
                            document_type=doc.document_type,
                            layout_version=doc.layout_version,
                            xml_path=f"{item.xml_path}/prod/CFOP",
                            tag="CFOP",
                            found_value=cfop,
                            expected_value=f"{expected_first}xxx",
                            rule_explanation="Operações com o exterior devem utilizar CFOP iniciado por 3 (entrada/importação) ou 7 (saída/exportação).",
                            source={"type": self.metadata.source_type, "reference": self.metadata.source_reference},
                            fiscal_impact="Rejeição SEFAZ 778/779: Informado CFOP de operação interna/interestadual para destinatário no exterior.",
                            suggested_fix=f"Substitua o primeiro dígito do CFOP por '{expected_first}'.",
                            confidence=1.0,
                        )
                    )
                continue

            # 2. Operação dentro do mesmo Estado (Interna)
            if dest_uf and emit_uf == dest_uf:
                expected_first = "5" if is_saida else "1"
                if first_digit != expected_first:
                    suggested_cfop = expected_first + cfop[1:]
                    diagnostics.append(
                        Diagnostic(
                            id=f"FIG-CFOP-001-item-{item.nItem}",
                            severity=Severity.ERROR,
                            category=Category.REFERENCE,
                            rule_id=self.metadata.id,
                            message=f"Item {item.nItem}: CFOP '{cfop}' é interestadual, mas emitente e destinatário pertencem à mesma UF ({emit_uf}).",
                            document_type=doc.document_type,
                            layout_version=doc.layout_version,
                            xml_path=f"{item.xml_path}/prod/CFOP",
                            tag="CFOP",
                            found_value=cfop,
                            expected_value=suggested_cfop,
                            rule_explanation="Operações onde a UF do emitente é idêntica à UF do destinatário devem utilizar CFOP iniciado por 1 (entrada) ou 5 (saída).",
                            source={"type": self.metadata.source_type, "reference": self.metadata.source_reference},
                            fiscal_impact="Rejeição SEFAZ 523: CFOP não é de Operação Interna e UF do emitente é igual à UF do destinatário.",
                            suggested_fix=f"Altere o CFOP para a figura fiscal interna correspondente: '{suggested_cfop}'.",
                            confidence=1.0,
                        )
                    )

            # 3. Operação Interestadual
            elif dest_uf and emit_uf != dest_uf:
                expected_first = "6" if is_saida else "2"
                if first_digit != expected_first:
                    suggested_cfop = expected_first + cfop[1:]
                    diagnostics.append(
                        Diagnostic(
                            id=f"FIG-CFOP-001-item-{item.nItem}",
                            severity=Severity.ERROR,
                            category=Category.REFERENCE,
                            rule_id=self.metadata.id,
                            message=f"Item {item.nItem}: CFOP '{cfop}' é interno, mas emitente ({emit_uf}) e destinatário ({dest_uf}) estão em UFs diferentes.",
                            document_type=doc.document_type,
                            layout_version=doc.layout_version,
                            xml_path=f"{item.xml_path}/prod/CFOP",
                            tag="CFOP",
                            found_value=cfop,
                            expected_value=suggested_cfop,
                            rule_explanation="Operações entre contribuintes de UFs distintas devem utilizar CFOP iniciado por 2 (entrada) ou 6 (saída).",
                            source={"type": self.metadata.source_type, "reference": self.metadata.source_reference},
                            fiscal_impact="Rejeição SEFAZ 522: CFOP de Operação Interna e UF do emitente difere da UF do destinatário.",
                            suggested_fix=f"Altere o CFOP para a figura fiscal interestadual correspondente: '{suggested_cfop}'.",
                            confidence=1.0,
                        )
                    )

        return diagnostics


class FigCFOPNFCeRule(BaseRule):
    """FIG-CFOP-002: Restrição de CFOP para NFC-e (modelo 65)."""

    metadata = RuleMetadata(
        id="FIG-CFOP-002",
        title="Restrição de CFOP para NFC-e (Modelo 65)",
        category=Category.REFERENCE,
        severity=Severity.ERROR,
        document_types=["NFCE"],
        description="A NFC-e destina-se exclusivamente a vendas a consumidor final em operação interna presencial, admitindo apenas CFOPs 5xxx.",
        source_type="manual_sefaz",
        source_reference="MOC NFC-e Anexo I - Regra de Validação I08-20",
    )

    def validate(self, doc: NormalizedDocument, context: Optional[Dict[str, Any]] = None) -> List[Diagnostic]:
        if doc.document_type != "NFCE" and doc.ide.mod != "65":
            return []

        diagnostics = []
        for item in doc.itens:
            cfop = item.CFOP.strip()
            if not cfop.startswith("5"):
                suggested = "5" + cfop[1:] if len(cfop) == 4 else "5102"
                diagnostics.append(
                    Diagnostic(
                        id=f"FIG-CFOP-002-item-{item.nItem}",
                        severity=Severity.ERROR,
                        category=Category.REFERENCE,
                        rule_id=self.metadata.id,
                        message=f"Item {item.nItem}: CFOP '{cfop}' inválido para NFC-e (modelo 65).",
                        document_type=doc.document_type,
                        layout_version=doc.layout_version,
                        xml_path=f"{item.xml_path}/prod/CFOP",
                        tag="CFOP",
                        found_value=cfop,
                        expected_value=suggested,
                        rule_explanation="NFC-e apenas autoriza itens com CFOP do grupo 5 (operação interna ao consumidor final presencial).",
                        source={"type": self.metadata.source_type, "reference": self.metadata.source_reference},
                        fiscal_impact="Rejeição SEFAZ 725: NFC-e com CFOP inválido.",
                        suggested_fix=f"Substitua o CFOP por um código autorizado para NFC-e (ex: '{suggested}').",
                        confidence=1.0,
                    )
                )
        return diagnostics


class FigCSTCRTRule(BaseRule):
    """FIG-CST-001: Compatibilidade entre Regime Tributário (CRT) e CST/CSOSN."""

    metadata = RuleMetadata(
        id="FIG-CST-001",
        title="Compatibilidade entre CRT e CST/CSOSN",
        category=Category.TAXATION,
        severity=Severity.ERROR,
        document_types=["NFE", "NFCE"],
        description="Emitentes optantes pelo Simples Nacional (CRT=1) devem usar CSOSN. Emitentes do Regime Normal (CRT=3) devem usar CST.",
        source_type="ajuste_sinief",
        source_reference="Ajuste SINIEF 07/05 e Convênio S/Nº de 1970 - Tabela CST/CSOSN",
    )

    def validate(self, doc: NormalizedDocument, context: Optional[Dict[str, Any]] = None) -> List[Diagnostic]:
        crt = doc.emit.CRT if doc.emit else None
        if not crt:
            return []

        diagnostics = []
        for item in doc.itens:
            icms = item.icms
            if icms is None:
                continue

            # CRT 1: Simples Nacional -> Exige CSOSN
            if crt == "1":
                if icms.CST is not None and icms.CSOSN is None:
                    suggested_csosn = "102" if icms.CST in ["40", "41", "50"] else "101"
                    diagnostics.append(
                        Diagnostic(
                            id=f"FIG-CST-001-item-{item.nItem}",
                            severity=Severity.ERROR,
                            category=Category.TAXATION,
                            rule_id=self.metadata.id,
                            message=f"Item {item.nItem}: Emitente é optante pelo Simples Nacional (CRT=1), mas informou CST normal '{icms.CST}'.",
                            document_type=doc.document_type,
                            layout_version=doc.layout_version,
                            xml_path=f"{icms.xml_subpath}/CST",
                            tag="CST",
                            found_value=icms.CST,
                            expected_value=f"CSOSN {suggested_csosn} (grupo ICMSSN...)",
                            rule_explanation="Empresas enquadradas no Simples Nacional (CRT=1) devem tributar via CSOSN (Código de Situação da Operação no Simples Nacional).",
                            source={"type": self.metadata.source_type, "reference": self.metadata.source_reference},
                            fiscal_impact="Rejeição SEFAZ 590: Informado CST para emitente do Simples Nacional.",
                            suggested_fix=f"Substitua o grupo de CST normal pelo grupo ICMSSN correspondente com CSOSN '{suggested_csosn}'.",
                            confidence=1.0,
                        )
                    )

            # CRT 3: Regime Normal -> Exige CST
            elif crt == "3":
                if icms.CSOSN is not None and icms.CST is None:
                    suggested_cst = "00" if icms.CSOSN == "101" else "40"
                    diagnostics.append(
                        Diagnostic(
                            id=f"FIG-CST-001-item-{item.nItem}",
                            severity=Severity.ERROR,
                            category=Category.TAXATION,
                            rule_id=self.metadata.id,
                            message=f"Item {item.nItem}: Emitente pertence ao Regime Normal (CRT=3), mas informou CSOSN '{icms.CSOSN}'.",
                            document_type=doc.document_type,
                            layout_version=doc.layout_version,
                            xml_path=f"{icms.xml_subpath}/CSOSN",
                            tag="CSOSN",
                            found_value=icms.CSOSN,
                            expected_value=f"CST {suggested_cst} (grupo ICMS...)",
                            rule_explanation="Empresas do Regime Normal (CRT=3) devem utilizar a Tabela B de CST (00, 10, 20, 40...), vedado o uso de CSOSN.",
                            source={"type": self.metadata.source_type, "reference": self.metadata.source_reference},
                            fiscal_impact="Rejeição SEFAZ 591: Informado CSOSN para emitente do Regime Normal.",
                            suggested_fix=f"Ajuste a figura fiscal para o CST aplicável da Tabela B (ex: CST '{suggested_cst}').",
                            confidence=1.0,
                        )
                    )

        return diagnostics


class FigCSTIsencaoRule(BaseRule):
    """FIG-CST-003: Validação de destaque de ICMS em operações isentas/não tributadas."""

    metadata = RuleMetadata(
        id="FIG-CST-003",
        title="Destaque indevido de ICMS em CST Isento ou Não Tributado",
        category=Category.TAXATION,
        severity=Severity.ERROR,
        document_types=["NFE", "NFCE"],
        description="CST 40 (Isenta), 41 (Não tributada) e 50 (Suspensão) não podem conter valor de ICMS destacado, exceto desoneração.",
        source_type="ajuste_sinief",
        source_reference="Ajuste SINIEF 07/05 - Manual de Orientação do Contribuinte",
    )

    def validate(self, doc: NormalizedDocument, context: Optional[Dict[str, Any]] = None) -> List[Diagnostic]:
        diagnostics = []
        for item in doc.itens:
            icms = item.icms
            if icms is None or icms.CST not in ["40", "41", "50"]:
                continue

            if icms.vICMS and icms.vICMS > 0:
                diagnostics.append(
                    Diagnostic(
                        id=f"FIG-CST-003-item-{item.nItem}",
                        severity=Severity.ERROR,
                        category=Category.TAXATION,
                        rule_id=self.metadata.id,
                        message=f"Item {item.nItem}: CST '{icms.CST}' não permite destaque de ICMS próprio (vICMS={icms.vICMS:.2f}).",
                        document_type=doc.document_type,
                        layout_version=doc.layout_version,
                        xml_path=f"{icms.xml_subpath}/vICMS",
                        tag="vICMS",
                        found_value=f"{icms.vICMS:.2f}",
                        expected_value="0.00 (ou ausente no grupo ICMS40)",
                        rule_explanation="Operações amparadas por isenção, não incidência ou suspensão não recolhem ICMS próprio na saída.",
                        source={"type": self.metadata.source_type, "reference": self.metadata.source_reference},
                        fiscal_impact="Rejeição SEFAZ ou recolhimento indevido de tributo sem base legal.",
                        suggested_fix="Remova o destaque de vICMS ou altere o CST para um enquadramento tributado (ex: CST 00 ou 20).",
                        confidence=1.0,
                    )
                )
        return diagnostics


class FigNCMFormatRule(BaseRule):
    """FIG-NCM-001: Validação do formato e estrutura do NCM."""

    metadata = RuleMetadata(
        id="FIG-NCM-001",
        title="Formato e Validade Estrutural do NCM",
        category=Category.REFERENCE,
        severity=Severity.ERROR,
        document_types=["NFE", "NFCE"],
        description="O NCM (Nomenclatura Comum do Mercosul) deve conter exatamente 8 dígitos numéricos válidos.",
        source_type="nota_tecnica",
        source_reference="Nota Técnica 2014.004 / 2016.002 - Validação de NCM",
    )

    def validate(self, doc: NormalizedDocument, context: Optional[Dict[str, Any]] = None) -> List[Diagnostic]:
        diagnostics = []
        for item in doc.itens:
            ncm = item.NCM.strip() if item.NCM else ""
            clean_ncm = re.sub(r"\D", "", ncm)

            if len(clean_ncm) != 8 or clean_ncm == "00000000":
                # Exceção legal: NCM '00' para serviços tributados pelo ISSQN
                if ncm == "00":
                    continue

                diagnostics.append(
                    Diagnostic(
                        id=f"FIG-NCM-001-item-{item.nItem}",
                        severity=Severity.ERROR,
                        category=Category.REFERENCE,
                        rule_id=self.metadata.id,
                        message=f"Item {item.nItem}: NCM '{ncm}' possui formato inválido (esperado código com 8 dígitos numéricos).",
                        document_type=doc.document_type,
                        layout_version=doc.layout_version,
                        xml_path=f"{item.xml_path}/prod/NCM",
                        tag="NCM",
                        found_value=ncm,
                        expected_value="8 dígitos numéricos (ex: 84713012)",
                        rule_explanation="A NCM deve ser informada de acordo com a Tarifa Externa Comum (TEC) da CAMEX, com 8 posições numéricas.",
                        source={"type": self.metadata.source_type, "reference": self.metadata.source_reference},
                        fiscal_impact="Rejeição SEFAZ 778/779 ou autuação por erro na classificação fiscal de mercadorias.",
                        suggested_fix="Consulte a tabela oficial da TEC/TIPI e informe a classificação NCM de 8 dígitos adequada ao produto.",
                        confidence=1.0,
                    )
                )
        return diagnostics


class FigChaveAcessoRule(BaseRule):
    """FIG-CHAVE-001: Validação do Dígito Verificador da Chave de Acesso."""

    metadata = RuleMetadata(
        id="FIG-CHAVE-001",
        title="Dígito Verificador e Integridade da Chave de Acesso",
        category=Category.REFERENCE,
        severity=Severity.ERROR,
        document_types=["NFE", "NFCE", "CTE"],
        description="Valida a formação dos 44 dígitos da chave de acesso e o dígito verificador calculado via Módulo 11.",
        source_type="manual_sefaz",
        source_reference="MOC Geral - Chave de Acesso de Documentos Fiscais Eletrônicos",
    )

    def validate(self, doc: NormalizedDocument, context: Optional[Dict[str, Any]] = None) -> List[Diagnostic]:
        if not doc.chave_acesso:
            return []

        clean_key = re.sub(r"\D", "", doc.chave_acesso)
        is_valid, error_msg = AccessKeyValidator.validate_key(clean_key)

        if not is_valid:
            return [
                Diagnostic(
                    id="FIG-CHAVE-001-DV",
                    severity=Severity.ERROR,
                    category=Category.REFERENCE,
                    rule_id=self.metadata.id,
                    message=f"Chave de acesso com dígito verificador ou extensão incorreta: {error_msg}",
                    document_type=doc.document_type,
                    layout_version=doc.layout_version,
                    xml_path=f"{doc.raw_root_prefix}/@Id",
                    tag="Id",
                    found_value=f"***{clean_key[-6:]}" if len(clean_key) >= 6 else clean_key,
                    expected_value="Chave de 44 dígitos com DV módulo 11 válido",
                    rule_explanation="O 44º dígito da chave de acesso é calculado com o algoritmo Módulo 11 sobre os 43 dígitos precedentes.",
                    source={"type": self.metadata.source_type, "reference": self.metadata.source_reference},
                    fiscal_impact="Rejeição SEFAZ 253: Rejeição: Digito Verificador da chave de acesso da NF-e invalido.",
                    suggested_fix="Recalcule o dígito verificador com o peso ponderado de 2 a 9 da direita para a esquerda.",
                    confidence=1.0,
                )
            ]
        return []

