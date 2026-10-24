"""Testes unitários para regras aritméticas e somatórios."""

import unittest
from pathlib import Path

from src.fiscal_xml_validator.ingestion import DocumentIngestion
from src.fiscal_xml_validator.parsers.nfe_parser import NFeParser
from src.fiscal_xml_validator.rules.arithmetic import TaxCalcICMSRule, TaxTotICMSRule, TaxTotNFRule, TaxTotProdRule


class TestRulesArithmetic(unittest.TestCase):

    def test_icms_arithmetic_divergence(self):
        fixture_path = Path("tests/fixtures/synthetic/nfe/invalid/nfe_icms_arithmetic.xml")
        ingested = DocumentIngestion.ingest_file(fixture_path)
        doc = NFeParser.parse(ingested.root_element)

        rule = TaxCalcICMSRule()
        diagnostics = rule.validate(doc)

        self.assertEqual(len(diagnostics), 1)
        diag = diagnostics[0]
        self.assertEqual(diag.rule_id, "TAX-CALC-001")
        self.assertEqual(diag.found_value, "12.00")
        self.assertEqual(diag.expected_value, "18.00")
        self.assertIn("/vICMS", diag.xml_path)

    def test_total_divergence(self):
        fixture_path = Path("tests/fixtures/synthetic/nfe/invalid/nfe_total_divergence.xml")
        ingested = DocumentIngestion.ingest_file(fixture_path)
        doc = NFeParser.parse(ingested.root_element)

        rule_prod = TaxTotProdRule()
        diag_prod = rule_prod.validate(doc)
        self.assertEqual(len(diag_prod), 1)
        self.assertEqual(diag_prod[0].rule_id, "TAX-TOT-001")
        self.assertEqual(diag_prod[0].found_value, "150.00")
        self.assertEqual(diag_prod[0].expected_value, "100.00")

        rule_nf = TaxTotNFRule()
        diag_nf = rule_nf.validate(doc)
        self.assertEqual(len(diag_nf), 1)
        self.assertEqual(diag_nf[0].rule_id, "TAX-TOT-003")


if __name__ == "__main__":
    unittest.main()

