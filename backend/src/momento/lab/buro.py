"""Buró de crédito como potenciador OPCIONAL (no núcleo).

El motor funciona sin buró — ese es el diferenciador: llega a quien no tiene
historial. Este módulo permite, si se quiere, sumar señales de buró y medir
cuánto aportan, y a cuántos afiliados el buró NO cubre (thin-file / sin historial).

Dos formas de traerlo:
  - `conectar` (conector simulado a Datacrédito/TransUnion/Experian): en un demo
    genera el reporte; en producción se reemplaza por el cliente real del buró.
  - `desde_excel`: carga un archivo de buró con las columnas de señales.

Señales de buró y sus cortes (bins), en el mismo formato que el scorecard.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

from momento.lab import metrics
from momento.lab.woe import binizar, matriz_woe, tabla_woe
from momento.scoring.scorecard import CORTES, ETIQUETAS, FEATURES

BUROS = {"datacredito": "Datacrédito", "transunion": "TransUnion", "experian": "Experian"}

BURO_FEATURES = ["score_buro", "moras_ult_12m", "nivel_endeudamiento"]

# cortes (límite superior exclusivo) y etiquetas por señal de buró.
BURO_CORTES = {
    "score_buro": [500, 650, 750, None],
    "moras_ult_12m": [1, 2, 4, None],
    "nivel_endeudamiento": [0.30, 0.50, 0.70, None],
}
BURO_ETIQUETAS = {
    "score_buro": ["<500", "500-649", "650-749", ">=750"],
    "moras_ult_12m": ["0", "1", "2-3", ">=4"],
    "nivel_endeudamiento": ["<30%", "30-50%", "50-70%", ">=70%"],
}
# Cobertura típica: parte de la población no tiene historial en buró (thin-file).
COBERTURA_DEFECTO = 0.72


def simular_buro(df: pd.DataFrame, seed: int = 7, cobertura: float = COBERTURA_DEFECTO) -> pd.DataFrame:
    """Adjunta señales de buró correlacionadas con el desenlace, con vacíos de cobertura.

    El buró es predictivo (por eso aporta), pero no cubre a todos: quien no tiene
    historial queda con las señales de buró en faltante.
    """
    rng = np.random.default_rng(seed)
    n = len(df)
    y = df["resultado"].to_numpy() if "resultado" in df else np.zeros(n)

    # score correlacionado con el buen desenlace + bastante ruido (predictivo,
    # no mágico: un buró real discrimina fuerte pero no perfecto).
    base = 610 + 45 * (y - 0.5) * 2 + rng.normal(0, 105, n)
    score = np.clip(base, 300, 950).round().astype(float)
    moras = np.clip(rng.poisson(np.where(y == 1, 0.5, 1.1), n), 0, 12).astype(float)
    endeud = np.clip(rng.beta(2, 5, n) + np.where(y == 1, -0.03, 0.06), 0.02, 0.98).round(3)

    out = df.copy()
    out["score_buro"] = score
    out["moras_ult_12m"] = moras
    out["nivel_endeudamiento"] = endeud

    # Vacíos de cobertura: sin historial -> señales de buró en NaN.
    sin_historial = rng.random(n) >= cobertura
    out.loc[sin_historial, BURO_FEATURES] = np.nan
    return out


def desde_excel(ruta: str | Path, df: pd.DataFrame) -> pd.DataFrame:
    """Carga señales de buró desde un Excel y las alinea por fila con `df`.

    Espera las columnas de `BURO_FEATURES` (acepta mayúsculas/acentos). Si el
    conteo de filas no coincide, alinea las que pueda y deja el resto en faltante.
    """
    raw = pd.read_excel(ruta)
    cols = {c.lower().strip(): c for c in raw.columns}
    faltan = [f for f in BURO_FEATURES if f not in cols]
    if faltan:
        raise ValueError(f"El archivo de buró debe traer: {', '.join(BURO_FEATURES)}.")
    out = df.copy()
    for f in BURO_FEATURES:
        serie = pd.to_numeric(raw[cols[f]], errors="coerce").reindex(range(len(df)))
        out[f] = serie.to_numpy()
    return out


def evaluar_aporte(train_df: pd.DataFrame, test_df: pd.DataFrame, fuente: str) -> dict:
    """Compara modelo SIN buró vs CON buró (proba logística), fuera de muestra.

    Devuelve métricas de ambos, el lift del buró, el IV de cada señal de buró y la
    cobertura real (qué % de la prueba tenía historial).
    """
    y_tr = train_df["resultado"].to_numpy()
    y_te = test_df["resultado"].to_numpy()

    proba_sin = _proba_logistica(train_df, test_df, FEATURES, CORTES, ETIQUETAS, y_tr)
    m_sin = metrics.resumen(y_te, proba_sin)

    feats_h = FEATURES + BURO_FEATURES
    cortes_h = {**CORTES, **BURO_CORTES}
    etq_h = {**ETIQUETAS, **BURO_ETIQUETAS}
    proba_con = _proba_logistica(train_df, test_df, feats_h, cortes_h, etq_h, y_tr)
    m_con = metrics.resumen(y_te, proba_con)

    # IV de las señales de buró (sobre entrenamiento).
    bins_b = binizar(train_df, BURO_FEATURES, BURO_CORTES, BURO_ETIQUETAS)
    woe_b = tabla_woe(bins_b, y_tr, BURO_FEATURES, BURO_ETIQUETAS)

    cobertura = float(test_df["score_buro"].notna().mean())
    return {
        "activo": True,
        "fuente": BUROS.get(fuente, fuente),
        "cobertura": round(cobertura, 3),
        "sin_cobertura_pct": round((1 - cobertura) * 100, 1),
        "iv": [{"feature": f, "iv": woe_b[f]["iv"]} for f in BURO_FEATURES],
        "metricas": {
            "sin_buro": m_sin,
            "con_buro": m_con,
            "lift": {k: round(m_con[k] - m_sin[k], 4) for k in m_sin},
        },
    }


def _proba_logistica(train_df, test_df, features, cortes, etiquetas, y_tr) -> np.ndarray:
    """Ajusta Logit sobre WoE(entrenamiento) y predice probabilidad en prueba."""
    bins_tr = binizar(train_df, features, cortes, etiquetas)
    woe = tabla_woe(bins_tr, y_tr, features, etiquetas)
    X_tr = matriz_woe(bins_tr, woe, features)
    modelo = sm.Logit(y_tr, sm.add_constant(X_tr, has_constant="add")).fit(disp=0, maxiter=200)

    bins_te = binizar(test_df, features, cortes, etiquetas)
    X_te = matriz_woe(bins_te, woe, features)
    return np.asarray(modelo.predict(sm.add_constant(X_te, has_constant="add")))
