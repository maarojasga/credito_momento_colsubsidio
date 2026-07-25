"""Proveedores geoespaciales (Motor 1).

Nada geoespacial se resuelve por sujeto en línea. Se precalcula una tabla
`manzana -> features` completa para Bogotá (~45k manzanas) y en corrida el
enriquecimiento geo es un JOIN. La única llamada externa por sujeto es la
geocodificación, cacheada agresivamente por dirección normalizada.

Proveedores:
  geo.geocode  dirección -> lat, lon, precisión   (Nominatim/OSM; fallback UPZ)
  geo.manzana  lat/lon   -> cod_manzana, sector, UPZ, localidad  (DANE MGN)
  geo.censo    manzana   -> NBI, %educación sup., hacinamiento... (CNPV 2018)
  geo.estrato  lat/lon   -> estrato socioeconómico  (Catastro Bogotá)
  geo.poi      lat/lon   -> distancia a colegios, IES, droguerías (SNIES, OSM)
"""

from __future__ import annotations

from momento.providers.base import Context
from momento.schemas import Signal, Subject


class GeoGeocode:
    id = "geo.geocode"
    version = "0.1.0"

    def requires(self) -> set[str]:
        return {"direccion"}

    def provides(self) -> set[str]:
        return {"geo.lat", "geo.lon", "geo.precision"}

    async def fetch(self, subject: Subject, ctx: Context) -> list[Signal]:
        raise NotImplementedError


class GeoManzana:
    id = "geo.manzana"
    version = "0.1.0"

    def requires(self) -> set[str]:
        return {"geo.lat", "geo.lon"}

    def provides(self) -> set[str]:
        return {"geo.cod_manzana", "geo.upz", "geo.localidad"}

    async def fetch(self, subject: Subject, ctx: Context) -> list[Signal]:
        raise NotImplementedError


class GeoCenso:
    id = "geo.censo"
    version = "0.1.0"

    def requires(self) -> set[str]:
        return {"geo.cod_manzana"}

    def provides(self) -> set[str]:
        return {"geo.nbi", "geo.educacion_superior", "geo.hacinamiento"}

    async def fetch(self, subject: Subject, ctx: Context) -> list[Signal]:
        raise NotImplementedError
