// Amortización de cuota fija (misma base que los documentos de contrato/extracto):
// tasa 1,80% M.V., seguro de vida deudores 0,09% mensual sobre el monto.

export const TASA_MV = 0.018;
export const SEGURO_MENSUAL = 0.0009;

export const money = (n: number) => "$" + Math.round(n).toLocaleString("es-CO");

const MES3 = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];
const MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
  "septiembre", "octubre", "noviembre", "diciembre"];

export const fechaCorta = (d: Date) =>
  String(d.getDate()).padStart(2, "0") + " " + MES3[d.getMonth()] + " " + d.getFullYear();
export const fechaLarga = (d: Date) =>
  d.getDate() + " de " + MESES[d.getMonth()] + " de " + d.getFullYear();

export interface CuotaPlan {
  n: number; venc: Date; cuota: number; interes: number; capital: number; saldo: number;
}

export function amortizar(monto: number, plazo: number, desde = new Date()): CuotaPlan[] {
  const i = TASA_MV;
  const cuota = (monto * i) / (1 - Math.pow(1 + i, -plazo));
  const plan: CuotaPlan[] = [];
  let saldo = monto;
  for (let k = 1; k <= plazo; k++) {
    const interes = saldo * i;
    const capital = cuota - interes;
    saldo = Math.max(0, saldo - capital);
    plan.push({ n: k, venc: new Date(desde.getFullYear(), desde.getMonth() + k, 5), cuota, interes, capital, saldo });
  }
  return plan;
}

export const cuotaMensual = (monto: number, plazo: number) =>
  (monto * TASA_MV) / (1 - Math.pow(1 + TASA_MV, -plazo));

export const seguroMensual = (monto: number) => monto * SEGURO_MENSUAL;
