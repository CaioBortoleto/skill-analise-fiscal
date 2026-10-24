"""Orquestrador principal de validação fiscal e correção de documentos XML."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from .corrector.fiscal_fixer import FiscalFixer
from .ingestion import DocumentIngestion, IngestedDocument
from .models import (
    Category,
    Diagnostic,
    DocumentOrigin,
    DocumentOriginType,
    FixResult,
    Severity,
    ValidationReport,
    ValidationSummary,
)
from .parsers.nfe_parser import NFeParser
from .rules import RulesEngine
from .security import DataMasker


class FiscalValidator:
    """Motor unificado de validação, auditoria e sugestão de correção fiscal."""

    def __init__(self, rules_engine: Optional[RulesEngine] = None):
        self.engine = rules_engine or RulesEngine()

    def validate_document(
        self,
        ingested: IngestedDocument,
        generate_fix: bool = True,
        context: Optional[Dict[str, Any]] = None,
    ) -> ValidationReport:
        """Executa o pipeline completo sobre um documento ingerido."""
        # Se for desconhecido ou não suportado
        if ingested.document_type not in ["NFE", "NFCE"]:
            summary = ValidationSummary(
                status="unsupported_document",
                critical=0,
                errors=1,
                warnings=0,
                infos=0,
            )
            diag = Diagnostic(
                id="DOC-UNSUPPORTED",
                severity=Severity.ERROR,
                category=Category.STRUCTURE,  # type: ignore
                rule_id="DOC-UNSUPPORTED",
                message=f"Tipo de documento '{ingested.document_type}' ou layout não suportado nesta versão.",
                document_type=ingested.document_type,
                layout_version=ingested.layout_version,
                xml_path="/",
                tag=DocumentIngestion.extract_clean_tag(ingested.root_element.tag),
                rule_explanation="O validador atualmente suporta NF-e (mod 55) e NFC-e (mod 65) no layout 4.00.",
                fiscal_impact="Não é possível realizar a conferência fiscal.",
                suggested_fix="Verifique se o documento é uma NF-e ou NFC-e válida.",
            )
            return ValidationReport(
                document={
                    "origin": ingested.origin.to_dict(),
                    "type": ingested.document_type,
                    "layout_version": ingested.layout_version,
                    "access_key_masked": DataMasker.mask_access_key(ingested.access_key),
                },
                summary=summary,
                diagnostics=[diag],
            )

        # Parsing estrutural
        normalized = NFeParser.parse(
            ingested.root_element,
            doc_type=ingested.document_type,
            layout_version=ingested.layout_version,
        )

        # Execução das regras fiscais e aritméticas
        diagnostics = self.engine.execute(normalized, context=context)

        # Contagem e sumário
        errors = sum(1 for d in diagnostics if d.severity == Severity.ERROR)
        warnings = sum(1 for d in diagnostics if d.severity == Severity.WARNING)
        infos = sum(1 for d in diagnostics if d.severity == Severity.INFO)
        critical = sum(1 for d in diagnostics if d.severity == Severity.CRITICAL)

        status = "valid" if (errors == 0 and critical == 0) else "issues_found"
        summary = ValidationSummary(
            status=status,
            critical=critical,
            errors=errors,
            warnings=warnings,
            infos=infos,
        )

        # Proposta experimental de correção (Diff)
        fix_result = None
        if generate_fix and (errors > 0 or warnings > 0):
            fix_result = FiscalFixer.propose_fixes(ingested, diagnostics)

        return ValidationReport(
            document={
                "origin": ingested.origin.to_dict(),
                "type": ingested.document_type,
                "model": normalized.ide.mod,
                "layout_version": normalized.layout_version,
                "access_key_masked": DataMasker.mask_access_key(ingested.access_key),
                "file_path": ingested.file_path,
            },
            summary=summary,
            diagnostics=diagnostics,
            fix_result=fix_result,
        )

    def validate_file(
        self,
        file_path: str | Path,
        generate_fix: bool = True,
        context: Optional[Dict[str, Any]] = None,
    ) -> ValidationReport:
        """Lê e valida um arquivo XML a partir do caminho no disco."""
        ingested = DocumentIngestion.ingest_file(file_path)
        return self.validate_document(ingested, generate_fix=generate_fix, context=context)

    def validate_xml(
        self,
        xml_content: str | bytes,
        file_path: Optional[str] = None,
        generate_fix: bool = True,
        context: Optional[Dict[str, Any]] = None,
    ) -> ValidationReport:
        """Valida conteúdo XML fornecido em memória (string ou bytes)."""
        raw_bytes = xml_content.encode("utf-8") if isinstance(xml_content, str) else xml_content
        ingested = DocumentIngestion.ingest_bytes(raw_bytes, file_path=file_path)
        return self.validate_document(ingested, generate_fix=generate_fix, context=context)

    def validate_directory(
        self,
        dir_path: str | Path,
        recursive: bool = True,
        generate_fix: bool = True,
    ) -> List[ValidationReport]:
        """Processa em lote todos os XMLs de uma pasta."""
        path = Path(dir_path)
        if not path.is_dir():
            raise NotADirectoryError(f"Caminho não é um diretório: {path}")

        pattern = "**/*.xml" if recursive else "*.xml"
        reports = []
        for file in path.glob(pattern):
            if file.is_file():
                try:
                    rep = self.validate_file(file, generate_fix=generate_fix)
                    reports.append(rep)
                except Exception as e:
                    # Registra falha de leitura individual sem parar o lote
                    rep = ValidationReport(
                        document={
                            "origin": {"type": "unknown", "label": "Erro de leitura"},
                            "type": "UNKNOWN",
                            "file_path": str(file),
                        },
                        summary=ValidationSummary(status="read_error", critical=1, errors=0, warnings=0, infos=0),
                        diagnostics=[
                            Diagnostic(
                                id="INGEST-ERR",
                                severity=Severity.CRITICAL,
                                category=Category.STRUCTURE,  # type: ignore
                                rule_id="INGEST-ERR",
                                message=f"Falha ao ingerir arquivo: {str(e)}",
                                xml_path=str(file),
                                tag="",
                                rule_explanation="O arquivo não pôde ser lido ou analisado com segurança.",
                                fiscal_impact="Arquivo ignorado na auditoria.",
                                suggested_fix="Verifique integridade e permissões do arquivo.",
                            )
                        ],
                    )
                    reports.append(rep)
        return reports
