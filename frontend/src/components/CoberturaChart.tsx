// Métrica de pitch (§4.5): cobertura de eventos vs volumen de contacto.
// La historia es el rendimiento decreciente: contactar mucho más gente casi no
// sube la cobertura, así que hay un punto óptimo cerca del 20%.

import type { PuntoCobertura } from "../types";

export default function CoberturaChart({ curva }: { curva: PuntoCobertura[] }) {
  // Punto destacado: el más cercano a 20% de contacto.
  const destacado = curva.reduce((a, b) =>
    Math.abs(b.contacto - 0.2) < Math.abs(a.contacto - 0.2) ? b : a
  );
  const maxContacto = curva.reduce((a, b) => (b.contacto > a.contacto ? b : a));
  const deltaPP = Math.round((maxContacto.cobertura - destacado.cobertura) * 100);
  const factor = (maxContacto.contacto / destacado.contacto).toLocaleString("es-CO", {
    maximumFractionDigits: 1,
  });

  return (
    <div className="pitch">
      <h2>Cobertura de eventos vs. volumen de contacto</h2>
      <div className="frase">
        Contactando solo el <b>{Math.round(destacado.contacto * 100)}%</b> capturamos el{" "}
        <b>{Math.round(destacado.cobertura * 100)}%</b> de las necesidades reales de crédito.
      </div>

      <div className="cob-grid">
        {/* línea de referencia en el nivel del punto óptimo */}
        <div className="cob-ref" style={{ bottom: `${destacado.cobertura * 100}%` }} />
        {curva.map((p) => {
          const activo = p.contacto === destacado.contacto;
          return (
            <div className={`cob-col${activo ? " activo" : ""}`} key={p.contacto}>
              <div className="cob-bar-wrap">
                {activo && <span className="cob-tag">punto óptimo</span>}
                <div className="cob-bar" style={{ height: `${p.cobertura * 100}%` }}>
                  <span className="cob-val">{Math.round(p.cobertura * 100)}%</span>
                </div>
              </div>
              <div className="cob-cap">
                contacto <b>{Math.round(p.contacto * 100)}%</b>
              </div>
            </div>
          );
        })}
      </div>

      <div className="cob-nota">
        Contactar <b>{factor}×</b> más personas ({Math.round(destacado.contacto * 100)}% →{" "}
        {Math.round(maxContacto.contacto * 100)}%) suma apenas <b>{deltaPP} pp</b> de cobertura.
      </div>
    </div>
  );
}
