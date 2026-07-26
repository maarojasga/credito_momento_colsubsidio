"""Ciclo de vida de la oferta tras ganar/promover un modelo.

Flujo: modelo promovido -> se envía la propuesta a la base de clientes
(`propuesta_enviada`) -> el cliente acepta (`aceptada`) o rechaza (`rechazada`)
-> al firmar queda `firmada` y se habilitan los extractos mensuales.

El estado vive en un JSON junto a la base (efímero en la nube, suficiente para
el demo). Del cliente solo se usa el subject_id; nada de datos personales.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

ESTADOS = ["pendiente", "propuesta_enviada", "aceptada", "firmada", "rechazada"]


def _ruta() -> Path:
    db = os.environ.get("MOMENTO_DB", "data/synthetic/momento.duckdb")
    return Path(db).resolve().parent / "ciclo.json"


def _cargar() -> dict:
    r = _ruta()
    return json.loads(r.read_text()) if r.exists() else {}


def _guardar(data: dict) -> None:
    r = _ruta()
    r.parent.mkdir(parents=True, exist_ok=True)
    r.write_text(json.dumps(data, ensure_ascii=False, indent=2))


def estado(subject_id: str) -> dict:
    data = _cargar()
    reg = data.get(subject_id)
    return reg if reg else {"estado": "pendiente", "historial": []}


def enviar_campana(subject_ids: list[str]) -> dict:
    """Envía la propuesta a la base: marca 'propuesta_enviada' a quien no haya
    avanzado ya (respeta aceptadas/firmadas)."""
    data = _cargar()
    enviadas = 0
    for sid in subject_ids:
        actual = data.get(sid, {}).get("estado", "pendiente")
        if actual in ("pendiente", "rechazada"):
            data[sid] = {"estado": "propuesta_enviada",
                         "historial": data.get(sid, {}).get("historial", []) + ["propuesta_enviada"]}
            enviadas += 1
    _guardar(data)
    return {"enviadas": enviadas, "total": len(subject_ids)}


def responder(subject_id: str, accion: str) -> dict:
    """El cliente acepta o rechaza la propuesta."""
    if accion not in ("aceptar", "rechazar"):
        raise ValueError("acción inválida")
    nuevo = "aceptada" if accion == "aceptar" else "rechazada"
    data = _cargar()
    reg = data.get(subject_id, {"estado": "pendiente", "historial": []})
    reg = {"estado": nuevo, "historial": reg.get("historial", []) + [nuevo]}
    data[subject_id] = reg
    _guardar(data)
    return reg


def firmar(subject_id: str, firmante: str | None = None) -> dict:
    """Firma electrónica del contrato: habilita el detalle y los extractos.

    Guarda el firmante y un sello de firma (hash del sujeto + nombre + momento),
    que es la evidencia de la aceptación electrónica (firma digital MVP).
    """
    data = _cargar()
    reg = data.get(subject_id, {"estado": "pendiente", "historial": []})
    if reg["estado"] not in ("aceptada", "firmada"):
        raise ValueError("solo se firma una propuesta aceptada")
    nombre = (firmante or "").strip() or "Afiliado Colsubsidio"
    ahora = datetime.now(timezone.utc).isoformat(timespec="seconds")
    sello = hashlib.sha256(f"{subject_id}|{nombre}|{ahora}".encode()).hexdigest()[:16].upper()
    firma = {"nombre": nombre, "fecha": ahora, "sello": sello}
    reg = {"estado": "firmada", "historial": reg.get("historial", []) + ["firmada"], "firma": firma}
    data[subject_id] = reg
    _guardar(data)
    return reg


def reabrir(subject_id: str) -> dict:
    """Deshace la respuesta (demo): vuelve a 'propuesta_enviada'."""
    data = _cargar()
    data[subject_id] = {"estado": "propuesta_enviada",
                        "historial": data.get(subject_id, {}).get("historial", []) + ["reabierta"]}
    _guardar(data)
    return data[subject_id]


def resumen(subject_ids: list[str]) -> dict:
    """Conteo por estado sobre la base de clientes del lote."""
    data = _cargar()
    conteo = {e: 0 for e in ESTADOS}
    for sid in subject_ids:
        conteo[data.get(sid, {}).get("estado", "pendiente")] += 1
    enviada = any(data.get(sid, {}).get("estado", "pendiente") != "pendiente" for sid in subject_ids)
    return {"conteo": conteo, "total": len(subject_ids), "campana_enviada": enviada}
