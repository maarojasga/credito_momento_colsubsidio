// Portal público del cliente: un link por cada paso que se libera al avanzar.
//   /oferta/:id   -> aceptar  ->  libera el contrato
//   /contrato/:id -> firmar (firma digital)  ->  libera el detalle
//   /detalle/:id  -> descargar contrato y extracto (PDF)

import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  contratoPdfUrl, extractoPdfUrl, firmarContrato, getCiclo, getOferta,
  reabrirOferta, responderOferta,
} from "../api/client";
import type { Oferta } from "../types";
import { fmtMoney } from "../utils";

function usePortal() {
  const { subjectId } = useParams<{ subjectId: string }>();
  const [oferta, setOferta] = useState<Oferta | null>(null);
  const [estado, setEstado] = useState<string>("pendiente");
  const [firma, setFirma] = useState<{ nombre: string; sello: string } | null>(null);
  useEffect(() => {
    if (!subjectId) return;
    getOferta(subjectId).then(setOferta).catch(() => {});
    getCiclo(subjectId).then((c) => { setEstado(c.estado); setFirma(c.firma ?? null); }).catch(() => {});
  }, [subjectId]);
  return { subjectId: subjectId!, oferta, estado, setEstado, firma, setFirma };
}

function Marco({ paso, estado, children }: { paso: number; estado: string; children: React.ReactNode }) {
  const firmada = estado === "firmada";
  const aceptada = ["aceptada", "firmada"].includes(estado);
  const pasos = [
    { n: 1, k: "Oferta", ok: true, done: aceptada },
    { n: 2, k: "Contrato", ok: aceptada, done: firmada },
    { n: 3, k: "Detalle", ok: firmada, done: firmada },
  ];
  return (
    <div className="portal-bg">
      <header className="portal-head">
        <span className="marca">MOMENTO</span>
        <span className="cobrand">Colsubsidio <span style={{ opacity: 0.5 }}>×</span> <b>30X</b></span>
      </header>
      <div className="portal-wrap">
        <div className="stepper">
          {pasos.map((p, i) => (
            <div key={p.n} className={`step ${p.n === paso ? "activo" : ""} ${p.ok ? "ok" : "lock"}`}>
              <span className="bola">{p.done ? "✓" : p.ok ? p.n : "🔒"}</span>
              <span className="etq">{p.k}</span>
              {i < 2 && <span className="linea" />}
            </div>
          ))}
        </div>
        {children}
      </div>
    </div>
  );
}

function OfertaCard({ o }: { o: Oferta }) {
  return (
    <div className="oferta-card" style={{ position: "static" }}>
      <div className="top">
        <span className="badge-pre">Tienes preaprobado</span>
        <div className="prod">{o.nombre_producto}</div>
      </div>
      <div className="cuerpo">
        <div className="monto">{fmtMoney(o.monto)}</div>
        <div className="plazo">a {o.plazo_meses} meses</div>
        <p className="razon">{o.razon_texto}</p>
      </div>
    </div>
  );
}

function Bloqueado({ texto, href, cta }: { texto: string; href: string; cta: string }) {
  return (
    <div className="portal-lock">
      <div className="cand">🔒</div>
      <p>{texto}</p>
      <Link to={href} className="btn primario">{cta}</Link>
    </div>
  );
}

// --- Paso 1: Oferta -----------------------------------------------------------

export function PortalOferta() {
  const { subjectId, oferta, estado, setEstado } = usePortal();
  const nav = useNavigate();
  if (!oferta) return <div className="portal-bg"><div className="cargando">CARGANDO…</div></div>;

  const responder = async (a: "aceptar" | "rechazar") =>
    setEstado((await responderOferta(subjectId, a)).estado);

  return (
    <Marco paso={1} estado={estado}>
      <OfertaCard o={oferta} />
      {["pendiente", "propuesta_enviada"].includes(estado) && (
        <div className="portal-acciones">
          <button className="btn primario grande" onClick={() => responder("aceptar")}>Aceptar mi oferta</button>
          <button className="btn" onClick={() => responder("rechazar")}>Ahora no</button>
        </div>
      )}
      {["aceptada", "firmada"].includes(estado) && (
        <div className="portal-ok">
          <p><b>✓ Aceptaste tu oferta.</b> Tu contrato ya está disponible.</p>
          <button className="btn primario grande" onClick={() => nav(`/contrato/${subjectId}`)}>
            Continuar al contrato →
          </button>
        </div>
      )}
      {estado === "rechazada" && (
        <div className="portal-ok">
          <p>Marcaste que ahora no. Puedes reconsiderarlo cuando quieras.</p>
          <button className="btn" onClick={async () => setEstado((await reabrirOferta(subjectId)).estado)}>
            Volver a considerar la oferta
          </button>
        </div>
      )}
    </Marco>
  );
}

// --- Paso 2: Contrato + firma digital -----------------------------------------

export function PortalContrato() {
  const { subjectId, oferta, estado, setEstado, firma, setFirma } = usePortal();
  const nav = useNavigate();
  const [nombre, setNombre] = useState("");
  const [acepta, setAcepta] = useState(false);
  const [firmando, setFirmando] = useState(false);
  if (!oferta) return <div className="portal-bg"><div className="cargando">CARGANDO…</div></div>;

  if (["pendiente", "propuesta_enviada"].includes(estado)) {
    return (
      <Marco paso={2} estado={estado}>
        <Bloqueado texto="Tu contrato se libera cuando aceptes tu oferta."
          href={`/oferta/${subjectId}`} cta="Ir a mi oferta" />
      </Marco>
    );
  }

  const firmar = async () => {
    setFirmando(true);
    try {
      const c = await firmarContrato(subjectId, nombre);
      setEstado(c.estado); setFirma(c.firma ?? null);
    } finally { setFirmando(false); }
  };

  return (
    <Marco paso={2} estado={estado}>
      <div className="portal-card">
        <h2>Tu contrato de crédito</h2>
        <div className="mini-cond">
          <div><span>Monto</span><b>{fmtMoney(oferta.monto)}</b></div>
          <div><span>Plazo</span><b>{oferta.plazo_meses} meses</b></div>
          <div><span>Tasa</span><b>1,80% M.V.</b></div>
        </div>
        <a href={contratoPdfUrl(subjectId)} target="_blank" rel="noopener noreferrer" className="doc-link">
          <span><span className="t">Leer el contrato completo</span><br /><span className="s">PDF · CONDICIONES Y PLAN DE PAGOS</span></span>
          <span className="ir">ABRIR →</span>
        </a>

        {estado === "aceptada" ? (
          <div className="firma-box">
            <div className="firma-titulo">✍️ Firma electrónica</div>
            <input className="firma-input" placeholder="Escribe tu nombre completo"
              value={nombre} onChange={(e) => setNombre(e.target.value)} />
            {nombre.trim() && <div className="firma-preview">{nombre}</div>}
            <label className="firma-check">
              <input type="checkbox" checked={acepta} onChange={(e) => setAcepta(e.target.checked)} />
              <span>Reconozco y firmo electrónicamente este contrato, aceptando sus condiciones.</span>
            </label>
            <button className="btn primario grande" disabled={!nombre.trim() || !acepta || firmando}
              onClick={firmar}>{firmando ? "Firmando…" : "Firmar contrato"}</button>
          </div>
        ) : (
          <div className="portal-ok">
            <p><b>✓ Contrato firmado</b> por {firma?.nombre}.</p>
            <div className="mono" style={{ color: "var(--gris-suave)" }}>SELLO DE FIRMA · {firma?.sello}</div>
            <button className="btn primario grande" style={{ marginTop: 12 }} onClick={() => nav(`/detalle/${subjectId}`)}>
              Ver mi detalle →
            </button>
          </div>
        )}
      </div>
    </Marco>
  );
}

// --- Paso 3: Detalle + descargas ----------------------------------------------

export function PortalDetalle() {
  const { subjectId, oferta, estado, firma } = usePortal();
  if (!oferta) return <div className="portal-bg"><div className="cargando">CARGANDO…</div></div>;

  if (estado !== "firmada") {
    return (
      <Marco paso={3} estado={estado}>
        <Bloqueado texto="Tu detalle se libera cuando firmes tu contrato."
          href={`/contrato/${subjectId}`} cta="Ir a mi contrato" />
      </Marco>
    );
  }

  return (
    <Marco paso={3} estado={estado}>
      <div className="portal-card">
        <div className="portal-ok" style={{ marginBottom: 18 }}>
          <p><b>✓ Tu crédito está activo.</b> Desembolso en trámite.</p>
          {firma && <div className="mono" style={{ color: "var(--gris-suave)" }}>Firmado por {firma.nombre} · sello {firma.sello}</div>}
        </div>
        <div className="mini-cond">
          <div><span>Producto</span><b>{oferta.nombre_producto}</b></div>
          <div><span>Monto</span><b>{fmtMoney(oferta.monto)}</b></div>
          <div><span>Plazo</span><b>{oferta.plazo_meses} meses</b></div>
        </div>
        <a href={contratoPdfUrl(subjectId)} target="_blank" rel="noopener noreferrer" className="doc-link">
          <span><span className="t">Contrato de crédito</span><br /><span className="s">PDF · FIRMADO · PLAN DE PAGOS</span></span>
          <span className="ir">DESCARGAR →</span>
        </a>
        <a href={extractoPdfUrl(subjectId)} target="_blank" rel="noopener noreferrer" className="doc-link">
          <span><span className="t">Extracto mensual</span><br /><span className="s">PDF · CUOTA, SALDO Y MOVIMIENTOS</span></span>
          <span className="ir">DESCARGAR →</span>
        </a>
      </div>
    </Marco>
  );
}
