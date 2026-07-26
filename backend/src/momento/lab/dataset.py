"""Datos etiquetados para entrenar el scorecard.

Dos fuentes:
  - `generar_sintetico`: histórico simulado con una relación conocida (ingreso y
    antigüedad ayudan, carga financiera alta perjudica…), para demostrar que el
    laboratorio recupera pesos sensatos. Es un *stand-in* honesto del histórico real.
  - `desde_excel`: enchufa TU histórico (mismas columnas de señales + una columna
    de desenlace binario), y el laboratorio entrena con datos reales.

Desenlace `resultado`: 1 = buen tomador (aceptó y pagó bien), 0 = no.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from momento.scoring.scorecard import FEATURES

# Nombres alternativos aceptados para la columna de desenlace en un Excel real.
_COLS_RESULTADO = ["resultado", "desenlace", "tomo_credito", "pago", "pago_bien", "target", "y"]


def generar_sintetico(n: int = 5000, seed: int = 42) -> pd.DataFrame:
    """Histórico simulado con señal conocida + ruido. Determinista por `seed`."""
    rng = np.random.default_rng(seed)

    ingreso = np.clip(rng.gamma(2.2, 1.7, n), 0.6, 15).round(2)              # SMMLV
    antiguedad = np.clip(rng.gamma(2.0, 22, n), 0, 300).round().astype(int)  # meses
    estrato = rng.integers(1, 7, n)
    carga = np.clip(rng.beta(2.2, 4.0, n), 0.02, 0.85).round(3)             # 0-1
    tenencia = np.clip(rng.beta(1.8, 3.0, n), 0, 1).round(3)                # 0-1
    edad = np.clip(rng.normal(41, 12, n), 18, 80).round().astype(int)

    df = pd.DataFrame({
        "ingreso_smmlv": ingreso,
        "antiguedad_empleo_meses": antiguedad,
        "estrato": estrato,
        "carga_financiera": carga,
        "tenencia_tc": tenencia,
        "edad": edad,
    })
    # Género: atributo protegido, INDEPENDIENTE del desenlace y ajeno al modelo.
    # Sirve para auditar que el scorecard no discrimina por sexo. 1 = Mujer.
    df["sexo"] = rng.integers(0, 2, n)

    # Log-odds de "buen tomador": relación real que el laboratorio debe recuperar.
    z = (
        -0.4
        + 0.55 * _z(ingreso)
        + 0.45 * _z(antiguedad)
        + 0.25 * _z(estrato.astype(float))
        - 0.60 * _z(carga)
        + 0.20 * _z(tenencia)
        + 0.15 * _z(edad.astype(float))
    )
    p = 1 / (1 + np.exp(-z))
    df["resultado"] = (rng.random(n) < p).astype(int)

    # Faltantes realistas en una señal (para probar el bin "faltante").
    faltan = rng.random(n) < 0.06
    df.loc[faltan, "carga_financiera"] = np.nan
    return df


def desde_excel(ruta: str | Path) -> pd.DataFrame:
    """Carga un histórico real: columnas de señales + una de desenlace."""
    raw = pd.read_excel(ruta)
    cols = {c.lower().strip(): c for c in raw.columns}
    col_res = next((cols[c] for c in _COLS_RESULTADO if c in cols), None)
    if col_res is None:
        raise ValueError(
            "El Excel debe traer una columna de desenlace binario "
            f"(alguna de: {', '.join(_COLS_RESULTADO)})."
        )
    faltan = [f for f in FEATURES if f not in cols]
    if faltan:
        raise ValueError(f"Faltan columnas de señales en el Excel: {', '.join(faltan)}")

    df = pd.DataFrame({f: pd.to_numeric(raw[cols[f]], errors="coerce") for f in FEATURES})
    df["resultado"] = pd.to_numeric(raw[col_res], errors="coerce").fillna(0).astype(int).clip(0, 1)
    for alias in ("sexo", "genero", "género"):
        if alias in cols:
            df["sexo"] = pd.to_numeric(raw[cols[alias]], errors="coerce")
            break
    return df


def _z(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=float)
    s = x.std()
    return (x - x.mean()) / (s if s > 1e-9 else 1.0)
