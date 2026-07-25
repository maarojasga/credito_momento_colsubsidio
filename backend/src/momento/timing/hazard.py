"""Modelo de riesgo en tiempo discreto (persona-periodo).

    logit h(t | x) = α(t) + β' x(t)

  α(t): dummies de mes calendario (estacionalidad de matrículas).
  x(t): estado de trayectoria + gasto reciente en educación.

Ajuste: statsmodels.GLM(family=Binomial()) sobre el panel person_period.
Devuelve hazard mensual calibrado y coeficientes leíbles como razones de odds.
El notebook 02_hazard compara los coeficientes recuperados contra la verdad de
campo de `timing/params.py`.
"""

from __future__ import annotations

import duckdb
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

FORMULA = "evento ~ C(estado) + edu_eventos_3m + C(mes_calendario)"


def cargar_panel(con: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    return con.execute(
        "SELECT subject_id, t_mes, mes_calendario, estado, edu_eventos_3m, evento "
        "FROM person_period"
    ).df()


MIN_FILAS_FIT = 5000


def ajustar_hazard(con: duckdb.DuckDBPyConnection):
    """Ajusta el GLM binomial sobre el panel y devuelve el modelo entrenado.

    Si el panel es pequeño (p.ej. un Excel de pocos afiliados), entrena el
    modelo sobre una población sintética de referencia con el mismo proceso
    generador: el timing es un modelo, y un puñado de filas no basta para
    estimarlo de forma estable. Las ventanas de los afiliados reales igual se
    calculan con SUS covariables (ver ventana.extraer_ventanas).
    """
    df = cargar_panel(con)
    if len(df) < MIN_FILAS_FIT:
        from momento.timing.sequences import generar_sintetico

        ref = generar_sintetico(n=2000, seed=7)
        df = pd.DataFrame(ref.person_period)
    modelo = smf.glm(FORMULA, data=df, family=sm.families.Binomial()).fit()
    return modelo


def predecir_hazard(modelo, panel: pd.DataFrame) -> np.ndarray:
    """Hazard mensual h[t] predicho sobre un panel (forward o histórico)."""
    return np.asarray(modelo.predict(panel), dtype=float)


def resumen_coeficientes(modelo) -> dict:
    """Coeficientes como razones de odds para el pitch y el manifiesto."""
    params = modelo.params
    return {
        "modelo": "dt-hazard-0.1",
        "n_obs": int(modelo.nobs),
        "coeficientes": {k: round(float(v), 4) for k, v in params.items()},
        "odds_ratio": {k: round(float(np.exp(v)), 4) for k, v in params.items()},
    }
