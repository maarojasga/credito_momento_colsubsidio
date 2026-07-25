// Métrica de pitch (§4.5): cobertura de eventos vs volumen de contacto.

import type { PuntoCobertura } from "../types";

export default function CoberturaChart({ curva }: { curva: PuntoCobertura[] }) {
  // Punto destacado: el más cercano a 20% de contacto.
  const destacado = curva.reduce((a, b) =>
    Math.abs(b.contacto - 0.2) < Math.abs(a.contacto - 0.2) ? b : a
  );
  return (
    <div className="pitch">
      <h2>Cobertura de eventos vs. volumen de contacto</h2>
      <div className="frase">
        Contactando solo el <b>{Math.round(destacado.contacto * 100)}%</b> capturamos el{" "}
        <b>{Math.round(destacado.cobertura * 100)}%</b> de las necesidades reales de crédito.
      </div>
      <div className="barras">
        {curva.map((p) => (
          <div className="barra-col" key={p.contacto}>
            <div className="barra-track">
              <div className="barra-fill" style={{ height: `${p.cobertura * 100}%` }} />
            </div>
            <div className="pct">{Math.round(p.cobertura * 100)}%</div>
            <div className="cap">contacto {Math.round(p.contacto * 100)}%</div>
          </div>
        ))}
      </div>
    </div>
  );
}
