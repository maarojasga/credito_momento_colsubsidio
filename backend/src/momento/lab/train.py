"""Entrena la tabla de puntos APRENDIDA (retador).

WoE -> regresión logística (statsmodels) -> puntos escalados (PDO). El resultado
tiene la MISMA estructura que la tabla experta (mismos cortes, distintos puntos),
así que el pipeline la puntúa igual y es comparable señal por señal.

Escala estándar de scorecard:
    factor = PDO / ln(2);  offset = base - factor * ln(odds_base)
    puntos_bin(f) = factor * beta_f * woe_bin(f) + (offset + factor*intercepto)/k
Los puntos se recentran para que el puntaje total promedio coincida con
PUNTAJE_BASE (500), de modo que campeón y retador vivan en la misma escala.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm

from momento.scoring.scorecard import CORTES, ETIQUETAS, FEATURES, PUNTAJE_BASE
from momento.lab.woe import MISSING, binizar, matriz_woe, tabla_woe

PDO = 40  # puntos para duplicar el odds


def entrenar(df: pd.DataFrame) -> dict:
    """Devuelve {tabla, coeficientes, iv, woe, base_rate, pseudo_r2}."""
    y = df["resultado"].to_numpy()
    bins = binizar(df)
    woe = tabla_woe(bins, y)
    X = matriz_woe(bins, woe)

    modelo = sm.Logit(y, sm.add_constant(X, has_constant="add")).fit(disp=0, maxiter=200)
    intercepto = float(modelo.params["const"])
    betas = {f: float(modelo.params[f]) for f in FEATURES}

    factor = PDO / np.log(2)
    reparto = (intercepto * factor) / len(FEATURES)

    # Puntos crudos por bin, luego se recentran al puntaje base.
    tabla_pts: dict[str, dict] = {}
    for feature in FEATURES:
        mapa_woe = {fila["bin"]: fila["woe"] for fila in woe[feature]["bins"]}
        pts_por_et = {
            et: factor * betas[feature] * mapa_woe.get(et, 0.0) + reparto
            for et in ETIQUETAS[feature] + [MISSING]
        }
        tabla_pts[feature] = pts_por_et

    # Recentrado: el total medio del retador debe igualar PUNTAJE_BASE.
    total_medio = PUNTAJE_BASE + _total_medio(df, tabla_pts)
    ajuste = (PUNTAJE_BASE - total_medio) / len(FEATURES)
    for feature in FEATURES:
        for et in tabla_pts[feature]:
            tabla_pts[feature][et] = int(round(tabla_pts[feature][et] + ajuste))

    tabla = _a_estructura(tabla_pts)
    return {
        "tabla": tabla,
        "coeficientes": {"intercepto": round(intercepto, 4),
                         **{f: round(b, 4) for f, b in betas.items()}},
        "iv": {f: woe[f]["iv"] for f in FEATURES},
        "woe": woe,
        "base_rate": round(float(y.mean()), 4),
        "pseudo_r2": round(float(modelo.prsquared), 4),
    }


def _total_medio(df: pd.DataFrame, tabla_pts: dict) -> float:
    bins = binizar(df)
    suma = np.zeros(len(df))
    for feature in FEATURES:
        suma += bins[feature].map(tabla_pts[feature]).to_numpy()
    return float(suma.mean())


def _a_estructura(tabla_pts: dict) -> dict:
    """De {feature: {etiqueta: puntos}} a la estructura del scorecard."""
    tabla: dict[str, dict] = {}
    for feature in FEATURES:
        bins = [
            (CORTES[feature][i], tabla_pts[feature][ETIQUETAS[feature][i]], ETIQUETAS[feature][i])
            for i in range(len(ETIQUETAS[feature]))
        ]
        tabla[feature] = {"bins": bins, "missing": tabla_pts[feature][MISSING]}
    return tabla
