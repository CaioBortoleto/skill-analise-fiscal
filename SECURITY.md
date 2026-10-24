# Política de Segurança e Privacidade Fiscal

## 1. Compromisso com Dados Fiscais Sensíveis

Documentos fiscais eletrônicos (NF-e, NFC-e, CT-e) contêm informações comerciais confidenciais e dados pessoais protegidos pela LGPD (Lei nº 13.709/2018).

Este projeto foi construído sob três diretrizes de proteção:
1. **Zero persistência não autorizada:** O motor de validação fiscal opera localmente e em memória, não transmitindo XMLs, notas fiscais ou certificados para servidores externos.
2. **Mascaramento estrutural:** Chaves de acesso, CPFs e dados de destinatários são mascarados antes de qualquer saída pública em logs e relatórios.
3. **Defesa ativa contra entradas maliciosas:** O parser desabilita DTDs externos por padrão, prevenindo ataques do tipo XML External Entity (XXE) e expansões de entidades (Billion Laughs / XML Bombs).

## 2. Relato Responsável de Vulnerabilidades

Caso identifique uma falha de segurança ou potencial vazamento de dados, pedimos a gentileza de **não abrir uma issue pública**.

Envie os detalhes técnicos para a equipe mantenedora através de canal seguro ou abra uma **Security Advisory** privada no GitHub.

