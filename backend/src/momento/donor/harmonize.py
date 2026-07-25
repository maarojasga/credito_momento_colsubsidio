"""Armonización de variables comunes X entre donante (IEFIC) y receptor.

X (comunes): edad, sexo, decil de ingreso derivado de la categoría,
composición del hogar, CIIU del empleador, localidad y estrato.

Fijar UN año de IEFIC y armonizar solo ese; el diccionario de variables se
revisa el día 1.
"""

from __future__ import annotations


def harmonize_donor(raw):
    """Lleva el donante a las mismas categorías y cortes que el receptor."""
    raise NotImplementedError


def harmonize_receptor(subjects):
    """Deriva X para los afiliados con los mismos cortes que el donante."""
    raise NotImplementedError
