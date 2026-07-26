// Laboratorio de Crédito: aprende los pesos del scorecard con WoE + regresión
// logística, compara campeón vs retador y permite promover a producción.

import { useEffect, useState } from "react";
import AppBar from "../components/AppBar";
import {
  entrenarModelo, getLabEstado, promoverModelo, revertirModelo,
  type ExperimentoLab, type MetricaSet,
} from "../api/client";
import { labelSenal } from "../utils";

type Estado = { version_produccion: string; hay_promovido: boolean; challenger_id: string | null };

const IV_MAX = 0.35; // referencia visual (IV > 0.3 = señal fuerte)

export default function LaboratorioView() {
  const [estado, setEstado] = useState<Estado | null>(null);
  const [exp, setExp] = useState<ExperimentoLab | null>(null);
  const [cargando, setCargando] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  const refrescar = () => getLabEstado().then(setEstado).catch(() => {});
  useEffect(() => { refrescar(); }, []);

  async function entrenar(file?: File) {
    setCargando(true); setMsg(null);
    try {
      setExp(await entrenarModelo(file));
    } catch (e) {
      setMsg(`Error al entrenar: ${String(e)}`);
    } finally {
      setCargando(false);
    }
  }

  async function promover() {
    if (!exp) return;
    await promoverModelo(exp.challenger_id);
    setMsg(`Modelo ${exp.challenger_id} promovido a producción. El pipeline ya usa los pesos aprendidos.`);
    refrescar();
  }
  async function revertir() {
    await revertirModelo();
    setMsg("Revertido al scorecard experto.");
    refrescar();
  }

  return (
    <>
      <AppBar />
      <div className="contenedor">
        <div className="seccion-titulo">
          <h1>Laboratorio de Crédito 🧪</h1>
          <span className="pista">
            Los pesos del scorecard no se ponen a mano: se aprenden con WoE + regresión logística
            y se validan contra el modelo experto antes de promoverlos.
          </span>
        </div>

        {/* Estado + acciones */}
        <div className="card" style={{ display: "flex", alignItems: "center", gap: 16, flexWrap: "wrap" }}>
          <div>
            <div style={{ fontSize: 12, color: "var(--grafito-60)" }}>Scorecard en producción</div>
            <div style={{ fontWeight: 800, fontSize: 18, color: "var(--azul-oscuro)" }}>
              {estado?.version_produccion ?? "…"}
            </div>
          </div>
          <span className={`legal ${estado?.hay_promovido ? "consentida" : "publica"}`}>
            {estado?.hay_promovido ? "modelo aprendido" : "modelo experto"}
          </span>
          <div className="spacer" style={{ flex: 1 }} />
          <label className="btn" style={{ cursor: "pointer" }}>
            ⬆ Entrenar con mi histórico
            <input type="file" accept=".xlsx,.xls" style={{ display: "none" }}
              onChange={(e) => e.target.files?.[0] && entrenar(e.target.files[0])} />
          </label>
          <button className="btn primario" disabled={cargando} onClick={() => entrenar()}>
            {cargando ? "Entrenando…" : "Entrenar (datos demo)"}
          </button>
          {estado?.hay_promovido && (
            <button className="btn" onClick={revertir}>Revertir a experto</button>
          )}
        </div>

        {msg && <div className="aviso" style={{ marginTop: 12 }}>{msg}</div>}

        {exp && (
          <>
            {/* Campeón vs Retador */}
            <div className="seccion-titulo" style={{ marginTop: 26 }}>
              <h2 style={{ margin: 0 }}>Campeón vs. Retador</h2>
              <span className="pista">
                Evaluado fuera de muestra ({exp.n_test.toLocaleString("es-CO")} casos de prueba ·
                tasa base {Math.round(exp.base_rate * 100)}%).
              </span>
            </div>
            <div className="metric-fila">
              <TarjetaMetrica titulo="Experto (campeón)" m={exp.metricas.campeon} />
              <TarjetaMetrica titulo="Aprendido (retador)" m={exp.metricas.retador} lift={exp.metricas.lift} destacado />
            </div>

            <div className="lab-grid">
              {/* Poder predictivo (IV) */}
              <div className="card">
                <h3>Poder predictivo por señal (Information Value)</h3>
                <p className="pista" style={{ marginTop: 4 }}>
                  Cuánto aporta cada base a predecir el desenlace. Referencia: &gt;0,3 fuerte ·
                  0,1–0,3 medio · &lt;0,1 débil.
                </p>
                <div style={{ marginTop: 12, display: "grid", gap: 10 }}>
                  {[...exp.iv].sort((a, b) => b.iv - a.iv).map((x) => (
                    <div key={x.feature} style={{ display: "grid", gridTemplateColumns: "160px 1fr 52px", alignItems: "center", gap: 10 }}>
                      <span style={{ fontSize: 13 }}>{labelSenal(x.feature)}</span>
                      <div style={{ background: "var(--gris-bg)", borderRadius: 6, height: 16, overflow: "hidden" }}>
                        <div style={{ width: `${Math.min(x.iv / IV_MAX, 1) * 100}%`, height: "100%",
                          background: x.iv >= 0.1 ? "var(--azul)" : "var(--gris-linea)", borderRadius: 6 }} />
                      </div>
                      <span className="mono" style={{ fontSize: 13, textAlign: "right" }}>{x.iv.toFixed(3)}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Equidad */}
              <div className="card">
                <h3>Equidad por género ⚖️</h3>
                <p className="pista" style={{ marginTop: 4 }}>
                  El modelo no usa el sexo. Auditamos que tampoco lo discrimine indirectamente.
                </p>
                <div style={{ marginTop: 14, display: "grid", gap: 12 }}>
                  {exp.equidad.grupos.map((g) => (
                    <div key={g.grupo} style={{ display: "grid", gridTemplateColumns: "90px 1fr 48px", alignItems: "center", gap: 10 }}>
                      <span style={{ fontSize: 14, fontWeight: 600 }}>{g.grupo}</span>
                      <div style={{ background: "var(--gris-bg)", borderRadius: 6, height: 18, overflow: "hidden" }}>
                        <div style={{ width: `${g.tasa_aprobacion * 100}%`, height: "100%", background: "var(--amarillo)" }} />
                      </div>
                      <span className="mono" style={{ fontSize: 13, textAlign: "right" }}>{Math.round(g.tasa_aprobacion * 100)}%</span>
                    </div>
                  ))}
                </div>
                {exp.equidad.brecha_pp != null && (
                  <div style={{ marginTop: 14, fontSize: 14 }}>
                    Brecha de aprobación:{" "}
                    <b style={{ color: exp.equidad.brecha_pp <= 3 ? "var(--verde, #2e7d32)" : "#c62828" }}>
                      {exp.equidad.brecha_pp} pp
                    </b>{" "}
                    {exp.equidad.brecha_pp <= 3 ? "— sin sesgo relevante." : "— requiere revisión."}
                  </div>
                )}
              </div>
            </div>

            {/* Puntos experto vs aprendido */}
            <div className="card" style={{ marginTop: 18 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
                <h3 style={{ margin: 0 }}>Tabla de puntos: experto vs. aprendido</h3>
                <span className="spacer" style={{ flex: 1 }} />
                <button className="btn primario" onClick={promover}>
                  Promover retador a producción →
                </button>
              </div>
              <div style={{ overflowX: "auto", marginTop: 12 }}>
                <table className="tabla-pts">
                  <thead>
                    <tr><th>Señal</th><th>Bin</th><th>Experto</th><th>Aprendido</th><th>Δ</th></tr>
                  </thead>
                  <tbody>
                    {exp.comparacion_puntos.map((r, i) => {
                      const delta = r.aprendido - r.experto;
                      const primero = i === 0 || exp.comparacion_puntos[i - 1].feature !== r.feature;
                      return (
                        <tr key={`${r.feature}-${r.bin}`} style={primero ? { borderTop: "2px solid var(--gris-linea)" } : undefined}>
                          <td style={{ color: primero ? "var(--azul-oscuro)" : "transparent", fontWeight: 600 }}>
                            {labelSenal(r.feature)}
                          </td>
                          <td style={{ color: "var(--grafito-60)" }}>{r.bin}</td>
                          <td className="mono">{r.experto}</td>
                          <td className="mono" style={{ fontWeight: 700 }}>{r.aprendido}</td>
                          <td className="mono" style={{ color: delta === 0 ? "var(--grafito-60)" : delta > 0 ? "#2e7d32" : "#c62828" }}>
                            {delta > 0 ? "+" : ""}{delta}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}
      </div>
    </>
  );
}

function TarjetaMetrica({ titulo, m, lift, destacado }: {
  titulo: string; m: MetricaSet; lift?: MetricaSet; destacado?: boolean;
}) {
  return (
    <div className="card" style={destacado ? { borderTop: "4px solid var(--azul)" } : undefined}>
      <div style={{ fontSize: 13, color: "var(--grafito-60)", fontWeight: 600 }}>{titulo}</div>
      <div className="metric-set">
        <Metric label="AUC" v={m.auc} d={lift?.auc} />
        <Metric label="Gini" v={m.gini} d={lift?.gini} />
        <Metric label="KS" v={m.ks} d={lift?.ks} />
      </div>
    </div>
  );
}

function Metric({ label, v, d }: { label: string; v: number; d?: number }) {
  return (
    <div>
      <div style={{ fontSize: 22, fontWeight: 800, color: "var(--azul-oscuro)" }}>{v.toFixed(3)}</div>
      <div style={{ fontSize: 12, color: "var(--grafito-60)" }}>{label}</div>
      {d != null && d !== 0 && (
        <div style={{ fontSize: 12, fontWeight: 700, color: d > 0 ? "#2e7d32" : "#c62828" }}>
          {d > 0 ? "▲ +" : "▼ "}{d.toFixed(3)}
        </div>
      )}
    </div>
  );
}
