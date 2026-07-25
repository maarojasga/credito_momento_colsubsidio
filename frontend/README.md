# MOMENTO — Frontend

Demo visual del motor de crédito. React consumiendo la API FastAPI del
`backend/`.

> En este reto la calidad visual del demo es parte de la calificación. React
> sobre FastAPI cuando hay front en el equipo; Streamlit solo si el equipo es
> de dos.

## Stack

React 18 · Vite · TypeScript.

## Dos vistas

| Vista | Ruta | Para quién | Qué muestra |
|---|---|---|---|
| **Operador** | `/operador` | Área de riesgo / negocio | Lote de sujetos, ventana por sujeto, tres señales con puntos y fuente, descarga del manifiesto de trazabilidad. |
| **Afiliado** | `/afiliado/:subjectId` | El afiliado | La oferta (producto, monto, plazo), la ventana, el canal y la narrativa validada. |

## Identidad de marca

Tokens en `src/styles/theme.css` (Colsubsidio):

- amarillo `#ffd000` — acentos, resaltados, CTA
- azul `#0067b1` — encabezados, estructura, badges de canal
- grafito `#575756` — texto

## Estructura

```
frontend/
├── package.json · vite.config.ts · tsconfig.json · index.html
└── src/
    ├── main.tsx · App.tsx        # router (/operador, /afiliado/:id)
    ├── api/client.ts             # cliente de la API FastAPI
    ├── types.ts                  # espejo de las respuestas del backend
    ├── utils.ts                  # formato de moneda, etiquetas de señales
    ├── styles/theme.css          # sistema de diseño Colsubsidio
    ├── pages/
    │   ├── OperadorView.tsx       # KPIs + métrica de pitch + tabla de ofertas
    │   └── AfiliadoView.tsx       # oferta + ventana + señales + trazabilidad
    └── components/
        ├── Logo.tsx · AppBar.tsx
        ├── CoberturaChart.tsx     # cobertura de eventos vs volumen de contacto
        ├── VentanaChart.tsx       # línea de tiempo con la ventana de 60 días
        ├── SenalesTop.tsx         # las tres señales con puntos y fuente
        └── ManifestDownload.tsx   # descarga del manifiesto de trazabilidad
```

## Correr

```bash
cd frontend
npm install
npm run dev
```

La API se espera en `http://localhost:8000` (configurable con `VITE_API_URL`).
