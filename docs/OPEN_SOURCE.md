# Código aberto e licenças

Este documento é um inventário técnico inicial, não um parecer jurídico.

## Estratégia

O Telegram Web poderá ser estudado e componentes isolados poderão ser incorporados somente quando o benefício superar o custo de desacoplamento e as obrigações de licença forem aceitas.

## Classificação inicial

| Área | Orientação inicial | Motivo |
|---|---|---|
| Layout de chat | Usar como referência ou avaliar adaptação | Alto valor visual |
| Lista de conversas | Avaliar componente isolado | Pode estar acoplada ao estado interno |
| Renderização de mensagens | Avaliar cuidadosamente | Depende de tipos e recursos específicos |
| Visualizadores de mídia | Avaliar por componente | Conferir dependências e ativos |
| Gravação e reprodução de áudio | Preferir bibliotecas desacopladas | Facilita licenciamento e manutenção |
| Cache, PWA e Web Workers | Usar como referência | Sincronização atual é específica do Telegram |
| Emojis e stickers | Reavaliar código e ativos separadamente | Licenças podem ser diferentes |
| MTProto e GramJS | Não utilizar | Ligação direta com a plataforma Telegram |
| TDLib | Não utilizar na comunicação do produto | É biblioteca cliente, não backend corporativo |
| Login do Telegram | Remover | Será substituído por identidade corporativa |
| Canais, bots e busca global | Remover | Fora do escopo do produto privado |
| Chamadas | Adiar | Exigem infraestrutura e segurança adicionais |

## Processo de incorporação

1. Registrar repositório e hash do commit.
2. Ler a licença raiz e licenças específicas.
3. Identificar dependências e ativos associados.
4. Verificar se o componente pode ser desacoplado da Telegram API.
5. Registrar alterações pretendidas.
6. Obter revisão do outro colaborador.
7. Obter revisão jurídica quando houver distribuição ou copyleft relevante.
8. Preservar avisos e atribuições obrigatórias.

## Inventário

| ID | Componente | Origem | Commit | Licença | Uso pretendido | Responsável | Estado |
|---|---|---|---|---|---|---|---|
| OS-001 | A definir | — | — | — | — | Outro colaborador | Em análise |

## Regra de isolamento

Código aprovado de terceiros deve ficar rastreável, preferencialmente em `third_party/`, acompanhado de avisos e inventário. Componentes reutilizados só podem consumir interfaces próprias do projeto, nunca clientes, endpoints ou tipos MTProto.

## GPL

Clientes web distribuídos sob GPL devem ser tratados como código copyleft. Antes de criar um fork ou obra derivada, a organização precisa aceitar as obrigações aplicáveis de fornecimento do código-fonte correspondente aos destinatários.
