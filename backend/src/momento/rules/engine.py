"""Motor de evaluación de reglas duras.

Pequeño y propio, con registro de cada regla disparada. Salida: conjunto
elegible + monto_max por producto. El scoring solo ordena dentro de ese
conjunto. Nunca imputa: si falta una feature requerida por una regla, el
producto queda no elegible con la razón explícita.
"""

from __future__ import annotations

import operator
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

RULES_PATH = Path(__file__).with_name("elegibilidad.yaml")

_OPS = {
    ">=": operator.ge,
    "<=": operator.le,
    ">": operator.gt,
    "<": operator.lt,
    "==": operator.eq,
    "!=": operator.ne,
}


@dataclass
class ResultadoElegibilidad:
    producto: str
    nombre: str
    elegible: bool
    monto_min: int | None = None
    monto_max: int | None = None
    plazo_meses: int | None = None
    reglas_disparadas: list[str] = field(default_factory=list)
    motivo_rechazo: str | None = None


def cargar_reglas(path: Path = RULES_PATH) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _evaluar_condicion(cond: dict, features: dict) -> tuple[bool, str]:
    """Devuelve (cumple, descripcion_legible). Faltante => no cumple."""
    key, op, valor = cond["key"], cond["op"], cond["valor"]
    desc = f"{key} {op} {valor}"
    if key not in features or features[key] is None:
        return False, f"{desc} [falta {key}]"
    return _OPS[op](features[key], valor), desc


def _eval_monto_expr(expr: str, features: dict) -> int | None:
    """Evalúa expresiones seguras del tipo '3 * ingreso_mensual'."""
    m = re.fullmatch(r"\s*(\d+)\s*\*\s*(\w+)\s*", expr)
    if not m:
        return None
    factor, key = int(m.group(1)), m.group(2)
    if key not in features or features[key] is None:
        return None
    return int(factor * features[key])


def _cumple_globales(features: dict) -> tuple[bool, list[str], str | None]:
    reglas = cargar_reglas()
    disparadas: list[str] = []
    indefinido = bool(features.get("contrato_indefinido", False))
    for req in reglas.get("requisitos_globales", []):
        if req.get("solo_si_contrato_no_indefinido") and indefinido:
            continue
        ok, desc = _evaluar_condicion(req, features)
        disparadas.append(f"global: {desc} -> {'ok' if ok else 'falla'}")
        if not ok:
            return False, disparadas, f"requisito global no cumplido: {desc}"
    return True, disparadas, None


def _monto_producto(nombre_prod: str, cfg: dict, features: dict, disparadas: list[str]) -> int | None:
    """Resuelve el monto_max del producto según sus reglas de capacidad."""
    for regla in cfg.get("reglas_capacidad", []):
        ok, desc = _evaluar_condicion(regla["si"], features)
        if ok:
            if "monto_max" in regla:
                disparadas.append(f"{nombre_prod}.capacidad: {desc} -> monto_max={regla['monto_max']}")
                return int(regla["monto_max"])
            if "monto_max_expr" in regla:
                m = _eval_monto_expr(regla["monto_max_expr"], features)
                disparadas.append(f"{nombre_prod}.capacidad: {desc} -> monto_max={m}")
                return m
    if "reglas_capacidad" in cfg:
        m = cfg.get("monto_max_default")
        disparadas.append(f"{nombre_prod}.capacidad: default -> monto_max={m}")
        return int(m) if m is not None else None
    return int(cfg["monto_max"]) if cfg.get("monto_max") is not None else None


def evaluar(features: dict, reglas: dict | None = None) -> list[ResultadoElegibilidad]:
    """Evalúa todos los productos y devuelve el conjunto con monto_max.

    Registra cada regla disparada para el manifiesto de trazabilidad.
    """
    reglas = reglas or cargar_reglas()
    globales_ok, disparadas_glob, motivo_glob = _cumple_globales(features)

    resultados: list[ResultadoElegibilidad] = []
    for prod, cfg in reglas.get("productos", {}).items():
        disparadas = list(disparadas_glob)
        nombre = cfg.get("nombre", prod)

        if not globales_ok:
            resultados.append(
                ResultadoElegibilidad(prod, nombre, False, reglas_disparadas=disparadas,
                                      motivo_rechazo=motivo_glob)
            )
            continue

        # Requisito específico del producto (p.ej. credito_mujer -> sexo == F).
        if "requiere" in cfg:
            ok, desc = _evaluar_condicion(cfg["requiere"], features)
            disparadas.append(f"{prod}.requiere: {desc} -> {'ok' if ok else 'falla'}")
            if not ok:
                resultados.append(
                    ResultadoElegibilidad(prod, nombre, False, reglas_disparadas=disparadas,
                                          motivo_rechazo=f"requisito de producto: {desc}")
                )
                continue

        monto_max = _monto_producto(prod, cfg, features, disparadas)
        resultados.append(
            ResultadoElegibilidad(
                producto=prod,
                nombre=nombre,
                elegible=True,
                monto_min=cfg.get("monto_min"),
                monto_max=monto_max,
                plazo_meses=cfg.get("plazo_meses"),
                reglas_disparadas=disparadas,
            )
        )
    return resultados
