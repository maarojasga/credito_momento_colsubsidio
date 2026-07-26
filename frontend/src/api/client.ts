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

export interface OpcionesEntrenar {
  file?: File;
  buroFuente?: string;
  buroFile?: File;
  integral?: boolean;
}

export async function entrenarModelo(opts: OpcionesEntrenar = {}): Promise<ExperimentoLab> {
  // Siempre enviamos un form (aunque sea con un campo), así el POST lleva
  // Content-Type y ningún proxy lo rechaza por venir sin cuerpo.
  const form = new FormData();
  form.append("_", "1");
  if (opts.file) form.append("file", opts.file);
  if (opts.buroFuente) form.append("buro_fuente", opts.buroFuente);
  if (opts.buroFile) form.append("buro_file", opts.buroFile);
  if (opts.integral) form.append("integral", "true");

  const ctrl = new AbortController();
  const timeout = setTimeout(() => ctrl.abort(), 90_000);
  try {
    const res = await fetch(`${BASE}/lab/entrenar`, { method: "POST", body: form, signal: ctrl.signal });
    if (!res.ok) {
      const d = await res.json().catch(() => ({}));
      throw new Error((d as { detail?: string }).detail ?? `${res.status} ${res.statusText}`);
    }
    return (await res.json()) as ExperimentoLab;
  } catch (e) {
    if (e instanceof DOMException && e.name === "AbortError") {
      throw new Error("La API tardó demasiado en responder. Reintenta en unos segundos.");
    }
    throw e;
  } finally {
    clearTimeout(timeout);
  }
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
  buro: BuroReporte;
  integral: IntegralReporte;
}
export interface BuroReporte {
  activo: boolean;
  fuente?: string;
  cobertura?: number;
  sin_cobertura_pct?: number;
  iv?: { feature: string; iv: number }[];
  metricas?: { sin_buro: MetricaSet; con_buro: MetricaSet; lift: MetricaSet };
}
export interface IntegralReporte {
  activo: boolean;
  n_features?: number;
  proveedores?: string[];
  cobertura_algun?: number;
  sin_ningun_pct?: number;
  cobertura_por_proveedor?: Record<string, number>;
  metricas?: { sin_buro: MetricaSet; integral: MetricaSet; lift: MetricaSet };
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
