// Cliente de la API FastAPI del backend.

import type { Oferta } from "../types";

const BASE = import.meta.env.VITE_API_URL ?? "/api";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${BASE}${path}`);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json() as Promise<T>;
}

export function getOferta(subjectId: string): Promise<Oferta> {
  return get<Oferta>(`/subjects/${subjectId}/oferta`);
}

export function getManifestUrl(subjectId: string): string {
  return `${BASE}/subjects/${subjectId}/manifest`;
}
