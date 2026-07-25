"""Construcción del payload de decisión que recibe el LLM.

El LLM recibe SOLO: producto, monto, plazo, y las tres señales con su valor y
sus puntos. No recibe el perfil completo, porque lo que no tiene no lo puede
filtrar ni inventar.
"""

from __future__ import annotations

from momento.schemas import Contribucion


def build_payload(
    producto: str,
    monto: int,
    plazo_meses: int,
    top_senales: list[Contribucion],
) -> dict:
    return {
        "producto": producto,
        "monto": monto,
        "plazo_meses": plazo_meses,
        "senales": [
            {"key": c.key, "value": c.value, "puntos": c.puntos, "source_id": c.source_id}
            for c in top_senales
        ],
    }
