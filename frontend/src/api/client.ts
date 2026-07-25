// Cliente de la API FastAPI del backend.

import type { ListaOfertas, Manifiesto, Metrics, Oferta, Stats } from "../types";

const BASE = import.meta.env.VITE_API_URL ?? "/api";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json() as Promise<T>;
}

export const getStats = () => get<Stats>("/stats");
export const getMetrics = () => get<Metrics>("/metrics");

export const getOfertas = (limit = 25, offset = 0, producto?: string) =>
  get<ListaOfertas>(
    `/ofertas?limit=${limit}&offset=${offset}` + (producto ? `&producto=${producto}` : "")
  );

export const getOferta = (subjectId: string) =>
  get<Oferta>(`/subjects/${subjectId}/oferta`);

export const getManifest = (subjectId: string) =>
  get<Manifiesto>(`/subjects/${subjectId}/manifest`);

export const getManifestUrl = (subjectId: string) =>
  `${BASE}/subjects/${subjectId}/manifest`;

export const plantillaUrl = () => `${BASE}/plantilla`;

export interface ResultadoCarga {
  ok: boolean;
  afiliados: number;
  ofertas: number;
  no_elegibles: number;
}

export async function cargarExcel(file: File): Promise<ResultadoCarga> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${BASE}/cargar-excel`, { method: "POST", body: form });
  if (!res.ok) {
    const detalle = await res.json().catch(() => ({}));
    throw new Error((detalle as { detail?: string }).detail ?? `${res.status} ${res.statusText}`);
  }
  return res.json() as Promise<ResultadoCarga>;
}

// --- Copiloto de IA (Gemini) ---

export const getCopilotoEstado = () =>
  get<{ disponible: boolean; modelo: string }>("/copiloto/estado");

export const getNarrativaIA = (subjectId: string) =>
  get<{ texto: string; origen: string }>(`/subjects/${subjectId}/narrativa-ia`);

export const getResumenLote = () => get<{ resumen: string }>("/copiloto/resumen");

export async function preguntarCopiloto(subjectId: string, pregunta: string): Promise<string> {
  const res = await fetch(`${BASE}/copiloto/explicar`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ subject_id: subjectId, pregunta }),
  });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return (await res.json()).respuesta as string;
}
