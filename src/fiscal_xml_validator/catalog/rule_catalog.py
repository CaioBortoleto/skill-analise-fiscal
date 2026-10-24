"""Catálogo estruturado de regras fiscais com rastreabilidade normativa.

Conforme seções 7.1 e 7.2 do AGENTS.md.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

from ..models import Category, Severity


@dataclass
class RuleMetadata:
    """Metadados de uma regra fiscal no catálogo oficial."""
    id: str
    title: str
    category: Category
    severity: Severity
    document_types: List[str]
    description: str
    source_type: str = "internal_rule"  # "internal_rule", "nota_tecnica", "ajuste_sinief", "manual_sefaz"
    source_reference: Optional[str] = None
    effective_from: Optional[str] = None
    effective_until: Optional[str] = None
    layout_versions: List[str] = field(default_factory=list)
    requires_context: bool = False
    status: str = "active"

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["category"] = self.category.value
        d["severity"] = self.severity.value
        return d


class RuleCatalog:
    """Repositório de regras com consulta e filtros."""

    _registry: Dict[str, RuleMetadata] = {}

    @classmethod
    def register(cls, meta: RuleMetadata) -> None:
        cls._registry[meta.id] = meta

    @classmethod
    def get(cls, rule_id: str) -> Optional[RuleMetadata]:
        return cls._registry.get(rule_id)

    @classmethod
    def list_rules(
        cls,
        document_type: Optional[str] = None,
        category: Optional[Category] = None,
        severity: Optional[Severity] = None,
    ) -> List[RuleMetadata]:
        results = []
        for meta in cls._registry.values():
            if document_type and meta.document_types and document_type not in meta.document_types:
                continue
            if category and meta.category != category:
                continue
            if severity and meta.severity != severity:
                continue
            results.append(meta)
        return sorted(results, key=lambda x: x.id)

    @classmethod
    def clear(cls) -> None:
        cls._registry.clear()

