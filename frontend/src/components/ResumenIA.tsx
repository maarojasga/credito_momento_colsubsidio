// Resumen ejecutivo del lote generado con IA (bajo demanda, para no gastar tokens
// en cada carga).

import { useState } from "react";
import { getResumenLote } from "../api/client";

export default function ResumenIA() {
  const [resumen, setResumen] = useState<string | null>(null);
  const [cargando, setCargando] = useState(false);

  async function generar() {
    setCargando(true);
    try {
      setResumen((await getResumenLote()).resumen);
    } catch (e) {
      setResumen(`No se pudo generar el resumen (${String(e)}).`);
    } finally {
      setCargando(false);
    }
  }

  return (
    <div className="card" style={{ borderLeft: "5px solid var(--azul)" }}>
      <div style={{ display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap" }}>
        <h3 style={{ margin: 0 }}>🤖 Resumen ejecutivo del lote</h3>
        <span className="spacer" style={{ flex: 1 }} />
        <button className="btn primario" disabled={cargando} onClick={generar}>
          {cargando ? "Generando…" : resumen ? "Regenerar" : "Generar con IA"}
        </button>
      </div>
      {resumen && (
        <p style={{ marginTop: 12, fontSize: 15, lineHeight: 1.6, whiteSpace: "pre-wrap" }}>
          {resumen}
        </p>
      )}
    </div>
  );
}
