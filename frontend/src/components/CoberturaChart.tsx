// Métrica estrella (§4.5): cobertura de necesidad vs volumen de contacto.
// La historia es el rendimiento decreciente: contactar mucho más gente casi no
// sube la cobertura, así que hay un punto óptimo cerca del 20%.

import type { PuntoCobertura } from "../types";

export default function CoberturaChart({ curva }: { curva: PuntoCobertura[] }) {
  const destacado = curva.reduce((a, b) =>
    Math.abs(b.contacto - 0.2) < Math.abs(a.contacto - 0.2) ? b : a
  );
  const maxContacto = curva.reduce((a, b) => (b.contacto > a.contacto ? b : a));
  const deltaPP = Math.round((maxContacto.cobertura - destacado.cobertura) * 100);
  const maxCob = Math.max(...curva.map((p) => p.cobertura));

  return (
    <div className="pitch">
      <div>
        <span className="kicker">§ Métrica estrella</span>
        <div className="cifra">{Math.round(destacado.cobertura * 100)}%</div>
        <p className="frase">
          de la necesidad real capturada contactando solo el{" "}
          <b>{Math.round(destacado.contacto * 100)}%</b> de los afiliados.
        </p>
        <div className="nota-pie">
          Hazard en tiempo discreto · contactar {(maxContacto.contacto / destacado.contacto)
            .toLocaleString("es-CO", { maximumFractionDigits: 1 })}× más suma apenas {deltaPP} pp
        </div>
      </div>

      <div>
        <div className="cob-grid">
          {curva.map((p) => {
            const activo = p.contacto === destacado.contacto;
            return (
              <div className={`cob-col${activo ? " activo" : ""}`} key={p.contacto}>
                <span className="cob-val">{Math.round(p.cobertura * 100)}%</span>
                <div className="cob-bar-wrap">
                  {activo && <span className="cob-tag">óptimo</span>}
                  <div className="cob-bar" style={{ height: `${(p.cobertura / maxCob) * 100}%` }} />
                </div>
              </div>
            );
          })}
        </div>
        <div className="cob-ejes">
          {curva.map((p) => (
            <span className="cob-cap" key={p.contacto}
              style={{ flex: 1, color: p.contacto === destacado.contacto ? "var(--amarillo)" : undefined }}>
              {Math.round(p.contacto * 100)}% contacto
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
