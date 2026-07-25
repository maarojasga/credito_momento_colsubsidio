"""Contrato de proveedor de señales.

Un proveedor declara qué keys requiere y cuáles emite; el registro resuelve
dependencias por orden topológico sobre el grafo `requires -> provides`.

Un proveedor que falla NO tumba la corrida: emite cero señales y el vector de
features queda con el hueco explícito. El scorecard maneja faltantes como
categoría propia, nunca imputando la media.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from momento.schemas import BaseLegal, Signal, Subject


@dataclass
class Context:
    """Contexto de corrida: conexión a datos, caché, fecha de referencia."""

    as_of: str
    cache_dir: str


class SignalProvider(Protocol):
    id: str
    version: str
    base_legal: BaseLegal
    ttl_days: int
    timeout_s: float

    def requires(self) -> set[str]:
        """Keys de entrada que el proveedor consume."""
        ...

    def provides(self) -> set[str]:
        """Keys que el proveedor emite."""
        ...

    async def fetch(self, subject: Subject, ctx: Context) -> list[Signal]:
        """Devuelve las señales para el sujeto, o [] si falla."""
        ...
