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
