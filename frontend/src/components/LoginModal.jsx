import { useState } from "react";
import { Check, X } from "lucide-react";
import { useAuth } from "@/context/AuthContext";

const SteamMark = ({ size = 22 }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
    <path d="M11.979 0C5.678 0 .511 4.86.022 11.037l6.432 2.658c.545-.371 1.203-.59 1.912-.59.063 0 .125.004.188.006l2.861-4.142V8.91c0-2.495 2.028-4.524 4.524-4.524 2.494 0 4.524 2.031 4.524 4.527s-2.03 4.525-4.524 4.525h-.105l-4.076 2.911c0 .052.004.105.004.159 0 1.875-1.515 3.396-3.39 3.396-1.635 0-3.016-1.173-3.331-2.727L.436 15.27C1.862 20.307 6.486 24 11.979 24c6.627 0 11.999-5.373 11.999-12S18.605 0 11.979 0zM7.540 18.21l-1.473-.61c.262.543.714.999 1.314 1.25 1.297.539 2.793-.076 3.332-1.375.263-.63.264-1.319.005-1.949s-.75-1.121-1.377-1.383c-.624-.26-1.290-.249-1.878-.03l1.523.63c.956.4 1.409 1.5 1.009 2.455-.397.957-1.497 1.41-2.454 1.012H7.540zm11.415-9.303c0-1.662-1.353-3.015-3.015-3.015-1.665 0-3.015 1.353-3.015 3.015 0 1.665 1.350 3.015 3.015 3.015 1.663 0 3.015-1.350 3.015-3.015zm-5.273-.005c0-1.252 1.013-2.266 2.265-2.266 1.249 0 2.266 1.014 2.266 2.266 0 1.251-1.017 2.265-2.266 2.265-1.253 0-2.265-1.014-2.265-2.265z" />
  </svg>
);

export const LoginModal = ({ open, onClose }) => {
  const [age, setAge] = useState(false);
  const [terms, setTerms] = useState(false);
  const { loginWithSteam } = useAuth();
  const ready = age && terms;
  if (!open) return null;

  return (
    <div className="lg-overlay" onClick={onClose} data-testid="login-overlay">
      <div className="lg-modal" onClick={(e) => e.stopPropagation()} data-testid="login-modal">
        <button className="lg-close" onClick={onClose} data-testid="login-close-button" aria-label="Закрыть"><X size={18} /></button>

        <div className="lg-panel" data-testid="login-gate">
          <h2>ВХОД НА STEAMGRADER</h2>
          <p>
            Сервис доступен только совершеннолетним пользователям (18+).
            Авторизуясь через Steam, вы подтверждаете свой возраст и принимаете условия использования.
          </p>

          <label className="lg-check" data-testid="login-age-check">
            <input type="checkbox" checked={age} onChange={(e) => setAge(e.target.checked)} data-testid="login-age-input" />
            <span className="lg-box"><Check size={14} strokeWidth={4} /></span>
            <span>Я подтверждаю, что мне больше 18 лет</span>
          </label>
          <label className="lg-check" data-testid="login-terms-check">
            <input type="checkbox" checked={terms} onChange={(e) => setTerms(e.target.checked)} data-testid="login-terms-input" />
            <span className="lg-box"><Check size={14} strokeWidth={4} /></span>
            <span>Я принимаю <a href="#" data-testid="login-terms-link">правила и политику</a> использования сайта</span>
          </label>

          <button className="lg-steam-btn" disabled={!ready} onClick={loginWithSteam} data-testid="login-steam-button">
            <SteamMark size={24} /> Войти через Steam +18
          </button>
          <span className="lg-foot">Вы перейдёте на официальную страницу входа Steam. Не аффилировано с Valve Corp.</span>
        </div>
      </div>
    </div>
  );
};
