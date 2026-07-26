"""Métricas de discriminación y calibración (lenguaje de área de riesgo).

AUC (Mann-Whitney), Gini = 2·AUC - 1, KS = máx separación de acumuladas.
Solo requieren un puntaje que ordene, así que sirven igual para campeón y retador.
"""

from __future__ import annotations

import numpy as np


def auc(y: np.ndarray, score: np.ndarray) -> float:
    """AUC vía el estadístico de Mann-Whitney (con manejo de empates)."""
    y = np.asarray(y)
    score = np.asarray(score, dtype=float)
    pos, neg = score[y == 1], score[y == 0]
    if len(pos) == 0 or len(neg) == 0:
        return 0.5
    ranks = _rankdata(np.concatenate([pos, neg]))
    r_pos = ranks[: len(pos)].sum()
    return float((r_pos - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg)))


def ks(y: np.ndarray, score: np.ndarray) -> float:
    """Máxima distancia entre las acumuladas de buenos y malos."""
    y = np.asarray(y)
    score = np.asarray(score, dtype=float)
    orden = np.argsort(-score)
    y = y[orden]
    buenos = np.cumsum(y == 1) / max((y == 1).sum(), 1)
    malos = np.cumsum(y == 0) / max((y == 0).sum(), 1)
    return float(np.abs(buenos - malos).max())


def calibracion(y: np.ndarray, score: np.ndarray, grupos: int = 10) -> list[dict]:
    """Por decil de puntaje: tasa de buenos observada (curva de ganancia)."""
    y = np.asarray(y)
    score = np.asarray(score, dtype=float)
    orden = np.argsort(score)
    y = y[orden]
    trozos = np.array_split(np.arange(len(y)), grupos)
    filas = []
    for i, idx in enumerate(trozos, 1):
        if len(idx) == 0:
            continue
        filas.append({"decil": i, "n": int(len(idx)),
                      "tasa_buenos": round(float(y[idx].mean()), 3)})
    return filas


def resumen(y: np.ndarray, score: np.ndarray) -> dict:
    a = auc(y, score)
    return {"auc": round(a, 4), "gini": round(2 * a - 1, 4), "ks": round(ks(y, score), 4)}


def _rankdata(x: np.ndarray) -> np.ndarray:
    """Rangos promedio (empates), equivalente a scipy.stats.rankdata."""
    orden = np.argsort(x, kind="mergesort")
    rangos = np.empty(len(x), dtype=float)
    rangos[orden] = np.arange(1, len(x) + 1)
    x_ord = x[orden]
    i = 0
    while i < len(x):
        j = i
        while j + 1 < len(x) and x_ord[j + 1] == x_ord[i]:
            j += 1
        if j > i:
            rangos[orden[i:j + 1]] = (i + 1 + j + 1) / 2
        i = j + 1
    return rangos
