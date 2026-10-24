"""Interface base para regras de validação fiscal."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from ..catalog.rule_catalog import RuleCatalog, RuleMetadata
from ..models import Diagnostic
from ..normalization.models import NormalizedDocument


class BaseRule(ABC):
    """Classe base abstrata para todas as regras de auditoria fiscal."""

    metadata: RuleMetadata

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if hasattr(cls, "metadata"):
            RuleCatalog.register(cls.metadata)

    @abstractmethod
    def validate(
        self,
        doc: NormalizedDocument,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Diagnostic]:
        """Executa a validação e retorna a lista de diagnósticos identificados."""
        pass

