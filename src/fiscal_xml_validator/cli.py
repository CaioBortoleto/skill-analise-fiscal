"""Interface de Linha de Comando (CLI) para validação e auditoria fiscal de XMLs.

Conforme seção 11 do AGENTS.md.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from .catalog.rule_catalog import RuleCatalog
from .corrector.fiscal_fixer import FiscalFixer
from .ingestion import AccessKeyValidator, DocumentIngestion
from .models import Category, Severity, ValidationReport
from .reporting.console_reporter import ConsoleReporter
from .reporting.markdown_reporter import MarkdownReporter
from .reporting.pdf_reporter import PDFReporter
from .security import DataMasker
from .validator import FiscalValidator


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="fiscal-xml",
        description="Validador e auditor fiscal de XMLs brasileiros (NF-e, NFC-e, CT-e)",
    )
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponíveis")

    # 1. validate
    validate_cmd = subparsers.add_parser("validate", help="Valida um arquivo XML ou diretório de documentos")
    validate_cmd.add_argument("path", help="Caminho do arquivo .xml ou diretório a validar")
    validate_cmd.add_argument(
        "--format",
        choices=["text", "json", "markdown", "pdf"],
        default="text",
        help="Formato de saída do relatório (padrão: text)",
    )
    validate_cmd.add_argument("--output", "-o", help="Salva a saída no arquivo especificado")
    validate_cmd.add_argument("--pdf", help="Gera relatório executivo apresentável em PDF no caminho especificado")
    validate_cmd.add_argument("--recursive", "-r", action="store_true", help="Busca XMLs recursivamente se path for pasta")
    validate_cmd.add_argument("--no-diff", action="store_true", help="Não inclui propostas de diff no relatório de texto")

    # 2. fix-suggest
    fix_cmd = subparsers.add_parser("fix-suggest", help="Gera proposta experimental de correção de figuras fiscais")
    fix_cmd.add_argument("path", help="Arquivo XML a analisar")
    fix_cmd.add_argument("--output-diff", help="Arquivo para salvar o diff unificado gerado")
    fix_cmd.add_argument(
        "--output-xml",
        help="Arquivo para salvar a sugestão de XML corrigido (nunca sobrescreve o original)",
    )

    # 3. rules list
    rules_cmd = subparsers.add_parser("rules", help="Gerencia e consulta catálogo de regras fiscais")
    rules_sub = rules_cmd.add_subparsers(dest="rules_action", help="Ações de regras")
    list_rules_cmd = rules_sub.add_parser("list", help="Lista regras ativas")
    list_rules_cmd.add_argument("--document", "-d", choices=["NFE", "NFCE", "CTE"], help="Filtra por documento")
    list_rules_cmd.add_argument(
        "--category",
        "-c",
        choices=["arithmetic", "reference", "taxation", "structure"],
        help="Filtra por categoria",
    )

    # 4. verify-key
    key_cmd = subparsers.add_parser("verify-key", help="Valida integridade e dígito verificador de chave de acesso DF-e")
    key_cmd.add_argument("key", help="Chave de acesso de 44 dígitos")

    return parser


def handle_validate(args: argparse.Namespace) -> int:
    target = Path(args.path)
    if not target.exists():
        print(f"Erro: Caminho '{target}' não encontrado.", file=sys.stderr)
        return 2

    validator = FiscalValidator()
    reports: List[ValidationReport] = []

    if target.is_dir():
        reports = validator.validate_directory(target, recursive=args.recursive, generate_fix=not args.no_diff)
    else:
        try:
            rep = validator.validate_file(target, generate_fix=not args.no_diff)
            reports.append(rep)
        except Exception as e:
            print(f"Erro ao processar '{target}': {e}", file=sys.stderr)
            return 2

    # Geração de PDF se solicitado via --format pdf ou --pdf
    pdf_dest = args.pdf or (args.output if args.format == "pdf" else None)
    if pdf_dest or args.format == "pdf":
        if not pdf_dest:
            pdf_dest = str(target.with_suffix(".relatorio_auditoria.pdf"))
        
        # Gera o PDF para o relatório principal
        if reports:
            try:
                generated_pdf = PDFReporter.generate_pdf(reports[0], pdf_dest)
                print(f"📄 Relatório executivo em PDF gerado com sucesso em: '{generated_pdf}'")
            except Exception as e:
                print(f"Erro ao gerar relatório PDF: {e}", file=sys.stderr)
                return 2

        if args.format == "pdf":
            has_errors = any(r.summary.errors > 0 or r.summary.critical > 0 for r in reports)
            return 1 if has_errors else 0

    # Formatação de saída texto / json / markdown
    output_str = ""
    if args.format == "json":
        import json
        if len(reports) == 1:
            output_str = reports[0].to_json(indent=2)
        else:
            output_str = json.dumps([r.to_dict() for r in reports], indent=2, ensure_ascii=False)
    elif args.format == "markdown":
        output_str = "\n\n---\n\n".join(MarkdownReporter.format_report(r) for r in reports)
    else:
        output_str = "\n\n".join(ConsoleReporter.format_report(r, show_diff=not args.no_diff) for r in reports)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output_str)
        print(f"Relatório gravado com sucesso em '{args.output}'.")
    else:
        print(output_str)

    has_errors = any(r.summary.errors > 0 or r.summary.critical > 0 for r in reports)
    return 1 if has_errors else 0


def handle_fix_suggest(args: argparse.Namespace) -> int:
    path = Path(args.path)
    if not path.is_file():
        print(f"Erro: Arquivo '{path}' não encontrado.", file=sys.stderr)
        return 2

    validator = FiscalValidator()
    try:
        report = validator.validate_file(path, generate_fix=True)
    except Exception as e:
        print(f"Erro ao auditar arquivo: {e}", file=sys.stderr)
        return 2

    fix_res = report.fix_result
    if not fix_res or not fix_res.has_changes:
        print("Nenhuma inconsistência passível de correção automática foi identificada.")
        return 0

    print("=" * 78)
    print(f"PROPOSTA EXPERIMENTAL DE CORREÇÃO FISCAL: {path.name}")
    print("=" * 78)
    print(f"Alterações propostas: {len(fix_res.proposals)}")
    for p in fix_res.proposals:
        print(f"  - Tag <{p.tag}> ({p.xml_path}): '{p.original_value}' -> '{p.proposed_value}'")
        print(f"    Motivo: {p.reason}")
    print("-" * 78)
    print("DIFF UNIFICADO:")
    print(fix_res.diff)
    print("-" * 78)

    if args.output_diff:
        with open(args.output_diff, "w", encoding="utf-8") as f:
            f.write(fix_res.diff)
        print(f"Diff gravado em '{args.output_diff}'.")

    if args.output_xml:
        out_xml_path = Path(args.output_xml)
        if out_xml_path.resolve() == path.resolve():
            print("Erro de segurança: Não é permitido sobrescrever o XML original.", file=sys.stderr)
            return 2
        with open(out_xml_path, "w", encoding="utf-8") as f:
            f.write(fix_res.suggested_xml)
        print(f"Sugestão de XML gravada com segurança em '{out_xml_path}'.")

    return 0


def handle_rules(args: argparse.Namespace) -> int:
    cat = Category(args.category) if getattr(args, "category", None) else None
    rules = RuleCatalog.list_rules(
        document_type=getattr(args, "document", None),
        category=cat,
    )
    print(f"CATÁLOGO DE REGRAS FISCAIS ATIVAS ({len(rules)} regras registradas):")
    print("=" * 78)
    for r in rules:
        print(f"[{r.id}] {r.title}")
        print(f"  Categoria:  {r.category.value} | Gravidade: {r.severity.value}")
        print(f"  Documentos: {', '.join(r.document_types) if r.document_types else 'Todos'}")
        print(f"  Descrição:  {r.description}")
        if r.source_reference:
            print(f"  Fonte:      {r.source_reference}")
        print("-" * 78)
    return 0


def handle_verify_key(args: argparse.Namespace) -> int:
    key = args.key
    is_valid, msg = AccessKeyValidator.validate_key(key)
    masked = DataMasker.mask_access_key(key)
    print(f"Chave analisada: {masked}")
    if is_valid:
        print("✅ Chave de acesso possui 44 dígitos e dígito verificador válido (Módulo 11).")
        return 0
    else:
        print(f"❌ Chave inválida: {msg}")
        return 1


def main(argv: Optional[List[str]] = None) -> int:
    parser = create_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    if args.command == "validate":
        return handle_validate(args)
    elif args.command == "fix-suggest":
        return handle_fix_suggest(args)
    elif args.command == "rules":
        return handle_rules(args)
    elif args.command == "verify-key":
        return handle_verify_key(args)

    return 0


if __name__ == "__main__":
    sys.exit(main())

