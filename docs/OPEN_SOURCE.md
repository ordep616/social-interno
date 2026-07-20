# Código aberto e licenças

Este documento é um inventário técnico inicial, não um parecer jurídico.

## Estratégia

O Telegram Web poderá ser estudado e componentes isolados poderão ser incorporados somente quando o benefício superar o custo de desacoplamento e as obrigações de licença forem aceitas.

## Fontes consultadas na F1

Consulta realizada em 2026-07-20, apenas para estudo técnico. Nenhum código, ativo ou dependência foi incorporado ao repositório.

| Cliente | Repositório | Referência consultada | Licença raiz | Observações |
|---|---|---|---|---|
| Telegram Web K | `https://github.com/morethanwords/tweb` | `b16aaea7744d63d28362235d704c264a4e287510` | GPL-3.0 | README identifica o projeto como Telegram Web K. Alto risco de acoplamento com MTProto, estado interno, assets e worker/cache próprios. |
| Telegram Web A | `https://github.com/Ajaxy/telegram-tt` | `58d8e948efe4ff1212b21d97b45b23b4db65a513` | GPL-3.0 | README identifica o projeto como Telegram Web A, com Teact próprio e customização de GramJS/MTProto. Útil para estudo por ter áreas de UI mais separadas. |

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

## Avaliação inicial por componente

Esta avaliação orienta a F1. O estado `Estudar` permite leitura e comparação de comportamento. O estado `Avaliar` permite pesquisa técnica mais profunda antes de qualquer proposta de incorporação. Nenhuma entrada abaixo está aprovada para uso em produto.

| Área | Referências candidatas | Uso recomendado agora | Risco principal | Próximo passo |
|---|---|---|---|---|
| Layout geral de chat | Web A: `src/components/main`, `src/components/left`, `src/components/middle`; Web K: `src/components` e `src/scss` | Estudar como referência visual e de responsividade | Identidade visual do Telegram e classes/estado globais | Criar design próprio com navegação e layout corporativos, sem copiar marca, cores ou estrutura fiel. |
| Lista de conversas | Web A: `src/components/left/LeftColumn.tsx`, `src/components/left/search`, `src/components/left/main`; Web K: componentes de diálogo/lista em `src/components` | Avaliar apenas padrões de interação | Forte acoplamento a chats, pastas, arquivamento e busca global do Telegram | Modelar lista a partir de `Conversation` corporativa e mocks do contrato. |
| Cabeçalho e painel de conversa | Web A: `src/components/middle/HeaderActions.tsx`, `src/components/middle/MiddleHeaderPanes.tsx`, `src/components/right`; Web K: topbar e painéis em `src/components` | Estudar como referência de densidade e estados | Menus e ações incluem recursos fora do MVP | Definir ações mínimas do MVP: busca local, detalhes, membros, arquivos autorizados. |
| Histórico e lista de mensagens | Web A: `src/components/middle/MessageList.tsx`; Web K: componentes de mensagens em `src/components` | Avaliar cuidadosamente | Virtualização, agrupamento, replies, mídia e estados dependem de tipos Telegram | Implementar histórico paginado por cursor conforme contrato corporativo. |
| Bolhas e renderização de mensagens | Web A: `src/components/middle/message`, `_message-content.scss`; Web K: renderizadores de mensagem em `src/components` | Estudar primeiro, sem copiar | Muitos formatos fora do MVP: stories, polls, gifts, games, premium, reactions específicas | Criar componentes próprios para texto, anexo, resposta, edição/exclusão e confirmação visual do MVP. |
| Compositor | Web A: `src/components/middle/composer`, `TextFormatter.tsx`, `AttachmentModal.tsx`, `SymbolMenu.tsx`; Web K: composer/input em `src/components` | Avaliar padrões de UX | Bot commands, stickers, emoji packs, voz e formatação rica podem sair do escopo | Começar com texto, anexo simulado, resposta e estados de envio definidos pelo contrato. |
| Visualizador de mídia | Web A: `src/components/mediaViewer`; Web K: `appMediaViewer*` em `src/components` | Avaliar por componente | Dependências de streaming, cache, formatos específicos e controles avançados | Implementar visualização segura própria para imagem/documento com URL temporária mockada. |
| Componentes básicos de UI | Web A: `src/components/ui` | Estudar padrões, preferir componentes próprios | Copyleft GPL e estilo visual associado ao Telegram | Criar design system mínimo próprio: botão, campo, avatar, badge, modal, menu, tabs e estados. |
| PWA, cache e service worker | Web A: `src/serviceWorker`; Web K: `sw.ts`, `src/mock`, cache/local storage | Usar apenas como referência | Cache atual é específico de Telegram, mídia e push; risco de persistir dados sensíveis | Definir política própria de cache corporativo antes de implementar PWA/offline. |
| Emojis, stickers e animações | Web A: `SymbolMenu`, componentes de emoji/sticker; Web K: `EMOJI.md`, assets e rlottie | Reavaliar separadamente | Licenças de ativos podem divergir da licença raiz | Usar emoji Unicode básico no MVP; adiar stickers/animações. |
| Áudio e vídeo | Web A: `VoiceRecordBar`, `VideoPlayer`; Web K: `opus-recorder`, media playback | Preferir bibliotecas desacopladas ou adiar | Licenças variadas, codecs e requisitos de privacidade | Fora do MVP para chamadas; áudio gravado só deve entrar após decisão específica. |

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
| OS-001 | Layout geral de chat | Web A: `https://github.com/Ajaxy/telegram-tt`; Web K: `https://github.com/morethanwords/tweb` | Web A `58d8e948efe4ff1212b21d97b45b23b4db65a513`; Web K `b16aaea7744d63d28362235d704c264a4e287510` | GPL-3.0 | Referência visual e responsiva, sem cópia de código | Outro colaborador | Estudar |
| OS-002 | Lista de conversas | Web A: `src/components/left`; Web K: `src/components` | Mesmos commits da F1 | GPL-3.0 | Avaliar padrões de busca, seleção, unread e estados vazios | Outro colaborador | Avaliar |
| OS-003 | Cabeçalho e detalhes da conversa | Web A: `src/components/middle`, `src/components/right`; Web K: `src/components` | Mesmos commits da F1 | GPL-3.0 | Referência de densidade, menus e painéis laterais | Outro colaborador | Estudar |
| OS-004 | Histórico e renderização de mensagens | Web A: `src/components/middle/MessageList.tsx`, `src/components/middle/message`; Web K: `src/components` | Mesmos commits da F1 | GPL-3.0 | Avaliar estrutura de lista, bolhas, anexos, respostas e estados | Outro colaborador | Avaliar com alto risco |
| OS-005 | Compositor de mensagens | Web A: `src/components/middle/composer`; Web K: `src/components` | Mesmos commits da F1 | GPL-3.0 | Avaliar UX de edição, anexos e envio, excluindo bots/stickers/voz por padrão | Outro colaborador | Avaliar |
| OS-006 | Visualizador de mídia | Web A: `src/components/mediaViewer`; Web K: `src/components/appMediaViewer*` | Mesmos commits da F1 | GPL-3.0 | Avaliar padrões de viewer, navegação e controles | Outro colaborador | Avaliar |
| OS-007 | Componentes básicos de UI | Web A: `src/components/ui`; Web K: componentes soltos em `src/components` | Mesmos commits da F1 | GPL-3.0 | Estudo de padrões; implementar equivalentes próprios | Outro colaborador | Estudar |
| OS-008 | PWA, cache e service worker | Web A: `src/serviceWorker`; Web K: `sw.ts` | Mesmos commits da F1 | GPL-3.0 | Referência arquitetural para cache, nunca política pronta | Outro colaborador | Estudar com alto risco |
| OS-009 | Emojis, stickers e animações | Web A: `SymbolMenu` e mensagem/emoji; Web K: `EMOJI.md`, assets e rlottie | Mesmos commits da F1 | GPL-3.0 e licenças de ativos a confirmar | Adiar incorporação; usar apenas emoji Unicode básico no MVP | Outro colaborador | Reavaliar |
| OS-010 | Áudio, vídeo e gravação | Web A: `VoiceRecordBar`, `VideoPlayer`; Web K: `opus-recorder`, media playback | Mesmos commits da F1 | GPL-3.0 e licenças variadas de dependências | Adiar ou substituir por biblioteca desacoplada após decisão | Outro colaborador | Adiar |

## Regra de isolamento

Código aprovado de terceiros deve ficar rastreável, preferencialmente em `third_party/`, acompanhado de avisos e inventário. Componentes reutilizados só podem consumir interfaces próprias do projeto, nunca clientes, endpoints ou tipos MTProto.

## GPL

Clientes web distribuídos sob GPL devem ser tratados como código copyleft. Antes de criar um fork ou obra derivada, a organização precisa aceitar as obrigações aplicáveis de fornecimento do código-fonte correspondente aos destinatários.

## Pendências para integração

- Confirmar se a organização aceita estudar apenas referências visuais GPL ou se qualquer derivação visual também deve passar por revisão jurídica.
- Definir a licença do código próprio antes de qualquer incorporação ou adaptação de código de terceiros.
- Definir identidade visual própria para reduzir risco de semelhança indevida com Telegram.
- Validar com o backend, no próximo marco, quais estados do contrato precisam aparecer nos mocks: permissões de edição/exclusão, upload, presença, digitação, leitura e erros autorizativos.
