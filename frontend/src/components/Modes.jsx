import casesBanner from "@/assets/mode-banners/cases.webp";
import minesBanner from "@/assets/mode-banners/mines.webp";
import upgraderBanner from "@/assets/mode-banners/upgrader.webp";

const MODES = [
  { id: "cases", title: "Кейсы", desc: "Открывайте кейсы и получайте предметы", tags: ["Предметы", "Классика"], banner: casesBanner },
  { id: "upgrader", title: "Апгрейдер", desc: "Улучшайте предмет до более дорогого", tags: ["Апгрейд", "Риск"], banner: upgraderBanner },
  { id: "mines", title: "Мины", desc: "Открывайте клетки и обходите мины", tags: ["Поле 5×5", "Множитель"], banner: minesBanner },
];

export const Modes = () => (
  <section data-testid="modes-section">
    <h2 className="sec-title">Режимы</h2>
    <div className="modes">
      {MODES.map(({ id, title, desc, tags, banner }) => (
        <article className={`mode mode-${id}`} key={id} data-testid={`mode-card-${id}`}>
          <div className="mode-art">
            <img className="mode-banner" src={banner} alt="" width={776} height={380} />
          </div>
          <div className="mode-body">
            <h3 data-testid={`mode-title-${id}`}>{title}</h3>
            <p>{desc}</p>
            <div className="mode-tags">
              {tags.map((t) => <span key={t}>{t}</span>)}
            </div>
          </div>
          <div className="mode-foot" data-testid={`mode-status-${id}`}>Скоро</div>
        </article>
      ))}
    </div>
  </section>
);
