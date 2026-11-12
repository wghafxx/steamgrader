import { useState } from "react";
import { ChevronDown, LogIn, LogOut } from "lucide-react";
import { Notifications } from "@/components/Notifications";
import { Logo } from "@/components/Logo";
import { Balance } from "@/components/Balance";
import { LoginModal } from "@/components/LoginModal";
import { useAuth } from "@/context/AuthContext";
import { OnlineCounter } from "@/components/OnlineCounter";

const MENU = ["Политика конфиденциальности", "Пользовательское соглашение", "Честная игра", "Поддержка"];
const TABS = ["Главная", "Режимы", "Инвентарь", "Сообщество"];

export const Header = ({ active, setActive }) => {
  const [menuOpen, setMenuOpen] = useState(false);
  const { user, logout, loginOpen: login, setLoginOpen: setLogin } = useAuth();

  return (
    <header className="hdr" data-testid="site-header">
      <div className="hdr-top">
        <a href="/" className="hdr-brand" data-testid="header-logo">
          <Logo size={22} />
          <span className="brand-word"><b>STEAM</b>GRADER</span>
        </a>
        <nav className="hdr-menu" data-testid="header-top-menu">
          {MENU.map((m, i) => (
            <button
              key={m}
              className={`hdr-menu-item ${active === m ? "is-active" : ""}`}
              onClick={() => setActive(m)}
              data-testid={`header-menu-item-${i}`}
            >
              {m}
            </button>
          ))}
        </nav>

        <div className="hdr-right">
          <OnlineCounter />
          <Notifications />

          {user ? (
            <>
              <Balance />
              <div className="profile-wrap">
                <button className="profile" onClick={() => setMenuOpen(!menuOpen)} data-testid="header-profile-button">
                  <span className="st-avatar" data-testid="header-profile-avatar">
                    {user.avatar ? <img src={user.avatar} alt="" /> : <span className="st-avatar-empty">?</span>}
                  </span>
                  <span className="profile-name" data-testid="header-profile-name">{user.nickname}</span>
                  <ChevronDown size={13} strokeWidth={3} />
                </button>
                {menuOpen && (
                  <div className="profile-menu" data-testid="header-profile-menu">
                    <button onClick={() => { logout(); setMenuOpen(false); }} data-testid="header-logout-button">
                      <LogOut size={15} /> Выйти
                    </button>
                  </div>
                )}
              </div>
            </>
          ) : (
            <button className="btn-login" onClick={() => setLogin(true)} data-testid="header-login-button">
              <LogIn size={15} /> Войти
            </button>
          )}
        </div>
      </div>

      <nav className="hdr-tabs" data-testid="header-main-nav">
        {TABS.map((t, i) => (
          <button
            key={t}
            className={`hdr-tab ${active === t ? "is-active" : ""}`}
            onClick={() => setActive(t)}
            data-testid={`header-tab-${i}`}
          >
            {t}
          </button>
        ))}
      </nav>
      <LoginModal open={login} onClose={() => setLogin(false)} />
    </header>
  );
};
