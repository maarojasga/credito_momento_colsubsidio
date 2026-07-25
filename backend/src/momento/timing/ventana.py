"""Extracción de la ventana de contacto (60 días).

    S = cumprod(1 - h)                        # supervivencia
    riesgo_ventana = rolling_sum(h * shift(S), window=2)   # prob. en 60 días
    t0 = argmax(riesgo_ventana)
    ventana = (fecha_base + t0, fecha_base + t0 + 2 meses)

La ventana es de dos meses, no de un día: un punto exacto es falsa precisión
y frágil en vivo.

Métrica de pitch (§4.5): cobertura de eventos contra volumen de contacto —
"capturamos ~60% de los eventos usando ~20% de los contactos".
"""

from __future__ import annotations

from datetime import date

import numpy as np

from momento.schemas import Ventana

HORIZONTE_MESES = 18
ANCHO_VENTANA = 2


def extraer_ventana(h: np.ndarray, fecha_base: date, subject_id: str, producto: str) -> Ventana:
    """Devuelve la ventana de 60 días con mayor riesgo acumulado."""
    raise NotImplementedError


def cobertura_vs_contacto(hazards, eventos_reales):
    """Curva cobertura de eventos vs volumen de contacto (métrica de pitch)."""
    raise NotImplementedError
