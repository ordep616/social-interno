# Contratos compartilhados

Esta é a única área técnica que normalmente exige aprovação dos dois colaboradores.

## Estado

Versão atual: `v1-draft`.

Os arquivos ainda são propostas. Depois da revisão conjunta, registrar `v1-approved` em `VERSION` e em `docs/DECISIONS.md`.

## Conteúdo

- `openapi.yaml`: contrato HTTP inicial.
- `events/`: esquemas dos eventos em tempo real.
- `examples/`: dados simulados para frontend e testes do backend.

## Compatibilidade

- Adicionar campo opcional pode ser compatível.
- Remover ou renomear campos exige nova versão.
- Alterar o significado de um campo exige nova versão.
- O frontend não deve depender de campos ausentes no contrato.
- O backend não deve retornar formatos diferentes dos exemplos sem atualizar o contrato.
