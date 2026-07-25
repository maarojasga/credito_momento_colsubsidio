"""Política de canal y hora de envío.

Política de canal: matriz (estado_trayectoria × grupo_edad × canales
disponibles) con orden de preferencia, más topes de frecuencia de contacto.
Canales: portal/autogestión, SMS, correo, WhatsApp, redes, asesor asistido.

Hora de envío: dentro de la ventana, día de semana y hora desde un prior de
respuesta por grupo de edad.
"""

from __future__ import annotations

from datetime import time

CANALES = ("portal", "sms", "correo", "whatsapp", "redes", "asesor")


def elegir_canal(estado_trayectoria: str, grupo_edad: str, canales_disponibles: set[str]) -> str:
    """Devuelve el canal preferido respetando disponibilidad y topes."""
    raise NotImplementedError


def elegir_hora(grupo_edad: str) -> time:
    """Hora de envío desde el prior de respuesta por grupo de edad."""
    raise NotImplementedError
