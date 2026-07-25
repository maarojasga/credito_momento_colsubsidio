"""Capa de almacenamiento DuckDB (§1.2).

Archivo único, clonable sin infraestructura. `signals` es append-only; la vista
`features` se materializa con as-of join contra una fecha de referencia.
"""

from __future__ import annotations

from pathlib import Path

import duckdb
import polars as pl

from momento.timing.sequences import SyntheticDataset

DDL = """
CREATE TABLE IF NOT EXISTS subjects (
    subject_id               TEXT PRIMARY KEY,
    categoria                TEXT,
    edad                     INTEGER,
    sexo                     TEXT,
    ingreso_smmlv            DOUBLE,
    ingreso_mensual          BIGINT,
    antiguedad_empleo_meses  INTEGER,
    contrato_indefinido      BOOLEAN,
    num_hijos                INTEGER,
    localidad                TEXT,
    estrato                  INTEGER
);

CREATE TABLE IF NOT EXISTS eventos (
    subject_id         TEXT,
    servicio           TEXT,
    categoria_servicio TEXT,
    monto              DOUBLE,
    ts                 TIMESTAMP
);

CREATE TABLE IF NOT EXISTS person_period (
    subject_id      TEXT,
    producto        TEXT,
    t_mes           INTEGER,
    mes_calendario  INTEGER,
    estado          TEXT,
    edu_eventos_3m  INTEGER,
    hazard_real     DOUBLE,
    evento          INTEGER
);

-- signals es append-only (§1.2). Se llena en el Motor 1; aquí queda la tabla.
CREATE TABLE IF NOT EXISTS signals (
    subject_id       TEXT,
    key              TEXT,
    value_num        DOUBLE,
    value_cat        TEXT,
    value_bool       BOOLEAN,
    source_id        TEXT,
    provider_id      TEXT,
    provider_version TEXT,
    confidence       DOUBLE,
    base_legal       TEXT,
    observed_at      TIMESTAMP,
    ingested_at      TIMESTAMP,
    ttl_days         INTEGER
);

CREATE TABLE IF NOT EXISTS manifests (
    manifest_hash TEXT PRIMARY KEY,
    payload       JSON
);
"""

# Vista de features con as-of join (§1.2). El as_of NO es opcional: sin él,
# entrenar el timing con señales posteriores al evento es fuga garantizada.
FEATURES_VIEW = """
CREATE OR REPLACE VIEW features AS
SELECT subject_id, key, arg_max(value_num, observed_at) AS value
FROM signals
WHERE observed_at <= ?
  AND observed_at + INTERVAL (ttl_days) DAY >= ?
GROUP BY subject_id, key;
"""


def connect(path: str | Path = "momento.duckdb") -> duckdb.DuckDBPyConnection:
    con = duckdb.connect(str(path))
    con.execute(DDL)
    return con


def _insert(con: duckdb.DuckDBPyConnection, tabla: str, filas: list[dict]) -> None:
    """Inserta en bloque vía Polars (camino vectorizado de DuckDB)."""
    if not filas:
        return
    df = pl.DataFrame(filas)  # noqa: F841 — referenciada por replacement scan
    cols = ", ".join(df.columns)
    con.execute(f"INSERT INTO {tabla} ({cols}) SELECT {cols} FROM df")


def load_synthetic(con: duckdb.DuckDBPyConnection, ds: SyntheticDataset, *, reset: bool = True) -> None:
    """Carga un dataset sintético en DuckDB."""
    if reset:
        for t in ("subjects", "eventos", "person_period"):
            con.execute(f"DELETE FROM {t}")
    _insert(con, "subjects", ds.subjects)
    _insert(con, "eventos", ds.eventos)
    _insert(con, "person_period", ds.person_period)
