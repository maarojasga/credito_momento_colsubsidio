// Las tres señales principales con su valor, puntos y fuente.

import type { SenalTop } from "../types";
import { labelSenal } from "../utils";

export default function SenalesTop({ senales }: { senales: SenalTop[] }) {
  const maxAbs = Math.max(1, ...senales.map((s) => Math.abs(s.puntos)));
  return (
    <div>
      {senales.map((s) => (
        <div className="senal" key={s.key}>
          <div className={`puntos ${s.puntos >= 0 ? "pos" : "neg"}`}>
            {s.puntos >= 0 ? "+" : "−"}
            {Math.abs(s.puntos)}
          </div>
          <div className="info">
            <div style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", gap: 16 }}>
              <span className="k">{labelSenal(s.key)}</span>
              <span className="mono" style={{ color: "var(--tinta)" }}>{String(s.value)}</span>
            </div>
            <div className="src">{s.source_id}</div>
            <div className="barra">
              <span style={{ width: `${Math.min((Math.abs(s.puntos) / maxAbs) * 100, 100)}%` }} />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
