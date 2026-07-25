# MOMENTO — Backend

Motor de crédito para el reto Colsubsidio x 30X. Python 3.11.

## Principios de diseño (no negociables)

1. **Las reglas duras no se aprenden.** Elegibilidad, cupos y capacidad de pago
   viven en un motor declarativo (`rules/`). El modelo solo ordena dentro del
   conjunto ya elegible.
2. **La señal es la unidad atómica, no la fila.** Todo entra como `Signal` con
   fuente, versión de proveedor, confianza, base legal y fecha de observación.
3. **La explicación se calcula, no se genera.** El aporte de cada señal sale de
   un scorecard aditivo; el LLM solo redacta y un validador lo comprueba.

## Stack

Python 3.11 · DuckDB + `spatial` · Polars · GeoPandas (solo preparación de
capas) · statsmodels · scikit-learn · optbinning · hmmlearn (opcional) ·
FastAPI · WhatsApp Cloud API.

## Estructura

```
backend/
├── pyproject.toml
├── data/{raw,donor,synthetic}/       # capas locales congeladas
├── src/momento/
│   ├── schemas.py                     # entidades pydantic v2
│   ├── providers/                     # Motor 1 — enriquecimiento
│   │   ├── base.py                    # Protocol SignalProvider
│   │   ├── geo.py  empleador.py  mercado.py  digital.py  encuesta.py
│   ├── enrichment/{dag,cache}.py      # orden topológico + caché en disco
│   ├── donor/{harmonize,match,validate}.py   # Motor 1.5 — imputación
│   ├── timing/{sequences,hazard,ventana}.py  # Motor 2 — la ventana
│   ├── rules/{elegibilidad.yaml,engine}.py   # Motor 3 — reglas duras
│   ├── scoring/{scorecard,rank}.py           # Motor 3 — scorecard aditivo
│   ├── explain/{contributions,narrative,validator}.py  # narrativa restringida
│   ├── delivery/{policy,whatsapp,email}.py   # Motor 4 — canal y entrega
│   ├── trace/manifest.py              # manifiesto de trazabilidad
│   └── api.py                         # FastAPI
├── notebooks/{01_donor,02_hazard,03_validacion}.ipynb
└── tests/
```

## Los cuatro motores

| Motor | Carpeta | Qué hace |
|---|---|---|
| 1 — Enriquecimiento | `providers/`, `enrichment/` | Resuelve señales por orden topológico `requires → provides`, con caché y circuit breaker. |
| 1.5 — Imputación | `donor/` | Fusión estadística IEFIC → afiliados vía predictive mean matching + hot-deck ponderado. |
| 2 — La ventana | `timing/` | Hazard en tiempo discreto (persona-periodo) → ventana de 60 días por sujeto. |
| 3 — Elegibilidad y scoring | `rules/`, `scoring/`, `explain/` | Reglas declarativas + scorecard aditivo + narrativa validada. |
| 4 — Canal y entrega | `delivery/` | Política de canal, hora de envío, WhatsApp/SMTP con idempotencia. |

## Correr

```bash
cd backend
pip install -e .
uvicorn momento.api:app --reload
```

## Datos sintéticos (Motor 2 — verdad de campo)

No hay dataset real de afiliados: la población, sus 36 meses de eventos y el
evento de necesidad de crédito se generan con un proceso **conocido**
(`timing/params.py`), para poder medir si el modelo lo recupera.

```bash
cd backend
PYTHONPATH=src python scripts/seed_synthetic.py --n 2000 --seed 42 \
    --out data/synthetic/momento.duckdb
```

Produce en DuckDB (~10 s, muy por debajo del presupuesto de 3 min):

- `subjects` — afiliados con categoría, ingreso, antigüedad, hogar, geo.
- `eventos` — ~470k eventos de servicio con estacionalidad real (matrículas
  nov–ene, turismo dic/jun, droguería plana).
- `person_period` — panel discreto `(subject_id, t_mes)` con el `hazard_real` y
  el label `evento`, listo para ajustar el modelo de tiempo discreto (§4.3).

Todo en `timing/params.py` es la verdad de campo: la matriz de transición de
estados, las tasas Poisson por servicio, la estacionalidad y los coeficientes
del hazard. Cambiar un número ahí cambia el mundo, no el modelo.

## Pipeline completo (precálculo de ofertas)

Una vez sembrados los datos, el pipeline corre los cuatro motores y precalcula
las ofertas + manifiestos. En vivo solo correría el envío del mensaje.

```bash
PYTHONPATH=src python scripts/build_ofertas.py \
    --db data/synthetic/momento.duckdb --as-of 2026-07-01
```

Encadena: enriquecimiento (señales con fuente/confianza/base legal) → hazard en
tiempo discreto + extracción de ventana → reglas duras → scorecard aditivo →
narrativa validada → política de canal → manifiesto de trazabilidad. Salida
típica (~19 s para 2.000 sujetos):

```
Enriquecimiento: 22,000 señales materializadas
Hazard ajustado sobre 44,283 filas person-period
Cobertura vs contacto (métrica de pitch §4.5):
  contactando 20% -> capturamos 75% de eventos
1,908 ofertas precalculadas · 92 no elegibles
```

## API

```bash
PYTHONPATH=src MOMENTO_DB=data/synthetic/momento.duckdb \
    uvicorn momento.api:app --reload
```

| Endpoint | Devuelve |
|---|---|
| `GET /health` | estado y ruta de la base |
| `GET /stats` | KPIs agregados (productos, canales, monto promedio) |
| `GET /metrics` | cobertura vs contacto (§4.5) y coeficientes del hazard |
| `GET /ofertas?limit&offset&producto` | lista paginada para el operador |
| `GET /subjects/{id}/oferta` | oferta del sujeto |
| `GET /subjects/{id}/manifest` | manifiesto de trazabilidad descargable |

## Puesta en marcha completa

```bash
cd backend && pip install -e .
PYTHONPATH=src python scripts/seed_synthetic.py     # 1. datos sintéticos
PYTHONPATH=src python scripts/build_ofertas.py      # 2. precálculo de ofertas
PYTHONPATH=src uvicorn momento.api:app --reload     # 3. API en :8000
pytest tests/                                        # (opcional) 14 tests
```
