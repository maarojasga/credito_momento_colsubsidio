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
