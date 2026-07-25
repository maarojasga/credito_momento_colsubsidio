"""Proveedor de huella digital (Motor 1).

  digital.correo  correo -> presencia en plataformas, perfil profesional
                  SINTÉTICO en el demo.  Base legal: sintetica.

Nunca entra a elegibilidad; solo puede aportar al ranking.
"""

from __future__ import annotations

from momento.providers.base import Context
from momento.schemas import Signal, Subject


class DigitalCorreo:
    id = "digital.correo"
    version = "0.1.0"

    def requires(self) -> set[str]:
        return {"correo"}

    def provides(self) -> set[str]:
        return {"digital.presencia", "digital.perfil_profesional"}

    async def fetch(self, subject: Subject, ctx: Context) -> list[Signal]:
        raise NotImplementedError
