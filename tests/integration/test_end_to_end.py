"""Testes de ponta a ponta (E2E) para validação completa e relatórios."""

import json
import unittest
from pathlib import Path

from src.fiscal_xml_validator.reporting.console_reporter import ConsoleReporter
from src.fiscal_xml_validator.reporting.markdown_reporter import MarkdownReporter
from src.fiscal_xml_validator.validator import FiscalValidator


class TestEndToEnd(unittest.TestCase):

    def setUp(self):
        self.validator = FiscalValidator()

    def test_valid_document_pipeline(self):
        path = Path("tests/fixtures/synthetic/nfe/valid/nfe_valid.xml")
        report = self.validator.validate_file(path)

        self.assertEqual(report.summary.status, "valid")
        self.assertEqual(report.summary.errors, 0)
        self.assertEqual(len(report.diagnostics), 0)

        # Testa exportação JSON
        json_str = report.to_json()
        data = json.loads(json_str)
        self.assertEqual(data["summary"]["status"], "valid")

        # Testa relatório Console e Markdown
        text = ConsoleReporter.format_report(report)
        self.assertIn("Nenhuma inconsistência foi encontrada", text)

        md = MarkdownReporter.format_report(report)
        self.assertIn("Nenhuma inconsistência foi encontrada", md)

    def test_invalid_document_pipeline_with_diff(self):
        path = Path("tests/fixtures/synthetic/nfe/invalid/nfe_icms_arithmetic.xml")
        report = self.validator.validate_file(path, generate_fix=True)

        self.assertEqual(report.summary.status, "issues_found")
        self.assertGreater(report.summary.errors, 0)
        self.assertIsNotNone(report.fix_result)
        self.assertTrue(report.fix_result.has_changes)

        # Testa saída console com diff
        text = ConsoleReporter.format_report(report, show_diff=True)
        self.assertIn("PROPOSTA EXPERIMENTAL DE CORREÇÃO", text)
        self.assertIn("TAX-CALC-001", text)


if __name__ == "__main__":
    unittest.main()

