// Las tres señales principales con su valor, puntos y fuente.

import type { SenalTop } from "../types";
import { labelSenal } from "../utils";

export default function SenalesTop({ senales }: { senales: SenalTop[] }) {
  return (
    <div>
      {senales.map((s) => (
        <div className="senal" key={s.key}>
          <div className={`puntos ${s.puntos >= 0 ? "pos" : "neg"}`}>
            {s.puntos >= 0 ? "+" : ""}
            {s.puntos}
          </div>
          <div className="info">
            <div className="k">
              {labelSenal(s.key)}: {String(s.value)}
            </div>
            <div className="src">
              fuente: <span className="mono">{s.source_id}</span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
