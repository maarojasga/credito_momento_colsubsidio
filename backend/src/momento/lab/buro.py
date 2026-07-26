"""Buró de crédito: tres proveedores con datos propios + modelo base integral.

El scorecard de PRODUCCIÓN es sin buró (el diferenciador: llega a quien no tiene
historial). Aparte, el laboratorio permite:
  - conectar un proveedor (Datacrédito / TransUnion / Experian), cada uno con su
    propio perfil sintético (rango de score, cobertura y fuerza distintos), y medir
    cuánto aporta ese buró;
  - construir un MODELO BASE INTEGRAL que considera todo —demografía + señales
    internas + los tres burós— como techo/referencia de lo que se podría lograr
    con toda la información disponible.

Las señales de buró usan el mismo formato de bins (cortes) que el scorecard.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import statsmodels.api as sm

from momento.lab import metrics
from momento.lab.woe import binizar, matriz_woe, tabla_woe
from momento.scoring.scorecard import CORTES, ETIQUETAS, FEATURES

# Perfil sintético por proveedor: rango real-ish de score, desplazamiento por
# desenlace (fuerza), ruido y cobertura (qué fracción de la población cubre).
PROVEEDORES = {
    "datacredito": {"nombre": "Datacrédito", "rango": (150, 950), "media": 620,
                    "shift": 48, "ruido": 100, "cobertura": 0.72},
    "transunion": {"nombre": "TransUnion", "rango": (300, 850), "media": 590,
                   "shift": 42, "ruido": 108, "cobertura": 0.66},
    "experian": {"nombre": "Experian", "rango": (300, 850), "media": 585,
                 "shift": 38, "ruido": 114, "cobertura": 0.60},
}
BUROS = {k: v["nombre"] for k, v in PROVEEDORES.items()}

BURO_SIGNALS = ["score_buro", "moras_ult_12m", "nivel_endeudamiento"]
BURO_FEATURES = BURO_SIGNALS  # nombres base (flujo de un solo proveedor)

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


def _senales_proveedor(df: pd.DataFrame, prof: dict, seed: int):
    """Genera (score, moras, endeudamiento, sin_historial) con el perfil dado."""
    rng = np.random.default_rng(seed)
    n = len(df)
    y = df["resultado"].to_numpy() if "resultado" in df else np.zeros(n)
    lo, hi = prof["rango"]

    base = prof["media"] + prof["shift"] * (y - 0.5) * 2 + rng.normal(0, prof["ruido"], n)
    score = np.clip(base, lo, hi).round().astype(float)
    moras = np.clip(rng.poisson(np.where(y == 1, 0.5, 1.1), n), 0, 12).astype(float)
    endeud = np.clip(rng.beta(2, 5, n) + np.where(y == 1, -0.03, 0.06), 0.02, 0.98).round(3)
    sin_historial = rng.random(n) >= prof["cobertura"]
    return score, moras, endeud, sin_historial


def simular_buro(df: pd.DataFrame, fuente: str = "datacredito", seed: int = 7) -> pd.DataFrame:
    """Adjunta las señales del proveedor `fuente` con sus nombres base."""
    prof = PROVEEDORES.get(fuente, PROVEEDORES["datacredito"])
    score, moras, endeud, sin = _senales_proveedor(df, prof, seed)
    out = df.copy()
    out["score_buro"], out["moras_ult_12m"], out["nivel_endeudamiento"] = score, moras, endeud
    out.loc[sin, BURO_SIGNALS] = np.nan
    return out


def simular_integral(df: pd.DataFrame, seed: int = 7) -> pd.DataFrame:
    """Adjunta las señales de los TRES proveedores con nombres prefijados."""
    out = df.copy()
    for i, (prov, prof) in enumerate(PROVEEDORES.items()):
        score, moras, endeud, sin = _senales_proveedor(df, prof, seed + i * 101)
        cols = {f"score_buro__{prov}": score, f"moras_ult_12m__{prov}": moras,
                f"nivel_endeudamiento__{prov}": endeud}
        for c, v in cols.items():
            out[c] = v
        sin_cols = [f"{s}__{prov}" for s in BURO_SIGNALS]
        out.loc[sin, sin_cols] = np.nan
    return out


def features_integrales():
    """(features, cortes, etiquetas) del modelo integral: internas + los 3 burós."""
    feats = list(FEATURES)
    cortes, etq = dict(CORTES), dict(ETIQUETAS)
    for prov in PROVEEDORES:
        for sig in BURO_SIGNALS:
            f = f"{sig}__{prov}"
            feats.append(f)
            cortes[f] = BURO_CORTES[sig]
            etq[f] = BURO_ETIQUETAS[sig]
    return feats, cortes, etq


def desde_excel(ruta: str | Path, df: pd.DataFrame) -> pd.DataFrame:
    """Carga señales de buró desde un Excel y las alinea por fila con `df`."""
    raw = pd.read_excel(ruta)
    cols = {c.lower().strip(): c for c in raw.columns}
    faltan = [f for f in BURO_SIGNALS if f not in cols]
    if faltan:
        raise ValueError(f"El archivo de buró debe traer: {', '.join(BURO_SIGNALS)}.")
    out = df.copy()
    for f in BURO_SIGNALS:
        serie = pd.to_numeric(raw[cols[f]], errors="coerce").reindex(range(len(df)))
        out[f] = serie.to_numpy()
    return out


def evaluar_aporte(train_df: pd.DataFrame, test_df: pd.DataFrame, fuente: str) -> dict:
    """Compara modelo SIN buró vs CON buró (un proveedor), fuera de muestra."""
    y_tr = train_df["resultado"].to_numpy()
    y_te = test_df["resultado"].to_numpy()

    proba_sin = _proba_logistica(train_df, test_df, FEATURES, CORTES, ETIQUETAS, y_tr)
    m_sin = metrics.resumen(y_te, proba_sin)

    feats_h = FEATURES + BURO_SIGNALS
    proba_con = _proba_logistica(train_df, test_df, feats_h,
                                 {**CORTES, **BURO_CORTES}, {**ETIQUETAS, **BURO_ETIQUETAS}, y_tr)
    m_con = metrics.resumen(y_te, proba_con)

    bins_b = binizar(train_df, BURO_SIGNALS, BURO_CORTES, BURO_ETIQUETAS)
    woe_b = tabla_woe(bins_b, y_tr, BURO_SIGNALS, BURO_ETIQUETAS)
    cobertura = float(test_df["score_buro"].notna().mean())
    return {
        "activo": True,
        "fuente": BUROS.get(fuente, fuente),
        "cobertura": round(cobertura, 3),
        "sin_cobertura_pct": round((1 - cobertura) * 100, 1),
        "iv": [{"feature": f, "iv": woe_b[f]["iv"]} for f in BURO_SIGNALS],
        "metricas": {
            "sin_buro": m_sin,
            "con_buro": m_con,
            "lift": {k: round(m_con[k] - m_sin[k], 4) for k in m_sin},
        },
    }


def evaluar_integral(train_df: pd.DataFrame, test_df: pd.DataFrame) -> dict:
    """Modelo BASE INTEGRAL: demografía + internas + los tres burós, vs sin buró."""
    y_tr = train_df["resultado"].to_numpy()
    y_te = test_df["resultado"].to_numpy()

    proba_sin = _proba_logistica(train_df, test_df, FEATURES, CORTES, ETIQUETAS, y_tr)
    m_sin = metrics.resumen(y_te, proba_sin)

    feats, cortes, etq = features_integrales()
    proba_full = _proba_logistica(train_df, test_df, feats, cortes, etq, y_tr)
    m_full = metrics.resumen(y_te, proba_full)

    # Cobertura por proveedor y "al menos uno".
    por_prov = {PROVEEDORES[p]["nombre"]: round(float(test_df[f"score_buro__{p}"].notna().mean()), 3)
                for p in PROVEEDORES}
    algun_col = test_df[[f"score_buro__{p}" for p in PROVEEDORES]].notna().any(axis=1)
    return {
        "activo": True,
        "n_features": len(feats),
        "proveedores": [PROVEEDORES[p]["nombre"] for p in PROVEEDORES],
        "cobertura_algun": round(float(algun_col.mean()), 3),
        "sin_ningun_pct": round(float((~algun_col).mean()) * 100, 1),
        "cobertura_por_proveedor": por_prov,
        "metricas": {
            "sin_buro": m_sin,
            "integral": m_full,
            "lift": {k: round(m_full[k] - m_sin[k], 4) for k in m_sin},
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
