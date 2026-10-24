#!/usr/bin/env python3
"""Script auxiliar da skill para validação e diagnóstico rápido de XMLs fiscais."""

import sys
from pathlib import Path

# Adiciona o diretório raiz ao path para importação dos módulos do motor
project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.fiscal_xml_validator.cli import main

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python validate_xml.py <caminho_xml> [--format text|json|markdown]")
        sys.exit(1)
    args = ["validate"] + sys.argv[1:]
    sys.exit(main(args))

