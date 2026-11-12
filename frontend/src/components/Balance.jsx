import { useState } from "react";
import { ChevronDown } from "lucide-react";

const CURRENCIES = [
  { code: "RUB", sign: "₽", name: "Рубли" },
  { code: "KZT", sign: "₸", name: "Тенге" },
  { code: "UAH", sign: "₴", name: "Гривны" },
];

export const Balance = () => {
  const [cur, setCur] = useState(CURRENCIES[0]);
  const [open, setOpen] = useState(false);

  return (
    <div className="balance" data-testid="header-balance">
      <button className="balance-cur" onClick={() => setOpen(!open)} data-testid="header-currency-button">
        <span data-testid="header-balance-value">0,00 {cur.sign}</span>
        <ChevronDown size={13} />
      </button>
      <button className="balance-add" data-testid="header-deposit-button">
        Пополнить
      </button>
      {open && (
        <div className="cur-menu" data-testid="header-currency-menu">
          {CURRENCIES.map((c) => (
            <button
              key={c.code}
              className={c.code === cur.code ? "is-active" : ""}
              onClick={() => { setCur(c); setOpen(false); }}
              data-testid={`header-currency-option-${c.code.toLowerCase()}`}
            >
              <b>{c.sign}</b> {c.name}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};
