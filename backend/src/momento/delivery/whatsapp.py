"""Entrega por WhatsApp Cloud API (Meta) con template message.

Clave de idempotencia (subject_id, producto, ventana): sin ella, una corrida
repetida duplica envíos.

RIESGO OPERATIVO CRÍTICO: las plantillas requieren aprobación de Meta y la
revisión puede tardar horas o rebotar. Enviar la plantilla a aprobación el
día 1, antes de escribir una sola línea del modelo.
"""

from __future__ import annotations


def idempotency_key(subject_id: str, producto: str, ventana) -> str:
    return f"{subject_id}:{producto}:{ventana.inicio}:{ventana.fin}"


async def enviar_template(telefono: str, template: str, params: dict, idem_key: str) -> dict:
    """Envía el template message y devuelve el estado de entrega."""
    raise NotImplementedError
