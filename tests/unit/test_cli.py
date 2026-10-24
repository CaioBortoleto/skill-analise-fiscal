"""Testes da interface de linha de comando (CLI)."""

import io
import sys
import unittest
from contextlib import redirect_stdout

from src.fiscal_xml_validator.cli import main


class TestCLI(unittest.TestCase):

    def test_cli_validate_valid_file(self):
        f = io.StringIO()
        with redirect_stdout(f):
            code = main(["validate", "tests/fixtures/synthetic/nfe/valid/nfe_valid.xml"])
        output = f.getvalue()
        self.assertEqual(code, 0)
        self.assertIn("Nenhuma inconsistência foi encontrada", output)

    def test_cli_validate_invalid_file(self):
        f = io.StringIO()
        with redirect_stdout(f):
            code = main(["validate", "tests/fixtures/synthetic/nfe/invalid/nfe_cfop_mismatch.xml"])
        output = f.getvalue()
        self.assertEqual(code, 1)
        self.assertIn("FIG-CFOP-001", output)

    def test_cli_rules_list(self):
        f = io.StringIO()
        with redirect_stdout(f):
            code = main(["rules", "list"])
        output = f.getvalue()
        self.assertEqual(code, 0)
        self.assertIn("TAX-CALC-001", output)
        self.assertIn("FIG-CFOP-001", output)

    def test_cli_verify_key(self):
        f = io.StringIO()
        with redirect_stdout(f):
            code = main(["verify-key", "35241000000000000191550010000000011000000017"])
        output = f.getvalue()
        self.assertEqual(code, 0)
        self.assertIn("dígito verificador válido", output)


if __name__ == "__main__":
    unittest.main()

