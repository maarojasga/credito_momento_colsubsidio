"""API FastAPI de MOMENTO.

Expone la corrida de lote y la consulta por sujeto, y sirve los manifiestos de
trazabilidad para descarga desde la UI (vista operador y vista afiliado).
"""

from __future__ import annotations

from fastapi import FastAPI

app = FastAPI(title="MOMENTO", version="0.1.0")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/subjects/{subject_id}/oferta")
def get_oferta(subject_id: str) -> dict:
    """Devuelve la oferta vigente del sujeto (producto, ventana, canal, razón)."""
    raise NotImplementedError


@app.get("/subjects/{subject_id}/manifest")
def get_manifest(subject_id: str) -> dict:
    """Devuelve el manifiesto de trazabilidad descargable."""
    raise NotImplementedError


@app.post("/batch")
def run_batch() -> dict:
    """Corre el lote de enriquecimiento + scoring. Objetivo: 2.000 en < 3 min."""
    raise NotImplementedError
