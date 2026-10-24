# Regras Aritméticas e Somatórios em Documentos Fiscais

Referência técnica para conferência dos cálculos de impostos e totais da NF-e e NFC-e.

---

## 1. Arredondamento Fiscal Brasileiro

Conforme a norma ABNT NBR 5891 e o Manual de Orientação do Contribuinte (MOC) da SEFAZ:
- Os cálculos intermediários devem ser apurados com a precisão permitida pelo layout (geralmente 2 a 4 casas decimais para alíquotas e quantidades).
- O valor financeiro final de cada tributo e total deve ser quantizado em **2 casas decimais** utilizando arredondamento bancário (`ROUND_HALF_UP`).
- É aceita uma tolerância de até R$ 0,01 decorrente do somatório de parcelas rateadas por item.

---

## 2. Fórmulas de Cálculo por Item

### A. ICMS Próprio (CST 00)
$$vICMS = \mathrm{round}(vBC \times \frac{pICMS}{100}, 2)$$
- Se houver redução de base (CST 20):
$$vBC = \mathrm{round}(vProd \times (1 - \frac{pRedBC}{100}), 2)$$

### B. PIS e COFINS
$$vPIS = \mathrm{round}(vBC \times \frac{pPIS}{100}, 2)$$
$$vCOFINS = \mathrm{round}(vBC \times \frac{pCOFINS}{100}, 2)$$

### C. IPI
$$vIPI = \mathrm{round}(vBC \times \frac{pIPI}{100}, 2)$$

---

## 3. Somatórios e Totais da Nota (`ICMSTot`)

O grupo `total/ICMSTot` deve refletir estritamente a soma dos itens:

| Campo no `ICMSTot` | Origem da Soma | Código de Rejeição SEFAZ |
|---|---|---|
| `vProd` | $\sum \mathrm{det/prod/vProd}$ | **Rejeição 531** |
| `vICMS` | $\sum \mathrm{det/imposto/ICMS/.../vICMS}$ | **Rejeição 532** |
| `vBC` | $\sum \mathrm{det/imposto/ICMS/.../vBC}$ | **Rejeição 533** |
| `vBCST` | $\sum \mathrm{det/imposto/ICMS/.../vBCST}$ | **Rejeição 534** |
| `vST` | $\sum \mathrm{det/imposto/ICMS/.../vICMSST}$ | **Rejeição 534** |
| `vPIS` | $\sum \mathrm{det/imposto/PIS/.../vPIS}$ | **Rejeição 602** |
| `vCOFINS` | $\sum \mathrm{det/imposto/COFINS/.../vCOFINS}$ | **Rejeição 603** |
| `vIPI` | $\sum \mathrm{det/imposto/IPI/.../vIPI}$ | **Rejeição 536** |

### Equação do Valor Total da NF-e (`vNF`):
$$vNF = vProd - vDesc - vICMSDeson + vST + vFCPST + vFrete + vSeg + vOutro + vII + vIPI + vIPIDevol$$

> Se $vNF$ informado divergir do somatório resultante dessa equação, a SEFAZ retornará **Rejeição 535: Total do Frete/Seguro/Desconto/NF difere do somatório dos itens**.

