# Guia de Contribuição

Obrigado pelo interesse em contribuir para o validador e auditor de figuras fiscais!

Nossa missão é construir a ferramenta open source mais confiável, acessível e segura para validação e correção de documentos fiscais brasileiros.

## Princípios de Contribuição

1. **Apenas dados sintéticos:** **NUNCA** inclua XMLs reais, chaves de acesso reais, certificados digitais (`.pfx`, `.pem`, `.cer`) ou dados pessoais de terceiros em issues, fixtures de teste, pull requests ou documentação. Utilize exclusivamente fixtures didáticas com a tag `<!-- FICTÍCIO -->`.
2. **Fundamentação normativa:** Ao propor ou alterar uma regra fiscal, informe a fonte legal ou técnica (Nota Técnica da SEFAZ, Manual de Orientação do Contribuinte, Ajuste SINIEF, Lei Complementar ou Convênio).
3. **Explicação e Diff:** Toda regra deve fornecer uma mensagem clara que responda:
   - Onde está o problema?
   - O que foi encontrado?
   - O que era esperado?
   - Qual regra foi violada?
   - Qual é o impacto fiscal?
   - Como corrigir?
4. **Testes obrigatórios:** Toda nova regra deve conter testes unitários positivos (onde o XML válido passa) e testes negativos (onde o erro é detectado com o XPath correto).

## Como Executar os Testes

```bash
python -m unittest discover -s tests
```

