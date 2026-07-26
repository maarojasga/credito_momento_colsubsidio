// Documento de contrato de crédito, imprimible (formato Colsubsidio · MOMENTO).

import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { getManifest, getOferta } from "../api/client";
import type { Manifiesto, Oferta } from "../types";
import { amortizar, cuotaMensual, fechaCorta, fechaLarga, money, seguroMensual } from "../credito";
import { labelSenal } from "../utils";

const MONO = "var(--mono)";
const kLabel = { fontFamily: MONO, fontSize: 9.5, letterSpacing: "0.08em", textTransform: "uppercase" as const, color: "#9ca3af" };
const kMini = { fontFamily: MONO, fontSize: 8.5, letterSpacing: "0.12em", textTransform: "uppercase" as const, color: "#9ca3af" };

export default function ContratoDoc() {
  const { subjectId } = useParams<{ subjectId: string }>();
  const nav = useNavigate();
  const [o, setO] = useState<Oferta | null>(null);
  const [man, setMan] = useState<Manifiesto | null>(null);

  useEffect(() => {
    if (!subjectId) return;
    getOferta(subjectId).then(setO).catch(() => {});
    getManifest(subjectId).then(setMan).catch(() => {});
  }, [subjectId]);

  if (!o) return <div className="doc-bg"><div className="cargando">CARGANDO CONTRATO…</div></div>;

  const cuota = cuotaMensual(o.monto, o.plazo_meses);
  const seguro = seguroMensual(o.monto);
  const total = cuota * o.plazo_meses;
  const plan = amortizar(o.monto, o.plazo_meses);
  const hoy = new Date();
  const primerVenc = new Date(hoy.getFullYear(), hoy.getMonth() + 1, 5);
  const hashDoc = o.subject_id.slice(0, 24);
  const baseDe = (key: string) => man?.senales.find((s) => s.key === key)?.base_legal ?? "declarada";

  const condiciones: [string, string][] = [
    ["Monto desembolsado", money(o.monto)],
    ["Plazo", `${o.plazo_meses} meses`],
    ["Tasa de interés remuneratoria", "1,80% mes vencido"],
    ["Tasa efectiva anual equivalente", "23,87% E.A."],
    ["Cuota fija mensual", money(cuota)],
    ["Seguro de vida deudores (mensual)", money(seguro)],
    ["Estudio de crédito", "$0 · sin costo"],
    ["Total a pagar", money(total + seguro * o.plazo_meses)],
    ["Forma de pago", o.canal === "asesor" ? "Libranza / débito automático" : "Débito automático"],
    ["Día de pago", "5 de cada mes"],
  ];
  const th = { textAlign: "left" as const, padding: "8px 12px", border: "1px solid #e5e7eb", ...kMini, fontWeight: 500 };
  const td = { padding: "7px 12px", border: "1px solid #e5e7eb", fontVariantNumeric: "tabular-nums" as const };

  return (
    <div className="doc-bg">
      <div className="doc-toolbar">
        <button className="btn" onClick={() => nav(`/afiliado/${o.subject_id}`)}>← Volver a la oferta</button>
        <button className="btn primario" onClick={() => window.print()}>Imprimir / Guardar PDF</button>
      </div>

      <div className="doc-sheet">
        <div className="doc-head">
          <span className="doc-marca">MOMENTO<small>MOTOR DE CRÉDITO · COLSUBSIDIO</small></span>
          <span style={{ fontFamily: MONO, fontSize: 9, letterSpacing: "0.1em", color: "#575756" }}>
            CONTRATO MOM-2026-{o.subject_id.slice(0, 8).toUpperCase()}
          </span>
        </div>

        <span style={{ fontFamily: MONO, fontSize: 9.5, letterSpacing: "0.16em", textTransform: "uppercase", color: "var(--azul)" }}>▸ Documento contractual</span>
        <h1 style={{ marginTop: 10 }}>Contrato de crédito de consumo</h1>
        <p style={{ marginTop: 10, color: "#575756", fontWeight: 500, lineHeight: 1.5 }}>
          {o.nombre_producto} · aprobado por el motor MOMENTO el {fechaLarga(hoy)}. Este documento recoge
          las condiciones aceptadas por el deudor a través del canal {o.canal.toUpperCase()} y queda vinculado
          al manifiesto de trazabilidad de la oferta.
        </p>

        {/* KPIs */}
        <div style={{ marginTop: 22, display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 1, background: "#e5e7eb", border: "1px solid #e5e7eb", borderRadius: 8, overflow: "hidden" }}>
          {[["Monto aprobado", money(o.monto)], ["Plazo", `${o.plazo_meses} meses`], ["Cuota fija", money(cuota)], ["Tasa", "1,80% M.V."]].map(([k, v]) => (
            <div key={k} style={{ background: "#fff", padding: "12px 14px" }}>
              <div style={kMini}>{k}</div>
              <div style={{ fontWeight: 700, fontSize: 19, letterSpacing: "-0.02em", marginTop: 6, fontVariantNumeric: "tabular-nums" }}>{v}</div>
            </div>
          ))}
        </div>

        {/* 1 Partes */}
        <h2 style={{ marginTop: 30 }}>1 · Partes</h2>
        <div style={{ marginTop: 12, border: "1px solid #e5e7eb", borderRadius: 8, overflow: "hidden" }}>
          {[
            ["Acreedor", "Caja Colombiana de Subsidio Familiar Colsubsidio · Línea de crédito social"],
            ["Deudor", `Afiliado identificado por hash de documento ${hashDoc}`],
            ["Sujeto MOMENTO", o.subject_id],
            ["Aceptación", `${o.canal.toUpperCase()} · ${fechaLarga(hoy)} · ${o.hora_envio}`],
          ].map(([k, v], idx, arr) => (
            <div key={k} style={{ display: "grid", gridTemplateColumns: "180px minmax(0,1fr)", gap: 16, padding: "10px 14px", borderBottom: idx < arr.length - 1 ? "1px solid #f1f2f4" : "none" }}>
              <span style={kLabel}>{k}</span>
              <span style={{ fontWeight: 600 }}>{v}</span>
            </div>
          ))}
        </div>

        {/* 2 Condiciones */}
        <h2 style={{ marginTop: 26 }}>2 · Condiciones financieras</h2>
        <div style={{ marginTop: 12, border: "1px solid #e5e7eb", borderRadius: 8, overflow: "hidden" }}>
          {condiciones.map(([k, v], idx) => (
            <div key={k} style={{ display: "grid", gridTemplateColumns: "minmax(0,1fr) 200px", gap: 16, padding: "9px 14px", borderBottom: idx < condiciones.length - 1 ? "1px solid #f1f2f4" : "none" }}>
              <span style={{ color: "#575756", fontWeight: 500 }}>{k}</span>
              <span style={{ textAlign: "right", fontFamily: MONO, fontSize: 11.5, fontWeight: 600, fontVariantNumeric: "tabular-nums" }}>{v}</span>
            </div>
          ))}
        </div>
        <p style={{ marginTop: 10, fontSize: 11, color: "#9ca3af", lineHeight: 1.5 }}>
          El valor total financiado incluye el seguro de vida deudores. La tasa es fija durante toda la vigencia;
          el deudor puede prepagar total o parcialmente sin sanción, conforme a la Ley 1555 de 2012.
        </p>

        {/* 3 Plan de pagos */}
        <h2 style={{ marginTop: 26 }}>3 · Plan de pagos</h2>
        <p style={{ marginTop: 8, color: "#575756", fontWeight: 500 }}>
          Amortización con cuota fija mensual. Primer vencimiento el {fechaLarga(primerVenc)}.
        </p>
        <table style={{ marginTop: 12, fontSize: 11 }}>
          <thead><tr style={{ background: "#fafafa" }}>
            {["Cuota", "Vencimiento", "Valor cuota", "Interés", "Abono a capital", "Saldo"].map((h, i) => (
              <th key={h} style={{ ...th, textAlign: i >= 2 ? "right" : "left" }}>{h}</th>
            ))}
          </tr></thead>
          <tbody>
            {plan.map((r) => (
              <tr key={r.n}>
                <td style={{ ...td, fontFamily: MONO }}>{String(r.n).padStart(2, "0")}</td>
                <td style={{ ...td, fontFamily: MONO, color: "#575756" }}>{fechaCorta(r.venc)}</td>
                <td style={{ ...td, textAlign: "right" }}>{money(r.cuota)}</td>
                <td style={{ ...td, textAlign: "right", color: "#575756" }}>{money(r.interes)}</td>
                <td style={{ ...td, textAlign: "right" }}>{money(r.capital)}</td>
                <td style={{ ...td, textAlign: "right", fontWeight: 600 }}>{money(r.saldo)}</td>
              </tr>
            ))}
          </tbody>
        </table>

        {/* 4 Obligaciones */}
        <h2 style={{ marginTop: 26 }}>4 · Obligaciones del deudor</h2>
        <ol style={{ margin: "12px 0 0", paddingLeft: 20, lineHeight: 1.65, color: "#3f3f46" }}>
          <li style={{ marginBottom: 6 }}>Pagar cada cuota en la fecha de vencimiento indicada en el plan de pagos, por los canales habilitados por Colsubsidio.</li>
          <li style={{ marginBottom: 6 }}>Mantener actualizados sus datos de contacto y su información de afiliación.</li>
          <li style={{ marginBottom: 6 }}>Informar cualquier cambio en su situación laboral que afecte la fuente de pago pactada.</li>
          <li style={{ marginBottom: 6 }}>Asumir los intereses de mora, liquidados a la tasa máxima legal permitida, sobre las cuotas no pagadas oportunamente.</li>
        </ol>

        {/* 5 Trazabilidad */}
        <h2 style={{ marginTop: 24 }}>5 · Tratamiento de datos y trazabilidad de la decisión</h2>
        <p style={{ marginTop: 10, lineHeight: 1.65, color: "#3f3f46" }}>
          La decisión se tomó con señales declaradas, cada una con fuente, base legal y fecha. <b>Ninguna señal
          proviene de un buró de crédito.</b> El puntaje se calculó con un scorecard aditivo ({o.puntos_scorecard} puntos)
          y la explicación entregada al deudor fue redactada sobre esa decisión y validada de forma determinista.
        </p>
        <div style={{ marginTop: 12, border: "1px solid #e5e7eb", borderRadius: 8, overflow: "hidden" }}>
          {o.top_senales.map((s, idx) => (
            <div key={s.key} style={{ display: "grid", gridTemplateColumns: "minmax(0,1fr) 150px 110px 70px", gap: 14, alignItems: "center", padding: "9px 14px", borderBottom: idx < o.top_senales.length - 1 ? "1px solid #f1f2f4" : "none", fontSize: 11.5 }}>
              <span style={{ fontWeight: 600 }}>{labelSenal(s.key)}</span>
              <span style={{ fontFamily: MONO, fontSize: 10.5, color: "#9ca3af" }}>{s.source_id}</span>
              <span style={{ fontFamily: MONO, fontSize: 10.5, color: "#575756" }}>{baseDe(s.key)}</span>
              <span style={{ textAlign: "right", fontFamily: MONO, fontSize: 11, fontWeight: 600 }}>{s.puntos >= 0 ? "+" : ""}{s.puntos} pts</span>
            </div>
          ))}
        </div>
        <p style={{ marginTop: 10, fontSize: 11, color: "#9ca3af", lineHeight: 1.5 }}>
          El afiliado autoriza el tratamiento de sus datos conforme a la Ley 1581 de 2012. Del documento de identidad
          solo se conserva su hash; nombre, correo y número de documento no se almacenan en el motor.
        </p>

        {/* Firmas */}
        <div style={{ marginTop: 34, display: "grid", gridTemplateColumns: "1fr 1fr", gap: 30 }}>
          <div>
            <div style={{ height: 44, borderBottom: "1px solid #0a0a0a" }} />
            <div style={{ marginTop: 8, fontSize: 11.5, fontWeight: 700 }}>Deudor</div>
            <div style={{ fontFamily: MONO, fontSize: 10, color: "#9ca3af", marginTop: 3 }}>ACEPTACIÓN ELECTRÓNICA · {o.canal.toUpperCase()} · {o.hora_envio}</div>
          </div>
          <div>
            <div style={{ height: 44, borderBottom: "1px solid #0a0a0a" }} />
            <div style={{ marginTop: 8, fontSize: 11.5, fontWeight: 700 }}>Colsubsidio · Crédito social</div>
            <div style={{ fontFamily: MONO, fontSize: 10, color: "#9ca3af", marginTop: 3 }}>FIRMA AUTORIZADA</div>
          </div>
        </div>

        <div style={{ marginTop: 26, padding: "14px 16px", background: "#fafafa", border: "1px solid #e5e7eb", borderLeft: "3px solid var(--amarillo)", borderRadius: 8, fontFamily: MONO, fontSize: 9.5, lineHeight: 1.8, letterSpacing: "0.04em", color: "#575756" }}>
          MANIFIESTO DE TRAZABILIDAD {hashDoc}<br />
          REGLAS DURAS EVALUADAS {man?.reglas_evaluadas.length ?? 0} · SCORECARD v0.1<br />
          DOCUMENTO DE DEMOSTRACIÓN — HACKATHON COLSUBSIDIO × 30X
        </div>

        <div className="doc-foot">
          <span>CAJA COLOMBIANA DE SUBSIDIO FAMILIAR COLSUBSIDIO · NIT 860.007.336-1</span>
          <span>HASH {o.subject_id.slice(0, 12)}…</span>
        </div>
      </div>
    </div>
  );
}
