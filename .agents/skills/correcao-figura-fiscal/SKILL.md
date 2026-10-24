---
name: correcao-figura-fiscal
description: >-
  Audita, valida e gera propostas de correção para figuras fiscais (CFOP, CST, CSOSN,
  NCM, ICMS, PIS, COFINS, IPI, bases de cálculo e totais) em documentos fiscais eletrônicos
  (NF-e modelo 55, NFC-e modelo 65, CT-e) a partir de arquivos XML, produzindo diagnósticos explicáveis
  e diffs unificados para revisão humana.
---

# Skill: Correção de Figuras Fiscais em XMLs

Esta skill capacita o agente a atuar como **Fiscal XML Architect**, realizando a auditoria, diagnóstico explicável e sugestão de correção de **figuras fiscais** em arquivos XML de DF-e (NF-e modelo 55, NFC-e modelo 65 e CT-e), com estrita observância das normas do SPED, SEFAZ e dos princípios inegociáveis de segurança e integridade fiscal.

## Quando usar esta skill

Use esta skill sempre que:
1. O usuário fornecer um ou mais arquivos XML de documentos fiscais e solicitar auditoria, conferência de tributos ou correção de dados fiscais.
2. Houver rejeição da SEFAZ (ex: Rejeição 522, 523, 531, 532, 535, 590, 591, 725, etc.) e o usuário precisar diagnosticar a causa e obter a correção necessária.
3. For necessário conferir a coerência entre:
   - **CFOP** e os estados do emitente e destinatário (operações internas, interestaduais ou exterior).
   - **CST / CSOSN** e o Regime Tributário do emitente (**CRT** 1 - Simples Nacional vs CRT 3 - Regime Normal).
   - Cálculos de bases de cálculo, alíquotas e valores de impostos (**ICMS, PIS, COFINS, IPI**).
   - Somatórios de itens com os totais gerais do documento (`ICMSTot`).
   - Formato e validade do **NCM** (8 dígitos) e Chave de Acesso (44 dígitos e DV módulo 11).
4. O usuário solicitar um **diff** ou sugestão de XML corrigido sem sobrescrever o arquivo original.

---

## Princípios Inegociáveis (Diretrizes de Segurança e Compliance)

1. **Nunca sobrescrever o XML original:** Qualquer sugestão de correção deve ser apresentada em formato de `diff` unificado ou salva em um arquivo apartado (ex: `documento.suggested.xml`), exigindo validação humana prévia.
2. **Privacidade de dados reais:** Nunca exibir ou logar chaves de acesso completas, CPFs ou certificados digitais. Use sempre o mascaramento seguro (ex: `3524...0017 (mascarada)`).
3. **Classificação de origem:** Registrar explicitamente se o documento analisado é `synthetic` (fictício para testes), `user_provided` (fornecido pelo usuário) ou `authorized_remote`.
4. **Precisão explicável (As 6 Perguntas):** Toda ocorrência deve responder:
   - *Onde está o problema?* (Tag, caminho XPath e item afetado).
   - *O que foi encontrado?* (Valor presente no XML).
   - *O que era esperado?* (Valor calculado ou exigência normativa).
   - *Qual regra foi violada?* (Identificador da regra e fonte técnica/normativa).
   - *Qual é o impacto fiscal?* (Rejeição SEFAZ, autuação ou recolhimento indevido).
   - *Como corrigir ou investigar?* (Ação prática recomendada).

---

## Fluxo de Trabalho Passo a Passo

### Passo 1: Ingestão e Identificação Segura do XML
Identifique o caminho do arquivo XML e execute a validação via CLI ou scripts da skill:

```bash
# Validação direta via CLI do projeto
python -m src.fiscal_xml_validator.cli validate caminho/do/documento.xml

# Geração de Relatório Executivo Apresentável em PDF (com todos os MOTIVOS)
python -m src.fiscal_xml_validator.cli validate caminho/do/documento.xml --pdf relatorio_auditoria.pdf

# Ou saída em formato JSON estruturado
python -m src.fiscal_xml_validator.cli validate caminho/do/documento.xml --format json
```

### Passo 2: Geração da Proposta de Correção (Diff Unificado)
Quando inconsistências corrigíveis forem identificadas (ex: erro aritmético em `vICMS`, CFOP invertido, divergência em `vProd` ou `vNF`), gere a proposta de correção sem alterar o original:

```bash
python -m src.fiscal_xml_validator.cli fix-suggest caminho/do/documento.xml --output-diff correcao.diff --output-xml documento.suggested.xml
```

### Passo 3: Avaliação de Figuras Fiscais Específicas

#### A. CFOP vs UF do Emitente e Destinatário (`FIG-CFOP-001` e `FIG-CFOP-002`)
- **Operação Interna (`UF_emit == UF_dest`):** CFOP deve iniciar por `1` (entrada) ou `5` (saída).
- **Operação Interestadual (`UF_emit != UF_dest`):** CFOP deve iniciar por `2` (entrada) ou `6` (saída).
- **Exterior (`idDest == 3` ou `UF == 'EX'`):** CFOP deve iniciar por `3` (importação) ou `7` (exportação).
- **NFC-e (modelo 65):** Restrita a operações internas presenciais a consumidor final, admitindo apenas grupo `5xxx`.

#### B. CST / CSOSN vs Regime Tributário (CRT) (`FIG-CST-001`)
- **CRT 1 (Simples Nacional):** Obriga o uso de CSOSN (Tabela B do Simples: `101, 102, 103, 201, 202, 203, 300, 400, 500, 900`). É vedado o uso de CST normal.
- **CRT 3 (Regime Normal):** Obriga o uso de CST de 2 dígitos (`00, 10, 20, 30, 40, 41, 50, 51, 60, 70, 90`). É vedado o uso de CSOSN.

#### C. Consistência Aritmética e Totais (`TAX-CALC-001` a `TAX-TOT-003`)
- $vICMS = vBC \times (pICMS / 100)$ (arredondamento bancário NBR 5891 a 2 casas).
- $vProd_{total} = \sum vProd_{itens}$.
- $vICMS_{total} = \sum vICMS_{itens}$.
- $vNF = vProd - vDesc - vICMSDeson + vST + vFCPST + vFrete + vSeg + vOutro + vII + vIPI + vIPIDevol$.

---

## Scripts Utilitários Disponíveis

- [scripts/validate_xml.py](./scripts/validate_xml.py): Script autônomo para validação rápida de XML.
- [scripts/suggest_fix.py](./scripts/suggest_fix.py): Script para geração de diff e sugestão de correção.

---

## Documentação e Referências Fiscais

- [references/matriz_fiscal_cfop_cst.md](./references/matriz_fiscal_cfop_cst.md): Matriz de enquadramento tributário CFOP x CST x CSOSN.
- [references/regras_aritmeticas.md](./references/regras_aritmeticas.md): Fórmulas de cálculo de tributos e regras de validação da SEFAZ.
- [references/seguranca_e_privacidade.md](./references/seguranca_e_privacidade.md): Diretrizes de proteção de dados fiscais reais e XXE.

