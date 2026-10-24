"""Modelos de dados fundamentais para diagnósticos e relatórios fiscais.

Em estrita conformidade com a seção 2.3 e 12.2 do AGENTS.md.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class DocumentOriginType(str, Enum):
    """Classificação da origem do documento (Seção 5.3 do AGENTS.md)."""
    SYNTHETIC = "synthetic"
    USER_PROVIDED = "user_provided"
    AUTHORIZED_REMOTE = "authorized_remote"
    UNKNOWN = "unknown"


class Severity(str, Enum):
    """Níveis de gravidade do diagnóstico."""
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class Category(str, Enum):
    """Categorias das ocorrências de validação."""
    STRUCTURE = "structure"
    ARITHMETIC = "arithmetic"
    TAXATION = "taxation"
    REFERENCE = "reference"
    SECURITY = "security"


@dataclass
class DocumentOrigin:
    """Metadados de procedência do documento."""
    type: DocumentOriginType
    label: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.value,
            "label": self.label,
        }


@dataclass
class Diagnostic:
    """Diagnóstico estruturado para cada ocorrência encontrada no XML.

    Campos obrigatórios e opcionais conforme Tabela da Seção 2.3 do AGENTS.md.
    """
    id: str
    severity: Severity
    category: Category
    rule_id: str
    message: str
    xml_path: str
    tag: str
    rule_explanation: str
    fiscal_impact: str
    suggested_fix: str
    document_type: Optional[str] = None
    layout_version: Optional[str] = None
    found_value: Optional[str] = None
    expected_value: Optional[str] = None
    source: Dict[str, Any] = field(default_factory=lambda: {"type": "internal_rule", "reference": None})
    confidence: Optional[float] = 1.0
    limitations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "rule_id": self.rule_id,
            "severity": self.severity.value,
            "category": self.category.value,
            "message": self.message,
            "document_type": self.document_type,
            "layout_version": self.layout_version,
            "xml_path": self.xml_path,
            "tag": self.tag,
            "found_value": self.found_value,
            "expected_value": self.expected_value,
            "rule_explanation": self.rule_explanation,
            "source": self.source,
            "fiscal_impact": self.fiscal_impact,
            "suggested_fix": self.suggested_fix,
            "confidence": self.confidence,
            "limitations": self.limitations,
        }


@dataclass
class ValidationSummary:
    """Sumário quantitativo dos diagnósticos."""
    status: str
    errors: int
    warnings: int
    infos: int
    critical: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "critical": self.critical,
            "errors": self.errors,
            "warnings": self.warnings,
            "infos": self.infos,
        }


@dataclass
class FixProposal:
    """Proposta atômica de correção de uma figura fiscal."""
    xml_path: str
    tag: str
    original_value: str
    proposed_value: str
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class FixResult:
    """Resultado da geração de proposta de correção experimental.

    Conforme seção 3 do AGENTS.md: nunca sobrescreve o original e
    apresenta as alterações em formato diff para revisão humana.
    """
    has_changes: bool
    proposals: List[FixProposal] = field(default_factory=list)
    diff: str = ""
    suggested_xml: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "has_changes": self.has_changes,
            "proposals": [p.to_dict() for p in self.proposals],
            "diff": self.diff,
        }


@dataclass
class ValidationReport:
    """Contrato de relatório final gerado pelo motor fiscal."""
    document: Dict[str, Any]
    summary: ValidationSummary
    diagnostics: List[Diagnostic]
    report_version: str = "1.0"
    fix_result: Optional[FixResult] = None
    notices: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "report_version": self.report_version,
            "document": self.document,
            "summary": self.summary.to_dict(),
            "diagnostics": [d.to_dict() for d in self.diagnostics],
            "notices": self.notices,
        }
        if self.fix_result:
            data["fix_result"] = self.fix_result.to_dict()
        return data

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

