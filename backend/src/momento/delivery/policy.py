"""Política de canal y hora de envío (Motor 4).

Matriz (grupo_edad × estado_trayectoria) con orden de preferencia de canal, más
la hora de envío desde un prior de respuesta por grupo de edad. Los canales
reales: portal/autogestión, SMS, correo, WhatsApp, redes, asesor asistido.
"""

from __future__ import annotations

from datetime import time

CANALES = ("portal", "sms", "correo", "whatsapp", "redes", "asesor")

# Orden de preferencia de canal por grupo de edad.
_PREFERENCIA = {
    "joven": ("whatsapp", "redes", "sms", "correo", "portal"),
    "adulto": ("whatsapp", "correo", "sms", "asesor", "portal"),
    "mayor": ("asesor", "correo", "sms", "whatsapp", "portal"),
}

# Prior de hora de mayor respuesta por grupo de edad.
_HORA = {"joven": time(19, 0), "adulto": time(12, 30), "mayor": time(10, 0)}


def grupo_edad(edad: int | None) -> str:
    if edad is None:
        return "adulto"
    if edad < 30:
        return "joven"
    if edad < 50:
        return "adulto"
    return "mayor"


def elegir_canal(edad: int | None, canales_disponibles: set[str] | None = None) -> str:
    """Devuelve el canal preferido disponible para el grupo de edad."""
    disponibles = canales_disponibles or set(CANALES)
    for canal in _PREFERENCIA[grupo_edad(edad)]:
        if canal in disponibles:
            return canal
    return "portal"


def elegir_hora(edad: int | None) -> time:
    """Hora de envío desde el prior de respuesta por grupo de edad."""
    return _HORA[grupo_edad(edad)]
