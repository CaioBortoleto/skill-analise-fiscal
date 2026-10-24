"""fiscal-xml-validator: Validador e auditor fiscal de XMLs brasileiros (NF-e, NFC-e, CT-e).

Diagnóstico explicável e propostas de correção para inconsistências em tributos,
CFOP, CST/CSOSN, NCM, bases, alíquotas e totais.
"""

from .catalog.rule_catalog import RuleCatalog, RuleMetadata
from .corrector.fiscal_fixer import FiscalFixer
from .ingestion import AccessKeyValidator, DocumentIngestion, IngestedDocument
from .models import (
    Category,
    Diagnostic,
    DocumentOrigin,
    DocumentOriginType,
    FixProposal,
    FixResult,
    Severity,
    ValidationReport,
    ValidationSummary,
)
from .reporting import ConsoleReporter, MarkdownReporter, PDFReporter
from .security import DataMasker, SafeXMLParser, SecurityException
from .validator import FiscalValidator

__version__ = "0.1.0"

__all__ = [
    "FiscalValidator",
    "FiscalFixer",
    "ValidationReport",
    "ValidationSummary",
    "Diagnostic",
    "DocumentOrigin",
    "DocumentOriginType",
    "Severity",
    "Category",
    "FixProposal",
    "FixResult",
    "ConsoleReporter",
    "MarkdownReporter",
    "PDFReporter",
    "RuleCatalog",
    "RuleMetadata",
    "SafeXMLParser",
    "DataMasker",
    "SecurityException",
    "DocumentIngestion",
    "IngestedDocument",
    "AccessKeyValidator",
]

