# Changelog

Todas as alterações notáveis neste projeto serão documentadas neste arquivo.

O formato é baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/), e este projeto adere ao [Semantic Versioning](https://semver.org/lang/pt-BR/).

## [0.1.0] - 2026-10-24

### Adicionado
- **Motor Central de Auditoria:** Implementação do `FiscalValidator` com suporte nativo a NF-e (modelo 55) e NFC-e (modelo 65) layout 4.00.
- **Motor de Correção Experimental (`FiscalFixer`):** Geração determinística de propostas de correção de figuras fiscais em formato `diff` unificado, sem alterar ou sobrescrever os XMLs originais.
- **Catálogo de Regras Fiscais:**
  - `TAX-CALC-001`: Consistência aritmética do ICMS próprio ($vBC \times pICMS$).
  - `TAX-CALC-003`: Consistência aritmética do PIS ($vBC \times pPIS$).
  - `TAX-CALC-004`: Consistência aritmética da COFINS ($vBC \times pCOFINS$).
  - `TAX-CALC-005`: Consistência aritmética do IPI ($vBC \times pIPI$).
  - `TAX-TOT-001`: Somatório do valor dos produtos (`vProd`).
  - `TAX-TOT-002`: Somatório do valor do ICMS (`vICMS`).
  - `TAX-TOT-003`: Equação do valor total da nota fiscal (`vNF`).
  - `FIG-CFOP-001`: Coerência entre CFOP e UF do emitente/destinatário (operações internas, interestaduais e exterior).
  - `FIG-CFOP-002`: Restrição de CFOP para NFC-e (modelo 65).
  - `FIG-CST-001`: Validação de incompatibilidade entre CRT do emitente (Simples Nacional vs Regime Normal) e CST/CSOSN.
  - `FIG-CST-003`: Destaque indevido de ICMS em operações isentas (CST 40, 41, 50).
  - `FIG-NCM-001`: Formato e validação estrutural de NCM com 8 dígitos.
  - `FIG-CHAVE-001`: Validação do Dígito Verificador Módulo 11 da Chave de Acesso de DF-e (44 dígitos).
- **Skill Antigravity Reutilizável:** Skill `correcao-figura-fiscal` para agentes de IA com runbooks, scripts e referências para diagnóstico automatizado.
- **Interface de Linha de Comando (CLI):** Comandos `validate`, `fix-suggest`, `rules list` e `verify-key`.
- **Relatórios:** Saídas em texto console com as 6 respostas estruturadas, JSON padronizado e Markdown.
- **Segurança:** Defesa ativa contra XXE e DoS, além de mascaramento obrigatório de dados sensíveis.
- **Fixtures Sintéticas:** Conjunto didático de XMLs para testes e demonstrações sem uso de dados reais.

