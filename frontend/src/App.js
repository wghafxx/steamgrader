import { useState } from "react";
import "@/App.css";
import { Header } from "@/components/Header";
import { Footer } from "@/components/Footer";
import { Modes } from "@/components/Modes";
import { Inventory } from "@/components/Inventory";
import { Chat } from "@/components/Chat";
import { AuthProvider } from "@/context/AuthContext";

function App() {
  const [active, setActive] = useState("Главная");

  return (
    <AuthProvider>
    <div className="site" data-testid="site-root">
      <div className="site-bg" aria-hidden="true" />
      <Header active={active} setActive={setActive} />
      <main className="site-main" data-testid="site-main">
        {active === "Режимы" && <Modes />}
        {active === "Инвентарь" && <Inventory />}
        {active === "Сообщество" && <Chat />}
        {active !== "Режимы" && active !== "Инвентарь" && active !== "Сообщество" && (
          <div className="main-box" data-testid="main-content-placeholder">
            <span className="main-box-label">{active}</span>
            <span className="main-box-hint">Раздел пока пустой</span>
          </div>
        )}
      </main>
      <Footer />
    </div>
    </AuthProvider>
  );
}

export default App;
