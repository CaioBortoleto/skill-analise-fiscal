"""Testes unitários para o motor de sugestão de correção fiscal e diffs."""

import unittest
from pathlib import Path

from src.fiscal_xml_validator.corrector.fiscal_fixer import FiscalFixer
from src.fiscal_xml_validator.ingestion import DocumentIngestion
from src.fiscal_xml_validator.parsers.nfe_parser import NFeParser
from src.fiscal_xml_validator.rules.arithmetic import TaxCalcICMSRule
from src.fiscal_xml_validator.rules.referential import FigCFOPUFRule


class TestFiscalFixer(unittest.TestCase):

    def test_propose_fix_for_icms_arithmetic(self):
        fixture_path = Path("tests/fixtures/synthetic/nfe/invalid/nfe_icms_arithmetic.xml")
        ingested = DocumentIngestion.ingest_file(fixture_path)
        doc = NFeParser.parse(ingested.root_element)

        diagnostics = TaxCalcICMSRule().validate(doc)
        self.assertEqual(len(diagnostics), 1)

        result = FiscalFixer.propose_fixes(ingested, diagnostics)
        self.assertTrue(result.has_changes)
        self.assertEqual(len(result.proposals), 1)

        proposal = result.proposals[0]
        self.assertEqual(proposal.tag, "vICMS")
        self.assertEqual(proposal.original_value, "12.00")
        self.assertEqual(proposal.proposed_value, "18.00")

        # Verifica formato do diff
        self.assertIn("--- original.xml", result.diff)
        self.assertIn("+++ sugestao_correcao_fiscal.xml", result.diff)
        self.assertIn("-            <vICMS>12.00</vICMS>", result.diff)
        self.assertIn("+            <vICMS>18.00</vICMS>", result.diff)

        # Garante que o XML original não foi alterado
        with open(fixture_path, "r", encoding="utf-8") as f:
            original_content = f.read()
        self.assertIn("<vICMS>12.00</vICMS>", original_content)

    def test_propose_fix_for_cfop_mismatch(self):
        fixture_path = Path("tests/fixtures/synthetic/nfe/invalid/nfe_cfop_mismatch.xml")
        ingested = DocumentIngestion.ingest_file(fixture_path)
        doc = NFeParser.parse(ingested.root_element)

        diagnostics = FigCFOPUFRule().validate(doc)
        self.assertEqual(len(diagnostics), 1)

        result = FiscalFixer.propose_fixes(ingested, diagnostics)
        self.assertTrue(result.has_changes)
        self.assertEqual(result.proposals[0].tag, "CFOP")
        self.assertEqual(result.proposals[0].original_value, "6102")
        self.assertEqual(result.proposals[0].proposed_value, "5102")


if __name__ == "__main__":
    unittest.main()

