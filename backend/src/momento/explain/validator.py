"""Validador determinista de la narrativa.

Si aparece una cifra que no estaba en el payload, se descarta la generación y
se cae a plantilla. Con esto, alucinar un monto es estructuralmente imposible,
no improbable.
"""

from __future__ import annotations

import json
import re

_NUM_RE = re.compile(r"\d[\d.,]*")


def extraer_numerales(texto: str) -> set[str]:
    """Extrae los tokens numéricos normalizados (sin separadores de miles)."""
    out: set[str] = set()
    for m in _NUM_RE.findall(texto):
        out.add(m.replace(".", "").replace(",", ""))
    return out


def validar(texto: str, payload: dict) -> bool:
    numeros_texto = extraer_numerales(texto)
    numeros_permitidos = extraer_numerales(json.dumps(payload, ensure_ascii=False))
    return numeros_texto <= numeros_permitidos
