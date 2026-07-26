// Copiloto de IA como botón flotante: preguntas del operador ancladas al
// manifiesto de trazabilidad de la oferta (no inventa datos).

import { useState } from "react";
import { preguntarCopiloto } from "../api/client";

const SUGERENCIAS = [
  "¿Por qué este producto y no otro?",
  "¿Qué señales pesaron más?",
  "¿Por qué esta ventana de contacto?",
];

export default function Copiloto({ subjectId }: { subjectId: string }) {
  const [open, setOpen] = useState(false);
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
    <div className="copiloto-fab">
      {open && (
        <div className="copiloto-panel" role="dialog" aria-label="Copiloto de IA">
          <div className="copiloto-head">
            <div>
              <div className="copiloto-titulo">🤖 Copiloto</div>
              <div className="copiloto-sub">Responde solo con el manifiesto: no inventa datos.</div>
            </div>
            <button className="copiloto-cerrar" onClick={() => setOpen(false)} aria-label="Cerrar">
              ✕
            </button>
          </div>

          <div className="copiloto-chips">
            {SUGERENCIAS.map((s) => (
              <button key={s} className="chip" onClick={() => { setPregunta(s); preguntar(s); }}>
                {s}
              </button>
            ))}
          </div>

          {respuesta && (
            <div className="copiloto-respuesta">{respuesta}</div>
          )}
          {cargando && <div className="copiloto-respuesta">Consultando…</div>}

          <div className="copiloto-input">
            <input
              value={pregunta}
              onChange={(e) => setPregunta(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && preguntar(pregunta)}
              placeholder="Escribe tu pregunta…"
            />
            <button className="btn primario" disabled={cargando} onClick={() => preguntar(pregunta)}>
              {cargando ? "…" : "Enviar"}
            </button>
          </div>
        </div>
      )}

      <button
        className="copiloto-toggle"
        onClick={() => setOpen((o) => !o)}
        aria-label={open ? "Cerrar copiloto" : "Abrir copiloto"}
      >
        {open ? "✕" : "🤖"}
      </button>
    </div>
  );
}
