"""Módulo de ingestão, classificação de origem e identificação do documento fiscal.

Conforme seções 4.1, 5.1 e 5.3 do AGENTS.md.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Tuple
import xml.etree.ElementTree as ET

from .models import DocumentOrigin, DocumentOriginType
from .security import SafeXMLParser


@dataclass
class IngestedDocument:
    """Documento fiscal ingerido e pré-classificado."""
    file_path: Optional[str]
    raw_bytes: bytes
    raw_text: str
    root_element: ET.Element
    document_type: str  # NFE, NFCE, CTE, UNKNOWN
    layout_version: Optional[str]
    origin: DocumentOrigin
    access_key: Optional[str] = None
    namespace: Optional[str] = None


class AccessKeyValidator:
    """Validador do algoritmo de Chave de Acesso de DF-e (44 dígitos e DV Módulo 11)."""

    @classmethod
    def calculate_dv(cls, key_43: str) -> int:
        """Calcula o dígito verificador módulo 11 com pesos de 2 a 9 da direita para a esquerda."""
        if len(key_43) != 43 or not key_43.isdigit():
            raise ValueError("A chave para cálculo do DV deve conter exatamente 43 dígitos numéricos.")

        weights = [2, 3, 4, 5, 6, 7, 8, 9]
        total = 0
        for i, char in enumerate(reversed(key_43)):
            weight = weights[i % len(weights)]
            total += int(char) * weight

        remainder = total % 11
        if remainder in (0, 1):
            return 0
        return 11 - remainder

    @classmethod
    def validate_key(cls, key: str) -> Tuple[bool, Optional[str]]:
        """Valida a chave completa de 44 dígitos."""
        clean_key = re.sub(r"\D", "", key)
        if len(clean_key) != 44:
            return False, f"Chave de acesso possui {len(clean_key)} dígitos; esperados exatamente 44 dígitos numéricos."

        expected_dv = cls.calculate_dv(clean_key[:43])
        found_dv = int(clean_key[43])
        if expected_dv != found_dv:
            return False, f"Dígito verificador inválido: encontrado {found_dv}, esperado {expected_dv}."

        return True, None


class DocumentIngestion:
    """Leitura, validação de limites e classificação de documentos XML."""

    @classmethod
    def detect_origin(cls, text: str, file_path: Optional[str] = None) -> DocumentOrigin:
        """Determina a origem conforme seção 5.3 do AGENTS.md."""
        lower_text = text.lower()
        if (
            "synthetic" in lower_text
            or "fictício" in lower_text
            or "ficticio" in lower_text
            or "exemplo didático" in lower_text
            or (file_path and "synthetic" in file_path.replace("\\", "/").lower())
        ):
            return DocumentOrigin(
                type=DocumentOriginType.SYNTHETIC,
                label="Documento fictício de demonstração/teste",
            )

        if file_path:
            return DocumentOrigin(
                type=DocumentOriginType.USER_PROVIDED,
                label=f"Arquivo local fornecido pelo usuário ({Path(file_path).name})",
            )

        return DocumentOrigin(
            type=DocumentOriginType.UNKNOWN,
            label="Origem não confirmada",
        )

    @classmethod
    def extract_clean_tag(cls, tag: str) -> str:
        """Remove o namespace XML da tag."""
        if "}" in tag:
            return tag.split("}", 1)[1]
        return tag

    @classmethod
    def extract_namespace(cls, tag: str) -> Optional[str]:
        """Extrai o namespace XML se presente."""
        if tag.startswith("{") and "}" in tag:
            return tag[1:].split("}", 1)[0]
        return None

    @classmethod
    def ingest_bytes(
        cls,
        raw_bytes: bytes,
        file_path: Optional[str] = None,
        max_bytes: int = SafeXMLParser.MAX_FILE_SIZE_BYTES,
    ) -> IngestedDocument:
        """Ingere e analisa bytes de um XML fiscal com validações completas."""
        SafeXMLParser.check_raw_bytes(raw_bytes, max_bytes)

        # Detecta codificação
        try:
            raw_text = raw_bytes.decode("utf-8")
        except UnicodeDecodeError:
            try:
                raw_text = raw_bytes.decode("iso-8859-1")
            except UnicodeDecodeError as e:
                raise ValueError(f"Codificação de caracteres inválida no XML: {e}") from e

        root = SafeXMLParser.parse_string(raw_bytes, max_bytes)
        origin = cls.detect_origin(raw_text, file_path)
        clean_root_tag = cls.extract_clean_tag(root.tag)
        ns = cls.extract_namespace(root.tag)

        doc_type = "UNKNOWN"
        layout_version = root.attrib.get("versao")
        access_key = None

        # Busca infNFe ou infCte recursivamente
        for elem in root.iter():
            local = cls.extract_clean_tag(elem.tag)
            if local == "infNFe":
                layout_version = elem.attrib.get("versao") or layout_version
                raw_id = elem.attrib.get("Id", "")
                if raw_id.startswith("NFe"):
                    access_key = raw_id[3:]
                # Descobre se é NF-e (55) ou NFC-e (65) pelo <mod>
                for sub in elem.iter():
                    if cls.extract_clean_tag(sub.tag) == "mod":
                        if sub.text == "65":
                            doc_type = "NFCE"
                        elif sub.text == "55":
                            doc_type = "NFE"
                if doc_type == "UNKNOWN":
                    doc_type = "NFE"
                break
            elif local == "infCte":
                layout_version = elem.attrib.get("versao") or layout_version
                doc_type = "CTE"
                raw_id = elem.attrib.get("Id", "")
                if raw_id.startswith("CTe"):
                    access_key = raw_id[3:]
                break

        if doc_type == "UNKNOWN":
            if "NFe" in clean_root_tag or "nfeProc" in clean_root_tag:
                doc_type = "NFE"
            elif "CTe" in clean_root_tag or "cteProc" in clean_root_tag:
                doc_type = "CTE"

        return IngestedDocument(
            file_path=file_path,
            raw_bytes=raw_bytes,
            raw_text=raw_text,
            root_element=root,
            document_type=doc_type,
            layout_version=layout_version,
            origin=origin,
            access_key=access_key,
            namespace=ns,
        )

    @classmethod
    def ingest_file(cls, file_path: str | Path) -> IngestedDocument:
        """Lê arquivo do disco e executa o processo de ingestão segura."""
        path = Path(file_path)
        if not path.exists() or not path.is_file():
            raise FileNotFoundError(f"Arquivo XML não encontrado: {path}")

        file_size = path.stat().st_size
        if file_size > SafeXMLParser.MAX_FILE_SIZE_BYTES:
            raise ValueError(
                f"Arquivo {path.name} ({file_size} bytes) excede o limite permitido de {SafeXMLParser.MAX_FILE_SIZE_BYTES} bytes."
            )

        with open(path, "rb") as f:
            raw_bytes = f.read()

        return cls.ingest_bytes(raw_bytes, file_path=str(path))

