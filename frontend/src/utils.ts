export const fmtMoney = (n: number) => "$" + n.toLocaleString("es-CO");

export const fmtMes = (iso: string) => {
  const meses = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];
  const d = new Date(iso + "T00:00:00");
  return `${meses[d.getMonth()]} ${d.getFullYear()}`;
};

export const LABEL_SENAL: Record<string, string> = {
  ingreso_smmlv: "Ingreso (SMMLV)",
  antiguedad_empleo_meses: "Antigüedad laboral",
  estrato: "Estrato",
  carga_financiera: "Carga financiera",
  tenencia_tc: "Tenencia de productos",
  edad: "Edad",
  num_hijos: "Composición del hogar",
};

export const labelSenal = (k: string) => LABEL_SENAL[k] ?? k;
