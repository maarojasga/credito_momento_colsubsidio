"""Entidades núcleo de MOMENTO (pydantic v2).

La señal es la unidad atómica del sistema: nada entra como columna suelta,
todo entra como registro con fuente, versión de proveedor, confianza, base
legal y fecha de observación.
"""

from __future__ import annotations

from datetime import date, datetime, time
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, EmailStr


class BaseLegal(StrEnum):
    PUBLICA = "publica"       # dato abierto o registro público
    CONSENTIDA = "consentida"  # el afiliado autorizó
    INFERIDA = "inferida"     # derivada estadísticamente, no observada
    SINTETICA = "sintetica"   # generada para el demo


class Subject(BaseModel):
    subject_id: str          # hash del documento, nunca el documento
    nombre: str | None = None
    correo: EmailStr | None = None
    direccion: str | None = None
    categoria: Literal["A", "B", "C", "D"]


class Signal(BaseModel):
    subject_id: str
    key: str                 # "geo.estrato", "encuesta.carga_financiera"
    value: float | int | str | bool
    value_type: Literal["num", "cat", "bool"]
    source_id: str           # "dane_mgn_2018", "iefic_2017"
    provider_id: str
    provider_version: str
    confidence: float        # [0, 1]
    base_legal: BaseLegal
    observed_at: datetime
    ingested_at: datetime
    ttl_days: int


class Evento(BaseModel):
    """Historial de uso de servicios."""

    subject_id: str
    servicio: str                    # "droguería", "recreación", "educación_continuada"
    categoria_servicio: str
    monto: float | None = None
    ts: datetime


class Ventana(BaseModel):
    subject_id: str
    producto: str
    inicio: date
    fin: date
    hazard_pico: float
    hazard_acumulado_ventana: float


class Contribucion(BaseModel):
    """Aporte de una señal al scorecard, en puntos enteros."""

    key: str
    value: float | int | str | bool
    puntos: int
    source_id: str


class Oferta(BaseModel):
    subject_id: str
    producto: str
    monto: int
    plazo_meses: int
    ventana: Ventana
    canal: str
    hora_envio: time
    puntos_scorecard: int
    top_senales: list[Contribucion]  # exactamente 3
    razon_texto: str
    manifest_hash: str
