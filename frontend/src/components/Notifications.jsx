import { useEffect, useState } from "react";
import { Bell } from "lucide-react";
import { useAuth } from "@/context/AuthContext";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const when = (iso) =>
  new Date(iso).toLocaleString("ru", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });

export const Notifications = () => {
  const { user } = useAuth();
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState([]);
  const [unread, setUnread] = useState(0);

  useEffect(() => {
    if (!user) {
      setItems([]);
      setUnread(0);
      return undefined;
    }
    const load = async () => {
      try {
        const res = await fetch(`${API}/notifications`, { credentials: "include" });
        if (!res.ok) return;
        const data = await res.json();
        setItems(data.items);
        setUnread(data.unread);
      } catch {
        /* keep the last known list */
      }
    };
    load();
    const timer = setInterval(load, 30000);
    return () => clearInterval(timer);
  }, [user]);

  const toggle = () => {
    const next = !open;
    setOpen(next);
    if (next && user && unread > 0) {
      fetch(`${API}/notifications/read`, { method: "POST", credentials: "include" });
      setUnread(0);
    }
  };

  return (
    <div className="ntf" data-testid="header-notifications">
      <button className="btn-bell" onClick={toggle} data-testid="header-notifications-button" aria-label="Уведомления">
        <Bell size={15} fill="currentColor" />
        {unread > 0 && <span className="ntf-badge" data-testid="header-notifications-badge">{unread}</span>}
      </button>
      {open && (
        <div className="ntf-menu" data-testid="header-notifications-menu">
          <div className="ntf-title">Уведомления</div>
          {!user && <div className="ntf-empty" data-testid="notifications-login-hint">Войдите через Steam, чтобы получать уведомления</div>}
          {user && items.length === 0 && <div className="ntf-empty" data-testid="notifications-empty">Новых уведомлений нет</div>}
          {items.map((n) => (
            <div className={`ntf-item ${n.read ? "" : "is-new"}`} key={n.id} data-testid={`notification-${n.id}`}>
              <b>{n.title}</b>
              <p>{n.text}</p>
              <time>{when(n.created_at)}</time>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
