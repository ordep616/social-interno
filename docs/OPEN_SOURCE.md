# Código aberto e licenças

Este documento é um inventário técnico inicial, não um parecer jurídico.

## Estratégia atual

O projeto adaptará uma plataforma Matrix auto-hospedada e criará uma interface própria. O objetivo não é copiar integralmente Telegram Web ou Element Web.

## Componentes principais a avaliar

| Área | Orientação inicial | Observação |
|---|---|---|
| Protocolo Matrix | Adotar | Usar especificação e APIs padronizadas |
| Synapse | Prova de conceito e revisão | Verificar versão, licença AGPL/comercial e operação |
| `matrix-js-sdk` | Adotar após registro | SDK com licença permissiva; fixar versão e commit |
| Element Web | Somente referência por padrão | Não copiar código antes de avaliar AGPL/GPL e dependências |
| Telegram Web | Somente referência por padrão | Não é necessário para a arquitetura Matrix |
| FastAPI | Opcional | Apenas para integrações corporativas futuras |
| Identidade e ícones oficiais | Não utilizar | O produto terá marca e ativos próprios |

## Processo de incorporação

1. Registrar repositório oficial e hash do commit ou versão da imagem.
2. Ler a licença raiz e licenças específicas.
3. Identificar dependências, imagens de contêiner e ativos associados.
4. Registrar a finalidade e a forma de integração.
5. Registrar configurações ou alterações mantidas pela equipe.
6. Obter revisão do outro colaborador.
7. Obter revisão jurídica quando houver copyleft, distribuição ou oferta pela rede relevante.
8. Preservar avisos e atribuições obrigatórias.

## Inventário

| ID | Componente | Origem | Versão/commit | Licença | Uso pretendido | Responsável | Estado |
|---|---|---|---|---|---|---|---|
| OS-001 | Synapse | `https://github.com/element-hq/synapse` | `v1.156.0` | AGPL-3.0 ou licença comercial | Homeserver da prova de conceito | Colaborador 1 | Configuração incorporada; execução e revisão jurídica pendentes |
| OS-002 | matrix-js-sdk | `https://github.com/matrix-org/matrix-js-sdk` | `v41.9.0` / `ab38767` | Apache-2.0 | SDK atrás de adaptador próprio | Colaborador 2 | Dependência incorporada; revisão pendente |
| OS-003 | Element Web | A registrar se houver uso | — | AGPL/GPL/comercial, a confirmar | Somente referência inicial | Colaborador 2 | Não incorporar |
| OS-004 | Telegram Web | A registrar se houver uso | — | GPL, a confirmar por repositório | Somente referência inicial | Colaborador 2 | Não incorporar |
| OS-005 | PostgreSQL | `https://github.com/postgres/postgres` | imagem `17.6-alpine` | PostgreSQL License | Banco do Synapse na prova de conceito | Colaborador 1 | Configuração incorporada |

## Regra de isolamento

- O acesso ao `matrix-js-sdk` deve ficar atrás de um adaptador próprio do frontend.
- Alterações de configuração do Synapse devem ficar rastreáveis na área `platform/`.
- Código copiado de terceiros deve preservar origem, licença e alterações.
- Não importar código do Element ou Telegram apenas por semelhança visual.
- Não usar MTProto, GramJS, TDLib, `api_id`, `api_hash` ou infraestrutura do Telegram.

## Revisão antes do piloto

Antes da homologação, revisar conjuntamente licenças do servidor, SDK, imagens de contêiner, bibliotecas do frontend, fontes, ícones, emojis e qualquer ativo distribuído.
