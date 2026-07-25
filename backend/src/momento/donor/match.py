"""Imputación desde encuestas (Motor 1.5).

Método objetivo (§3.2): predictive mean matching con hot-deck ponderado sobre
IEFIC. Copiar el vector Y COMPLETO de un donante real preserva la estructura
conjunta entre las Y, y los pesos de expansión evitan el sesgo hacia estratos
sobremuestreados.

    fit_predictor / hot_deck_impute  -> requieren el microdato IEFIC real.

Como el demo no dispone del microdato IEFIC, `imputar_desde_encuesta` entrega
una imputación SINTÉTICA con la misma forma de contrato: base legal `inferida`,
confianza reducida y confianza aún menor en celdas de bajo soporte. Nunca entra
a elegibilidad, solo al ranking. Sustituir por el hot-deck real es un cambio
local cuando el microdato esté disponible.
"""

from __future__ import annotations

import hashlib

K_DONORS = 5

# Media de carga financiera (servicio de deuda / ingreso) por categoría.
_CARGA_BASE = {"A": 0.34, "B": 0.30, "C": 0.27, "D": 0.24}
# Propensión de tenencia de tarjeta de crédito por categoría.
_TENENCIA_TC_BASE = {"A": 0.35, "B": 0.55, "C": 0.72, "D": 0.85}


def _ruido_estable(subject_id: str, salt: str) -> float:
    """Pseudo-aleatorio determinista en [0, 1) por sujeto (reproducible)."""
    h = hashlib.sha256(f"{subject_id}:{salt}".encode()).hexdigest()
    return int(h[:8], 16) / 0xFFFFFFFF


def imputar_desde_encuesta(sub: dict) -> list[tuple[str, float, float]]:
    """Devuelve [(key, value, confidence)] de las señales imputadas.

    La confianza baja si la celda (categoría) tiene poco soporte esperado (§3.4).
    """
    cat = sub.get("categoria", "A")
    sid = sub["subject_id"]

    carga = _CARGA_BASE.get(cat, 0.30) + (_ruido_estable(sid, "carga") - 0.5) * 0.10
    carga = round(max(0.0, min(carga, 0.9)), 3)

    tenencia = _TENENCIA_TC_BASE.get(cat, 0.5) + (_ruido_estable(sid, "tc") - 0.5) * 0.15
    tenencia = round(max(0.0, min(tenencia, 1.0)), 3)

    # Categoría D tiene menor soporte muestral en IEFIC -> confianza reducida.
    conf = 0.45 if cat == "D" else 0.6

    return [
        ("encuesta.carga_financiera", carga, conf),
        ("encuesta.tenencia_tc", tenencia, conf),
    ]
