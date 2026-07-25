# Despliegue — Backend en GCP (Cloud Run) · Frontend en Vercel

Arquitectura: el backend es FastAPI con **DuckDB embebido** (un solo archivo,
sin servidor de base de datos aparte) y las ofertas se **precalculan**. Por eso
la base sintética se hornea dentro de la imagen en tiempo de build, y el runtime
solo sirve lectura. El frontend es un SPA de Vite que consume la API.

```
Vercel (frontend estático)  ──/api/*──►  Cloud Run (FastAPI + DuckDB en la imagen)
```

---

## 0. Todo desde Cloud Shell (recomendado)

Cloud Shell (icono `>_` arriba a la derecha en console.cloud.google.com) ya trae
`gcloud`, `git`, `docker` y `node`. El deploy usa **Cloud Build**, así que no
necesitas Docker local.

```bash
# 1. Proyecto
gcloud config set project TU_PROJECT_ID

# 2. Traer el código (si el repo es privado, autentícate antes: gh auth login)
git clone https://github.com/maarojasga/credito_momento_colsubsidio.git
cd credito_momento_colsubsidio
git checkout claude/folder-structure-front-back-vv7d6w

# 3. Habilitar servicios (una sola vez por proyecto)
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com

# 4. Desplegar el backend (Cloud Build compila el Dockerfile)
cd backend
gcloud run deploy momento-api \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 512Mi --port 8080
#   Si pregunta por crear un repo de Artifact Registry, responde "y".
#   Al terminar imprime la Service URL: https://momento-api-XXXX-uc.a.run.app

# 5. Probar
SERVICE_URL=$(gcloud run services describe momento-api --region us-central1 --format='value(status.url)')
curl "$SERVICE_URL/health"
curl "$SERVICE_URL/stats"
```

### Frontend desde el mismo Cloud Shell

**Opción A — Vercel CLI** (necesitas un token de vercel.com/account/tokens):

```bash
cd ../frontend
sed -i "s#https://momento-api-XXXXXXXX-uc.a.run.app#$SERVICE_URL#" vercel.json
npx vercel --prod --token TU_TOKEN_VERCEL --yes
```

**Opción B — todo en GCP con Firebase Hosting** (sin salir de Google):

```bash
cd ../frontend
npm install
echo "VITE_API_URL=$SERVICE_URL" > .env.production   # CORS ya está abierto
npm run build
npx firebase-tools login --no-localhost
npx firebase-tools init hosting   # public: dist · SPA: sí · no sobreescribir index.html
npx firebase-tools deploy --only hosting
```

Con Firebase el navegador va directo a Cloud Run (usa CORS, ya habilitado); con
Vercel queda en el mismo origen vía el proxy de `vercel.json`.

---

## 1. Backend en Cloud Run

Archivos ya incluidos: `backend/Dockerfile` (multi-stage), `backend/.dockerignore`,
`backend/requirements-build.txt`.

### Requisitos una sola vez

```bash
gcloud auth login
gcloud config set project TU_PROJECT_ID
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com
```

### Desplegar

Desde `backend/` (Cloud Run detecta el `Dockerfile` automáticamente):

```bash
cd backend
gcloud run deploy momento-api \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --port 8080
```

Al terminar imprime la URL del servicio, p.ej.
`https://momento-api-XXXXXXXX-uc.a.run.app`. Verifícala:

```bash
curl https://momento-api-XXXXXXXX-uc.a.run.app/health
curl https://momento-api-XXXXXXXX-uc.a.run.app/stats
```

**Notas**
- El build corre `seed_synthetic.py` + `build_ofertas.py`, así que la imagen ya
  trae las 1.908 ofertas y sus manifiestos. Para regenerar con otros datos, vuelve
  a desplegar (o parametriza el `--n`/`--seed`/`--as-of` en el Dockerfile).
- La API abre DuckDB en **read_only**; el filesystem de solo lectura de Cloud Run
  no es problema.
- CORS ya está abierto (`allow_origins=["*"]`), pero con el proxy de Vercel (paso 2)
  el frontend queda en el mismo origen y ni siquiera se usa CORS.
- Escala a cero: sin tráfico no cobra. El primer request tras inactividad tiene
  cold start (~1-2 s).

---

## 2. Frontend en Vercel

Archivo ya incluido: `frontend/vercel.json` (proxy `/api` → Cloud Run + fallback SPA).

### Paso previo: pon tu URL de Cloud Run

Edita `frontend/vercel.json` y reemplaza el placeholder por la URL real:

```json
{ "source": "/api/:path*", "destination": "https://momento-api-XXXXXXXX-uc.a.run.app/:path*" }
```

Así el cliente (que llama a `/api/...`) llega a la API sin CORS y en el mismo origen.

### Desplegar (opción CLI)

```bash
cd frontend
npm i -g vercel
vercel --prod
```

Cuando pregunte, define **Root Directory = `frontend`** (o córrelo desde esa carpeta).
Vercel detecta Vite: build `npm run build`, salida `dist`.

### Desplegar (opción panel web)

1. Importa el repo en vercel.com.
2. **Root Directory:** `frontend`.
3. Framework: Vite (autodetectado). Build `npm run build`, Output `dist`.
4. Deploy.

### Alternativa sin editar vercel.json (variable de entorno)

Si prefieres no usar el proxy, borra el primer rewrite y define en Vercel la
variable `VITE_API_URL` con la URL de Cloud Run. El cliente la toma
automáticamente (`src/api/client.ts`). En ese caso el navegador va directo a
Cloud Run y usa CORS (ya está abierto).

---

## 3. Comprobación end-to-end

1. Abre la URL de Vercel → debe cargar la vista **operador** con KPIs y la tabla.
2. Clic en una fila → vista **afiliado** con oferta, ventana y trazabilidad.
3. "Descargar manifiesto" → baja el JSON de trazabilidad.

Si la tabla sale vacía y aparece el aviso amarillo, el frontend no está llegando
a la API: revisa la URL en `vercel.json` (o `VITE_API_URL`) y que `/api/health`
responda desde el dominio de Vercel.

---

## Costos y límites (demo)

- **Cloud Run**: capa gratuita generosa; con escala a cero el costo de un demo es
  prácticamente nulo.
- **Vercel**: plan Hobby gratuito sirve el SPA sin problema.
- Para el envío **real** por WhatsApp (Motor 4) se necesita la plantilla aprobada
  por Meta y credenciales — eso corre aparte y no bloquea el despliegue del demo.
