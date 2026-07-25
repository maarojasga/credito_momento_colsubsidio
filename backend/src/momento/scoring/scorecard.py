"""Scorecard aditivo (bins con puntos enteros).

Aditivo por construcción, no una aproximación posterior. Los faltantes son un
bin propio con sus propios puntos, sin imputación. La tabla de puntos es el
artefacto de auditoría que el área de riesgo ya sabe leer.

En producción los cortes se ajustan con `optbinning` (WoE óptimo). Aquí los
bins son de experto para el demo; cambiar a optbinning es un reemplazo local de
`_TABLA`. Las tres señales principales son los tres aportes de mayor |puntos|:
aritmética sobre la decisión real, no una heurística.
"""

from __future__ import annotations

from momento.schemas import Contribucion

PUNTAJE_BASE = 500

# feature -> lista de bins (limite_superior_exclusivo, puntos, etiqueta).
# El último bin usa None como límite (captura el resto). "__missing__" aparte.
_TABLA: dict[str, dict] = {
    "ingreso_smmlv": {
        "bins": [(2, 10, "<2 SMMLV"), (4, 30, "2-4"), (6, 50, "4-6"), (None, 70, ">=6")],
        "missing": 0,
    },
    "antiguedad_empleo_meses": {
        "bins": [(6, -30, "<6m"), (24, 10, "6-24m"), (60, 35, "24-60m"), (None, 55, ">=60m")],
        "missing": -10,
    },
    "estrato": {
        "bins": [(3, 5, "1-2"), (4, 20, "3"), (5, 35, "4"), (None, 50, "5-6")],
        "missing": 0,
    },
    "carga_financiera": {
        "bins": [(0.25, 40, "baja"), (0.32, 15, "media-baja"), (0.40, -10, "media-alta"),
                 (None, -35, "alta")],
        "missing": 0,
    },
    "tenencia_tc": {
        "bins": [(0.30, 0, "baja"), (0.60, 10, "media"), (None, 20, "alta")],
        "missing": 0,
    },
    "edad": {
        "bins": [(25, 0, "18-24"), (45, 20, "25-44"), (60, 25, "45-59"), (None, 10, ">=60")],
        "missing": 0,
    },
}


def _puntos_bin(feature: str, valor) -> tuple[int, str]:
    cfg = _TABLA[feature]
    if valor is None:
        return cfg["missing"], "faltante"
    for limite, puntos, etiqueta in cfg["bins"]:
        if limite is None or valor < limite:
            return puntos, etiqueta
    return cfg["bins"][-1][1], cfg["bins"][-1][2]


class Scorecard:
    version = "sc-0.1"

    def score(self, features_sub: dict) -> tuple[int, list[Contribucion]]:
        """features_sub: {feature: {value, source_id, ...}}.

        Devuelve (puntos_totales, aportes por señal en puntos).
        """
        aportes: list[Contribucion] = []
        total = PUNTAJE_BASE
        for feature in _TABLA:
            info = features_sub.get(feature)
            valor = info["value"] if info else None
            puntos, _etiqueta = _puntos_bin(feature, valor)
            total += puntos
            aportes.append(Contribucion(
                key=feature,
                value=valor if valor is not None else "faltante",
                puntos=puntos,
                source_id=info["source_id"] if info else "n/a",
            ))
        return total, aportes

    def top_senales(self, aportes: list[Contribucion], n: int = 3) -> list[Contribucion]:
        """Los n aportes de mayor valor absoluto en puntos."""
        return sorted(aportes, key=lambda c: abs(c.puntos), reverse=True)[:n]
