// Descarga del manifiesto de trazabilidad (lo que convierte el demo en
// candidato de producción).

import { getManifestUrl } from "../api/client";

export default function ManifestDownload({ subjectId }: { subjectId: string }) {
  return (
    <a
      className="btn primario"
      href={getManifestUrl(subjectId)}
      download={`manifiesto_${subjectId}.json`}
      style={{ display: "inline-block" }}
    >
      Descargar manifiesto (JSON)
    </a>
  );
}
