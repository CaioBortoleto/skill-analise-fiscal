# Matriz Fiscal: CFOP, CST, CSOSN e Enquadramento Tributário

Referência técnica para apoio à auditoria e conferência de figuras fiscais brasileiras.

---

## 1. Regra Geográfica de CFOP (Código Fiscal de Operações e Prestações)

O primeiro dígito do CFOP define a abrangência territorial da operação:

| Primeiro Dígito | Sentido da Operação | Abrangência | Relação de UF |
|---|---|---|---|
| **1** | Entrada / Aquisição | Interna | UF Emitente == UF Destinatário |
| **2** | Entrada / Aquisição | Interestadual | UF Emitente != UF Destinatário |
| **3** | Entrada / Importação | Exterior | Destinatário no Exterior ou Importação direta |
| **5** | Saída / Prestação | Interna | UF Emitente == UF Destinatário |
| **6** | Saída / Prestação | Interestadual | UF Emitente != UF Destinatário |
| **7** | Saída / Exportação | Exterior | Destinatário no Exterior (`idDest=3` ou `UF=EX`) |

### Rejeições SEFAZ Relacionadas:
- **Rejeição 522:** CFOP de Operação Interna e UF do emitente difere da UF do destinatário.
- **Rejeição 523:** CFOP não é de Operação Interna e UF do emitente é igual à UF do destinatário.
- **Rejeição 725:** NFC-e com CFOP inválido (NFC-e modelo 65 só aceita CFOP iniciado por 5).
- **Rejeição 778/779:** Informado CFOP de operação interna/interestadual para destinatário no exterior.

---

## 2. Regime Tributário (CRT) vs CST / CSOSN

O Código de Regime Tributário (`CRT`) do emitente determina qual tabela de situação tributária do ICMS deve ser utilizada:

### CRT 1 — Simples Nacional
Obrigatório o uso de **CSOSN** (Tabela B do Simples Nacional).
- `101`: Tributada pelo Simples Nacional com permissão de crédito de ICMS.
- `102`: Tributada pelo Simples Nacional sem permissão de crédito.
- `103`: Isenção do ICMS no Simples Nacional para faixa de receita bruta.
- `201`: Tributada pelo Simples Nacional com permissão de crédito e com cobrança do ICMS por Substituição Tributária (ST).
- `202`: Tributada pelo Simples Nacional sem permissão de crédito e com cobrança do ICMS por ST.
- `203`: Isenção do ICMS no Simples Nacional para faixa de receita e cobrança de ST.
- `300`: Imune.
- `400`: Não tributada pelo Simples Nacional.
- `500`: ICMS cobrado anteriormente por substituição tributária (substituído) ou por antecipação.
- `900`: Outros (aplicável em casos excepcionais previstos na legislação estadual).

> **Atenção:** Empresas com `CRT=1` que utilizam CST normal (ex: CST 00) recebem **Rejeição 590: Informado CST para emitente do Simples Nacional**.

### CRT 3 — Regime Normal (Lucro Presumido / Lucro Real)
Obrigatório o uso de **CST** de 2 dígitos (Tabela B do Convênio S/Nº de 1970).
- `00`: Tributada integralmente (exige `vBC`, `pICMS`, `vICMS`).
- `10`: Tributada e com cobrança do ICMS por substituição tributária.
- `20`: Com redução de base de cálculo (exige `pRedBC`, `vBC`, `pICMS`, `vICMS`).
- `30`: Isenta ou não tributada e com cobrança do ICMS por substituição tributária.
- `40`: Isenta.
- `41`: Não tributada.
- `50`: Suspensão.
- `51`: Diferimento (pode exigir cálculo de diferimento parcial ou total).
- `60`: ICMS cobrado anteriormente por substituição tributária.
- `70`: Com redução de base de cálculo e cobrança do ICMS por substituição tributária.
- `90`: Outras.

> **Atenção:** Empresas com `CRT=3` que utilizam CSOSN recebem **Rejeição 591: Informado CSOSN para emitente do Regime Normal**.

