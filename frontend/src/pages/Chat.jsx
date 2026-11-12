import { useCallback, useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import { api } from "../api";
import Icon from "../components/Icon";

const EXAMPLES = [
  "How many days of annual leave do I get?",
  "How many sick days do I have left?",
  "Can I claim 30,000 INR for a client dinner?",
  "What's the status of my expense claims?",
];

function Sources({ sources }) {
  const [open, setOpen] = useState(null);
  return (
    <div className="sources">
      <span className="sources-label">Sources</span>
      <ul>
        {sources.map((s, i) => (
          <li key={`${s.source}-${s.page}-${i}`}>
            <button className="doc" aria-expanded={open === i} onClick={() => setOpen(open === i ? null : i)}>
              <Icon name="document" size={16} />
              <span className="doc-name">{s.source}</span>
              {s.page > 0 && <span className="doc-page">page {s.page}</span>}
            </button>
            {open === i && <blockquote className="snippet">{s.snippet}</blockquote>}
          </li>
        ))}
      </ul>
    </div>
  );
}

function Message({ m, feedback, copied, onFeedback, onCopy }) {
  if (m.role === "user") {
    return (
      <div className="msg user">
        <p>{m.content}</p>
      </div>
    );
  }
  return (
    <div className="msg bot">
      <div className="prose">
        <ReactMarkdown>{m.content}</ReactMarkdown>
      </div>
      {m.sources?.length > 0 && <Sources sources={m.sources} />}
      <div className="answer-actions" aria-label="Answer actions">
        <button className={`icon-action ${feedback === "up" ? "selected" : ""}`} type="button" title="Helpful" aria-label="This answer was helpful" aria-pressed={feedback === "up"} onClick={() => onFeedback(feedback === "up" ? null : "up")}><Icon name="thumbUp" size={17} /></button>
        <button className={`icon-action ${feedback === "down" ? "selected" : ""}`} type="button" title="Not helpful" aria-label="This answer was not helpful" aria-pressed={feedback === "down"} onClick={() => onFeedback(feedback === "down" ? null : "down")}><Icon name="thumbDown" size={17} /></button>
        <button className="icon-action" type="button" title={copied ? "Copied" : "Copy answer"} aria-label={copied ? "Answer copied" : "Copy answer"} onClick={onCopy}><Icon name="copy" size={17} /></button>
        {copied && <span className="copy-status" role="status">Copied</span>}
        {feedback && <span className="copy-status" role="status">Thanks for your feedback</span>}
      </div>
    </div>
  );
}

export default function Chat() {
  const [conversations, setConversations] = useState([]);
  const [activeId, setActiveId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [answerFeedback, setAnswerFeedback] = useState({});
  const [copiedKey, setCopiedKey] = useState("");
  const activeRef = useRef(null); // always the current conversation, even inside async code
  const endRef = useRef(null);

  const refreshList = useCallback(() => api.conversations().then(setConversations).catch(() => {}), []);
  useEffect(() => {
    refreshList();
  }, [refreshList]);
  useEffect(() => {
    endRef.current?.scrollIntoView?.({ behavior: "smooth", block: "end" });
  }, [messages, sending]);

  function setActive(id) {
    activeRef.current = id;
    setActiveId(id);
  }

  async function openConversation(id) {
    setSidebarOpen(false);
    setError("");
    setActive(id);
    try {
      const c = await api.conversation(id);
      if (activeRef.current === id) setMessages(c.messages);
    } catch (e) {
      setError(e.message);
    }
  }

  function newChat() {
    setActive(null);
    setMessages([]);
    setError("");
    setAnswerFeedback({});
    setCopiedKey("");
    setSidebarOpen(false);
  }

  function messageKey(index) {
    return `${activeId ?? "draft"}:${index}`;
  }

  async function copyAnswer(text, key) {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedKey(key);
      window.setTimeout(() => setCopiedKey((current) => current === key ? "" : current), 1800);
    } catch {
      setError("Clipboard access is unavailable in this browser.");
    }
  }

  async function removeConversation(id) {
    if (!window.confirm("Delete this conversation?")) return;
    try {
      await api.deleteConversation(id);
      if (activeRef.current === id) newChat();
      refreshList();
    } catch (e) {
      setError(e.message);
    }
  }

  async function send(text) {
    const message = text.trim();
    if (!message || sending) return;
    const convId = activeRef.current;
    setInput("");
    setError("");
    setSending(true);
    setMessages((m) => [...m, { role: "user", content: message, sources: [] }]);
    try {
      const res = await api.chat(message, convId);
      if (activeRef.current === convId) {
        if (convId === null) setActive(res.conversation_id);
        setMessages((m) => [...m, { role: "assistant", content: res.answer, sources: res.sources }]);
      }
      refreshList();
    } catch (e) {
      if (activeRef.current === convId) setMessages((m) => m.slice(0, -1)); // take the question back
      setInput(message);
      setError(e.message);
    } finally {
      setSending(false);
    }
  }

  function onKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send(input);
    }
  }

  return (
    <div className="chat">
      <aside className={`sidebar ${sidebarOpen ? "open" : ""}`} aria-label="Conversations">
        <button className="btn primary wide" onClick={newChat}><Icon name="plus" />New chat</button>
        {conversations.length === 0 ? (
          <p className="muted pad">Your conversations will appear here.</p>
        ) : (
          <ul className="convs">
            {conversations.map((c) => (
              <li key={c.id} className={c.id === activeId ? "active" : ""}>
                <button className="conv-title" onClick={() => openConversation(c.id)}>{c.title}</button>
                <button className="conv-del" aria-label={`Delete conversation: ${c.title}`} onClick={() => removeConversation(c.id)}>×</button>
              </li>
            ))}
          </ul>
        )}
      </aside>

      <section className="thread">
        <button className="btn ghost menu-btn" onClick={() => setSidebarOpen(!sidebarOpen)} aria-expanded={sidebarOpen}>
          Conversations
        </button>

        <div className="messages">
          <div className="messages-inner">
            {messages.length === 0 && !sending ? (
              <div className="empty">
                <h2>What do you want to know about company policy?</h2>
                <p className="muted">Answers come only from your company's documents, with sources you can open.</p>
                <ul>
                  {EXAMPLES.map((q) => (
                    <li key={q}>
                      <button onClick={() => send(q)}>{q}</button>
                    </li>
                  ))}
                </ul>
              </div>
            ) : (
              messages.map((m, i) => {
                const key = messageKey(i);
                return <Message key={i} m={m} feedback={answerFeedback[key]} copied={copiedKey === key} onFeedback={(value) => setAnswerFeedback((current) => ({ ...current, [key]: value }))} onCopy={() => copyAnswer(m.content, key)} />;
              })
            )}
            {sending && (
              <div className="msg bot thinking" role="status">
                Checking the policies<span className="dots" aria-hidden="true"><i /><i /><i /></span>
              </div>
            )}
            <div ref={endRef} />
          </div>
        </div>

        <div className="composer">
          <div className="composer-inner">
            {error && <p className="error" role="alert">{error}</p>}
            <div className="composer-row">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={onKeyDown}
                placeholder="Ask a question about a policy"
                aria-label="Your question"
                rows={1}
                maxLength={2000}
              />
              <button className="btn primary" onClick={() => send(input)} disabled={sending || !input.trim()}>
                Send
              </button>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
