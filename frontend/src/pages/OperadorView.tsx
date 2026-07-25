// Vista operador (área de riesgo / negocio): KPIs, métrica de pitch y el lote
// de ofertas con su ventana, canal y señales. Clic en una fila -> vista afiliado.

import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import AppBar from "../components/AppBar";
import CoberturaChart from "../components/CoberturaChart";
import { getMetrics, getOfertas, getStats } from "../api/client";
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

export default function OperadorView() {
  const nav = useNavigate();
  const [stats, setStats] = useState<Stats | null>(null);
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [lista, setLista] = useState<ListaOfertas | null>(null);
  const [producto, setProducto] = useState("");
  const [page, setPage] = useState(0);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getStats().then(setStats).catch((e) => setError(String(e)));
    getMetrics().then(setMetrics).catch(() => {});
  }, []);

  useEffect(() => {
    getOfertas(PAGE, page * PAGE, producto || undefined)
      .then(setLista)
      .catch((e) => setError(String(e)));
  }, [producto, page]);

  return (
    <>
      <AppBar />
      <div className="contenedor">
        {error && (
          <div className="aviso">
            No se pudo conectar con la API ({error}). Corre <span className="mono">seed_synthetic</span> y{" "}
            <span className="mono">build_ofertas</span>, luego levanta{" "}
            <span className="mono">uvicorn momento.api:app</span>.
          </div>
        )}

        {stats && (
          <div className="grid kpis">
            <Kpi valor={stats.total_ofertas.toLocaleString("es-CO")} etiqueta="Ofertas generadas" />
            <Kpi valor={fmtMoney(stats.monto_promedio)} etiqueta="Monto promedio" />
            <Kpi valor={Object.keys(stats.productos).length.toString()} etiqueta="Productos" />
            <Kpi valor={Object.keys(stats.canales).length.toString()} etiqueta="Canales" />
          </div>
        )}

        {metrics?.cobertura_contacto && (
          <div style={{ marginTop: 18 }}>
            <CoberturaChart curva={metrics.cobertura_contacto} />
          </div>
        )}

        <div className="seccion-titulo">
          <h2>Ofertas del lote</h2>
          <span className="pista">clic en una fila para ver la experiencia del afiliado</span>
        </div>

        <div className="filtros">
          {PRODUCTOS.map((p) => (
            <button
              key={p.key}
              className={`chip ${producto === p.key ? "activo" : ""}`}
              onClick={() => {
                setProducto(p.key);
                setPage(0);
              }}
            >
              {p.label}
            </button>
          ))}
        </div>

        {lista && (
          <>
            <table className="ofertas">
              <thead>
                <tr>
                  <th>Sujeto</th>
                  <th>Producto</th>
                  <th>Monto</th>
                  <th>Ventana</th>
                  <th>Canal</th>
                  <th>Puntos</th>
                </tr>
              </thead>
              <tbody>
                {lista.items.map((o) => (
                  <tr key={o.subject_id} onClick={() => nav(`/afiliado/${o.subject_id}`)}>
                    <td className="mono">{o.subject_id.slice(0, 12)}…</td>
                    <td>{o.nombre_producto}</td>
                    <td>{fmtMoney(o.monto)}</td>
                    <td>
                      {fmtMes(o.ventana_inicio)} – {fmtMes(o.ventana_fin)}
                    </td>
                    <td>
                      <span className="badge canal">{o.canal}</span>
                    </td>
                    <td>
                      <span className="badge puntos">{o.puntos_scorecard}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>

            <div className="paginador">
              <button className="btn primario" disabled={page === 0} onClick={() => setPage(page - 1)}>
                ← Anterior
              </button>
              <span>
                {page * PAGE + 1}–{Math.min((page + 1) * PAGE, lista.total)} de{" "}
                {lista.total.toLocaleString("es-CO")}
              </span>
              <button
                className="btn primario"
                disabled={(page + 1) * PAGE >= lista.total}
                onClick={() => setPage(page + 1)}
              >
                Siguiente →
              </button>
            </div>
          </>
        )}
      </div>
    </>
  );
}

function Kpi({ valor, etiqueta }: { valor: string; etiqueta: string }) {
  return (
    <div className="card kpi">
      <div className="valor">{valor}</div>
      <div className="etiqueta">{etiqueta}</div>
    </div>
  );
}
