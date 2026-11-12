import { createContext, useContext, useEffect, useState } from "react";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;
const AuthCtx = createContext(null);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [loginOpen, setLoginOpen] = useState(false);

  const refresh = async () => {
    try {
      const res = await fetch(`${API}/auth/me`, { credentials: "include" });
      const data = await res.json();
      setUser(data.user);
    } catch {
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
    if (window.location.search.includes("login=")) {
      window.history.replaceState({}, "", window.location.pathname);
    }
  }, []);

  const loginWithSteam = () => {
    window.location.href = `${API}/auth/steam`;
  };

  const logout = async () => {
    await fetch(`${API}/auth/logout`, { method: "POST", credentials: "include" });
    setUser(null);
  };

  return (
    <AuthCtx.Provider value={{ user, loading, loginWithSteam, logout, refresh, loginOpen, setLoginOpen }}>
      {children}
    </AuthCtx.Provider>
  );
};

export const useAuth = () => useContext(AuthCtx);
