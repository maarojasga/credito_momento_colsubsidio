"""Validación de la imputación por holdout dentro del donante.

| Qué                  | Métrica                          | Umbral            |
|----------------------|----------------------------------|-------------------|
| Tenencia (binaria)   | AUC + calibración (Brier)        | AUC > 0.68        |
| Carga financiera     | Cobertura del intervalo de 5     | cobertura >= 80%  |
| Distribución marginal| KS entre Y imputada e Y real     | D < 0.10          |
| Estructura conjunta  | ‖ΔR‖ vs baseline de regresiones  | menor que baseline|

La última fila es la que justifica el método (hot-deck preserva la
correlación conjunta que una regresión por Y independiente destruye).
"""

from __future__ import annotations


def validate_holdout(donor_x, donor_y, weights) -> dict:
    """Corre el holdout y devuelve el tablero de métricas de §3.3."""
    raise NotImplementedError
