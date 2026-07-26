"""Weight of Evidence (WoE) e Information Value (IV) por señal.

Usa los MISMOS cortes que el scorecard campeón, así que cada bin del retador es
comparable con el del experto. WoE = ln(%buenos / %malos) del bin; IV = suma de
(%buenos - %malos) * WoE. El IV es la vara clásica de poder predictivo:
  < 0.02 inútil · 0.02-0.1 débil · 0.1-0.3 medio · 0.3-0.5 fuerte · > 0.5 sospechoso.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from momento.scoring.scorecard import CORTES, ETIQUETAS, FEATURES

MISSING = "faltante"


def bin_de(feature: str, valor) -> str:
    """Etiqueta de bin para un valor (o 'faltante')."""
    if valor is None or (isinstance(valor, float) and np.isnan(valor)):
        return MISSING
    for limite, etiqueta in zip(CORTES[feature], ETIQUETAS[feature]):
        if limite is None or valor < limite:
            return etiqueta
    return ETIQUETAS[feature][-1]


def binizar(df: pd.DataFrame) -> pd.DataFrame:
    """DataFrame de etiquetas de bin por feature."""
    return pd.DataFrame({f: df[f].map(lambda v: bin_de(f, v)) for f in FEATURES})


def tabla_woe(bins: pd.DataFrame, y: np.ndarray) -> dict:
    """Por feature: bins con conteos, WoE e IV. Ajuste de Laplace (0.5) por celda."""
    y = np.asarray(y)
    tot_buenos = max((y == 1).sum(), 1)
    tot_malos = max((y == 0).sum(), 1)
    resultado: dict[str, dict] = {}

    for feature in FEATURES:
        orden = ETIQUETAS[feature] + [MISSING]
        filas, iv = [], 0.0
        for et in orden:
            mask = bins[feature].values == et
            n = int(mask.sum())
            if n == 0:
                continue
            buenos = int(y[mask].sum())
            malos = n - buenos
            pb = (buenos + 0.5) / tot_buenos
            pm = (malos + 0.5) / tot_malos
            woe = float(np.log(pb / pm))
            iv += (pb - pm) * woe
            filas.append({
                "bin": et, "n": n, "buenos": buenos, "malos": malos,
                "tasa_buenos": round(buenos / n, 3), "woe": round(woe, 4),
            })
        resultado[feature] = {"bins": filas, "iv": round(iv, 4)}
    return resultado


def matriz_woe(bins: pd.DataFrame, woe: dict) -> pd.DataFrame:
    """Reemplaza cada etiqueta de bin por su WoE (matriz para la regresión)."""
    out = {}
    for feature in FEATURES:
        mapa = {fila["bin"]: fila["woe"] for fila in woe[feature]["bins"]}
        out[feature] = bins[feature].map(mapa).fillna(0.0)
    return pd.DataFrame(out)
