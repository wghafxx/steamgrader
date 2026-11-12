import { useEffect, useState } from "react";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const visitorId = () => {
  let id = localStorage.getItem("visitor_id");
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem("visitor_id", id);
  }
  return id;
};

export const OnlineCounter = () => {
  const [online, setOnline] = useState(null);

  useEffect(() => {
    const ping = async () => {
      try {
        const res = await fetch(`${API}/online/ping`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ visitor_id: visitorId() }),
        });
        setOnline((await res.json()).online);
      } catch {
        setOnline(null);
      }
    };
    ping();
    const timer = setInterval(ping, 20000);
    return () => clearInterval(timer);
  }, []);

  return (
    <div className="online" data-testid="header-online">
      <span className="online-dot" />
      <span className="online-label">В сети</span>
      <b data-testid="header-online-count">{online ?? "—"}</b>
    </div>
  );
};
