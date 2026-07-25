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

## Arrancar

```bash
# Backend
cd backend && pip install -e . && uvicorn momento.api:app --reload

# Frontend (en otra terminal)
cd frontend && npm install && npm run dev
```
