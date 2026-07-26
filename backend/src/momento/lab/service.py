"""Orquesta un experimento del laboratorio: campeón vs retador.

Parte el histórico en entrenamiento/prueba, aprende la tabla retadora, puntúa
ambos scorecards sobre la prueba (out-of-sample) y devuelve métricas, lift,
Information Value, comparación de puntos y una foto de equidad por estrato.
"""

from __future__ import annotations

import hashlib
import json

import numpy as np
import pandas as pd

from momento.lab import metrics, store
from momento.lab.dataset import generar_sintetico
from momento.lab.train import entrenar
from momento.lab.woe import MISSING, binizar
from momento.scoring.scorecard import (
    ETIQUETAS, FEATURES, PUNTAJE_BASE, _TABLA,
)


def _mapa_puntos(tabla: dict) -> dict[str, dict]:
    """{feature: {etiqueta_bin: puntos}} incluyendo el bin faltante."""
    out: dict[str, dict] = {}
    for feature, cfg in tabla.items():
        m = {et: pts for _lim, pts, et in cfg["bins"]}
        m[MISSING] = cfg["missing"]
        out[feature] = m
    return out


def puntear(df: pd.DataFrame, tabla: dict) -> np.ndarray:
    """Puntaje total por fila con una tabla dada (vectorizado)."""
    bins = binizar(df)
    total = np.full(len(df), float(PUNTAJE_BASE))
    mapa = _mapa_puntos(tabla)
    for feature in FEATURES:
        total += bins[feature].map(mapa[feature]).to_numpy(dtype=float)
    return total


def _split(df: pd.DataFrame, seed: int, frac_train: float = 0.7):
    rng = np.random.default_rng(seed)
    idx = rng.permutation(len(df))
    corte = int(len(df) * frac_train)
    return df.iloc[idx[:corte]].reset_index(drop=True), df.iloc[idx[corte:]].reset_index(drop=True)


def _comparar_puntos(entrenado: dict) -> list[dict]:
    """Puntos experto vs aprendido, bin por bin, para la tabla lado a lado."""
    ret = entrenado["tabla"]
    filas = []
    for feature in FEATURES:
        exp = {et: pts for _l, pts, et in _TABLA[feature]["bins"]}
        exp[MISSING] = _TABLA[feature]["missing"]
        apr = {et: pts for _l, pts, et in ret[feature]["bins"]}
        apr[MISSING] = ret[feature]["missing"]
        for et in ETIQUETAS[feature] + [MISSING]:
            filas.append({
                "feature": feature, "bin": et,
                "experto": int(exp[et]), "aprendido": int(apr[et]),
            })
    return filas


def _equidad(df: pd.DataFrame, totales: np.ndarray, cutoff: float) -> dict:
    """Tasa de aprobación por género: el modelo no usa sexo, no debe discriminarlo."""
    if "sexo" not in df.columns:
        return {"grupos": [], "brecha_pp": None}
    aprob = totales >= cutoff
    etiquetas = {0: "Hombre", 1: "Mujer"}
    filas = []
    for g in sorted(df["sexo"].dropna().unique()):
        mask = df["sexo"].to_numpy() == g
        if mask.sum() == 0:
            continue
        filas.append({"grupo": etiquetas.get(int(g), str(int(g))), "n": int(mask.sum()),
                      "tasa_aprobacion": round(float(aprob[mask].mean()), 3)})
    tasas = [f["tasa_aprobacion"] for f in filas]
    brecha = round((max(tasas) - min(tasas)) * 100, 2) if len(tasas) >= 2 else 0.0
    return {"grupos": filas, "brecha_pp": brecha}


def correr_experimento(
    df: pd.DataFrame | None = None,
    seed: int = 42,
    buro_fuente: str | None = None,
    buro_archivo: str | None = None,
    integral: bool = False,
) -> dict:
    """Entrena y evalúa. Persiste el retador. Devuelve el reporte completo.

    El scorecard de producción es SIN buró (el diferenciador). Aparte:
      - `buro_fuente` mide cuánto aporta un proveedor de buró;
      - `integral` construye el modelo base integral (demografía + internas + los
        tres burós) como techo/referencia. Nada de esto toca la tabla que se
        promueve a producción.
    """
    from momento.lab import buro as buro_mod

    if df is None:
        df = generar_sintetico(seed=seed)
    df = df.reset_index(drop=True)

    if buro_fuente:
        df = (buro_mod.desde_excel(buro_archivo, df) if buro_archivo
              else buro_mod.simular_buro(df, buro_fuente, seed=seed))
    if integral:
        df = buro_mod.simular_integral(df, seed=seed)

    train_df, test_df = _split(df, seed)
    entrenado = entrenar(train_df)
    tabla_ret = entrenado["tabla"]

    y_test = test_df["resultado"].to_numpy()
    tot_camp = puntear(test_df, _TABLA)
    tot_ret = puntear(test_df, tabla_ret)

    m_camp = metrics.resumen(y_test, tot_camp)
    m_ret = metrics.resumen(y_test, tot_ret)
    lift = {k: round(m_ret[k] - m_camp[k], 4) for k in m_camp}

    cutoff = float(np.median(tot_ret))
    challenger_id = hashlib.sha1(
        json.dumps(entrenado["coeficientes"], sort_keys=True).encode()
    ).hexdigest()[:8]

    reporte = {
        "challenger_id": challenger_id,
        "n_train": int(len(train_df)),
        "n_test": int(len(test_df)),
        "base_rate": entrenado["base_rate"],
        "pseudo_r2": entrenado["pseudo_r2"],
        "coeficientes": entrenado["coeficientes"],
        "iv": [{"feature": f, "iv": entrenado["iv"][f]} for f in FEATURES],
        "metricas": {"campeon": m_camp, "retador": m_ret, "lift": lift},
        "calibracion": {
            "campeon": metrics.calibracion(y_test, tot_camp),
            "retador": metrics.calibracion(y_test, tot_ret),
        },
        "comparacion_puntos": _comparar_puntos(entrenado),
        "equidad": _equidad(test_df, tot_ret, cutoff),
        "buro": (buro_mod.evaluar_aporte(train_df, test_df, buro_fuente)
                 if buro_fuente else {"activo": False}),
        "integral": (buro_mod.evaluar_integral(train_df, test_df)
                     if integral else {"activo": False}),
        "tabla": tabla_ret,
    }
    store.guardar_retador(reporte)
    return reporte
