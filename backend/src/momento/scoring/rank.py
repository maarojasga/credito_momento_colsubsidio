"""Ranking de productos elegibles y monto sugerido.

El scoring SOLO ordena dentro del conjunto que las reglas duras declararon
elegible. La afinidad de producto combina perfil del afiliado y estado de
trayectoria; el monto sugerido respeta el `monto_max` de las reglas.
"""

from __future__ import annotations

from momento.rules.engine import ResultadoElegibilidad

# Afinidad base por producto según estado de trayectoria (§4.2).
_AFINIDAD_ESTADO = {
    "transicion_superior": {"libranza": 0.4, "cupo_rotativo": 0.2},
    "formando_hogar": {"cupo_rotativo": 0.3, "credito_mujer": 0.2},
    "hijos_primaria": {"cupo_rotativo": 0.2, "rotativo_seguros_impuestos": 0.2},
    "consolidando": {"libranza": 0.3},
    "nido_vacio": {"rotativo_seguros_impuestos": 0.2},
}


def _afinidad(producto: str, feats: dict, estado: str) -> float:
    score = _AFINIDAD_ESTADO.get(estado, {}).get(producto, 0.0)
    if producto == "libranza" and feats.get("contrato_indefinido"):
        score += 0.3
    if producto == "credito_mujer" and feats.get("categoria") in ("A", "B"):
        score += 0.3
    if producto == "cupo_rotativo":
        score += 0.1  # producto general, siempre razonable
    return score


def _monto_sugerido(res: ResultadoElegibilidad, feats: dict) -> int:
    ingreso = feats.get("ingreso_mensual") or 0
    tope = res.monto_max or res.monto_min or 150000
    piso = res.monto_min or 150000
    objetivo = round(ingreso * 1.2 / 50000) * 50000
    return int(max(piso, min(tope, objetivo)))


def elegir_producto(elegibles: list[ResultadoElegibilidad], feats: dict, estado: str
                    ) -> tuple[ResultadoElegibilidad, int] | None:
    """Devuelve (producto_elegido, monto_sugerido) o None si no hay elegibles."""
    candidatos = [r for r in elegibles if r.elegible]
    if not candidatos:
        return None
    mejor = max(candidatos, key=lambda r: (_afinidad(r.producto, feats, estado), r.monto_max or 0))
    return mejor, _monto_sugerido(mejor, feats)
