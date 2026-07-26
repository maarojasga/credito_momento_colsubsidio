"""Persistencia del retador entrenado y promoción a producción.

El retador se guarda como JSON junto a la base. `promover` lo copia al archivo
que `Scorecard.en_produccion` lee, con lo cual el pipeline pasa a usar los pesos
aprendidos. `revertir` vuelve al experto borrando ese archivo.
"""

from __future__ import annotations

import json
from pathlib import Path

from momento.scoring.scorecard import _ruta_promovido, tabla_a_json


def _ruta_retador() -> Path:
    return _ruta_promovido().parent / "scorecard_retador.json"


def guardar_retador(payload: dict) -> None:
    ruta = _ruta_retador()
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(payload, ensure_ascii=False, indent=2))


def cargar_retador() -> dict | None:
    ruta = _ruta_retador()
    return json.loads(ruta.read_text()) if ruta.exists() else None


def promover(challenger_id: str) -> dict:
    retador = cargar_retador()
    if retador is None or retador.get("challenger_id") != challenger_id:
        raise ValueError("No hay un retador con ese id para promover.")
    destino = _ruta_promovido()
    destino.write_text(json.dumps({
        "version": f"sc-aprendido-{challenger_id}",
        "tabla": tabla_a_json(_estructura_desde_json(retador["tabla"])),
    }, ensure_ascii=False, indent=2))
    return {"promovido": True, "version": f"sc-aprendido-{challenger_id}"}


def revertir() -> dict:
    ruta = _ruta_promovido()
    if ruta.exists():
        ruta.unlink()
    return {"promovido": False, "version": "sc-experto-0.1"}


def estado() -> dict:
    prom = _ruta_promovido()
    ret = cargar_retador()
    version = "sc-experto-0.1"
    if prom.exists():
        version = json.loads(prom.read_text()).get("version", "sc-aprendido")
    return {
        "version_produccion": version,
        "hay_promovido": prom.exists(),
        "challenger_id": ret.get("challenger_id") if ret else None,
    }


def _estructura_desde_json(bins_por_feature: dict) -> dict:
    """El retador ya se guarda con bins como listas JSON; passthrough a tabla_a_json."""
    return {
        feature: {
            "bins": [(None if lim is None else float(lim), int(pts), et)
                     for lim, pts, et in cfg["bins"]],
            "missing": int(cfg["missing"]),
        }
        for feature, cfg in bins_por_feature.items()
    }
