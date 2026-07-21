# Instruções locais — plataforma

## Finalidade

Esta pasta pertence ao Colaborador 1 e contém Synapse, PostgreSQL,
configuração, infraestrutura, segurança e operação.

## Regras

- O Synapse é o servidor de mensagens; não crie outro backend de chat.
- Mantenha cadastro público e comunicação externa desabilitados.
- Não coloque segredos, chaves ou credenciais reais no repositório.
- Não altere `../frontend/`; valide a plataforma com um cliente Matrix genérico.
- Não acesse diretamente o banco do Synapse para implementar regras de negócio.
- OIDC, federação, criptografia, retenção e convenções compartilhadas exigem
  decisão conjunta antes de mudanças definitivas.
- Preserve versões explícitas e registre dependências em `../docs/OPEN_SOURCE.md`.

## Validação

Mudanças devem incluir os testes operacionais aplicáveis, documentação de
configuração e, quando relevante, procedimento de restauração ou reversão.
