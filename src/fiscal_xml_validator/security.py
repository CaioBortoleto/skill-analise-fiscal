"""Componente de segurança, proteção contra XXE e anonimização de dados fiscais.

Conforme seções 5.2 e 13 do AGENTS.md.
"""

from __future__ import annotations

import io
import re
from typing import Optional
import xml.etree.ElementTree as ET


class SecurityException(Exception):
    """Exceção levantada quando violações de segurança XML são detectadas."""
    pass


class SafeXMLParser:
    """Parser seguro de XML com defesa contra XXE, expansão de entidades e sobrecarga."""

    MAX_FILE_SIZE_BYTES = 15 * 1024 * 1024  # 15 MB
    MAX_ELEMENTS = 100_000
    FORBIDDEN_PATTERNS = [
        re.compile(rb"<!ENTITY", re.IGNORECASE),
        re.compile(rb"<!DOCTYPE", re.IGNORECASE),
        re.compile(rb"SYSTEM\s+[\"']", re.IGNORECASE),
        re.compile(rb"PUBLIC\s+[\"']", re.IGNORECASE),
    ]

    @classmethod
    def check_raw_bytes(cls, content: bytes, max_bytes: int = MAX_FILE_SIZE_BYTES) -> None:
        """Verifica se o conteúdo bruto viola limites de tamanho ou contém DTDs maliciosos."""
        if len(content) > max_bytes:
            raise SecurityException(
                f"Tamanho do arquivo ({len(content)} bytes) excede o limite máximo permitido ({max_bytes} bytes)."
            )

        for pattern in cls.FORBIDDEN_PATTERNS:
            if pattern.search(content):
                raise SecurityException(
                    "Declarações DTD/ENTITY externas detectadas no XML. Parsing bloqueado para evitar XXE."
                )

    @classmethod
    def parse_string(cls, xml_text: str | bytes, max_bytes: int = MAX_FILE_SIZE_BYTES) -> ET.Element:
        """Interpreta string ou bytes XML com restrições ativas de segurança."""
        raw_bytes = xml_text.encode("utf-8") if isinstance(xml_text, str) else xml_text
        cls.check_raw_bytes(raw_bytes, max_bytes)

        # ET.iterparse para monitorar contagem de elementos
        count = 0
        stream = io.BytesIO(raw_bytes)
        context = ET.iterparse(stream, events=("start",))
        try:
            for _, _ in context:
                count += 1
                if count > cls.MAX_ELEMENTS:
                    raise SecurityException(
                        f"Quantidade excessiva de elementos XML ({count} > {cls.MAX_ELEMENTS}). Possível DoS."
                    )
        except ET.ParseError as e:
            raise ValueError(f"XML malformado: {e}") from e

        # Retorna o elemento raiz final
        return ET.fromstring(raw_bytes)


class DataMasker:
    """Mecanismo para mascarar identificadores fiscais e chaves em logs e relatórios."""

    @staticmethod
    def mask_access_key(key: Optional[str]) -> str:
        """Mascara chave de acesso fiscal de 44 dígitos preservando apenas início e fim."""
        if not key:
            return ""
        clean = re.sub(r"\D", "", key)
        if len(clean) == 44:
            return f"{clean[:4]}...{clean[-4:]} (mascarada)"
        if len(clean) > 8:
            return f"{clean[:3]}...{clean[-3:]}"
        return "***"

    @staticmethod
    def mask_cpf(cpf: Optional[str]) -> str:
        """Mascara CPF preservando apenas parte intermediária."""
        if not cpf:
            return ""
        clean = re.sub(r"\D", "", cpf)
        if len(clean) == 11:
            return f"***.{clean[3:6]}.{clean[6:9]}-**"
        return "***"

    @staticmethod
    def mask_cnpj(cnpj: Optional[str]) -> str:
        """Mascara CNPJ para exibição segura."""
        if not cnpj:
            return ""
        clean = re.sub(r"\D", "", cnpj)
        if len(clean) == 14:
            return f"{clean[:2]}.***.***/{clean[8:12]}-{clean[12:]}"
        return clean

