// Vista afiliado.
// La oferta (producto, monto, plazo), la ventana, el canal y la narrativa
// validada.

import { useParams } from "react-router-dom";

export default function AfiliadoView() {
  const { subjectId } = useParams<{ subjectId: string }>();
  return (
    <main>
      <h1>MOMENTO · Afiliado</h1>
      <p>Oferta para el sujeto {subjectId}. (Por implementar.)</p>
    </main>
  );
}
