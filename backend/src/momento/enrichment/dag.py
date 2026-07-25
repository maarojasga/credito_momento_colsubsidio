"""Resolución de dependencias entre proveedores por orden topológico.

El registro construye el grafo `requires -> provides` y ejecuta los proveedores
en orden. Ejecución con asyncio + semáforo por proveedor, timeout individual,
circuit breaker tras N fallos.

Objetivo de latencia: lote de 2.000 sujetos en menos de 3 minutos, con todo lo
geoespacial precalculado.
"""

from __future__ import annotations

from momento.providers.base import Context, SignalProvider
from momento.schemas import Signal, Subject


class ProviderRegistry:
    def __init__(self) -> None:
        self._providers: list[SignalProvider] = []

    def register(self, provider: SignalProvider) -> None:
        self._providers.append(provider)

    def topological_order(self) -> list[SignalProvider]:
        """Ordena por el grafo requires -> provides. Levanta si hay ciclo."""
        raise NotImplementedError

    async def run(self, subject: Subject, ctx: Context) -> list[Signal]:
        """Ejecuta el DAG para un sujeto y devuelve todas las señales."""
        raise NotImplementedError
