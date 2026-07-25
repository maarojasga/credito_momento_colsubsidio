"""Motor de evaluación de reglas duras.

Pequeño y propio, con registro de cada regla disparada. Salida: conjunto
elegible + monto_max por producto. El scoring solo ordena dentro de ese
conjunto.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

RULES_PATH = Path(__file__).with_name("elegibilidad.yaml")


@dataclass
class ResultadoElegibilidad:
    producto: str
    elegible: bool
    monto_max: int | None = None
    reglas_disparadas: list[str] = field(default_factory=list)


def cargar_reglas(path: Path = RULES_PATH) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def evaluar(features: dict, reglas: dict | None = None) -> list[ResultadoElegibilidad]:
    """Evalúa todos los productos y devuelve el conjunto elegible con monto_max.

    Registra cada regla disparada para el manifiesto de trazabilidad.
    """
    raise NotImplementedError
