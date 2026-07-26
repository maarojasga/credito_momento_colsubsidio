// Vista afiliado: la oferta tal como la recibe la persona (tarjeta sticky) + el
// respaldo de la decisión (cuándo, por qué, trazabilidad).

import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import AppBar from "../components/AppBar";
import Copiloto from "../components/Copiloto";
import ManifestDownload from "../components/ManifestDownload";
import SenalesTop from "../components/SenalesTop";
import VentanaChart from "../components/VentanaChart";
import { getManifest, getNarrativaIA, getOferta } from "../api/client";
import type { Manifiesto, Oferta } from "../types";
import { fmtMoney, labelSenal } from "../utils";

export default function AfiliadoView() {
  const { subjectId } = useParams<{ subjectId: string }>();
  const nav = useNavigate();
  const [oferta, setOferta] = useState<Oferta | null>(null);
  const [manifiesto, setManifiesto] = useState<Manifiesto | null>(null);
  const [narrativa, setNarrativa] = useState<{ texto: string; origen: string } | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!subjectId) return;
    getOferta(subjectId).then(setOferta).catch((e) => setError(String(e)));
    getManifest(subjectId).then(setManifiesto).catch(() => {});
    getNarrativaIA(subjectId).then(setNarrativa).catch(() => {});
  }, [subjectId]);

  if (error) return <Marco><div className="aviso">No se encontró la oferta ({error}).</div></Marco>;
  if (!oferta) return <Marco><div className="cargando">CARGANDO OFERTA…</div></Marco>;

  return (
    <Marco>
      <div className="volver" onClick={() => nav("/operador")}>◂ Volver al lote</div>

      <div className="afiliado-wrap">
        {/* --- Oferta como la ve el afiliado --- */}
        <div className="oferta-card">
          <div className="top">
            <span className="badge-pre">Tienes preaprobado</span>
            <div className="prod">{oferta.nombre_producto}</div>
          </div>
          <div className="cuerpo">
            <div className="monto">{fmtMoney(oferta.monto)}</div>
            <div className="plazo">a {oferta.plazo_meses} meses</div>
            <p className="razon">{narrativa?.texto ?? oferta.razon_texto}</p>
            <div className="envio">
              <span className="punto" />
              <span>
                Se envía por {oferta.canal} a las {oferta.hora_envio} ·{" "}
                {narrativa?.origen === "gemini" ? "narrativa con IA (validada)" : "narrativa validada"}
              </span>
            </div>
          </div>
        </div>

        {/* --- Respaldo de la decisión --- */}
        <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
          <div className="panel">
            <div className="panel-head">
              <h3>¿Cuándo? La ventana del momento justo</h3>
              <span className="etq">60 días</span>
            </div>
            <p className="intro">
              Un hazard en tiempo discreto estima el mes de mayor probabilidad de necesidad. La
              oferta se entrega dentro de esa ventana, no antes.
            </p>
            <VentanaChart inicio={oferta.ventana_inicio} fin={oferta.ventana_fin} />
          </div>

          <div className="panel">
            <div className="panel-head">
              <h3>¿Por qué? Las tres señales que más pesaron</h3>
              <span className="etq" style={{ color: "var(--grafito-60)" }}>
                Scorecard <b style={{ color: "var(--tinta)" }}>{oferta.puntos_scorecard}</b> pts
              </span>
            </div>
            <p className="intro">
              Cada aporte sale de la tabla de puntos, no de una aproximación. El texto de la oferta
              solo redacta lo que estos puntos ya decidieron.
            </p>
            <SenalesTop senales={oferta.top_senales} />
          </div>

          {manifiesto && (
            <div className="panel suave">
              <div className="panel-head">
                <h3>Trazabilidad</h3>
                <span className="etq">Manifiesto v0.1</span>
              </div>
              <p className="intro">
                Cada señal entra con fuente y base legal. Ninguna proviene de un buró de crédito.
              </p>
              <div className="manifiesto">
                {manifiesto.senales.map((s) => (
                  <div className="fila" key={s.key}>
                    <span className="nombre">{labelSenal(s.key)}</span>
                    <span className="mono">{s.source_id}</span>
                    <span style={{ textAlign: "right" }}>
                      {s.base_legal && <span className={`legal ${s.base_legal}`}>{s.base_legal}</span>}
                    </span>
                  </div>
                ))}
              </div>
              <div style={{ marginTop: 22, display: "flex", alignItems: "center", justifyContent: "space-between", gap: 24, flexWrap: "wrap" }}>
                <span className="mono" style={{ color: "var(--grafito-60)" }}>
                  REGLAS EVALUADAS {manifiesto.reglas_evaluadas.length} · HASH {manifiesto.manifest_hash.slice(0, 20)}…
                </span>
                <ManifestDownload subjectId={oferta.subject_id} />
              </div>
            </div>
          )}
        </div>
      </div>

      <Copiloto subjectId={oferta.subject_id} />
    </Marco>
  );
}

function Marco({ children }: { children: React.ReactNode }) {
  return (
    <>
      <AppBar />
      <div className="contenedor" style={{ animation: "momFade .5s cubic-bezier(.16,1,.3,1) both" }}>
        {children}
      </div>
    </>
  );
}
