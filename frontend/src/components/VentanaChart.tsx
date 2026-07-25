// Línea de tiempo de 12 meses con la ventana de contacto de 60 días resaltada.

import { fmtMes } from "../utils";

const MESES = ["E", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"];

export default function VentanaChart({
  inicio,
  fin,
}: {
  inicio: string;
  fin: string;
}) {
  const dIni = new Date(inicio + "T00:00:00");
  const dFin = new Date(fin + "T00:00:00");
  const hoy = new Date();
  const base = new Date(hoy.getFullYear(), hoy.getMonth(), 1);

  const meses = Array.from({ length: 12 }, (_, i) => {
    const d = new Date(base.getFullYear(), base.getMonth() + i, 1);
    const dentro = d >= new Date(dIni.getFullYear(), dIni.getMonth(), 1) &&
                   d < new Date(dFin.getFullYear(), dFin.getMonth(), 1);
    const pico = d.getFullYear() === dIni.getFullYear() && d.getMonth() === dIni.getMonth();
    return { label: MESES[d.getMonth()], dentro, pico };
  });

  return (
    <div>
      <div className="timeline">
        {meses.map((m, i) => (
          <div key={i} className={`mes ${m.pico ? "pico" : m.dentro ? "dentro" : ""}`}>
            <div className="bloque" />
            {m.label}
          </div>
        ))}
      </div>
      <div style={{ fontSize: 13, color: "var(--grafito-60)" }}>
        Ventana óptima de contacto: <b style={{ color: "var(--azul-oscuro)" }}>
          {fmtMes(inicio)} – {fmtMes(fin)}
        </b>
      </div>
    </div>
  );
}
