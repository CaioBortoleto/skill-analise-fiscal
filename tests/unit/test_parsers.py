"""Testes unitários para o parser de NF-e."""

import unittest
from pathlib import Path

from src.fiscal_xml_validator.ingestion import DocumentIngestion
from src.fiscal_xml_validator.parsers.nfe_parser import NFeParser


class TestParsers(unittest.TestCase):

    def test_parse_valid_nfe(self):
        fixture_path = Path("tests/fixtures/synthetic/nfe/valid/nfe_valid.xml")
        ingested = DocumentIngestion.ingest_file(fixture_path)
        doc = NFeParser.parse(ingested.root_element, doc_type="NFE")

        self.assertEqual(doc.document_type, "NFE")
        self.assertEqual(doc.ide.mod, "55")
        self.assertEqual(doc.emit.UF, "SP")
        self.assertEqual(doc.emit.CRT, "3")
        self.assertIsNotNone(doc.dest)
        self.assertEqual(doc.dest.UF, "SP")

        self.assertEqual(len(doc.itens), 1)
        item = doc.itens[0]
        self.assertEqual(item.cProd, "PROD-001")
        self.assertEqual(item.CFOP, "5102")
        self.assertEqual(item.NCM, "84713012")
        self.assertIsNotNone(item.icms)
        self.assertEqual(item.icms.CST, "00")
        self.assertEqual(str(item.icms.vBC), "100.00")
        self.assertEqual(str(item.icms.pICMS), "18.00")
        self.assertEqual(str(item.icms.vICMS), "18.00")

        self.assertIsNotNone(doc.total)
        self.assertEqual(str(doc.total.vProd), "100.00")
        self.assertEqual(str(doc.total.vICMS), "18.00")
        self.assertEqual(str(doc.total.vNF), "100.00")


if __name__ == "__main__":
    unittest.main()

