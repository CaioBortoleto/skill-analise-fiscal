"""Testes de ingestão, detecção de origem e validação de chaves de acesso."""

import unittest
from pathlib import Path

from src.fiscal_xml_validator.ingestion import AccessKeyValidator, DocumentIngestion
from src.fiscal_xml_validator.models import DocumentOriginType


class TestIngestion(unittest.TestCase):

    def test_detect_synthetic_origin(self):
        sample = "<nfe><!-- FICTÍCIO: teste didático --></nfe>"
        origin = DocumentIngestion.detect_origin(sample)
        self.assertEqual(origin.type, DocumentOriginType.SYNTHETIC)

    def test_detect_user_provided_origin(self):
        sample = "<nfe><infNFe></infNFe></nfe>"
        origin = DocumentIngestion.detect_origin(sample, file_path="minha_nota.xml")
        self.assertEqual(origin.type, DocumentOriginType.USER_PROVIDED)

    def test_access_key_dv_calculation(self):
        # 3524100000000000019155001000000001100000001 -> DV = 7
        key_43 = "3524100000000000019155001000000001100000001"
        dv = AccessKeyValidator.calculate_dv(key_43)
        self.assertEqual(dv, 7)

    def test_validate_valid_key(self):
        valid_key = "35241000000000000191550010000000011000000017"
        is_valid, msg = AccessKeyValidator.validate_key(valid_key)
        self.assertTrue(is_valid)
        self.assertIsNone(msg)

    def test_validate_invalid_key_length(self):
        invalid_len = "3524100000000000019155001"
        is_valid, msg = AccessKeyValidator.validate_key(invalid_len)
        self.assertFalse(is_valid)
        self.assertIn("44 dígitos", msg or "")

    def test_validate_invalid_key_dv(self):
        invalid_dv = "35241000000000000191550010000000011000000019"
        is_valid, msg = AccessKeyValidator.validate_key(invalid_dv)
        self.assertFalse(is_valid)
        self.assertIn("Dígito verificador inválido", msg or "")


if __name__ == "__main__":
    unittest.main()

