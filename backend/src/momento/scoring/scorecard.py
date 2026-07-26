"""Scorecard aditivo (bins con puntos enteros).

Aditivo por construcción, no una aproximación posterior. Los faltantes son un
bin propio con sus propios puntos, sin imputación. La tabla de puntos es el
artefacto de auditoría que el área de riesgo ya sabe leer.

Dos tablas conviven con la MISMA estructura y los MISMOS cortes:
  - la tabla EXPERTA (`_TABLA`, campeón por defecto), puntos puestos a mano;
  - una tabla APRENDIDA (retador), cuyos puntos salen de WoE + regresión
    logística en el Laboratorio de Crédito y que, si se promueve, reemplaza a la
    experta en el pipeline.

Como solo cambian los puntos (no los cortes), campeón y retador son comparables
señal por señal y ambos se puntúan con `_puntos_bin`.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

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

# Cortes canónicos por feature (compartidos por campeón y retador).
CORTES: dict[str, list] = {f: [b[0] for b in cfg["bins"]] for f, cfg in _TABLA.items()}
ETIQUETAS: dict[str, list[str]] = {f: [b[2] for b in cfg["bins"]] for f, cfg in _TABLA.items()}
FEATURES: list[str] = list(_TABLA)


def _puntos_bin(tabla: dict, feature: str, valor) -> tuple[int, str]:
    cfg = tabla[feature]
    if valor is None:
        return cfg["missing"], "faltante"
    for limite, puntos, etiqueta in cfg["bins"]:
        if limite is None or valor < limite:
            return puntos, etiqueta
    return cfg["bins"][-1][1], cfg["bins"][-1][2]


def _ruta_promovido() -> Path:
    """Ubicación del scorecard promovido, junto a la base de datos."""
    db = os.environ.get("MOMENTO_DB", "data/synthetic/momento.duckdb")
    return Path(db).resolve().parent / "scorecard_promovido.json"


class Scorecard:
    def __init__(self, tabla: dict | None = None, version: str = "sc-experto-0.1"):
        self.tabla = tabla if tabla is not None else _TABLA
        self.version = version

    @classmethod
    def experto(cls) -> "Scorecard":
        return cls(_TABLA, "sc-experto-0.1")

    @classmethod
    def en_produccion(cls) -> "Scorecard":
        """La que usa el pipeline: la promovida si existe, si no la experta."""
        ruta = _ruta_promovido()
        if ruta.exists():
            data = json.loads(ruta.read_text())
            tabla = _tabla_desde_json(data["tabla"])
            return cls(tabla, data.get("version", "sc-aprendido"))
        return cls.experto()

    def score(self, features_sub: dict) -> tuple[int, list[Contribucion]]:
        """features_sub: {feature: {value, source_id, ...}}.

        Devuelve (puntos_totales, aportes por señal en puntos).
        """
        aportes: list[Contribucion] = []
        total = PUNTAJE_BASE
        for feature in self.tabla:
            info = features_sub.get(feature)
            valor = info["value"] if info else None
            puntos, _etiqueta = _puntos_bin(self.tabla, feature, valor)
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


def _tabla_desde_json(bins_por_feature: dict) -> dict:
    """Reconstruye la estructura interna (con tuplas y None) desde JSON."""
    tabla: dict[str, dict] = {}
    for feature, cfg in bins_por_feature.items():
        bins = [(None if lim is None else float(lim), int(pts), et)
                for lim, pts, et in cfg["bins"]]
        tabla[feature] = {"bins": bins, "missing": int(cfg["missing"])}
    return tabla


def tabla_a_json(tabla: dict) -> dict:
    """Serializa una tabla de puntos a JSON (None -> null)."""
    return {
        feature: {
            "bins": [[lim, pts, et] for lim, pts, et in cfg["bins"]],
            "missing": cfg["missing"],
        }
        for feature, cfg in tabla.items()
    }
