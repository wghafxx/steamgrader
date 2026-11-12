import { useEffect, useRef, useState } from "react";
import { Lock, Send } from "lucide-react";
import { useAuth } from "@/context/AuthContext";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const MAX = 300;

const time = (iso) => new Date(iso).toLocaleTimeString("ru", { hour: "2-digit", minute: "2-digit" });

const Message = ({ m, own }) => (
  <div className={`chat-msg ${own ? "is-own" : ""}`} data-testid={`chat-message-${m.id}`}>
    <span className="st-avatar">
      {m.avatar ? <img src={m.avatar} alt="" /> : <span className="st-avatar-empty">?</span>}
    </span>
    <div className="chat-msg-body">
      <div className="chat-msg-head">
        <b>{m.nickname}</b>
        <time>{time(m.created_at)}</time>
      </div>
      <p>{m.text}</p>
    </div>
  </div>
);

export const Chat = () => {
  const { user, loading, setLoginOpen } = useAuth();
  const [messages, setMessages] = useState([]);
  const [text, setText] = useState("");
  const [error, setError] = useState("");
  const listRef = useRef(null);
  const lastId = messages[messages.length - 1]?.id;

  useEffect(() => {
    if (!user) return undefined;
    const load = async () => {
      try {
        const res = await fetch(`${API}/chat/messages`, { credentials: "include" });
        if (res.ok) setMessages((await res.json()).messages);
      } catch {
        setError("Нет связи с сервером");
      }
    };
    load();
    const timer = setInterval(load, 3000);
    return () => clearInterval(timer);
  }, [user]);

  useEffect(() => {
    if (listRef.current) listRef.current.scrollTop = listRef.current.scrollHeight;
  }, [lastId]);

  const send = async (e) => {
    e.preventDefault();
    if (!text.trim()) return;
    setError("");
    const res = await fetch(`${API}/chat/messages`, {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    const data = await res.json();
    if (!res.ok) {
      setError(typeof data.detail === "string" ? data.detail : "Сообщение не отправлено");
      return;
    }
    setMessages((prev) => (prev.some((m) => m.id === data.id) ? prev : [...prev, data]));
    setText("");
  };

  if (loading) return null;

  if (!user) {
    return (
      <section className="chat chat--locked" data-testid="chat-locked">
        <Lock size={34} />
        <b>Общий чат только для вошедших</b>
        <span>Войдите через Steam, чтобы читать и писать сообщения</span>
        <button className="btn-login" onClick={() => setLoginOpen(true)} data-testid="chat-login-button">Войти</button>
      </section>
    );
  }

  return (
    <section className="chat" data-testid="chat">
      <div className="chat-head">
        <h2 className="sec-title">Общий чат</h2>
        <span data-testid="chat-rules">Без ссылок, рекламы и спама</span>
      </div>
      <div className="chat-list" ref={listRef} data-testid="chat-list">
        {messages.length === 0 && <div className="chat-empty" data-testid="chat-empty">Сообщений пока нет. Напишите первым</div>}
        {messages.map((m) => <Message key={m.id} m={m} own={m.steamid === user.steamid} />)}
      </div>
      {error && <div className="chat-error" data-testid="chat-error">{error}</div>}
      <form className="chat-form" onSubmit={send} data-testid="chat-form">
        <input
          value={text}
          onChange={(e) => setText(e.target.value)}
          maxLength={MAX}
          placeholder="Написать сообщение"
          data-testid="chat-input"
        />
        <span className="chat-count" data-testid="chat-counter">{text.length}/{MAX}</span>
        <button type="submit" disabled={!text.trim()} data-testid="chat-send-button" aria-label="Отправить">
          <Send size={17} />
        </button>
      </form>
    </section>
  );
};
