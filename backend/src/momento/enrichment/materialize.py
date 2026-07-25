"""Materialización de señales (Motor 1) desde los atributos del sujeto.

En producción cada `key` la emite un proveedor externo (geo, RUES, encuesta…).
En el demo, los atributos sintéticos del afiliado se convierten en registros
`Signal` con fuente, versión, confianza y base legal — para que el principio
"la señal es la unidad atómica" sea real y trazable, no una promesa.

Las señales imputadas (carga financiera, tenencia) se marcan `inferida` con
confianza reducida y NUNCA se usan como restricción dura (solo ranking).
"""

from __future__ import annotations

from datetime import datetime

import duckdb

from momento.donor.match import imputar_desde_encuesta

# (key, columna_origen, value_type, source_id, provider_id, provider_version,
#  confidence, base_legal, ttl_days)
_MAPA_DIRECTO = [
    ("geo.estrato", "estrato", "num", "catastro_bogota_2025", "geo.estrato", "0.1.0", 0.95, "publica", 365),
    ("geo.localidad", "localidad", "cat", "dane_mgn_2018", "geo.manzana", "0.1.0", 0.98, "publica", 3650),
    ("demografia.edad", "edad", "num", "afiliacion_colsubsidio", "afiliacion", "0.1.0", 1.0, "consentida", 365),
    ("demografia.sexo", "sexo", "cat", "afiliacion_colsubsidio", "afiliacion", "0.1.0", 1.0, "consentida", 3650),
    ("empleo.antiguedad_meses", "antiguedad_empleo_meses", "num", "pila", "empleador.rues", "0.1.0", 0.9, "consentida", 180),
    ("empleo.contrato_indefinido", "contrato_indefinido", "bool", "pila", "empleador.rues", "0.1.0", 0.9, "consentida", 180),
    ("ingreso.smmlv", "ingreso_smmlv", "num", "pila", "afiliacion", "0.1.0", 0.9, "consentida", 180),
    ("ingreso.mensual", "ingreso_mensual", "num", "pila", "afiliacion", "0.1.0", 0.9, "consentida", 180),
    ("hogar.num_hijos", "num_hijos", "num", "afiliacion_colsubsidio", "afiliacion", "0.1.0", 0.85, "consentida", 365),
]


def _fila_signal(subject_id: str, key: str, value, vtype: str, source_id: str,
                 provider_id: str, version: str, conf: float, legal: str,
                 ttl: int, observed_at: datetime) -> dict:
    return {
        "subject_id": subject_id,
        "key": key,
        "value_num": float(value) if vtype == "num" else None,
        "value_cat": str(value) if vtype == "cat" else None,
        "value_bool": bool(value) if vtype == "bool" else None,
        "source_id": source_id,
        "provider_id": provider_id,
        "provider_version": version,
        "confidence": conf,
        "base_legal": legal,
        "observed_at": observed_at,
        "ingested_at": observed_at,
        "ttl_days": ttl,
    }


def materializar_subject(sub: dict, observed_at: datetime) -> list[dict]:
    filas: list[dict] = []
    sid = sub["subject_id"]

    for key, col, vtype, src, prov, ver, conf, legal, ttl in _MAPA_DIRECTO:
        if col in sub and sub[col] is not None:
            filas.append(_fila_signal(sid, key, sub[col], vtype, src, prov, ver, conf, legal, ttl, observed_at))

    # Señales imputadas desde encuesta (Motor 1.5) — base legal inferida.
    for key, value, conf in imputar_desde_encuesta(sub):
        filas.append(_fila_signal(sid, key, value, "num", "iefic_2017", "encuesta.donante",
                                  "0.1.0", conf, "inferida", 180, observed_at))
    return filas


def run_enrichment(con: duckdb.DuckDBPyConnection, observed_at: datetime, *, reset: bool = True) -> int:
    """Lee subjects, materializa señales y las escribe en `signals` (append-only)."""
    import polars as pl

    if reset:
        con.execute("DELETE FROM signals")

    subs = con.execute("SELECT * FROM subjects").pl().to_dicts()
    filas: list[dict] = []
    for sub in subs:
        filas.extend(materializar_subject(sub, observed_at))

    if filas:
        df = pl.DataFrame(filas)  # noqa: F841 — replacement scan de DuckDB
        cols = ", ".join(df.columns)
        con.execute(f"INSERT INTO signals ({cols}) SELECT {cols} FROM df")
    return len(filas)
