// Marca MOMENTO con el chevron amarillo inspirado en la identidad Colsubsidio.

export default function Logo({ size = 30 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 100 100" aria-label="MOMENTO" role="img">
      <g fill="#ffd000" stroke="#575756" strokeWidth="1.5">
        <polygon points="8,50 40,18 40,50" />
        <polygon points="8,50 40,50 40,82" />
        <polygon points="42,18 74,18 58,34 42,34" />
        <polygon points="42,38 58,38 42,54" />
        <polygon points="46,50 74,82 46,82" />
      </g>
    </svg>
  );
}
