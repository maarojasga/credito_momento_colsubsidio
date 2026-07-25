"""API FastAPI de MOMENTO.

Sirve las ofertas y manifiestos precalculados, y permite **subir un Excel de
afiliados manualmente** (la imagen arranca sin datos). Todo lo pesado corre en
la ingesta; en vivo solo correría el envío del mensaje.
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import date
from pathlib import Path

import duckdb
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

# Ruta ESCRIBIBLE de la base (en Cloud Run: /tmp). Local: data/synthetic/.
DB_PATH = os.environ.get("MOMENTO_DB", "data/synthetic/momento.duckdb")
# Plantilla de Excel para descargar desde la UI.
PLANTILLA_PATH = os.environ.get("MOMENTO_PLANTILLA", "afiliados.xlsx")
AS_OF = date(2026, 7, 1)

app = FastAPI(title="MOMENTO", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_OFERTA_COLS = [
    "subject_id", "producto", "nombre_producto", "monto", "plazo_meses", "canal",
    "hora_envio", "puntos_scorecard", "ventana_inicio", "ventana_fin", "hazard_pico",
    "razon_texto", "narrativa_origen", "top_senales", "manifest_hash",
]


def _open_ro() -> duckdb.DuckDBPyConnection | None:
    """Conexión de solo lectura, o None si aún no hay base (estado vacío)."""
    if not Path(DB_PATH).exists():
        return None
    return duckdb.connect(DB_PATH, read_only=True)


def _tiene_ofertas(con: duckdb.DuckDBPyConnection) -> bool:
    try:
        return con.execute("SELECT count(*) FROM ofertas").fetchone()[0] > 0
    except duckdb.Error:
        return False


def _oferta_dict(row: tuple, cols: list[str]) -> dict:
    d = dict(zip(cols, row))
    d["top_senales"] = json.loads(d["top_senales"]) if d.get("top_senales") else []
    for k in ("ventana_inicio", "ventana_fin"):
        if d.get(k) is not None:
            d[k] = d[k].isoformat()
    return d


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "db": DB_PATH, "con_datos": Path(DB_PATH).exists()}


@app.get("/stats")
def stats() -> dict:
    con = _open_ro()
    if con is None or not _tiene_ofertas(con):
        if con:
            con.close()
        return {"total_ofertas": 0, "productos": {}, "canales": {}, "monto_promedio": 0}
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


@app.get("/metrics")
def metrics() -> dict:
    con = _open_ro()
    if con is None:
        return {}
    try:
        rows = con.execute("SELECT clave, valor FROM metricas").fetchall()
        return {clave: json.loads(valor) for clave, valor in rows}
    except duckdb.Error:
        return {}
    finally:
        con.close()


@app.get("/ofertas")
def listar_ofertas(limit: int = 50, offset: int = 0, producto: str | None = None) -> dict:
    con = _open_ro()
    if con is None or not _tiene_ofertas(con):
        if con:
            con.close()
        return {"total": 0, "items": []}
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


@app.get("/subjects/{subject_id}/oferta")
def get_oferta(subject_id: str) -> dict:
    con = _open_ro()
    if con is None:
        raise HTTPException(404, "Aún no hay datos cargados")
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
    con = _open_ro()
    if con is None:
        raise HTTPException(404, "Aún no hay datos cargados")
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


# --- Copiloto de IA (Gemini) --------------------------------------------------

class PreguntaCopiloto(BaseModel):
    subject_id: str
    pregunta: str | None = None


@app.get("/copiloto/estado")
def copiloto_estado() -> dict:
    from momento.copiloto import GEMINI_MODEL, disponible
    return {"disponible": disponible(), "modelo": GEMINI_MODEL}


@app.get("/subjects/{subject_id}/narrativa-ia")
def narrativa_ia_endpoint(subject_id: str) -> dict:
    """Genera la narrativa de la oferta con IA (validada), o cae a plantilla."""
    from momento.copiloto import narrativa_ia

    con = _open_ro()
    if con is None:
        raise HTTPException(404, "Aún no hay datos cargados")
    try:
        row = con.execute(
            "SELECT producto, monto, plazo_meses, top_senales FROM ofertas WHERE subject_id = ?",
            [subject_id],
        ).fetchone()
    finally:
        con.close()
    if row is None:
        raise HTTPException(404, "Sujeto sin oferta")

    producto, monto, plazo, top_json = row
    payload = {
        "producto": producto,
        "monto": monto,
        "plazo_meses": plazo,
        "senales": json.loads(top_json) if top_json else [],
    }
    texto, origen = narrativa_ia(payload)
    return {"texto": texto, "origen": origen, "validado": True}


@app.post("/copiloto/explicar")
def copiloto_explicar(q: PreguntaCopiloto) -> dict:
    """Responde una pregunta del operador anclada al manifiesto de la oferta."""
    from momento.copiloto import explicar

    con = _open_ro()
    if con is None:
        raise HTTPException(404, "Aún no hay datos cargados")
    try:
        h = con.execute("SELECT manifest_hash FROM ofertas WHERE subject_id = ?",
                        [q.subject_id]).fetchone()
        if h is None:
            raise HTTPException(404, "Sujeto sin oferta")
        payload = con.execute("SELECT payload FROM manifests WHERE manifest_hash = ?",
                              [h[0]]).fetchone()
    finally:
        con.close()
    manifiesto = json.loads(payload[0])
    return {"respuesta": explicar(manifiesto, q.pregunta)}


@app.get("/copiloto/resumen")
def copiloto_resumen() -> dict:
    """Resumen ejecutivo del lote generado con IA."""
    from momento.copiloto import resumen_lote

    con = _open_ro()
    if con is None or not _tiene_ofertas(con):
        if con:
            con.close()
        return {"resumen": "Aún no hay ofertas cargadas."}
    try:
        total = con.execute("SELECT count(*) FROM ofertas").fetchone()[0]
        productos = dict(con.execute(
            "SELECT nombre_producto, count(*) FROM ofertas GROUP BY 1 ORDER BY 2 DESC").fetchall())
        canales = dict(con.execute("SELECT canal, count(*) FROM ofertas GROUP BY 1").fetchall())
        monto_prom = con.execute("SELECT round(avg(monto)) FROM ofertas").fetchone()[0]
        ventanas = dict(con.execute(
            "SELECT strftime(ventana_inicio, '%Y-%m') m, count(*) FROM ofertas "
            "GROUP BY 1 ORDER BY 1").fetchall())
    finally:
        con.close()
    agregados = {"total_ofertas": total, "productos": productos, "canales": canales,
                 "monto_promedio": monto_prom, "ventanas_por_mes": ventanas}
    return {"resumen": resumen_lote(agregados), "agregados": agregados}


@app.get("/plantilla")
def descargar_plantilla() -> FileResponse:
    """Descarga la plantilla de Excel con los encabezados y ejemplos."""
    if not Path(PLANTILLA_PATH).exists():
        raise HTTPException(404, "Plantilla no disponible")
    return FileResponse(PLANTILLA_PATH, filename="afiliados_plantilla.xlsx",
                        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


@app.post("/cargar-excel")
async def cargar_excel(file: UploadFile = File(...)) -> dict:
    """Sube un Excel de afiliados, corre el pipeline y reemplaza los datos.

    Escribe a una base temporal y la mueve atómicamente sobre la activa, para no
    interrumpir las lecturas en curso.
    """
    if not file.filename or not file.filename.lower().endswith((".xlsx", ".xlsm")):
        raise HTTPException(400, "Sube un archivo .xlsx")

    from momento.ingest import ingestar_excel

    tmp_xlsx = Path(tempfile.gettempdir()) / "afiliados_upload.xlsx"
    tmp_xlsx.write_bytes(await file.read())

    building = DB_PATH + ".building"
    try:
        r = ingestar_excel(str(tmp_xlsx), building, AS_OF)
    except Exception as e:  # noqa: BLE001 — reportar al usuario
        Path(building).unlink(missing_ok=True)
        raise HTTPException(400, f"No se pudo procesar el Excel: {e}")

    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    os.replace(building, DB_PATH)
    return {"ok": True, "afiliados": r["afiliados"], "ofertas": r["ofertas"],
            "no_elegibles": r["no_elegibles"]}
