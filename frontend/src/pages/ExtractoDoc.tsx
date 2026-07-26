// Extracto mensual del crédito, imprimible (formato Colsubsidio · MOMENTO).

import { useEffect, useState } from "react";
import { useNavigate, useParams, useSearchParams } from "react-router-dom";
import { getOferta } from "../api/client";
import type { Oferta } from "../types";
import { amortizar, cuotaMensual, fechaCorta, money, seguroMensual } from "../credito";

const MONO = "var(--mono)";
const kMini = { fontFamily: MONO, fontSize: 8.5, letterSpacing: "0.12em", textTransform: "uppercase" as const, color: "#9ca3af" };

export default function ExtractoDoc() {
  const { subjectId } = useParams<{ subjectId: string }>();
  const [sp] = useSearchParams();
  const nav = useNavigate();
  const [o, setO] = useState<Oferta | null>(null);

  useEffect(() => {
    if (subjectId) getOferta(subjectId).then(setO).catch(() => {});
  }, [subjectId]);

  if (!o) return <div className="doc-bg"><div className="cargando">CARGANDO EXTRACTO…</div></div>;

  const plazo = o.plazo_meses;
  const pagadas = Math.min(plazo - 1, Math.max(1, Number(sp.get("pagadas") ?? 3)));
  const cuota = cuotaMensual(o.monto, plazo);
  const seguro = seguroMensual(o.monto);
  const plan = amortizar(o.monto, plazo);
  const saldoActual = plan.slice(pagadas).reduce((t, b) => t + b.capital, 0);
  const interesMes = plan[pagadas].interes;
  const capitalMes = plan[pagadas].capital;
  const maxCuota = cuota;

  const hoy = new Date();
  const corte = new Date(hoy.getFullYear(), hoy.getMonth(), 30);
  const vence = new Date(hoy.getFullYear(), hoy.getMonth() + 1, 5);
  const MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"];

  const resumen: [string, string][] = [
    ["Saldo total", money(saldoActual)],
    ["Cuotas pagadas", `${pagadas} / ${plazo}`],
    ["Monto original", money(o.monto)],
    ["Tasa fija", "1,80% M.V."],
  ];
  const detalle: [string, string][] = [
    ["Abono a capital", money(capitalMes)],
    ["Intereses", money(interesMes)],
    ["Seguro de vida", money(seguro)],
    ["Total cuota", money(cuota + seguro)],
  ];
  const movimientos = [
    ["05 " + fechaCorta(new Date(hoy.getFullYear(), hoy.getMonth(), 5)).slice(3), `Pago cuota ${String(pagadas).padStart(2, "0")}`, "débito automático", "−" + money(cuota + seguro), "#0f7a48"],
    [fechaCorta(new Date(hoy.getFullYear(), hoy.getMonth(), 5)), "Intereses del periodo", "liquidación", money(plan[Math.max(0, pagadas - 1)].interes), "#0a0a0a"],
    [fechaCorta(new Date(hoy.getFullYear(), hoy.getMonth(), 5)), "Seguro de vida deudores", "liquidación", money(seguro), "#0a0a0a"],
    [fechaCorta(new Date(hoy.getFullYear(), hoy.getMonth(), 12)), "Abono extraordinario a capital", "whatsapp", "−" + money(120000), "#0f7a48"],
    [fechaCorta(corte), "Saldo al corte", "—", money(saldoActual), "#0a0a0a"],
  ] as const;
  const th = { textAlign: "left" as const, padding: "8px 12px", border: "1px solid #e5e7eb", ...kMini, fontWeight: 500 };
  const td = { padding: "7px 12px", border: "1px solid #e5e7eb" };

  return (
    <div className="doc-bg">
      <div className="doc-toolbar">
        <button className="btn" onClick={() => nav(`/afiliado/${o.subject_id}`)}>← Volver a la oferta</button>
        <button className="btn primario" onClick={() => window.print()}>Imprimir / Guardar PDF</button>
      </div>

      <div className="doc-sheet">
        <div className="doc-head">
          <span className="doc-marca">MOMENTO<small>EXTRACTO DE CRÉDITO</small></span>
          <span style={{ fontFamily: MONO, fontSize: 9, letterSpacing: "0.1em", color: "#575756" }}>
            OBLIGACIÓN 40{o.subject_id.slice(0, 8).toUpperCase()}
          </span>
        </div>

        <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 30, flexWrap: "wrap" }}>
          <div>
            <span style={{ fontFamily: MONO, fontSize: 9.5, letterSpacing: "0.16em", textTransform: "uppercase", color: "var(--azul)" }}>▸ Extracto mensual</span>
            <h1 style={{ marginTop: 10 }}>{o.nombre_producto}</h1>
            <p style={{ marginTop: 8, color: "#575756", fontWeight: 500 }}>
              Periodo {MESES[hoy.getMonth()]} {hoy.getFullYear()} · corte {fechaCorta(corte)}
            </p>
          </div>
          <div style={{ textAlign: "right", border: "1px solid #e5e7eb", borderRadius: 10, padding: "14px 18px", minWidth: 230 }}>
            <div style={kMini}>Total a pagar este mes</div>
            <div style={{ fontWeight: 700, fontSize: 30, letterSpacing: "-0.03em", marginTop: 6, fontVariantNumeric: "tabular-nums" }}>{money(cuota + seguro)}</div>
            <div style={{ fontFamily: MONO, fontSize: 10, color: "#c0392b", marginTop: 6 }}>VENCE {fechaCorta(vence)}</div>
          </div>
        </div>

        {/* resumen */}
        <div style={{ marginTop: 24, display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 1, background: "#e5e7eb", border: "1px solid #e5e7eb", borderRadius: 8, overflow: "hidden" }}>
          {resumen.map(([k, v]) => (
            <div key={k} style={{ background: "#fff", padding: "12px 14px" }}>
              <div style={kMini}>{k}</div>
              <div style={{ fontWeight: 700, fontSize: 18, letterSpacing: "-0.02em", marginTop: 6, fontVariantNumeric: "tabular-nums" }}>{v}</div>
            </div>
          ))}
        </div>

        <div style={{ marginTop: 26, display: "grid", gridTemplateColumns: "minmax(0,1fr) 250px", gap: 26, alignItems: "start" }}>
          <div>
            <h2>Movimientos del periodo</h2>
            <table style={{ marginTop: 12, fontSize: 11.5 }}>
              <thead><tr style={{ background: "#fafafa" }}>
                {["Fecha", "Descripción", "Canal", "Valor"].map((h, i) => (
                  <th key={h} style={{ ...th, textAlign: i === 3 ? "right" : "left" }}>{h}</th>
                ))}
              </tr></thead>
              <tbody>
                {movimientos.map((m, i) => (
                  <tr key={i}>
                    <td style={{ ...td, fontFamily: MONO, color: "#575756" }}>{m[0]}</td>
                    <td style={{ ...td, fontWeight: 600 }}>{m[1]}</td>
                    <td style={{ ...td, fontFamily: MONO, fontSize: 10.5, color: "#575756" }}>{m[2]}</td>
                    <td style={{ ...td, textAlign: "right", fontVariantNumeric: "tabular-nums", color: m[4], fontWeight: 600 }}>{m[3]}</td>
                  </tr>
                ))}
              </tbody>
            </table>

            <h2 style={{ marginTop: 26 }}>Cómo va tu crédito</h2>
            <p style={{ marginTop: 8, color: "#575756", fontWeight: 500, lineHeight: 1.5 }}>
              Has pagado {pagadas} de {plazo} cuotas. En azul lo abonado a capital y en amarillo los intereses del periodo.
            </p>
            <div style={{ marginTop: 14, display: "flex", alignItems: "flex-end", gap: 4, height: 88 }}>
              {plan.map((b, k) => (
                <div key={k} style={{ flex: 1, display: "flex", flexDirection: "column", justifyContent: "flex-end", gap: 5 }}>
                  <div style={{ height: Math.round((b.interes / maxCuota) * 62), background: "var(--amarillo)", borderRadius: "2px 2px 0 0" }} />
                  <div style={{ height: Math.round((b.capital / maxCuota) * 62), background: k < pagadas ? "var(--azul)" : "#dfe3e9", borderRadius: "0 0 2px 2px" }} />
                  <span style={{ fontFamily: MONO, fontSize: 7.5, textAlign: "center", color: "#9ca3af" }}>{b.n}</span>
                </div>
              ))}
            </div>
          </div>

          <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
            <div style={{ border: "1px solid #e5e7eb", borderRadius: 10, overflow: "hidden" }}>
              <div style={{ background: "var(--azul)", color: "#fff", padding: "12px 14px" }}>
                <div style={{ fontFamily: MONO, fontSize: 8.5, letterSpacing: "0.12em", textTransform: "uppercase", color: "var(--amarillo)" }}>Paga fácil</div>
                <div style={{ fontWeight: 700, fontSize: 14, marginTop: 6, lineHeight: 1.3 }}>Débito automático el 5 de cada mes</div>
              </div>
              <div style={{ padding: "12px 14px", fontSize: 11.5, lineHeight: 1.6, color: "#3f3f46" }}>
                También puedes pagar por WhatsApp respondiendo <b>PAGAR</b>, en la app Colsubsidio, o en cualquier droguería y supermercado Colsubsidio con el número de obligación.
              </div>
            </div>
            <div style={{ border: "1px solid #e5e7eb", borderRadius: 10, padding: 14 }}>
              <div style={kMini}>Detalle de la cuota</div>
              {detalle.map(([k, v], i) => (
                <div key={k} style={{ display: "flex", alignItems: "baseline", justifyContent: "space-between", gap: 12, padding: "8px 0", borderBottom: i < detalle.length - 1 ? "1px solid #f1f2f4" : "none", fontSize: 11.5 }}>
                  <span style={{ color: "#575756", fontWeight: 500 }}>{k}</span>
                  <span style={{ fontFamily: MONO, fontWeight: 600, fontVariantNumeric: "tabular-nums" }}>{v}</span>
                </div>
              ))}
            </div>
            <div style={{ border: "1px solid #e5e7eb", borderRadius: 10, padding: 14, background: "#fafafa" }}>
              <div style={kMini}>Si te atrasas</div>
              <p style={{ marginTop: 8, fontSize: 11.5, lineHeight: 1.6, color: "#3f3f46" }}>
                Los intereses de mora se liquidan a la tasa máxima legal vigente. Si prevés una dificultad, escríbenos antes del vencimiento: podemos revisar tu plan de pagos.
              </p>
            </div>
          </div>
        </div>

        <div style={{ marginTop: 26, padding: "14px 16px", background: "#fff", border: "1px solid #e5e7eb", borderLeft: "3px solid var(--amarillo)", borderRadius: 8, fontFamily: MONO, fontSize: 9.5, lineHeight: 1.8, letterSpacing: "0.04em", color: "#575756" }}>
          SUJETO {o.subject_id} · OBLIGACIÓN 40{o.subject_id.slice(0, 8).toUpperCase()}<br />
          TASA 1,80% M.V. · 23,87% E.A. FIJA · SIN CONSULTA A BURÓ DE CRÉDITO<br />
          DOCUMENTO DE DEMOSTRACIÓN — HACKATHON COLSUBSIDIO × 30X
        </div>

        <div className="doc-foot">
          <span>CAJA COLOMBIANA DE SUBSIDIO FAMILIAR COLSUBSIDIO · NIT 860.007.336-1</span>
          <span>PQR: LÍNEA 7457000 BOGOTÁ</span>
        </div>
      </div>
    </div>
  );
}
