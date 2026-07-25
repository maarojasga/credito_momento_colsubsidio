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
npx vercel --prod --token TU_TOKEN_VERCEL --yes \
  --build-env VITE_API_URL=$SERVICE_URL
```

El frontend llama directo a la API con esa URL (CORS ya está abierto). El
`vercel.json` solo trae el fallback SPA para React Router.

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

En ambos casos el navegador va directo a Cloud Run usando CORS (ya habilitado).

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
- CORS ya está abierto (`allow_origins=["*"]`), así que el frontend en Vercel
  puede llamar a la API directamente con `VITE_API_URL`.
- Escala a cero: sin tráfico no cobra. El primer request tras inactividad tiene
  cold start (~1-2 s).

---

## 2. Frontend en Vercel

Archivo ya incluido: `frontend/vercel.json` (solo el fallback SPA para React
Router). El frontend apunta a la API con la variable `VITE_API_URL`; el cliente
la toma automáticamente (`src/api/client.ts`) y, como el CORS del backend está
abierto, el navegador llama directo a Cloud Run.

### Panel web (UI)

1. **vercel.com → Add New → Project → Import** el repo `maarojasga/credito_momento_colsubsidio`.
2. **Root Directory:** `frontend` (clic en *Edit*; el proyecto no está en la raíz).
3. Framework: *Vite* (autodetectado). Build `npm run build`, Output `dist`.
4. **Environment Variables** → agrega `VITE_API_URL` = la URL de Cloud Run
   (`echo $SERVICE_URL`).
5. **Deploy.**

> El código vive en la rama `claude/folder-structure-front-back-vv7d6w` (aún no
> hay `main` con contenido). Si el deploy sale vacío, en **Settings → Git →
> Production Branch** pon esa rama y vuelve a desplegar; o mergea la rama a `main`.
>
> Las variables `VITE_` se inyectan en el **build**: si cambias `VITE_API_URL`,
> haz *Redeploy*.

### CLI (opción)

```bash
cd frontend
npx vercel --prod --build-env VITE_API_URL=https://momento-api-XXXX-uc.a.run.app
```

---

## 3. Comprobación end-to-end

1. Abre la URL de Vercel → debe cargar la vista **operador** con KPIs y la tabla.
2. Clic en una fila → vista **afiliado** con oferta, ventana y trazabilidad.
3. "Descargar manifiesto" → baja el JSON de trazabilidad.

Si la tabla sale vacía y aparece el aviso amarillo, el frontend no está llegando
a la API: revisa `VITE_API_URL` en Vercel (Settings → Environment Variables),
haz *Redeploy*, y confirma que `TU_URL/health` responde.

---

## Costos y límites (demo)

- **Cloud Run**: capa gratuita generosa; con escala a cero el costo de un demo es
  prácticamente nulo.
- **Vercel**: plan Hobby gratuito sirve el SPA sin problema.
- Para el envío **real** por WhatsApp (Motor 4) se necesita la plantilla aprobada
  por Meta y credenciales — eso corre aparte y no bloquea el despliegue del demo.
