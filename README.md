# fiscal-xml-validator 🇧🇷

> **Validador e auditor de figuras fiscais em XMLs brasileiros (NF-e e NFC-e): diagnósticos explicáveis e propostas de correção em formato diff para rejeições da SEFAZ, CFOP, CST/CSOSN, NCM, bases, alíquotas e totais.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14%20%7C%203.15-blue)](pyproject.toml)
[![Tests Status](https://img.shields.io/badge/tests-24%20passed-brightgreen.svg)](tests/)
[![Zero Dependencies](https://img.shields.io/badge/dependencies-zero%20mandatory-success)](pyproject.toml)

---

## 💡 O Problema que Este Projeto Resolve

A validação de documentos fiscais eletrônicos no Brasil (NF-e modelo 55, NFC-e modelo 65) é historicamente frustrante:
- Erros da SEFAZ trazem mensagens crípticas como `Rejeição 522: CFOP de Operação Interna e UF do emitente difere da UF do destinatário` ou `Rejeição 531: Total do Valor dos Produtos difere do somatório dos itens`.
- Sistemas ERP frequentemente erram no cálculo de arredondamento de ICMS, PIS e COFINS ou aplicam figuras fiscais incompatíveis com o Regime Tributário do contribuinte (CRT).
- Ferramentas tradicionais apenas dizem **"inválido"**, sem indicar **onde** está o erro, **qual valor** era esperado, **qual a base legal** e **como corrigir**.
- E o mais grave: correções automáticas descuidadas podem corromper arquivos fiscais originais ou vazar dados confidenciais.

O **`fiscal-xml-validator`** foi criado para resolver isso de ponta a ponta. Ele transforma documentos fiscais complexos em **diagnósticos explicáveis**, verifica regras da SEFAZ e propõe **correções em formato diff unificado** — sem nunca alterar o arquivo original silenciosamente.

---

## ⚡ Demonstração Prática: Da Inconsistência ao Diagnóstico com Diff

Imagine um XML de NF-e emitido em SP com destino a SP, onde o ERP preencheu erroneamente um CFOP interestadual (`6102`) e calculou um valor de ICMS divergente da alíquota:

### 1. Executando a auditoria:
```bash
python -m src.fiscal_xml_validator.cli validate tests/fixtures/synthetic/nfe/invalid/nfe_cfop_mismatch.xml
```

### 2. Relatório gerado:
```text
==============================================================================
  RELATÓRIO DE AUDITORIA FISCAL DE XML
==============================================================================
Origem do Documento: Documento fictício de demonstração/teste
Tipo de Documento:   NFE (Modelo 55)
Versão do Layout:    4.00
Chave de Acesso:     3524...0017 (mascarada)
------------------------------------------------------------------------------
Status: ISSUES_FOUND | Erros: 1 | Avisos: 0 | Informativos: 0
==============================================================================

FORAM IDENTIFICADAS 1 OCORRÊNCIA(S):

[ERROR] FIG-CFOP-001 — Item 1: CFOP '6102' é interestadual, mas emitente e destinatário pertencem à mesma UF (SP).
  1. Localização:  Tag <CFOP> em /NFe/infNFe/det[1]/prod/CFOP
  2. Encontrado:   6102
  3. Esperado:     5102
  4. Regra:        Operações onde a UF do emitente é idêntica à UF do destinatário devem utilizar CFOP iniciado por 1 (entrada) ou 5 (saída).
     Fonte:        Convênio S/Nº de 1970 (Tabela CFOP) e MOC Anexo I - Regra I08-10
  5. Impacto:      Rejeição SEFAZ 523: CFOP não é de Operação Interna e UF do emitente é igual à UF do destinatário.
  6. Sugestão:     Altere o CFOP para a figura fiscal interna correspondente: '5102'.
------------------------------------------------------------------------------

PROPOSTA EXPERIMENTAL DE CORREÇÃO (DIFF UNIFICADO):
Atenção: Valide previamente as alterações com um responsável fiscal.
------------------------------------------------------------------------------
--- original.xml
+++ sugestao_correcao_fiscal.xml
@@ -40,3 +40,3 @@
         <NCM>84713012</NCM>
-        <CFOP>6102</CFOP>
+        <CFOP>5102</CFOP>
         <uCom>UN</uCom>
------------------------------------------------------------------------------
```

---

## 🚀 Instalação Rápida (Zero Dependências Obrigatórias)

O motor utiliza exclusivamente a biblioteca padrão do Python (`xml.etree.ElementTree`, `decimal`, `difflib`, `argparse`). Não é necessário compilar binários externos nem instalar pacotes pesados para começar.

```bash
# Clone o repositório
git clone https://github.com/seu-usuario/fiscal-xml-validator.git
cd fiscal-xml-validator

# Execute os testes para garantir a conformidade do ambiente
python -m unittest discover -s tests
```

---

## 🛠️ Modos de Uso

### 1. Interface de Linha de Comando (CLI)

```bash
# Validar um XML local
python -m src.fiscal_xml_validator.cli validate caminho/da/nota.xml

# Gerar relatório executivo apresentável em PDF (com todos os MOTIVOS e embasamento)
python -m src.fiscal_xml_validator.cli validate caminho/da/nota.xml --pdf relatorio_auditoria.pdf

# Validar uma pasta inteira recursivamente
python -m src.fiscal_xml_validator.cli validate ./notas/ --recursive

# Obter relatório em formato JSON estruturado para automações e CI/CD
python -m src.fiscal_xml_validator.cli validate caminho/da/nota.xml --format json

# Gerar sugestão de XML corrigido em arquivo separado (sem tocar no original)
python -m src.fiscal_xml_validator.cli fix-suggest nota.xml --output-diff correcao.patch --output-xml nota.sugerida.xml

# Listar todas as regras fiscais ativas no catálogo oficial
python -m src.fiscal_xml_validator.cli rules list

# Validar formato e Dígito Verificador (Módulo 11) de uma Chave de Acesso
python -m src.fiscal_xml_validator.cli verify-key 35241000000000000191550010000000011000000017
```

### 2. Uso Programático em Python

```python
from src.fiscal_xml_validator import FiscalValidator

validator = FiscalValidator()

# Valida um arquivo do disco
report = validator.validate_file("caminho/do/documento.xml", generate_fix=True)

print(f"Status: {report.summary.status}")
print(f"Erros encontrados: {report.summary.errors}")

for diag in report.diagnostics:
    print(f"[{diag.rule_id}] {diag.message}")
    print(f"  Tag: <{diag.tag}> | Esperado: {diag.expected_value}")

if report.fix_result and report.fix_result.has_changes:
    print("Diff sugerido:")
    print(report.fix_result.diff)
```

### 3. Integração como Skill de Agente de IA (Antigravity / Cursor / Claude)

O repositório já inclui a pasta [`skills/correcao-figura-fiscal/`](skills/correcao-figura-fiscal/SKILL.md) estruturada com frontmatter padrão, runbooks e referências normativas. Agentes de IA podem ler diretamente o `SKILL.md` para automatizar tarefas de triagem fiscal e auditoria de lotes de notas fiscais.

---

## 📋 Catálogo de Regras Implementadas

| Identificador | Categoria | Descrição | Fonte Normativa |
|---|---|---|---|
| `TAX-CALC-001` | Aritmética | Consistência de $vBC \times pICMS == vICMS$ | MOC Anexo I - Regra N12-20 |
| `TAX-CALC-003` | Aritmética | Consistência de $vBC \times pPIS == vPIS$ | MOC Anexo I - Regra Q07-10 |
| `TAX-CALC-004` | Aritmética | Consistência de $vBC \times pCOFINS == vCOFINS$ | MOC Anexo I - Regra S07-10 |
| `TAX-CALC-005` | Aritmética | Consistência de $vBC \times pIPI == vIPI$ | MOC Anexo I - Regra O14-10 |
| `TAX-TOT-001` | Aritmética | Somatório de `vProd` dos itens vs `ICMSTot.vProd` | MOC Regra W07-10 (Rejeição 531) |
| `TAX-TOT-002` | Aritmética | Somatório de `vICMS` dos itens vs `ICMSTot.vICMS` | MOC Regra W04-10 (Rejeição 532) |
| `TAX-TOT-003` | Aritmética | Equação legal do valor total da nota (`vNF`) | MOC Regra W16-10 (Rejeição 535) |
| `FIG-CFOP-001` | Referência | Coerência de CFOP com UF emitente/destinatário | Convênio S/Nº de 1970 / MOC I08-10 |
| `FIG-CFOP-002` | Referência | Restrição de CFOP 5xxx para NFC-e (mod 65) | MOC NFC-e Regra I08-20 |
| `FIG-CST-001` | Tributação | Conflito CRT do Emitente (Simples vs Normal) e CST/CSOSN | Ajuste SINIEF 07/05 (Rejeição 590/591) |
| `FIG-CST-003` | Tributação | Destaque indevido de ICMS em CST Isento (40, 41, 50) | Ajuste SINIEF 07/05 |
| `FIG-NCM-001` | Referência | Formato e estrutura do código NCM (8 dígitos) | Nota Técnica 2014.004 |
| `FIG-CHAVE-001`| Referência | Integridade e Dígito Verificador da Chave (Módulo 11) | MOC Geral (Rejeição 253) |

---

## 🔒 Segurança, Privacidade e LGPD

1. **Proteção contra XXE (XML External Entity):** O parser rejeita proativamente declarações DTD/ENTITY externas e payloads de expansão de entidades (*Billion Laughs*).
2. **Mascaramento Automático de Chaves e Documentos:** Chaves de acesso, CPFs e dados pessoais nunca são expostos na íntegra em relatórios ou logs públicos.
3. **Não alteração do arquivo original:** As propostas de correção são puramente analíticas e apresentadas em diffs separados para auditoria prévia.
4. **Sem telemetria oculta:** Nenhum XML é enviado para servidores de terceiros.

---

## 🛣️ Roadmap

- [x] **Fase 1 (MVP Confiável):** Parser seguro com defesas contra XXE, modelos NF-e/NFC-e layout 4.00, regras aritméticas de ICMS, PIS, COFINS, IPI, totais da nota, CFOP geográfico, CST vs CRT, CLI completa, geração de diffs e testes sintéticos.
- [ ] **Fase 2 (Cobertura Fiscal Ampliada):** Regras de Substituição Tributária (ICMS-ST com MVA e redução de base), validação de tabela CEST oficial e códigos de benefício fiscal (cBenef).
- [ ] **Fase 3 (Conectores e CI/CD):** Action oficial do GitHub para validação de XMLs fiscais em pull requests e relatórios em HTML interativo.
- [ ] **Fase 4 (Reforma Tributária):** Suporte contextual aos novos campos de CBS e IBS conforme publicação dos layouts oficiais da Emenda Constitucional 132/2023.

---

## 🤝 Como Contribuir

Contribuições são muito bem-vindas!
1. Leia o nosso [Guia de Contribuição](CONTRIBUTING.md).
2. **Atenção:** Nunca anexe XMLs reais ou dados fiscais confidenciais. Utilize apenas dados fictícios estruturados com a marcação `<!-- FICTÍCIO -->`.
3. Para sugerir uma nova regra fiscal, informe a Nota Técnica ou Ajuste SINIEF correspondente.

---

## 📄 Licença

Distribuído sob a licença **MIT**. Consulte o arquivo [LICENSE](LICENSE) para obter mais informações.

> **Aviso Legal:** Esta ferramenta é um utilitário open source de apoio técnico e auditoria. Os diagnósticos e propostas de correção gerados não substituem a análise de um contador ou especialista tributário habilitado e não constituem garantia de inexistência de passivos fiscais perante os órgãos de fiscalização.

