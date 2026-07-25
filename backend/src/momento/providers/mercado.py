"""Proveedor de mercado (Motor 1).

  mercado.tasas  producto -> tasa activa vigente de mercado
                 Fuente: Superfinanciera.  Base legal: pública.
"""

from __future__ import annotations

from momento.providers.base import Context
from momento.schemas import Signal, Subject


class MercadoTasas:
    id = "mercado.tasas"
    version = "0.1.0"

    def requires(self) -> set[str]:
        return set()

    def provides(self) -> set[str]:
        return {"mercado.tasa_activa"}

    async def fetch(self, subject: Subject, ctx: Context) -> list[Signal]:
        raise NotImplementedError
