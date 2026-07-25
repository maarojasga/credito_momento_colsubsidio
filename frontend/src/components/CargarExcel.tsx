// Control de subida manual del Excel de afiliados.

import { useRef, useState } from "react";
import { cargarExcel, plantillaUrl } from "../api/client";

export default function CargarExcel({
  onCargado,
  compacto = false,
}: {
  onCargado: () => void;
  compacto?: boolean;
}) {
  const input = useRef<HTMLInputElement>(null);
  const [estado, setEstado] = useState<"idle" | "cargando" | "ok" | "error">("idle");
  const [mensaje, setMensaje] = useState("");

  async function subir(file: File) {
    setEstado("cargando");
    setMensaje(`Procesando ${file.name}…`);
    try {
      const r = await cargarExcel(file);
      setEstado("ok");
      setMensaje(`Listo: ${r.afiliados} afiliados · ${r.ofertas} ofertas · ${r.no_elegibles} no elegibles`);
      onCargado();
    } catch (e) {
      setEstado("error");
      setMensaje(`Error: ${String(e instanceof Error ? e.message : e)}`);
    }
  }

  return (
    <div className={`card ${compacto ? "" : "card-carga"}`}>
      {!compacto && <h3>Cargar afiliados</h3>}
      {!compacto && (
        <p style={{ fontSize: 13, color: "var(--grafito-60)", margin: "6px 0 14px" }}>
          Sube un Excel con tus afiliados. Solo se guarda el hash del documento; nombre, correo y
          documento nunca se almacenan.
        </p>
      )}
      <input
        ref={input}
        type="file"
        accept=".xlsx,.xlsm"
        style={{ display: "none" }}
        onChange={(e) => {
          const f = e.target.files?.[0];
          if (f) subir(f);
          e.target.value = "";
        }}
      />
      <div style={{ display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center" }}>
        <button
          className="btn primario"
          disabled={estado === "cargando"}
          onClick={() => input.current?.click()}
        >
          {estado === "cargando" ? "Procesando…" : "⬆ Subir Excel"}
        </button>
        <a className="btn amarillo" href={plantillaUrl()} download>
          ⬇ Descargar plantilla
        </a>
      </div>
      {mensaje && (
        <div
          style={{
            marginTop: 12,
            fontSize: 13,
            fontWeight: 600,
            color:
              estado === "error"
                ? "#c0392b"
                : estado === "ok"
                ? "var(--ok)"
                : "var(--grafito-60)",
          }}
        >
          {mensaje}
        </div>
      )}
    </div>
  );
}
