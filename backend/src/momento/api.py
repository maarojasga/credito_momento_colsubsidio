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
from fastapi import Body, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
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


@app.on_event("startup")
def _precargar_lab() -> None:
    """Importa la pila del laboratorio (statsmodels/scipy) en el arranque, no en
    la primera petición. Sin esto, el primer 'Entrenar' paga ~15s de imports en
    frío, que en la nube puede pasar el timeout del proxy y parecer que 'no sirve'."""
    try:
        import momento.lab.buro  # noqa: F401
        import momento.lab.service  # noqa: F401
    except Exception:  # el arranque no debe fallar por el warmup
        pass

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


# --- Ciclo de vida: campaña -> aceptación -> firma -> extractos ----------------

class RespuestaCliente(BaseModel):
    accion: str  # "aceptar" | "rechazar"


class FirmaBody(BaseModel):
    firmante: str | None = None


class EnvioCorreo(BaseModel):
    correo: str
    tipo: str = "oferta"  # "oferta" | "contrato"
    base_url: str


def _subject_ids() -> list[str]:
    con = _open_ro()
    if con is None:
        return []
    try:
        return [r[0] for r in con.execute("SELECT subject_id FROM ofertas").fetchall()]
    finally:
        con.close()


@app.post("/campana/enviar")
def campana_enviar() -> dict:
    """Envía la propuesta (+ contrato) a toda la base de clientes del lote."""
    from momento import ciclo
    ids = _subject_ids()
    if not ids:
        raise HTTPException(404, "No hay ofertas para enviar")
    return ciclo.enviar_campana(ids)


@app.get("/campana/estado")
def campana_estado() -> dict:
    from momento import ciclo
    return ciclo.resumen(_subject_ids())


@app.get("/subjects/{subject_id}/ciclo")
def ciclo_estado(subject_id: str) -> dict:
    from momento import ciclo
    return ciclo.estado(subject_id)


@app.post("/subjects/{subject_id}/responder")
def ciclo_responder(subject_id: str, body: RespuestaCliente) -> dict:
    from momento import ciclo
    try:
        return ciclo.responder(subject_id, body.accion)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/subjects/{subject_id}/firmar")
def ciclo_firmar(subject_id: str, body: FirmaBody | None = Body(default=None)) -> dict:
    from momento import ciclo
    try:
        return ciclo.firmar(subject_id, body.firmante if body else None)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/subjects/{subject_id}/reabrir")
def ciclo_reabrir(subject_id: str) -> dict:
    from momento import ciclo
    return ciclo.reabrir(subject_id)


@app.post("/subjects/{subject_id}/enviar-correo")
def enviar_correo(subject_id: str, body: EnvioCorreo) -> dict:
    """Envía la oferta o el contrato como link al portal del cliente."""
    from momento import correo
    oferta, _ = _oferta_y_manifiesto(subject_id)
    ruta = "contrato" if body.tipo == "contrato" else "oferta"
    link = f"{body.base_url.rstrip('/')}/{ruta}/{subject_id}"
    if body.tipo == "contrato":
        html, asunto = correo.cuerpo_contrato(oferta, link), "Tu contrato de crédito Colsubsidio"
    else:
        html, asunto = correo.cuerpo_oferta(oferta, link), "Tu crédito preaprobado Colsubsidio"
    res = correo.enviar(body.correo, asunto, html)
    res["link"] = link
    return res


def _oferta_y_manifiesto(subject_id: str) -> tuple[dict, dict]:
    con = _open_ro()
    if con is None:
        raise HTTPException(404, "Aún no hay datos cargados")
    try:
        row = con.execute(
            "SELECT nombre_producto, monto, plazo_meses, canal, hora_envio, puntos_scorecard, "
            "top_senales, manifest_hash FROM ofertas WHERE subject_id = ?", [subject_id]).fetchone()
        if row is None:
            raise HTTPException(404, "Sujeto sin oferta")
        payload = con.execute("SELECT payload FROM manifests WHERE manifest_hash = ?", [row[7]]).fetchone()
    finally:
        con.close()
    oferta = {
        "subject_id": subject_id, "nombre_producto": row[0], "monto": row[1], "plazo_meses": row[2],
        "canal": row[3], "hora_envio": row[4], "puntos_scorecard": row[5],
        "top_senales": json.loads(row[6]) if row[6] else [],
    }
    manifiesto = json.loads(payload[0]) if payload else {"senales": [], "reglas_evaluadas": []}
    return oferta, manifiesto


@app.get("/subjects/{subject_id}/contrato.pdf")
def contrato_pdf(subject_id: str) -> Response:
    from momento import ciclo, documentos
    oferta, manifiesto = _oferta_y_manifiesto(subject_id)
    firma = ciclo.estado(subject_id).get("firma")
    pdf = documentos.contrato_pdf(oferta, manifiesto, firma=firma)
    return Response(content=pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f'inline; filename="contrato_{subject_id}.pdf"'})


@app.get("/subjects/{subject_id}/extracto.pdf")
def extracto_pdf(subject_id: str, pagadas: int = 3) -> Response:
    from momento import documentos
    oferta, _ = _oferta_y_manifiesto(subject_id)
    pdf = documentos.extracto_pdf(oferta, pagadas=pagadas)
    return Response(content=pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f'inline; filename="extracto_{subject_id}.pdf"'})


# --- Laboratorio de Crédito ---------------------------------------------------

class PromoverModelo(BaseModel):
    challenger_id: str


@app.get("/lab/estado")
def lab_estado() -> dict:
    from momento.lab import store
    return store.estado()


@app.post("/lab/entrenar")
async def lab_entrenar(
    file: UploadFile | None = File(default=None),
    buro_fuente: str | None = Form(default=None),
    buro_file: UploadFile | None = File(default=None),
    integral: bool = Form(default=False),
) -> dict:
    """Entrena el retador. Sin archivo usa el histórico sintético etiquetado;
    con archivo, entrena sobre TU histórico (señales + columna de desenlace).

    Buró OPCIONAL: `buro_fuente` (datacredito/transunion/experian) conecta el
    buró simulado; `buro_file` carga un archivo de buró. El scorecard de
    producción sigue siendo sin buró; solo se mide cuánto aportaría."""
    from momento.lab.dataset import desde_excel
    from momento.lab.service import correr_experimento

    df = None
    if file is not None:
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            tmp.write(await file.read())
            ruta = tmp.name
        try:
            df = desde_excel(ruta)
        except ValueError as e:
            raise HTTPException(400, str(e))
        finally:
            os.unlink(ruta)

    fuente = (buro_fuente or "").strip() or None
    buro_archivo = None
    if buro_file is not None:
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            tmp.write(await buro_file.read())
            buro_archivo = tmp.name
        fuente = fuente or "archivo"
    try:
        return correr_experimento(df, buro_fuente=fuente, buro_archivo=buro_archivo, integral=integral)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"No se pudo entrenar: {e}")
    finally:
        if buro_archivo:
            os.unlink(buro_archivo)


@app.post("/lab/promover")
def lab_promover(body: PromoverModelo) -> dict:
    from momento.lab import store
    try:
        return store.promover(body.challenger_id)
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/lab/revertir")
def lab_revertir() -> dict:
    from momento.lab import store
    return store.revertir()


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
