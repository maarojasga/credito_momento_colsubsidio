"""API FastAPI de MOMENTO.

Sirve las ofertas y manifiestos precalculados (todo lo pesado corre offline; en
vivo solo correría el envío). Alimenta la vista operador y la vista afiliado.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import duckdb
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

DB_PATH = os.environ.get("MOMENTO_DB", "data/synthetic/momento.duckdb")

app = FastAPI(title="MOMENTO", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _con() -> duckdb.DuckDBPyConnection:
    if not Path(DB_PATH).exists():
        raise HTTPException(503, f"No existe la base {DB_PATH}. Corre seed_synthetic y build_ofertas.")
    return duckdb.connect(DB_PATH, read_only=True)


def _oferta_dict(row: tuple, cols: list[str]) -> dict:
    d = dict(zip(cols, row))
    d["top_senales"] = json.loads(d["top_senales"]) if d.get("top_senales") else []
    for k in ("ventana_inicio", "ventana_fin"):
        if d.get(k) is not None:
            d[k] = d[k].isoformat()
    return d


_OFERTA_COLS = [
    "subject_id", "producto", "nombre_producto", "monto", "plazo_meses", "canal",
    "hora_envio", "puntos_scorecard", "ventana_inicio", "ventana_fin", "hazard_pico",
    "razon_texto", "narrativa_origen", "top_senales", "manifest_hash",
]


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "db": DB_PATH, "existe": Path(DB_PATH).exists()}


@app.get("/stats")
def stats() -> dict:
    """Métricas agregadas para el encabezado de la vista operador."""
    con = _con()
    try:
        total = con.execute("SELECT count(*) FROM ofertas").fetchone()[0]
        productos = dict(con.execute(
            "SELECT nombre_producto, count(*) FROM ofertas GROUP BY 1 ORDER BY 2 DESC").fetchall())
        canales = dict(con.execute("SELECT canal, count(*) FROM ofertas GROUP BY 1").fetchall())
        monto_prom = con.execute("SELECT round(avg(monto)) FROM ofertas").fetchone()[0]
        return {"total_ofertas": total, "productos": productos, "canales": canales,
                "monto_promedio": monto_prom}
    finally:
        con.close()


@app.get("/ofertas")
def listar_ofertas(limit: int = 50, offset: int = 0, producto: str | None = None) -> dict:
    """Lista paginada de ofertas para la tabla del operador."""
    con = _con()
    try:
        where = "WHERE producto = ?" if producto else ""
        params = [producto] if producto else []
        total = con.execute(f"SELECT count(*) FROM ofertas {where}", params).fetchone()[0]
        rows = con.execute(
            f"SELECT {', '.join(_OFERTA_COLS)} FROM ofertas {where} "
            "ORDER BY puntos_scorecard DESC LIMIT ? OFFSET ?",
            [*params, limit, offset],
        ).fetchall()
        return {"total": total, "items": [_oferta_dict(r, _OFERTA_COLS) for r in rows]}
    finally:
        con.close()


@app.get("/metrics")
def metrics() -> dict:
    """Métricas del modelo: cobertura vs contacto (§4.5) y coeficientes de hazard."""
    con = _con()
    try:
        rows = con.execute("SELECT clave, valor FROM metricas").fetchall()
        return {clave: json.loads(valor) for clave, valor in rows}
    finally:
        con.close()


@app.get("/subjects/{subject_id}/oferta")
def get_oferta(subject_id: str) -> dict:
    con = _con()
    try:
        row = con.execute(
            f"SELECT {', '.join(_OFERTA_COLS)} FROM ofertas WHERE subject_id = ?",
            [subject_id],
        ).fetchone()
        if row is None:
            raise HTTPException(404, "Sujeto sin oferta (no elegible o inexistente)")
        return _oferta_dict(row, _OFERTA_COLS)
    finally:
        con.close()


@app.get("/subjects/{subject_id}/manifest")
def get_manifest(subject_id: str) -> dict:
    """Manifiesto de trazabilidad descargable desde la UI."""
    con = _con()
    try:
        h = con.execute("SELECT manifest_hash FROM ofertas WHERE subject_id = ?",
                        [subject_id]).fetchone()
        if h is None:
            raise HTTPException(404, "Sujeto sin oferta")
        payload = con.execute("SELECT payload FROM manifests WHERE manifest_hash = ?",
                              [h[0]]).fetchone()
        return json.loads(payload[0])
    finally:
        con.close()
