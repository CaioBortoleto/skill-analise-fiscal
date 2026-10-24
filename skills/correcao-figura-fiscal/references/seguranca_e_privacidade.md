# Segurança, Proteção de Dados e Tratamento de XMLs Reais

Em conformidade com a LGPD (Lei Geral de Proteção de Dados) e as seções 5.2 e 13 do AGENTS.md.

---

## 1. Classificação de Documentos Fiscais

Cada documento submetido à auditoria deve ser classificado em uma das seguintes categorias:
- `synthetic`: Arquivo fictício gerado especificamente para testes, benchmarks ou demonstrações.
- `user_provided`: Documento local submetido pelo usuário para auditoria.
- `authorized_remote`: Documento consultado via canal oficial autorizado com certificado digital.
- `unknown`: Procedência não confirmada.

---

## 2. Mascaramento Obrigatório em Logs e Relatórios

XMLs fiscais contêm dados comerciais sensíveis e dados pessoais (CPF de destinatários, endereços, faturamento).

- **Chave de Acesso:** Nunca expor os 44 dígitos completos em relatórios públicos ou logs. Exibir mascarado: `3524...0017 (mascarada)`.
- **CPF:** Mascarar os primeiros e últimos dígitos: `***.456.789-**`.
- **CNPJ:** Apresentar com formato parcial em materiais de demonstração.

---

## 3. Prevenção de Ataques XML (XXE e DoS)

- **Desativação de DTDs Externas:** O parser bloqueia qualquer documento que contenha declarações `<!DOCTYPE` ou `<!ENTITY` com apontamento para URIs externas ou arquivos locais.
- **Limite de Tamanho:** Arquivos acima de 15 MB são rejeitados antes da interpretação em memória.
- **Contagem de Elementos:** Documentos com mais de 100.000 nós XML disparam exceção de sobrecarga para evitar ataques do tipo *Billion Laughs* / *XML Bomb*.

