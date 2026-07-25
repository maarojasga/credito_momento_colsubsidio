// Espejo de las respuestas de la API (backend/src/momento/api.py).

export interface SenalTop {
  key: string;
  value: number | string | boolean;
  puntos: number;
  source_id: string;
}

export interface Oferta {
  subject_id: string;
  producto: string;
  nombre_producto: string;
  monto: number;
  plazo_meses: number;
  canal: string;
  hora_envio: string;
  puntos_scorecard: number;
  ventana_inicio: string;
  ventana_fin: string;
  hazard_pico: number;
  razon_texto: string;
  narrativa_origen: string;
  top_senales: SenalTop[];
  manifest_hash: string;
}

export interface Stats {
  total_ofertas: number;
  productos: Record<string, number>;
  canales: Record<string, number>;
  monto_promedio: number;
}

export interface PuntoCobertura {
  contacto: number;
  cobertura: number;
}

export interface Metrics {
  cobertura_contacto: PuntoCobertura[];
  hazard_coeficientes: {
    modelo: string;
    n_obs: number;
    coeficientes: Record<string, number>;
    odds_ratio: Record<string, number>;
  };
}

export interface ListaOfertas {
  total: number;
  items: Oferta[];
}

export type BaseLegal = "publica" | "consentida" | "inferida" | "sintetica";

export interface SenalManifiesto {
  key: string;
  value: number | string | boolean;
  puntos: number;
  source_id: string;
  provider_version: string | null;
  confidence: number | null;
  base_legal: BaseLegal | null;
  observed_at: string | null;
}

export interface Manifiesto {
  manifest_hash: string;
  subject_id: string;
  as_of: string;
  senales: SenalManifiesto[];
  reglas_evaluadas: { regla: string }[];
  scorecard: { version: string; puntos_totales: number; aportes: { key: string; puntos: number }[] };
  hazard: { modelo: string; ventana: [string, string]; hazard_pico: number };
  narrativa: { origen: string; validador: string };
  entrega: { canal: string; hora: string; estado: string };
}
