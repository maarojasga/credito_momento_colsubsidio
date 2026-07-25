"""Proveedor de encuesta / donante (Motor 1, alimentado por Motor 1.5).

  encuesta.donante  perfil -> carga financiera, tenencia por producto,
                    canasta de gasto.  Fuente: IEFIC + ENPH, imputación
                    estadística.  Base legal: inferida.

Las señales imputadas propagan su confianza (celdas con soporte bajo se marcan
como confianza reducida) y NUNCA se usan como restricción dura.
"""

from __future__ import annotations

from momento.providers.base import Context
from momento.schemas import Signal, Subject


class EncuestaDonante:
    id = "encuesta.donante"
    version = "0.1.0"

    def requires(self) -> set[str]:
        return {"categoria", "geo.localidad", "geo.estrato", "empleador.ciiu"}

    def provides(self) -> set[str]:
        return {"encuesta.carga_financiera", "encuesta.tenencia", "encuesta.canasta"}

    async def fetch(self, subject: Subject, ctx: Context) -> list[Signal]:
        raise NotImplementedError
