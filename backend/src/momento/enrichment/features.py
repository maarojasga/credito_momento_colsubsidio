"""Carga de features con as-of join sobre `signals`.

El as_of NO es opcional: sin él, entrenar/decidir con señales posteriores al
evento es fuga de información. Devuelve por sujeto un dict de features con su
metadata (fuente, confianza, base legal) para el manifiesto de trazabilidad.
"""

from __future__ import annotations

from datetime import datetime

import duckdb

# Mapa señal (dotted) -> nombre de feature que consumen reglas y scorecard.
MAPA_KEY_FEATURE = {
    "geo.estrato": "estrato",
    "geo.localidad": "localidad",
    "demografia.edad": "edad",
    "demografia.sexo": "sexo",
    "empleo.antiguedad_meses": "antiguedad_empleo_meses",
    "empleo.contrato_indefinido": "contrato_indefinido",
    "ingreso.smmlv": "ingreso_smmlv",
    "ingreso.mensual": "ingreso_mensual",
    "hogar.num_hijos": "num_hijos",
    "encuesta.carga_financiera": "carga_financiera",
    "encuesta.tenencia_tc": "tenencia_tc",
}

_ASOF_SQL = """
SELECT subject_id, key, value_num, value_cat, value_bool,
       source_id, provider_version, confidence, base_legal, observed_at
FROM (
    SELECT *, row_number() OVER (
        PARTITION BY subject_id, key ORDER BY observed_at DESC
    ) AS rn
    FROM signals
    WHERE observed_at <= ?
      AND observed_at + INTERVAL (ttl_days) DAY >= ?
)
WHERE rn = 1
"""


def _valor(row: dict):
    if row["value_num"] is not None:
        v = row["value_num"]
        return int(v) if float(v).is_integer() else v
    if row["value_cat"] is not None:
        return row["value_cat"]
    return row["value_bool"]


def cargar_features(con: duckdb.DuckDBPyConnection, as_of: datetime) -> dict[str, dict]:
    """Devuelve {subject_id: {feature: {value, source_id, confidence, ...}}}."""
    rows = con.execute(_ASOF_SQL, [as_of, as_of]).pl().to_dicts()
    out: dict[str, dict] = {}
    for r in rows:
        feat = MAPA_KEY_FEATURE.get(r["key"])
        if feat is None:
            continue
        out.setdefault(r["subject_id"], {})[feat] = {
            "value": _valor(r),
            "signal_key": r["key"],
            "source_id": r["source_id"],
            "provider_version": r["provider_version"],
            "confidence": r["confidence"],
            "base_legal": r["base_legal"],
            "observed_at": r["observed_at"],
        }
    return out


def valores(features_sub: dict) -> dict:
    """Extrae {feature: value} plano para reglas y scorecard."""
    return {k: v["value"] for k, v in features_sub.items()}
