// Vista afiliado: la oferta tal como la recibe la persona + el panel de
// trazabilidad que respalda la decisión.

import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import AppBar from "../components/AppBar";
import ManifestDownload from "../components/ManifestDownload";
import SenalesTop from "../components/SenalesTop";
import VentanaChart from "../components/VentanaChart";
import { getManifest, getOferta } from "../api/client";
import type { Manifiesto, Oferta } from "../types";
import { fmtMoney, labelSenal } from "../utils";

export default function AfiliadoView() {
  const { subjectId } = useParams<{ subjectId: string }>();
  const [oferta, setOferta] = useState<Oferta | null>(null);
  const [manifiesto, setManifiesto] = useState<Manifiesto | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!subjectId) return;
    getOferta(subjectId).then(setOferta).catch((e) => setError(String(e)));
    getManifest(subjectId).then(setManifiesto).catch(() => {});
  }, [subjectId]);

  if (error) return <Marco><div className="aviso">No se encontró la oferta ({error}).</div></Marco>;
  if (!oferta) return <Marco><div className="cargando">Cargando oferta…</div></Marco>;

  return (
    <Marco>
      <Link to="/operador" style={{ fontWeight: 600 }}>← Volver al operador</Link>
      <div className="afiliado-wrap" style={{ marginTop: 16 }}>
        {/* --- Oferta como la ve el afiliado --- */}
        <div className="oferta-card">
          <div className="top">
            <div style={{ fontSize: 13, opacity: 0.8 }}>Tienes preaprobado</div>
            <div className="prod">{oferta.nombre_producto}</div>
          </div>
          <div className="cuerpo">
            <div className="monto">{fmtMoney(oferta.monto)}</div>
            <div className="plazo">a {oferta.plazo_meses} meses</div>
            <div className="razon">{oferta.razon_texto}</div>
            <div style={{ marginTop: 14, fontSize: 12, color: "var(--grafito-60)" }}>
              Se enviará por <b>{oferta.canal}</b> a las <b>{oferta.hora_envio}</b> ·
              narrativa validada ({oferta.narrativa_origen})
            </div>
          </div>
        </div>

        {/* --- Respaldo de la decisión --- */}
        <div style={{ display: "grid", gap: 18 }}>
          <div className="card">
            <h3>¿Cuándo? La ventana del momento justo</h3>
            <VentanaChart inicio={oferta.ventana_inicio} fin={oferta.ventana_fin} />
          </div>

          <div className="card">
            <h3>¿Por qué? Las tres señales que más pesaron</h3>
            <p style={{ fontSize: 13, color: "var(--grafito-60)", marginTop: 4 }}>
              Puntaje total del scorecard: <b>{oferta.puntos_scorecard}</b>. Cada aporte sale de la
              tabla de puntos, no de una aproximación.
            </p>
            <SenalesTop senales={oferta.top_senales} />
          </div>

          {manifiesto && (
            <div className="card">
              <h3>Trazabilidad</h3>
              <p style={{ fontSize: 13, color: "var(--grafito-60)", marginTop: 4 }}>
                Cada señal declara su fuente y base legal. Ninguna proviene de un buró de crédito.
              </p>
              <table style={{ width: "100%", fontSize: 13, borderCollapse: "collapse" }}>
                <tbody>
                  {manifiesto.senales.map((s) => (
                    <tr key={s.key}>
                      <td style={{ padding: "6px 0" }}>{labelSenal(s.key)}</td>
                      <td className="mono" style={{ color: "var(--grafito-60)" }}>{s.source_id}</td>
                      <td style={{ textAlign: "right" }}>
                        {s.base_legal && <span className={`legal ${s.base_legal}`}>{s.base_legal}</span>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              <div style={{ marginTop: 12, fontSize: 12, color: "var(--grafito-60)" }}>
                Reglas evaluadas: {manifiesto.reglas_evaluadas.length} · hash{" "}
                <span className="mono">{manifiesto.manifest_hash.slice(0, 22)}…</span>
              </div>
              <div style={{ marginTop: 14 }}>
                <ManifestDownload subjectId={oferta.subject_id} />
              </div>
            </div>
          )}
        </div>
      </div>
    </Marco>
  );
}

function Marco({ children }: { children: React.ReactNode }) {
  return (
    <>
      <AppBar />
      <div className="contenedor">{children}</div>
    </>
  );
}
