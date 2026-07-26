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

// --- Laboratorio de Crédito ---

export const getLabEstado = () =>
  get<{ version_produccion: string; hay_promovido: boolean; challenger_id: string | null }>(
    "/lab/estado"
  );

export async function entrenarModelo(file?: File): Promise<ExperimentoLab> {
  const opts: RequestInit = { method: "POST" };
  if (file) {
    const form = new FormData();
    form.append("file", file);
    opts.body = form;
  }
  const res = await fetch(`${BASE}/lab/entrenar`, opts);
  if (!res.ok) {
    const d = await res.json().catch(() => ({}));
    throw new Error((d as { detail?: string }).detail ?? `${res.status} ${res.statusText}`);
  }
  return res.json() as Promise<ExperimentoLab>;
}

export async function promoverModelo(challengerId: string): Promise<void> {
  const res = await fetch(`${BASE}/lab/promover`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ challenger_id: challengerId }),
  });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
}

export async function revertirModelo(): Promise<void> {
  const res = await fetch(`${BASE}/lab/revertir`, { method: "POST" });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
}

export interface MetricaSet {
  auc: number;
  gini: number;
  ks: number;
}
export interface ExperimentoLab {
  challenger_id: string;
  n_train: number;
  n_test: number;
  base_rate: number;
  pseudo_r2: number;
  coeficientes: Record<string, number>;
  iv: { feature: string; iv: number }[];
  metricas: { campeon: MetricaSet; retador: MetricaSet; lift: MetricaSet };
  comparacion_puntos: { feature: string; bin: string; experto: number; aprendido: number }[];
  equidad: { grupos: { grupo: string; n: number; tasa_aprobacion: number }[]; brecha_pp: number | null };
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
