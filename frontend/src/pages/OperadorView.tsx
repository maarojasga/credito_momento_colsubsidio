// Vista operador (home): hero, franja de KPIs, métrica estrella, resumen IA y el
// lote de ofertas. Clic en una fila -> vista afiliado.

import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import AppBar from "../components/AppBar";
import CargarExcel from "../components/CargarExcel";
import CoberturaChart from "../components/CoberturaChart";
import ResumenIA from "../components/ResumenIA";
import {
  enviarCampana, getCampanaEstado, getMetrics, getOfertas, getStats,
  type CampanaEstado,
} from "../api/client";
import type { ListaOfertas, Metrics, Stats } from "../types";
import { fmtMes, fmtMoney } from "../utils";

const PAGE = 25;

const PRODUCTOS = [
  { key: "", label: "Todos" },
  { key: "libranza", label: "Libranza" },
  { key: "cupo_rotativo", label: "Cupo rotativo" },
  { key: "credito_mujer", label: "Crédito Mujer" },
  { key: "rotativo_seguros_impuestos", label: "Rotativo seguros" },
];

const PROD_COLOR: Record<string, string> = {
  libranza: "#0067b1",
  cupo_rotativo: "#00a499",
  credito_mujer: "#7b4dc0",
  rotativo_seguros_impuestos: "#ff6a4d",
};

export default function OperadorView() {
  const nav = useNavigate();
  const [stats, setStats] = useState<Stats | null>(null);
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [lista, setLista] = useState<ListaOfertas | null>(null);
  const [producto, setProducto] = useState("");
  const [page, setPage] = useState(0);
  const [campana, setCampana] = useState<CampanaEstado | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refrescar = useCallback(() => {
    getStats().then(setStats).catch((e) => setError(String(e)));
    getMetrics().then(setMetrics).catch(() => {});
    getCampanaEstado().then(setCampana).catch(() => {});
    getOfertas(PAGE, page * PAGE, producto || undefined)
      .then(setLista)
      .catch((e) => setError(String(e)));
  }, [producto, page]);

  const lanzarCampana = async () => { await enviarCampana(); refrescar(); };

  useEffect(() => { refrescar(); }, [refrescar]);

  const vacio = stats !== null && stats.total_ofertas === 0;

  return (
    <>
      <AppBar />

      {/* Hero */}
      <section className="hero">
        <div className="contenedor" style={{ paddingTop: 16, paddingBottom: 0 }}>
          <div className="hero-inner">
            <div className="hero-glow" aria-hidden />
            <div className="hero-body">
              <span className="kicker">▸ Reto 01 · Crédito hiperpersonalizado</span>
              <h1>El crédito correcto, en el momento justo.</h1>
              <p>
                Motor de crédito sin buró: detecta cuándo un afiliado va a necesitar crédito, ordena
                los productos para los que ya es elegible y entrega la oferta por el canal correcto.
                Todo auditable.
              </p>
              <div className="principios">
                <span>La norma no se aprende</span><span>·</span>
                <span>La señal es la unidad atómica</span><span>·</span>
                <span>La explicación se calcula, no se genera</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <div className="contenedor" style={{ paddingTop: 8 }}>
        {error && (
          <div className="aviso" style={{ marginBottom: 20 }}>
            No se pudo conectar con la API ({error}). Verifica que el backend esté arriba.
          </div>
        )}

        {vacio && (
          <div style={{ maxWidth: 640, margin: "48px auto" }}>
            <div className="card" style={{ textAlign: "center" }}>
              <h2>Aún no hay afiliados cargados</h2>
              <p style={{ color: "var(--grafito-60)", margin: "8px 0 20px" }}>
                Sube tu Excel de afiliados para generar las ofertas. Descarga la plantilla si
                necesitas el formato de columnas.
              </p>
              <CargarExcel onCargado={refrescar} />
            </div>
          </div>
        )}

        {stats && !vacio && (
          <>
            {/* Franja de KPIs */}
            <div className="kpi-strip">
              <KpiCol valor={stats.total_ofertas.toLocaleString("es-CO")} etiqueta="Ofertas generadas" color="var(--amarillo)" />
              <KpiCol valor={fmtMoney(stats.monto_promedio)} etiqueta="Monto promedio" color="var(--azul)" />
              <KpiCol valor={Object.keys(stats.productos).length.toString()} etiqueta="Productos elegibles" color="var(--amarillo)" />
              <KpiCol valor={Object.keys(stats.canales).length.toString()} etiqueta="Canales de entrega" color="var(--azul)" />
            </div>

            {metrics?.cobertura_contacto && (
              <div style={{ marginTop: 40 }}>
                <CoberturaChart curva={metrics.cobertura_contacto} />
              </div>
            )}

            <div style={{ marginTop: 20 }}>
              <ResumenIA />
            </div>

            {/* Embudo de campaña */}
            <div className="card" style={{ marginTop: 20 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
                <h3 style={{ margin: 0 }}>Campaña a la base de clientes 📨</h3>
                <span className="pista">propuesta → aceptación → firma → extractos</span>
                <span className="spacer" style={{ flex: 1 }} />
                <button className="btn primario" onClick={lanzarCampana}>
                  {campana?.campana_enviada ? "Reenviar propuesta" : "Enviar propuesta a la base →"}
                </button>
              </div>
              {campana && (
                <div className="embudo">
                  {[
                    ["Propuesta enviada", campana.conteo.propuesta_enviada + campana.conteo.aceptada + campana.conteo.firmada, "var(--azul)"],
                    ["Aceptada", campana.conteo.aceptada + campana.conteo.firmada, "var(--azul-oscuro)"],
                    ["Firmada", campana.conteo.firmada, "var(--ok)"],
                    ["Rechazada", campana.conteo.rechazada, "var(--rojo)"],
                  ].map(([k, v, c]) => (
                    <div className="embudo-col" key={k as string}>
                      <div className="embudo-n" style={{ color: c as string }}>{v as number}</div>
                      <div className="embudo-k">{k as string}</div>
                    </div>
                  ))}
                  <div className="embudo-col">
                    <div className="embudo-n" style={{ color: "var(--gris-suave)" }}>{campana.conteo.pendiente}</div>
                    <div className="embudo-k">Sin enviar</div>
                  </div>
                </div>
              )}
            </div>

            {/* Lote */}
            <div className="seccion-titulo">
              <div>
                <h2>El lote de ofertas.</h2>
                <p className="pista" style={{ margin: "12px 0 0" }}>
                  Clic en una fila para ver la experiencia del afiliado y el respaldo de la decisión.
                </p>
              </div>
              <span className="spacer" />
              <CargarExcel onCargado={refrescar} compacto />
            </div>

            <div className="filtros">
              {PRODUCTOS.map((p) => (
                <button
                  key={p.key}
                  className={`chip ${producto === p.key ? "activo" : ""}`}
                  onClick={() => { setProducto(p.key); setPage(0); }}
                >
                  {p.label}
                </button>
              ))}
            </div>
          </>
        )}

        {!vacio && lista && (
          <>
            <div className="lote-wrap">
              <table className="ofertas">
                <thead>
                  <tr>
                    <th>Sujeto</th><th>Producto</th><th>Monto</th>
                    <th>Ventana</th><th>Canal</th><th style={{ textAlign: "right" }}>Puntos</th>
                  </tr>
                </thead>
                <tbody>
                  {lista.items.map((o) => (
                    <tr key={o.subject_id} onClick={() => nav(`/afiliado/${o.subject_id}`)}>
                      <td className="mono">{o.subject_id.slice(0, 12)}…</td>
                      <td>
                        <span className="prod-cell">
                          <span className="prod-dot" style={{ background: PROD_COLOR[o.producto] ?? "#0067b1" }} />
                          {o.nombre_producto}
                        </span>
                      </td>
                      <td>{fmtMoney(o.monto)}</td>
                      <td className="mono">{fmtMes(o.ventana_inicio)} – {fmtMes(o.ventana_fin)}</td>
                      <td><span className="badge canal">{o.canal}</span></td>
                      <td>
                        <span className="puntos-cell">
                          <span className="puntos-bar">
                            <span style={{ width: `${Math.round((o.puntos_scorecard / 820) * 100)}%` }} />
                          </span>
                          <span className="badge puntos">{o.puntos_scorecard}</span>
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="paginador">
              <span className="rango">
                {page * PAGE + 1}–{Math.min((page + 1) * PAGE, lista.total)} de{" "}
                {lista.total.toLocaleString("es-CO")}
              </span>
              <div className="botones">
                <button className="btn" disabled={page === 0} onClick={() => setPage(page - 1)}>
                  ← Anterior
                </button>
                <button className="btn" disabled={(page + 1) * PAGE >= lista.total} onClick={() => setPage(page + 1)}>
                  Siguiente →
                </button>
              </div>
            </div>

            <p className="privacidad">
              Privacidad · solo se almacena el hash del documento. Nombre, correo y número de
              documento nunca se guardan. Ninguna señal proviene de un buró de crédito.
            </p>
          </>
        )}
      </div>
    </>
  );
}

function KpiCol({ valor, etiqueta, color }: { valor: string; etiqueta: string; color: string }) {
  return (
    <div className="kpi-col">
      <span className="barra" style={{ background: color }} />
      <span className="valor">{valor}</span>
      <span className="etiqueta">{etiqueta}</span>
    </div>
  );
}
