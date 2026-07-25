"""Predictive mean matching con hot-deck ponderado.

1. Ajustar g(X) -> Y_principal en el donante con pesos de expansión.
2. Predecir ŷ = g(X) en donante y receptor.
3. Estratificar exacto por (localidad × categoría).
4. Dentro del estrato, tomar los k=5 donantes más cercanos en |ŷr − ŷd|.
5. Sortear uno de los 5 con probabilidad proporcional al peso de expansión,
   y copiar su vector Y COMPLETO (preserva la estructura conjunta).
6. La dispersión entre los 5 donantes es el intervalo de incertidumbre.

Los pesos de expansión NO son opcionales: el sorteo del donante debe ser
proporcional al factor de expansión, o el resultado queda sesgado hacia los
estratos sobremuestreados.
"""

from __future__ import annotations

K_DONORS = 5


def fit_predictor(donor_x, donor_y, expansion_weights):
    """Ajusta g(X) -> Y_principal ponderado por expansión."""
    raise NotImplementedError


def hot_deck_impute(receptor_x, donor_x, donor_y, expansion_weights, k: int = K_DONORS):
    """Imputa el vector Y completo por hot-deck ponderado. Devuelve Y + intervalo."""
    raise NotImplementedError
