// Laboratorio de Crédito: aprende los pesos del scorecard con WoE + regresión
// logística, compara campeón vs retador, y —opcional— mide cuánto aporta el buró.

import { useEffect, useState } from "react";
import AppBar from "../components/AppBar";
import {
  entrenarModelo, getLabEstado, promoverModelo, revertirModelo,
  type ExperimentoLab, type MetricaSet,
} from "../api/client";
import { labelSenal } from "../utils";

type Estado = { version_produccion: string; hay_promovido: boolean; challenger_id: string | null };

const IV_MAX = 0.5; // referencia visual
const BURO_LABEL: Record<string, string> = {
  score_buro: "Score de buró",
  moras_ult_12m: "Moras últ. 12m",
  nivel_endeudamiento: "Endeudamiento",
};
const BUROS = [
  { id: "datacredito", nombre: "Datacrédito" },
  { id: "transunion", nombre: "TransUnion" },
  { id: "experian", nombre: "Experian" },
];

export default function LaboratorioView() {
  const [estado, setEstado] = useState<Estado | null>(null);
  const [exp, setExp] = useState<ExperimentoLab | null>(null);
  const [cargando, setCargando] = useState(false);
  const [msg, setMsg] = useState<string | null>(null);

  // Fuente de buró (opcional).
  const [buroSel, setBuroSel] = useState("");
  const [buroFile, setBuroFile] = useState<File | null>(null);

  const refrescar = () => getLabEstado().then(setEstado).catch(() => {});
  useEffect(() => { refrescar(); }, []);

  async function entrenar(hist?: File) {
    setCargando(true); setMsg(null);
    try {
      setExp(await entrenarModelo({
        file: hist,
        buroFuente: buroSel || undefined,
        buroFile: buroFile || undefined,
      }));
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

  const buroActivo = !!buroSel || !!buroFile;

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

        {/* Fuente de buró (opcional) */}
        <div className="card buro-card" style={{ marginTop: 14 }}>
          <div style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
            <div>
              <h3 style={{ margin: 0 }}>Buró de crédito <span style={{ fontWeight: 400, color: "var(--grafito-60)", fontSize: 13 }}>· opcional</span></h3>
              <p className="pista" style={{ margin: "4px 0 0" }}>
                El motor funciona <b>sin buró</b> (llega a quien no tiene historial). Si lo tienes,
                mide cuánto aporta — sin cambiar el scorecard de producción.
              </p>
            </div>
            <div className="spacer" style={{ flex: 1 }} />
            <select className="buro-select" value={buroSel}
              onChange={(e) => { setBuroSel(e.target.value); setBuroFile(null); }}>
              <option value="">— Sin buró —</option>
              {BUROS.map((b) => <option key={b.id} value={b.id}>Conectar {b.nombre}</option>)}
            </select>
            <label className="btn" style={{ cursor: "pointer" }}>
              📄 Cargar datos de buró
              <input type="file" accept=".xlsx,.xls" style={{ display: "none" }}
                onChange={(e) => { setBuroFile(e.target.files?.[0] ?? null); setBuroSel(""); }} />
            </label>
          </div>
          {buroActivo && (
            <div style={{ marginTop: 10, fontSize: 13 }}>
              <span className="legal consentida">
                {buroFile ? `archivo: ${buroFile.name}` : `conectado: ${BUROS.find((b) => b.id === buroSel)?.nombre}`}
              </span>{" "}
              <span style={{ color: "var(--grafito-60)" }}>
                — al entrenar se añade la comparación “Sin buró vs. Con buró”.
              </span>
            </div>
          )}
        </div>

        {msg && <div className="aviso" style={{ marginTop: 12 }}>{msg}</div>}

        {exp && (
          <>
            {/* Aporte del buró (si está activo) */}
            {exp.buro?.activo && exp.buro.metricas && (
              <div className="card buro-resultado" style={{ marginTop: 18 }}>
                <div style={{ display: "flex", alignItems: "baseline", gap: 10, flexWrap: "wrap" }}>
                  <h2 style={{ margin: 0 }}>Aporte del buró</h2>
                  <span className="pista">Fuente: {exp.buro.fuente}</span>
                </div>
                <div className="buro-grid">
                  <div>
                    <div className="metric-set" style={{ marginTop: 4 }}>
                      <TarjetaMetrica titulo="Sin buró (interno)" m={exp.buro.metricas.sin_buro} plano />
                      <TarjetaMetrica titulo="Con buró (híbrido)" m={exp.buro.metricas.con_buro} lift={exp.buro.metricas.lift} plano />
                    </div>
                    <div className="buro-cobertura">
                      ⚠️ El <b>{exp.buro.sin_cobertura_pct}%</b> de los afiliados <b>no tiene historial en buró</b>.
                      Para ellos, el modelo sin buró es la única opción — ahí está el diferenciador.
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: 13, fontWeight: 600, marginBottom: 8 }}>Poder predictivo del buró (IV)</div>
                    <div style={{ display: "grid", gap: 8 }}>
                      {exp.buro.iv?.map((x) => (
                        <div key={x.feature} style={{ display: "grid", gridTemplateColumns: "130px 1fr 46px", alignItems: "center", gap: 8 }}>
                          <span style={{ fontSize: 13 }}>{BURO_LABEL[x.feature] ?? x.feature}</span>
                          <div style={{ background: "var(--gris-bg)", borderRadius: 6, height: 14, overflow: "hidden" }}>
                            <div style={{ width: `${Math.min(x.iv / IV_MAX, 1) * 100}%`, height: "100%", background: "var(--azul-oscuro)" }} />
                          </div>
                          <span className="mono" style={{ fontSize: 12, textAlign: "right" }}>{x.iv.toFixed(3)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Campeón vs Retador (sin buró, el de producción) */}
            <div className="seccion-titulo" style={{ marginTop: 26 }}>
              <h2 style={{ margin: 0 }}>Campeón vs. Retador <span style={{ fontSize: 14, fontWeight: 400, color: "var(--grafito-60)" }}>· scorecard de producción (sin buró)</span></h2>
              <span className="pista">
                Evaluado fuera de muestra ({exp.n_test.toLocaleString("es-CO")} casos ·
                tasa base {Math.round(exp.base_rate * 100)}%).
              </span>
            </div>
            <div className="metric-fila">
              <TarjetaMetrica titulo="Experto (campeón)" m={exp.metricas.campeon} />
              <TarjetaMetrica titulo="Aprendido (retador)" m={exp.metricas.retador} lift={exp.metricas.lift} destacado />
            </div>

            <div className="lab-grid">
              {/* Poder predictivo (IV) interno */}
              <div className="card">
                <h3>Poder predictivo por señal (Information Value)</h3>
                <p className="pista" style={{ marginTop: 4 }}>
                  Cuánto aporta cada base interna a predecir el desenlace. &gt;0,3 fuerte ·
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
                    <b style={{ color: exp.equidad.brecha_pp <= 3 ? "#2e7d32" : "#c62828" }}>
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

function TarjetaMetrica({ titulo, m, lift, destacado, plano }: {
  titulo: string; m: MetricaSet; lift?: MetricaSet; destacado?: boolean; plano?: boolean;
}) {
  return (
    <div className={plano ? "" : "card"} style={destacado ? { borderTop: "4px solid var(--azul)" } : undefined}>
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
