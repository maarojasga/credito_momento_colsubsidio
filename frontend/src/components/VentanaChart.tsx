// Hazard mensual + ventana de 60 días resaltada.

import type { Ventana } from "../types";

export default function VentanaChart({ ventana }: { ventana: Ventana }) {
  return (
    <figure>
      <figcaption>
        Ventana: {ventana.inicio} → {ventana.fin}
      </figcaption>
      {/* Por implementar: curva de hazard con la ventana resaltada. */}
    </figure>
  );
}
