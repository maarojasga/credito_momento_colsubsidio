// Las tres señales principales con su valor, puntos y fuente.

import type { Contribucion } from "../types";

export default function SenalesTop({ senales }: { senales: Contribucion[] }) {
  return (
    <ul>
      {senales.map((s) => (
        <li key={s.key}>
          <strong>{s.key}</strong>: {String(s.value)} · {s.puntos > 0 ? "+" : ""}
          {s.puntos} pts · <em>{s.source_id}</em>
        </li>
      ))}
    </ul>
  );
}
