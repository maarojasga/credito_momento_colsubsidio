// Vista afiliado: la oferta tal como la recibe la persona (tarjeta sticky) + el
// respaldo de la decisión (cuándo, por qué, trazabilidad).

import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import AppBar from "../components/AppBar";
import Copiloto from "../components/Copiloto";
import ManifestDownload from "../components/ManifestDownload";
import SenalesTop from "../components/SenalesTop";
import VentanaChart from "../components/VentanaChart";
import {
  contratoPdfUrl, enviarCorreo, extractoPdfUrl, firmarContrato, getCiclo, getManifest,
  getNarrativaIA, getOferta, reabrirOferta, responderOferta,
} from "../api/client";
import type { Manifiesto, Oferta } from "../types";
import { fmtMoney, labelSenal } from "../utils";

export default function AfiliadoView() {
  const { subjectId } = useParams<{ subjectId: string }>();
  const nav = useNavigate();
  const [oferta, setOferta] = useState<Oferta | null>(null);
  const [manifiesto, setManifiesto] = useState<Manifiesto | null>(null);
  const [narrativa, setNarrativa] = useState<{ texto: string; origen: string } | null>(null);
  const [estado, setEstado] = useState<string>("pendiente");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!subjectId) return;
    getOferta(subjectId).then(setOferta).catch((e) => setError(String(e)));
    getManifest(subjectId).then(setManifiesto).catch(() => {});
    getNarrativaIA(subjectId).then(setNarrativa).catch(() => {});
    getCiclo(subjectId).then((c) => setEstado(c.estado)).catch(() => {});
  }, [subjectId]);

  const responder = async (accion: "aceptar" | "rechazar") => {
    if (!subjectId) return;
    setEstado((await responderOferta(subjectId, accion)).estado);
  };
  const firmar = async () => { if (subjectId) setEstado((await firmarContrato(subjectId)).estado); };
  const reabrir = async () => { if (subjectId) setEstado((await reabrirOferta(subjectId)).estado); };

  if (error) return <Marco><div className="aviso">No se encontró la oferta ({error}).</div></Marco>;
  if (!oferta) return <Marco><div className="cargando">CARGANDO OFERTA…</div></Marco>;

  return (
    <Marco>
      <div className="volver" onClick={() => nav("/operador")}>◂ Volver al lote</div>

      <div className="afiliado-wrap">
        <div className="col-izq">
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

        {/* --- Ciclo: aceptar -> firmar -> documentos --- */}
        <CicloAccion
          estado={estado}
          subjectId={oferta.subject_id}
          canal={oferta.canal}
          onResponder={responder}
          onFirmar={firmar}
          onReabrir={reabrir}
        />
        <Compartir subjectId={oferta.subject_id} />
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

function CicloAccion({ estado, subjectId, canal, onResponder, onFirmar, onReabrir }: {
  estado: string; subjectId: string; canal: string;
  onResponder: (a: "aceptar" | "rechazar") => void; onFirmar: () => void; onReabrir: () => void;
}) {
  // Propuesta pendiente de respuesta.
  if (estado === "pendiente" || estado === "propuesta_enviada") {
    return (
      <div className="ciclo-accion">
        <div className="fila">
          <button className="btn primario" onClick={() => onResponder("aceptar")}>Aceptar oferta</button>
          <button className="btn" onClick={() => onResponder("rechazar")}>No, gracias</button>
        </div>
        <div className="ciclo-nota">Respuesta del afiliado por {canal}</div>
      </div>
    );
  }
  // Aceptada: falta firmar el contrato.
  if (estado === "aceptada") {
    return (
      <div className="ciclo-ok">
        <div className="cab"><i />Propuesta aceptada · falta firmar</div>
        <div className="cuerpo">
          <a href={contratoPdfUrl(subjectId)} target="_blank" rel="noopener noreferrer" className="doc-link">
            <span><span className="t">Revisar contrato</span><br /><span className="s">PDF · CONDICIONES Y PLAN DE PAGOS</span></span>
            <span className="ir">ABRIR →</span>
          </a>
          <button className="btn primario" onClick={onFirmar}>Firmar contrato</button>
          <span className="ciclo-nota" onClick={onReabrir} style={{ cursor: "pointer" }}>◂ Deshacer respuesta</span>
        </div>
      </div>
    );
  }
  // Firmada: documentos disponibles (contrato + extractos).
  if (estado === "firmada") {
    return (
      <div className="ciclo-ok">
        <div className="cab"><i />Contrato firmado · desembolso en trámite</div>
        <div className="cuerpo">
          <span style={{ fontSize: 13.5, color: "var(--grafito-60)", fontWeight: 500 }}>
            Los documentos quedaron disponibles en el chat de {canal}.
          </span>
          <a href={contratoPdfUrl(subjectId)} target="_blank" rel="noopener noreferrer" className="doc-link">
            <span><span className="t">Contrato de crédito</span><br /><span className="s">PDF · CONDICIONES Y PLAN DE PAGOS</span></span>
            <span className="ir">ABRIR →</span>
          </a>
          <a href={extractoPdfUrl(subjectId)} target="_blank" rel="noopener noreferrer" className="doc-link">
            <span><span className="t">Extracto mensual</span><br /><span className="s">PDF · CUOTA, SALDO Y MOVIMIENTOS</span></span>
            <span className="ir">ABRIR →</span>
          </a>
        </div>
      </div>
    );
  }
  // Rechazada.
  return (
    <div className="ciclo-rechazo">
      <span style={{ fontFamily: "var(--mono)", fontSize: 11, letterSpacing: "0.06em", textTransform: "uppercase", color: "var(--rojo)" }}>
        Oferta rechazada por el afiliado
      </span>
      <span style={{ fontSize: 13.5, color: "var(--grafito-60)", fontWeight: 500, lineHeight: 1.5 }}>
        No se genera contrato. La oferta vuelve a evaluarse en la próxima ventana de necesidad, con señales actualizadas.
      </span>
      <span className="ciclo-nota" onClick={onReabrir} style={{ cursor: "pointer" }}>◂ Deshacer respuesta</span>
    </div>
  );
}

function Compartir({ subjectId }: { subjectId: string }) {
  const origin = typeof window !== "undefined" ? window.location.origin : "";
  const [correo, setCorreo] = useState("");
  const [tipo, setTipo] = useState<"oferta" | "contrato">("oferta");
  const [msg, setMsg] = useState<string | null>(null);
  const [copiado, setCopiado] = useState("");

  const link = (t: string) => `${origin}/${t}/${subjectId}`;
  const copiar = (t: string) => {
    navigator.clipboard?.writeText(link(t));
    setCopiado(t); setTimeout(() => setCopiado(""), 1500);
  };
  const enviar = async () => {
    if (!correo.trim()) return;
    setMsg("Enviando…");
    try {
      const r = await enviarCorreo(subjectId, correo, tipo, origin);
      setMsg(r.enviado
        ? `✓ Correo enviado a ${correo} (${r.proveedor}).`
        : r.simulado
          ? `Correo simulado (SMTP sin configurar). El link del ${tipo}: ${r.link}`
          : `No se pudo enviar: ${r.error ?? "error"}`);
    } catch (e) { setMsg(`Error: ${String(e)}`); }
  };

  return (
    <div className="ciclo-accion">
      <div style={{ fontWeight: 700, fontSize: 14, marginBottom: 10 }}>Compartir con el cliente</div>
      <div style={{ display: "flex", flexDirection: "column", gap: 6, marginBottom: 12 }}>
        {(["oferta", "contrato", "detalle"] as const).map((t) => (
          <button key={t} className="chip" style={{ justifyContent: "space-between" }} onClick={() => copiar(t)}>
            <span>Link de {t}</span>
            <span className="mono" style={{ color: "var(--azul)" }}>{copiado === t ? "¡copiado!" : "copiar"}</span>
          </button>
        ))}
      </div>
      <div style={{ display: "flex", gap: 8 }}>
        <select className="buro-select" value={tipo} onChange={(e) => setTipo(e.target.value as "oferta" | "contrato")}
          style={{ padding: "9px 10px" }}>
          <option value="oferta">Oferta</option>
          <option value="contrato">Contrato</option>
        </select>
        <input className="firma-input" style={{ flex: 1, padding: "9px 12px", fontSize: 14 }}
          placeholder="correo@cliente.com" value={correo} onChange={(e) => setCorreo(e.target.value)} />
        <button className="btn primario" onClick={enviar}>Enviar</button>
      </div>
      {msg && <div className="ciclo-nota" style={{ textTransform: "none", letterSpacing: 0, marginTop: 10, wordBreak: "break-all" }}>{msg}</div>}
    </div>
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
