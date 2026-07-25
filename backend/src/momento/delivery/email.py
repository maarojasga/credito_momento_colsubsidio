"""Entrega por correo (SMTP) — respaldo del canal WhatsApp."""

from __future__ import annotations


async def enviar_correo(destino: str, asunto: str, cuerpo: str, idem_key: str) -> dict:
    """Envía el correo y devuelve el estado de entrega."""
    raise NotImplementedError
