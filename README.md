# MOMENTO

**Reto de Crédito · Hackathon Colsubsidio x 30X** · ventana de construcción: 5 días

Motor de crédito sin buró: enriquece afiliados con señales trazables, predice
*cuándo* aparece la necesidad de crédito, ordena productos elegibles con un
scorecard aditivo y entrega la oferta por el canal correcto — todo auditable.

## Estructura del repo

```
credito_momento_colsubsidio/
├── backend/    # Motor Python (FastAPI · DuckDB · statsmodels · optbinning)
├── frontend/   # Demo React (vista operador + vista afiliado)
└── docs/        # Especificación técnica
```

- **[`backend/`](backend/README.md)** — los cuatro motores: enriquecimiento,
  imputación desde encuestas, la ventana (hazard en tiempo discreto),
  elegibilidad + scorecard + narrativa validada, y canal/entrega.
- **[`frontend/`](frontend/README.md)** — demo visual que consume la API.
- **[`docs/especificacion.md`](docs/especificacion.md)** — la spec completa (v0.1).

## Principios de diseño (no negociables)

1. **Las reglas duras no se aprenden.** El modelo solo ordena dentro del
   conjunto ya elegible.
2. **La señal es la unidad atómica, no la fila.** Fuente, versión, confianza,
   base legal y fecha en cada dato.
3. **La explicación se calcula, no se genera.** Scorecard aditivo; el LLM solo
   redacta lo que ya se decidió, con validador determinista.

## Estado

Pipeline **end-to-end funcional** sobre datos sintéticos (no hay dataset real de
afiliados; ver `docs/especificacion.md` §4.1):

- ✅ Generador sintético con verdad de campo → DuckDB (2.000 sujetos, ~470k eventos)
- ✅ Enriquecimiento: señales con fuente, versión, confianza y base legal
- ✅ Hazard en tiempo discreto (recupera la verdad de campo) + ventana de 60 días
- ✅ Reglas duras declarativas + scorecard aditivo + narrativa validada
- ✅ Política de canal + manifiesto de trazabilidad descargable
- ✅ API FastAPI + frontend React con identidad Colsubsidio (operador + afiliado)

Métrica de pitch obtenida: **contactando el 20% capturamos el 75%** de las
necesidades reales de crédito.

Pendiente de conectar a fuentes reales (día 1 del plan): capas geo (DANE, catastro),
RUES, microdato IEFIC y el envío en vivo por WhatsApp (plantilla a aprobación de Meta).

## Arrancar

```bash
# Backend — datos + pipeline + API
cd backend && pip install -e .
PYTHONPATH=src python scripts/seed_synthetic.py     # datos sintéticos en DuckDB
PYTHONPATH=src python scripts/build_ofertas.py      # precálculo de ofertas
PYTHONPATH=src uvicorn momento.api:app --reload     # API en :8000

# Frontend (en otra terminal)
cd frontend && npm install && npm run dev           # UI en :5173 (proxy a :8000)
```
