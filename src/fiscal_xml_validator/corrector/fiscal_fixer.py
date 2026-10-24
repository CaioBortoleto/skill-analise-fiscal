"""Mecanismo experimental para sugestão de correção de figuras fiscais e geração de diffs.

Conforme seção 3 do AGENTS.md:
- Nunca altera ou sobrescreve silenciosamente o arquivo original.
- Gera propostas de correção baseadas em diagnósticos determinísticos.
- Produz diff unificado legível para conferência humana prévia.
"""

from __future__ import annotations

import copy
import difflib
import re
from typing import List, Optional, Tuple
import xml.etree.ElementTree as ET

from ..ingestion import DocumentIngestion, IngestedDocument
from ..models import Diagnostic, FixProposal, FixResult


class FiscalFixer:
    """Gera sugestões de correção de figuras fiscais sem alterar o XML original."""

    @classmethod
    def _find_element_by_path(cls, root: ET.Element, xml_path: str, tag: str) -> Optional[ET.Element]:
        """Localiza o elemento alvo a partir do caminho estrutural."""
        # Se for atributo (ex: @Id)
        if tag.startswith("@"):
            return None

        # Converte caminho como /nfeProc/NFe/infNFe/det[1]/imposto/ICMS/ICMS00/vICMS
        parts = [p for p in xml_path.split("/") if p]
        curr = root

        # Se a raiz estiver na primeira parte do caminho, pula
        root_tag = DocumentIngestion.extract_clean_tag(curr.tag)
        if parts and parts[0] == root_tag:
            parts = parts[1:]

        for part in parts:
            # Verifica índice, ex: det[1]
            match = re.match(r"^([^\[]+)(?:\[(\d+)\])?$", part)
            if not match:
                return None
            target_name, idx_str = match.groups()
            idx = int(idx_str) if idx_str else 1

            matched_children = [
                c for c in curr
                if DocumentIngestion.extract_clean_tag(c.tag) == target_name
            ]
            if len(matched_children) < idx:
                return None
            curr = matched_children[idx - 1]

        if DocumentIngestion.extract_clean_tag(curr.tag) == tag:
            return curr
        return None

    @classmethod
    def propose_fixes(
        cls,
        doc: IngestedDocument,
        diagnostics: List[Diagnostic],
    ) -> FixResult:
        """Analisa os diagnósticos e gera uma árvore corrigida e um diff unificado."""
        # Trabalha sempre em uma cópia profunda (imutabilidade do original)
        cloned_root = copy.deepcopy(doc.root_element)
        proposals: List[FixProposal] = []

        for diag in diagnostics:
            # Apenas propõe correções para casos com expected_value definido e não-genérico
            if not diag.expected_value or "xxx" in diag.expected_value or "grupo" in diag.expected_value:
                continue

            target_elem = cls._find_element_by_path(cloned_root, diag.xml_path, diag.tag)
            if target_elem is not None:
                original_text = (target_elem.text or "").strip()
                proposed_text = diag.expected_value.strip()

                if original_text != proposed_text:
                    target_elem.text = proposed_text
                    proposals.append(
                        FixProposal(
                            xml_path=diag.xml_path,
                            tag=diag.tag,
                            original_value=original_text,
                            proposed_value=proposed_text,
                            reason=f"[{diag.rule_id}] {diag.message}",
                        )
                    )

        if not proposals:
            return FixResult(has_changes=False, proposals=[], diff="", suggested_xml=doc.raw_text)

        # Registra namespace padrão da SEFAZ para evitar prefixos ns0: artificiais
        if doc.namespace:
            ET.register_namespace("", doc.namespace)
        else:
            ET.register_namespace("", "http://www.portalfiscal.inf.br/nfe")

        # Serializa o XML sugerido com indentação adequada
        ET.indent(cloned_root, space="  ")
        raw_xml = ET.tostring(cloned_root, encoding="utf-8").decode("utf-8")
        suggested_xml = '<?xml version="1.0" encoding="UTF-8"?>\n' + raw_xml

        # Gera diff unificado
        orig_lines = doc.raw_text.splitlines(keepends=True)
        suggested_lines = suggested_xml.splitlines(keepends=True)
        diff_lines = list(
            difflib.unified_diff(
                orig_lines,
                suggested_lines,
                fromfile="original.xml",
                tofile="sugestao_correcao_fiscal.xml",
                n=3,
            )
        )
        diff_text = "".join(diff_lines)

        return FixResult(
            has_changes=True,
            proposals=proposals,
            diff=diff_text,
            suggested_xml=suggested_xml,
        )
