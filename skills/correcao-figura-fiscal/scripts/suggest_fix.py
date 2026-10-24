#!/usr/bin/env python3
"""Script auxiliar da skill para geração de proposta de correção e diff de figuras fiscais."""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.fiscal_xml_validator.cli import main

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python suggest_fix.py <caminho_xml> [--output-diff diff.patch] [--output-xml sugerido.xml]")
        sys.exit(1)
    args = ["fix-suggest"] + sys.argv[1:]
    sys.exit(main(args))

