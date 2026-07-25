"""Scorecard aditivo (optbinning + logística -> puntos enteros).

Se elige scorecard sobre GBM + SHAP porque:
  - es aditivo por construcción, no una aproximación posterior;
  - los faltantes son un bin propio con sus propios puntos, sin imputación;
  - la tabla de puntos es el artefacto de auditoría que riesgo ya sabe leer.

Las tres señales principales son los tres aportes de mayor valor absoluto en
puntos: aritmética sobre la decisión real, no una heurística de explicación.
"""

from __future__ import annotations

from momento.schemas import Contribucion


class Scorecard:
    version = "sc-0.1"

    def fit(self, X, y):
        """Binning óptimo con WoE + logística + conversión a puntos enteros."""
        raise NotImplementedError

    def score(self, features: dict) -> tuple[int, list[Contribucion]]:
        """Devuelve (puntos_totales, aportes por señal en puntos)."""
        raise NotImplementedError

    def top_senales(self, aportes: list[Contribucion], n: int = 3) -> list[Contribucion]:
        """Los n aportes de mayor valor absoluto en puntos."""
        return sorted(aportes, key=lambda c: abs(c.puntos), reverse=True)[:n]
