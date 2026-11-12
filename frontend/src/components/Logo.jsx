export const Logo = ({ size = 30 }) => (
  <svg width={size} height={size} viewBox="0 0 32 32" fill="none" aria-hidden="true">
    <defs>
      <linearGradient id="lg-mark" x1="16" y1="2" x2="16" y2="20" gradientUnits="userSpaceOnUse">
        <stop stopColor="#8fd3ff" />
        <stop offset="1" stopColor="#1a9fff" />
      </linearGradient>
    </defs>
    <path d="M16 2 29 14v6L16 8 3 20v-6z" fill="url(#lg-mark)" />
    <path d="M16 12 29 24v6L16 18 3 30v-6z" fill="#fff" />
  </svg>
);
