"""Generador sintético con verdad de campo y estados de trayectoria.

Generamos los datos con un proceso conocido, así medimos si el modelo lo
recupera:

1. Muestrear afiliados: categoría según distribución real; edad condicional a
   categoría; hogar desde CNPV; dirección de manzanas reales; empleador del RUES.
2. Asignar estado latente inicial in {formando_hogar, hijos_primaria,
   transicion_superior, consolidando, nido_vacio}.
3. Emitir 36 meses de eventos con tasas Poisson dependientes del estado, con
   estacionalidad real (matrículas nov–ene, turismo dic/jun, droguería plana).
4. Generar el evento de necesidad de crédito desde un hazard CONOCIDO.
5. Censurar por la derecha al final de la ventana de observación.

Estados por reglas sobre features de ventana móvil (rápido y auditable);
HMM categórico (hmmlearn) solo como objetivo secundario si sobra tiempo.
"""

from __future__ import annotations

ESTADOS = (
    "formando_hogar",
    "hijos_primaria",
    "transicion_superior",
    "consolidando",
    "nido_vacio",
)


def generar_sintetico(n: int, seed: int, meses: int = 36):
    """Genera n afiliados con `meses` de eventos y hazard conocido."""
    raise NotImplementedError


def estado_por_reglas(features_ventana) -> str:
    """Asigna estado de trayectoria por reglas sobre features de ventana móvil."""
    raise NotImplementedError
