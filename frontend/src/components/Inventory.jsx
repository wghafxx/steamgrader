import { Backpack } from "lucide-react";

const SLOTS = Array.from({ length: 24 });

export const Inventory = () => (
  <section data-testid="inventory-section">
    <div className="inv-head">
      <h2 className="sec-title">Инвентарь</h2>
      <span className="inv-count" data-testid="inventory-count">0 предметов · 0,00</span>
    </div>
    <div className="inv">
      <div className="inv-grid" data-testid="inventory-grid">
        {SLOTS.map((_, i) => <div className="inv-slot" key={i} data-testid={`inventory-slot-${i}`} />)}
      </div>
      <aside className="inv-side" data-testid="inventory-empty-state">
        <Backpack size={44} strokeWidth={1.3} />
        <b>Инвентарь пуст</b>
        <span>Выигранные предметы появятся здесь</span>
      </aside>
    </div>
  </section>
);
