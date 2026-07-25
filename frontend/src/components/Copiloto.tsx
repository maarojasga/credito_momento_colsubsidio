// Copiloto de IA: preguntas del operador ancladas al manifiesto de la oferta.

import { useState } from "react";
import { preguntarCopiloto } from "../api/client";

const SUGERENCIAS = [
  "¿Por qué este producto y no otro?",
  "¿Qué señales pesaron más?",
  "¿Por qué esta ventana de contacto?",
];

export default function Copiloto({ subjectId }: { subjectId: string }) {
  const [pregunta, setPregunta] = useState("");
  const [respuesta, setRespuesta] = useState<string | null>(null);
  const [cargando, setCargando] = useState(false);

  async function preguntar(q: string) {
    if (!q.trim()) return;
    setCargando(true);
    setRespuesta(null);
    try {
      setRespuesta(await preguntarCopiloto(subjectId, q));
    } catch (e) {
      setRespuesta(`No se pudo consultar el copiloto (${String(e)}).`);
    } finally {
      setCargando(false);
    }
  }

  return (
    <div className="card">
      <h3>🤖 Copiloto · pregúntale a la decisión</h3>
      <p style={{ fontSize: 13, color: "var(--grafito-60)", margin: "4px 0 12px" }}>
        Responde solo con el manifiesto de trazabilidad: no inventa datos.
      </p>
      <div style={{ display: "flex", gap: 8, flexWrap: "wrap", marginBottom: 10 }}>
        {SUGERENCIAS.map((s) => (
          <button key={s} className="chip" onClick={() => { setPregunta(s); preguntar(s); }}>
            {s}
          </button>
        ))}
      </div>
      <div style={{ display: "flex", gap: 8 }}>
        <input
          value={pregunta}
          onChange={(e) => setPregunta(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && preguntar(pregunta)}
          placeholder="Escribe tu pregunta…"
          style={{
            flex: 1, padding: "9px 12px", borderRadius: 9,
            border: "1px solid var(--gris-linea)", fontSize: 14,
          }}
        />
        <button className="btn primario" disabled={cargando} onClick={() => preguntar(pregunta)}>
          {cargando ? "…" : "Preguntar"}
        </button>
      </div>
      {respuesta && (
        <div
          style={{
            marginTop: 14, background: "var(--gris-bg)", borderRadius: 9,
            padding: "12px 14px", fontSize: 14, lineHeight: 1.55, whiteSpace: "pre-wrap",
          }}
        >
          {respuesta}
        </div>
      )}
    </div>
  );
}
