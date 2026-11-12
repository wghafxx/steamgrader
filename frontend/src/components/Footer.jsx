import { Download, PlusSquare, Users } from "lucide-react";
import { FaDiscord, FaInstagram, FaTelegram, FaTiktok, FaXTwitter } from "react-icons/fa6";
import { Logo } from "@/components/Logo";

const SOCIALS = [
  { id: "telegram", name: "Telegram", Icon: FaTelegram },
  { id: "discord", name: "Discord", Icon: FaDiscord },
  { id: "tiktok", name: "TikTok", Icon: FaTiktok },
  { id: "twitter", name: "Twitter", Icon: FaXTwitter },
  { id: "instagram", name: "Instagram", Icon: FaInstagram },
];

const COLS = [
  { title: "Платформа", links: ["Главная", "Режимы", "Лидерборд", "Бонусы"] },
  { title: "Поддержка", links: ["Справка", "Честная игра", "Связаться с нами"] },
  { title: "Документы", links: ["Пользовательское соглашение", "Политика конфиденциальности", "Ответственная игра"] },
];

export const Footer = () => (
  <footer className="ftr" data-testid="site-footer">
    <div className="ftr-inner">
      <div className="ftr-about">
        <div className="ftr-brand" data-testid="footer-logo">
          <Logo size={34} />
          <span className="brand-word"><b>STEAM</b>GRADER</span>
        </div>
        <p data-testid="footer-disclaimer">
          Набросок дизайна. Сайт не связан с Valve Corporation и платформой Steam. 18+
        </p>
        <div className="ftr-social" data-testid="footer-socials">
          {SOCIALS.map(({ id, name, Icon }) => (
            <a href="#" key={id} aria-label={name} title={name} data-testid={`footer-social-${id}`}>
              <Icon size={18} />
            </a>
          ))}
        </div>
      </div>
      {COLS.map((c, ci) => (
        <div className="ftr-col" key={c.title} data-testid={`footer-column-${ci}`}>
          <h4>{c.title}</h4>
          {c.links.map((l, li) => (
            <a href="#" key={l} data-testid={`footer-link-${ci}-${li}`}>{l}</a>
          ))}
        </div>
      ))}
    </div>
    <div className="ftr-copy" data-testid="footer-copyright">© 2026 Steamgrader. Все права защищены.</div>

    <div className="statusbar" data-testid="footer-statusbar">
      <button data-testid="statusbar-add-button"><PlusSquare size={15} /> Пополнить баланс</button>
      <button data-testid="statusbar-activity-button"><Download size={15} /> История ставок</button>
      <button data-testid="statusbar-chat-button">Друзья и чат <Users size={15} /></button>
    </div>
  </footer>
);
