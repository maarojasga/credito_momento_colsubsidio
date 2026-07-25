// Descarga del manifiesto de trazabilidad (lo que convierte el demo en
// candidato de producción).

import { getManifestUrl } from "../api/client";

export default function ManifestDownload({ subjectId }: { subjectId: string }) {
  return (
    <a href={getManifestUrl(subjectId)} download={`manifest_${subjectId}.json`}>
      Descargar manifiesto de trazabilidad
    </a>
  );
}
