// Espejo de las entidades del backend (backend/src/momento/schemas.py).

export type Categoria = "A" | "B" | "C" | "D";

export type BaseLegal = "publica" | "consentida" | "inferida" | "sintetica";

export interface Contribucion {
  key: string;
  value: number | string | boolean;
  puntos: number;
  source_id: string;
}

export interface Ventana {
  subject_id: string;
  producto: string;
  inicio: string; // ISO date
  fin: string; // ISO date
  hazard_pico: number;
  hazard_acumulado_ventana: number;
}

export interface Oferta {
  subject_id: string;
  producto: string;
  monto: number;
  plazo_meses: number;
  ventana: Ventana;
  canal: string;
  hora_envio: string; // ISO time
  puntos_scorecard: number;
  top_senales: Contribucion[]; // exactamente 3
  razon_texto: string;
  manifest_hash: string;
}
