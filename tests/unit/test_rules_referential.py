"""Testes unitários para regras de figuras fiscais (CFOP, CST x CRT, NCM)."""

import unittest
from pathlib import Path

from src.fiscal_xml_validator.ingestion import DocumentIngestion
from src.fiscal_xml_validator.parsers.nfe_parser import NFeParser
from src.fiscal_xml_validator.rules.referential import FigCFOPUFRule, FigCSTCRTRule, FigNCMFormatRule


class TestRulesReferential(unittest.TestCase):

    def test_cfop_interstate_mismatch(self):
        fixture_path = Path("tests/fixtures/synthetic/nfe/invalid/nfe_cfop_mismatch.xml")
        ingested = DocumentIngestion.ingest_file(fixture_path)
        doc = NFeParser.parse(ingested.root_element)

        rule = FigCFOPUFRule()
        diagnostics = rule.validate(doc)

        self.assertEqual(len(diagnostics), 1)
        diag = diagnostics[0]
        self.assertEqual(diag.rule_id, "FIG-CFOP-001")
        self.assertEqual(diag.found_value, "6102")
        self.assertEqual(diag.expected_value, "5102")
        self.assertIn("/prod/CFOP", diag.xml_path)

    def test_cst_crt_conflict(self):
        fixture_path = Path("tests/fixtures/synthetic/nfe/invalid/nfe_cst_crt_conflict.xml")
        ingested = DocumentIngestion.ingest_file(fixture_path)
        doc = NFeParser.parse(ingested.root_element)

        rule = FigCSTCRTRule()
        diagnostics = rule.validate(doc)

        self.assertEqual(len(diagnostics), 1)
        diag = diagnostics[0]
        self.assertEqual(diag.rule_id, "FIG-CST-001")
        self.assertEqual(diag.found_value, "00")
        self.assertIn("CSOSN", diag.expected_value or "")


if __name__ == "__main__":
    unittest.main()

