"""Generador sintético con verdad de campo (§4.1).

Generamos los datos con un proceso CONOCIDO (ver `params.py`), así medimos si
el modelo lo recupera:

1. Muestrear afiliados: categoría según distribución real; edad, ingreso,
   sexo, antigüedad y hogar condicionales a la categoría.
2. Asignar estado latente inicial y evolucionarlo con una cadena de Markov
   conocida (la matriz de transición es un activo de pitch).
3. Emitir 36 meses de eventos con tasas Poisson dependientes del estado y
   estacionalidad real (matrículas nov–ene, turismo dic/jun, droguería plana).
4. Generar el evento de necesidad de crédito desde un hazard CONOCIDO, función
   del estado, del mes y del gasto reciente en educación.
5. Censurar por la derecha al final de la ventana de observación.

La salida es un `SyntheticDataset` con tres tablas listas para DuckDB:
`subjects`, `eventos` y el panel `person_period` (con el label ya puesto).
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta

import numpy as np

from momento.timing import params as P

ESTADOS = P.ESTADOS  # re-export por compatibilidad


@dataclass
class SyntheticDataset:
    subjects: list[dict] = field(default_factory=list)
    eventos: list[dict] = field(default_factory=list)
    person_period: list[dict] = field(default_factory=list)

    def resumen(self) -> dict:
        n = len(self.subjects)
        eventos_credito = sum(1 for r in self.person_period if r["evento"] == 1)
        return {
            "subjects": n,
            "eventos_servicio": len(self.eventos),
            "filas_person_period": len(self.person_period),
            "eventos_credito": eventos_credito,
            "tasa_evento": round(eventos_credito / n, 4) if n else 0.0,
        }


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + np.exp(-x))


def _add_months(d: date, months: int) -> date:
    m = d.month - 1 + months
    year = d.year + m // 12
    month = m % 12 + 1
    return date(year, month, 1)


def _subject_id(doc: int, seed: int) -> str:
    """Hash del documento, nunca el documento (schemas.Subject).

    Se sala con el seed para que cada corrida sea un universo de sujetos
    distinto.
    """
    return "sub_" + hashlib.sha256(f"{seed}:{doc}".encode()).hexdigest()[:16]


def _estado_inicial(edad: int, num_hijos: int, rng: np.random.Generator) -> str:
    """Heurística de estado inicial por ciclo de vida (edad × hijos)."""
    if num_hijos == 0:
        return "formando_hogar" if edad < 35 else "nido_vacio" if edad > 50 else "consolidando"
    if edad < 40:
        return "hijos_primaria"
    if edad <= 52:
        return "transicion_superior"
    return "nido_vacio"


def _muestrear_subject(doc: int, seed: int, rng: np.random.Generator) -> dict:
    categoria = P.CATEGORIAS[rng.choice(len(P.CATEGORIAS), p=P.P_CATEGORIA)]

    lo, hi = P.INGRESO_SMMLV_RANGO[categoria]
    # lognormal centrada en el rango, recortada a [lo, hi].
    ingreso_smmlv = float(np.clip(rng.uniform(lo, hi) * rng.lognormal(0, 0.12), lo, hi))
    ingreso_mensual = int(round(ingreso_smmlv * P.SMMLV, -3))

    edad = int(np.clip(rng.normal(P.EDAD_MEDIA[categoria], P.EDAD_SD), P.EDAD_MIN, P.EDAD_MAX))
    sexo = "F" if rng.random() < P.P_FEMENINO else "M"

    antiguedad = int(P.ANTIGUEDAD_MIN_MESES + rng.exponential(P.ANTIGUEDAD_MEDIA_MESES))
    contrato_indefinido = bool(rng.random() < P.P_CONTRATO_INDEFINIDO)

    # Hijos: más probables en edades intermedias.
    lam = 1.6 if 28 <= edad <= 50 else 0.5
    num_hijos = int(min(rng.poisson(lam), 5))

    localidad = P.LOCALIDADES[rng.integers(len(P.LOCALIDADES))]
    estrato = {"A": 2, "B": 3, "C": 4, "D": 5}[categoria]
    estrato = int(np.clip(estrato + rng.integers(-1, 2), 1, 6))

    return {
        "subject_id": _subject_id(doc, seed),
        "categoria": categoria,
        "edad": edad,
        "sexo": sexo,
        "ingreso_smmlv": round(ingreso_smmlv, 2),
        "ingreso_mensual": ingreso_mensual,
        "antiguedad_empleo_meses": antiguedad,
        "contrato_indefinido": contrato_indefinido,
        "num_hijos": num_hijos,
        "localidad": localidad,
        "estrato": estrato,
        "_estado_inicial": _estado_inicial(edad, num_hijos, rng),
    }


def _trayectoria_estados(estado0: str, meses: int, rng: np.random.Generator) -> list[str]:
    idx = {e: i for i, e in enumerate(P.ESTADOS)}
    trans = np.array(P.TRANSICION)
    estado = idx[estado0]
    salida = [P.ESTADOS[estado]]
    for _ in range(1, meses):
        estado = int(rng.choice(len(P.ESTADOS), p=trans[estado]))
        salida.append(P.ESTADOS[estado])
    return salida


def _eventos_y_periodos(sub: dict, estado0: str, rng: np.random.Generator,
                        meses: int, fecha_inicio: date) -> tuple[list[dict], list[dict]]:
    """Genera los eventos de servicio y las filas person-period de UN sujeto."""
    sid = sub["subject_id"]
    income_scale = float(np.clip(0.7 + 0.15 * sub["ingreso_smmlv"], 0.7, 2.5))
    estados = _trayectoria_estados(estado0, meses, rng)

    eventos: list[dict] = []
    edu_eventos_por_mes: list[int] = []
    for t in range(meses):
        mes_cal = (fecha_inicio.month - 1 + t) % 12
        tasas = P.TASA_BASE[estados[t]]
        edu_este_mes = 0
        for j, servicio in enumerate(P.SERVICIOS):
            rate = tasas[j] * P.ESTACIONALIDAD[servicio][mes_cal] * income_scale
            cnt = int(rng.poisson(rate))
            if servicio == "educacion":
                edu_este_mes = cnt
            for _ in range(cnt):
                monto = float(P.MONTO_MEDIO[servicio] * income_scale * rng.lognormal(0, 0.35))
                dia = int(rng.integers(0, 27))
                ts = datetime.combine(_add_months(fecha_inicio, t), datetime.min.time()) + timedelta(
                    days=dia, hours=int(rng.integers(8, 21))
                )
                eventos.append({
                    "subject_id": sid, "servicio": servicio, "categoria_servicio": servicio,
                    "monto": round(monto, -2), "ts": ts,
                })
        edu_eventos_por_mes.append(edu_este_mes)

    # --- Evento de necesidad de crédito desde el hazard conocido --------
    person_period: list[dict] = []
    for t in range(meses):
        edu_3m = sum(edu_eventos_por_mes[max(0, t - 2): t + 1])
        z = (edu_3m - 1.5) / 1.5  # estandarización de referencia fija
        mes_cal = (fecha_inicio.month - 1 + t) % 12
        logit = (
            P.HAZARD_INTERCEPTO
            + P.HAZARD_EFECTO_ESTADO[estados[t]]
            + P.HAZARD_EFECTO_MES[mes_cal]
            + P.HAZARD_BETA_EDUCACION * z
        )
        h = _sigmoid(logit)
        person_period.append({
            "subject_id": sid, "producto": "credito", "t_mes": t,
            "mes_calendario": mes_cal + 1, "estado": estados[t],
            "edu_eventos_3m": edu_3m, "hazard_real": round(float(h), 5), "evento": 0,
        })
        if rng.random() < h:
            person_period[-1]["evento"] = 1
            break  # censura por la derecha: no hay más filas tras el evento
    return eventos, person_period


def generar_eventos(subjects: list[dict], seed: int = 42, meses: int = 36,
                    fecha_inicio: date = date(2023, 7, 1)) -> tuple[list[dict], list[dict]]:
    """Genera eventos + person_period para una lista de sujetos dada.

    Sirve tanto para los sujetos sintéticos como para los que vienen de un Excel.
    Cada sujeto debe traer subject_id, ingreso_smmlv, edad y num_hijos. El estado
    inicial se toma de `_estado_inicial` si viene, o se deriva de edad y hogar.
    """
    rng = np.random.default_rng(seed)
    eventos: list[dict] = []
    person_period: list[dict] = []
    for sub in subjects:
        estado0 = sub.get("_estado_inicial") or _estado_inicial(
            int(sub.get("edad") or 40), int(sub.get("num_hijos") or 0), rng)
        e, p = _eventos_y_periodos(sub, estado0, rng, meses, fecha_inicio)
        eventos.extend(e)
        person_period.extend(p)
    return eventos, person_period


def generar_sintetico(
    n: int = 2000,
    seed: int = 42,
    meses: int = 36,
    fecha_inicio: date = date(2023, 7, 1),
) -> SyntheticDataset:
    """Muestrea `n` afiliados y genera sus eventos con un hazard conocido.

    Determinista dado `seed`. `fecha_inicio` fija la ventana de observación (no
    se usa la fecha de hoy, para reproducibilidad).
    """
    rng = np.random.default_rng(seed)
    subjects_full = [_muestrear_subject(doc, seed, rng) for doc in range(n)]
    eventos, person_period = generar_eventos(subjects_full, seed, meses, fecha_inicio)

    ds = SyntheticDataset()
    ds.subjects = [{k: v for k, v in s.items() if not k.startswith("_")} for s in subjects_full]
    ds.eventos = eventos
    ds.person_period = person_period
    return ds
