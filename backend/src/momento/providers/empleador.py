"""Proveedor de empleador (Motor 1).

  empleador.rues  NIT o razón social -> CIIU, tamaño, antigüedad, estado
                  Fuente: RUES / Cámara de Comercio.  Base legal: pública.
"""

from __future__ import annotations

from momento.providers.base import Context
from momento.schemas import Signal, Subject


class EmpleadorRues:
    id = "empleador.rues"
    version = "0.1.0"

    def requires(self) -> set[str]:
        return {"empleador.nit"}

    def provides(self) -> set[str]:
        return {"empleador.ciiu", "empleador.tamano", "empleador.antiguedad"}

    async def fetch(self, subject: Subject, ctx: Context) -> list[Signal]:
        raise NotImplementedError
