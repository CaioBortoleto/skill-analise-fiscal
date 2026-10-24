"""Testes de segurança: proteção contra XXE, limites de tamanho e mascaramento."""

import unittest
from pathlib import Path

from src.fiscal_xml_validator.security import DataMasker, SafeXMLParser, SecurityException


class TestSecurity(unittest.TestCase):

    def test_xxe_payload_is_blocked(self):
        fixture_path = Path("tests/fixtures/synthetic/security/xxe_attack.xml")
        with open(fixture_path, "rb") as f:
            content = f.read()

        with self.assertRaises(SecurityException) as ctx:
            SafeXMLParser.parse_string(content)
        self.assertIn("XXE", str(ctx.exception))

    def test_size_limit_exceeded(self):
        huge_bytes = b"<a>" + b" " * 1000 + b"</a>"
        with self.assertRaises(SecurityException):
            SafeXMLParser.parse_string(huge_bytes, max_bytes=500)

    def test_mask_access_key(self):
        valid_key = "35241000000000000191550010000000011000000017"
        masked = DataMasker.mask_access_key(valid_key)
        self.assertEqual(masked, "3524...0017 (mascarada)")
        self.assertNotIn("000000000191", masked)

    def test_mask_cpf(self):
        cpf = "12345678901"
        masked = DataMasker.mask_cpf(cpf)
        self.assertEqual(masked, "***.456.789-**")

    def test_mask_cnpj(self):
        cnpj = "00000000000191"
        masked = DataMasker.mask_cnpj(cnpj)
        self.assertEqual(masked, "00.***.***/0001-91")


if __name__ == "__main__":
    unittest.main()

