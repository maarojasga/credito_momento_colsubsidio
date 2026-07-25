"""Manifiesto de trazabilidad por oferta.

Cada oferta emite un manifiesto JSON con hash de contenido: señales (con
fuente, versión, confianza, base legal, observed_at), reglas evaluadas,
scorecard (puntos y aportes), hazard/ventana, narrativa (prompt_hash +
validador) y entrega. Exportable como archivo descargable desde la UI.

Esto es lo que convierte el proyecto de demo a candidato de producción.
"""

from __future__ import annotations

import hashlib
import json


def build_manifest(
    subject_id: str,
    as_of: str,
    senales: list[dict],
    reglas_evaluadas: list[dict],
    scorecard: dict,
    hazard: dict,
    narrativa: dict,
    entrega: dict,
) -> dict:
    payload = {
        "subject_id": subject_id,
        "as_of": as_of,
        "senales": senales,
        "reglas_evaluadas": reglas_evaluadas,
        "scorecard": scorecard,
        "hazard": hazard,
        "narrativa": narrativa,
        "entrega": entrega,
    }
    manifest_hash = "sha256:" + hashlib.sha256(
        json.dumps(payload, sort_keys=True, ensure_ascii=False).encode()
    ).hexdigest()
    return {"manifest_hash": manifest_hash, **payload}
