"""Extracción de la ventana de contacto (60 días).

    S = cumprod(1 - h)                                 # supervivencia
    riesgo_ventana = rolling_sum(h * shift(S), win=2)  # prob. de evento en 60 días
    t0 = argmax(riesgo_ventana)
    ventana = (fecha_base + t0, fecha_base + t0 + 2 meses)

La ventana es de dos meses, no de un día: un punto exacto es falsa precisión.

Métrica de pitch (§4.5): cobertura de eventos vs volumen de contacto —
"capturamos ~60% de los eventos usando ~20% de los contactos".
"""

from __future__ import annotations

from datetime import date

import duckdb
import numpy as np
import pandas as pd

from momento.schemas import Ventana
from momento.timing.hazard import predecir_hazard

HORIZONTE_MESES = 18
ANCHO_VENTANA = 2


def _add_months(d: date, months: int) -> date:
    m = d.month - 1 + months
    return date(d.year + m // 12, m % 12 + 1, 1)


def _estado_reciente(con: duckdb.DuckDBPyConnection) -> dict[str, tuple[str, float]]:
    """Último estado y promedio de gasto educativo por sujeto (base del forward)."""
    rows = con.execute(
        """
        WITH ult AS (
            SELECT subject_id, estado,
                   row_number() OVER (PARTITION BY subject_id ORDER BY t_mes DESC) rn
            FROM person_period
        ),
        edu AS (
            SELECT subject_id, avg(edu_eventos_3m) AS edu_prom FROM person_period GROUP BY 1
        )
        SELECT u.subject_id, u.estado, e.edu_prom
        FROM ult u JOIN edu e USING (subject_id)
        WHERE u.rn = 1
        """
    ).pl().to_dicts()
    return {r["subject_id"]: (r["estado"], float(r["edu_prom"])) for r in rows}


def panel_forward(con: duckdb.DuckDBPyConnection, as_of: date,
                  horizonte: int = HORIZONTE_MESES) -> pd.DataFrame:
    """Construye el panel forward por sujeto sobre el horizonte de predicción.

    Mantiene el último estado conocido y proyecta el gasto educativo por su
    promedio; la estacionalidad de mes calendario da la forma dentro del año.
    """
    base = _estado_reciente(con)
    filas = []
    for sid, (estado, edu_prom) in base.items():
        for k in range(horizonte):
            mes_cal = (as_of.month - 1 + k) % 12 + 1
            filas.append({
                "subject_id": sid, "k": k, "mes_calendario": mes_cal,
                "estado": estado, "edu_eventos_3m": edu_prom,
            })
    return pd.DataFrame(filas)


def extraer_ventanas(con: duckdb.DuckDBPyConnection, modelo, as_of: date,
                     producto: str = "credito") -> dict[str, Ventana]:
    """Devuelve la ventana de 60 días de mayor riesgo por sujeto."""
    panel = panel_forward(con, as_of)
    panel["h"] = predecir_hazard(modelo, panel)

    ventanas: dict[str, Ventana] = {}
    for sid, g in panel.groupby("subject_id", sort=False):
        h = g["h"].to_numpy()
        S = np.cumprod(1.0 - h)
        S_prev = np.concatenate([[1.0], S[:-1]])
        riesgo_mes = h * S_prev                      # prob. de evento en cada mes
        riesgo_ventana = riesgo_mes + np.concatenate([riesgo_mes[1:], [0.0]])  # win=2
        t0 = int(np.argmax(riesgo_ventana))
        ventanas[sid] = Ventana(
            subject_id=sid,
            producto=producto,
            inicio=_add_months(as_of, t0),
            fin=_add_months(as_of, t0 + ANCHO_VENTANA),
            hazard_pico=round(float(h[t0]), 5),
            hazard_acumulado_ventana=round(float(riesgo_ventana[t0]), 5),
        )
    return ventanas


def cobertura_vs_contacto(con: duckdb.DuckDBPyConnection, modelo,
                          percentiles=(0.1, 0.2, 0.3, 0.5)) -> list[dict]:
    """Curva cobertura de eventos vs volumen de contacto (métrica de pitch §4.5).

    Ordena las filas person-period por hazard predicho; para cada fracción de
    contactos (las de mayor hazard), mide qué fracción de eventos reales cae ahí.
    """
    df = con.execute(
        "SELECT mes_calendario, estado, edu_eventos_3m, evento FROM person_period"
    ).df()
    df["h"] = predecir_hazard(modelo, df)
    df = df.sort_values("h", ascending=False).reset_index(drop=True)
    total_eventos = int(df["evento"].sum())
    n = len(df)

    curva = []
    for p in percentiles:
        k = max(1, int(n * p))
        capturados = int(df.iloc[:k]["evento"].sum())
        curva.append({
            "contacto": round(p, 3),
            "cobertura": round(capturados / total_eventos, 3) if total_eventos else 0.0,
        })
    return curva
