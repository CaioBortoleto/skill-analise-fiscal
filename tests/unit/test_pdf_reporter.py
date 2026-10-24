"""Testes unitários para o gerador de relatórios em PDF."""

import unittest
from pathlib import Path

from src.fiscal_xml_validator.reporting.pdf_reporter import PDFReporter
from src.fiscal_xml_validator.validator import FiscalValidator


class TestPDFReporter(unittest.TestCase):

    def test_generate_pdf_report(self):
        fixture_path = Path("tests/fixtures/synthetic/nfe/invalid/nfe_cfop_mismatch.xml")
        validator = FiscalValidator()
        report = validator.validate_file(fixture_path, generate_fix=True)

        out_pdf = Path("tests/fixtures/synthetic/nfe/invalid/test_output.pdf")
        try:
            generated = PDFReporter.generate_pdf(report, out_pdf)
            self.assertTrue(out_pdf.exists())
            self.assertGreater(out_pdf.stat().st_size, 1000)
            self.assertEqual(generated, str(out_pdf.resolve()))
        finally:
            if out_pdf.exists():
                out_pdf.unlink()


if __name__ == "__main__":
    unittest.main()

