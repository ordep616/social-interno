"use client";

import { FormEvent, useMemo, useState } from "react";

type Conversation = {
  id: number;
  name: string;
  initials: string;
  preview: string;
  time: string;
  unread?: number;
  online?: boolean;
  color: string;
};

const conversations: Conversation[] = [
  { id: 1, name: "Produto & Design", initials: "PD", preview: "Marina: Fechamos a pauta de hoje?", time: "10:42", unread: 3, color: "#7259d9" },
  { id: 2, name: "Carlos Mendes", initials: "CM", preview: "O documento já está na pasta.", time: "10:31", online: true, color: "#218a78" },
  { id: 3, name: "Comunicados", initials: "CO", preview: "RH: Novo calendário disponível", time: "09:15", color: "#d7684f" },
  { id: 4, name: "Equipe Comercial", initials: "EC", preview: "Você: Perfeito, envio ainda hoje.", time: "Ontem", color: "#bf8735" },
  { id: 5, name: "Fernanda Lima", initials: "FL", preview: "Obrigada pela ajuda!", time: "Ontem", color: "#b44f7c" },
];

const initialMessages = [
  { id: 1, author: "Marina", text: "Bom dia! Atualizei a proposta com os pontos da reunião.", time: "10:18", mine: false },
  { id: 2, author: "Você", text: "Ótimo. Vou revisar a parte de segurança e acesso corporativo.", time: "10:22", mine: true },
  { id: 3, author: "Rafael", text: "Incluí também a matriz de componentes que podemos adaptar do projeto aberto.", time: "10:29", mine: false },
  { id: 4, author: "Marina", text: "Fechamos a pauta de hoje? Depois seguimos com o protótipo para homologação.", time: "10:42", mine: false },
];

export default function Home() {
  const [active, setActive] = useState(1);
  const [query, setQuery] = useState("");
  const [draft, setDraft] = useState("");
  const [messages, setMessages] = useState(initialMessages);

  const visibleConversations = useMemo(
    () => conversations.filter((item) => item.name.toLowerCase().includes(query.toLowerCase())),
    [query],
  );
  const current = conversations.find((item) => item.id === active) ?? conversations[0];

  function sendMessage(event: FormEvent) {
    event.preventDefault();
    const text = draft.trim();
    if (!text) return;
    setMessages((items) => [...items, { id: Date.now(), author: "Você", text, time: "agora", mine: true }]);
    setDraft("");
  }

  return (
    <main className="app-shell">
      <aside className="rail" aria-label="Navegação principal">
        <div className="brand-mark" aria-label="Nexo">N</div>
        <nav>
          <button className="rail-button active" aria-label="Conversas">⌁</button>
          <button className="rail-button" aria-label="Contatos">♙</button>
          <button className="rail-button" aria-label="Arquivos">▱</button>
        </nav>
        <div className="rail-bottom">
          <button className="rail-button" aria-label="Configurações">⚙</button>
          <div className="avatar small">PO</div>
        </div>
      </aside>

      <section className="inbox" aria-label="Conversas">
        <header className="inbox-header">
          <div>
            <p className="eyebrow">ESPAÇO DE TRABALHO</p>
            <h1>Nexo</h1>
          </div>
          <button className="new-chat" aria-label="Nova conversa">＋</button>
        </header>
        <label className="search">
          <span>⌕</span>
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Buscar conversas" />
        </label>
        <div className="section-label"><span>Recentes</span><button>Filtrar</button></div>
        <div className="conversation-list">
          {visibleConversations.map((item) => (
            <button key={item.id} className={`conversation ${item.id === active ? "selected" : ""}`} onClick={() => setActive(item.id)}>
              <span className="avatar" style={{ background: item.color }}>{item.initials}{item.online && <i />}</span>
              <span className="conversation-copy">
                <span className="conversation-top"><strong>{item.name}</strong><time>{item.time}</time></span>
                <span className="conversation-bottom"><span>{item.preview}</span>{item.unread && <b>{item.unread}</b>}</span>
              </span>
            </button>
          ))}
        </div>
        <footer className="security-note"><span>●</span> Ambiente corporativo protegido</footer>
      </section>

      <section className="chat" aria-label={`Conversa com ${current.name}`}>
        <header className="chat-header">
          <div className="chat-person">
            <span className="avatar" style={{ background: current.color }}>{current.initials}</span>
            <div><strong>{current.name}</strong><span>{current.id === 1 ? "8 participantes" : current.online ? "online agora" : "membro da organização"}</span></div>
          </div>
          <div className="header-actions"><button aria-label="Pesquisar na conversa">⌕</button><button aria-label="Detalhes">···</button></div>
        </header>

        <div className="messages">
          <div className="date-pill">Hoje</div>
          <div className="encryption"><span>◆</span><div><strong>Conversa interna</strong><p>Mensagens e arquivos permanecem no ambiente da organização.</p></div></div>
          {messages.map((message) => (
            <article key={message.id} className={`message ${message.mine ? "mine" : ""}`}>
              {!message.mine && <span className="message-author">{message.author}</span>}
              <p>{message.text}</p>
              <time>{message.time}{message.mine && "  ✓✓"}</time>
            </article>
          ))}
        </div>

        <form className="composer" onSubmit={sendMessage}>
          <button type="button" aria-label="Anexar arquivo">＋</button>
          <input value={draft} onChange={(event) => setDraft(event.target.value)} placeholder="Escreva uma mensagem…" aria-label="Mensagem" />
          <button type="button" aria-label="Adicionar emoji">☺</button>
          <button className="send" type="submit" aria-label="Enviar mensagem">➤</button>
        </form>
      </section>

      <aside className="details" aria-label="Detalhes da conversa">
        <div className="detail-hero">
          <span className="avatar large" style={{ background: current.color }}>{current.initials}</span>
          <h2>{current.name}</h2>
          <p>{current.id === 1 ? "8 participantes" : "Conta corporativa"}</p>
        </div>
        <div className="quick-actions"><button><span>⌕</span>Buscar</button><button><span>♧</span>Silenciar</button></div>
        <div className="detail-block"><button>Arquivos compartilhados <b>12</b><span>›</span></button><button>Links <b>5</b><span>›</span></button></div>
        <div className="detail-block"><h3>Governança</h3><p><span className="status-dot" /> Retenção de 365 dias</p><p><span className="status-dot" /> Auditoria habilitada</p></div>
      </aside>
    </main>
  );
}
