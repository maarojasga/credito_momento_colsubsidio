"""Ranking de productos elegibles por puntaje del scorecard.

El scoring SOLO ordena dentro del conjunto que las reglas duras declararon
elegible. Nunca aprueba un producto no elegible.
"""

from __future__ import annotations

from momento.rules.engine import ResultadoElegibilidad


def rank_productos(elegibles: list[ResultadoElegibilidad], features: dict):
    """Ordena los productos elegibles por puntaje y devuelve el mejor con detalle."""
    raise NotImplementedError
