"""Redacción de la narrativa por el LLM (restringida al payload).

El LLM solo redacta lo que el scorecard ya decidió. Si la generación no pasa
el validador determinista, se cae a plantilla.
"""

from __future__ import annotations


def generar_narrativa(payload: dict) -> str:
    """Redacta la razón de la oferta a partir del payload de decisión."""
    raise NotImplementedError


def plantilla_fallback(payload: dict) -> str:
    """Narrativa de respaldo, garantizada libre de cifras ajenas al payload."""
    raise NotImplementedError
