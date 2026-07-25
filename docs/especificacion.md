# MOMENTO — Especificación técnica
**Reto de Crédito · Hackathon Colsubsidio x 30X**
Versión 0.1 · ventana de construcción: 5 días

---

## 0. Principio de diseño

Tres separaciones no negociables. Todo lo demás es implementación.

1. **Las reglas duras no se aprenden.** Elegibilidad, cupos y capacidad de pago viven en un motor declarativo. El modelo solo ordena dentro del conjunto ya elegible. Un modelo nunca puede aprobar algo que la norma prohíbe.
2. **La señal es la unidad atómica, no la fila.** Nada entra al sistema como columna suelta: entra como registro con fuente, versión de proveedor, confianza, base legal y fecha de observación. Sin esto la trazabilidad es imposible de reconstruir después.
3. **La explicación se calcula, no se genera.** El aporte de cada señal sale de un scorecard aditivo. El LLM solo redacta lo que el scorecard ya decidió, y hay un validador que lo comprueba.

---

## 1. Modelo de datos

### 1.1 Entidades

Ver `backend/src/momento/schemas.py`. Entidades núcleo: `Subject`, `Signal`,
`Evento`, `Ventana`, `Contribucion`, `Oferta`, y el enum `BaseLegal`
(`publica`, `consentida`, `inferida`, `sintetica`).

### 1.2 Almacenamiento

**DuckDB**, archivo único, con la extensión `spatial`. Hace el *point-in-polygon*
contra las manzanas del DANE con índice R-tree sin levantar PostGIS, lee Parquet
y shapefile directo, y el repo entero es clonable sin infraestructura.

Tablas núcleo: `subjects`, `signals` (append-only), `eventos`, `person_period`,
`ofertas`, `manifests`.

La vista de features se materializa con **as-of join** contra una fecha de
referencia. El `as_of` no es opcional: sin él, entrenar el modelo de *timing* con
señales posteriores al evento es fuga de información garantizada.

```sql
CREATE VIEW features AS
SELECT subject_id, key, arg_max(value_num, observed_at) AS value
FROM signals
WHERE observed_at <= $as_of
  AND observed_at + INTERVAL (ttl_days) DAY >= $as_of
GROUP BY subject_id, key;
```

---

## 2. Motor 1 — Enriquecimiento

### 2.1 Contrato de proveedor

Ver `backend/src/momento/providers/base.py`. El registro resuelve dependencias
por **orden topológico** sobre el grafo `requires → provides`. Ejecución con
`asyncio` + semáforo por proveedor, timeout individual, *circuit breaker* tras N
fallos, y caché en disco con clave `(provider_id, version, hash(inputs))`.

Un proveedor que falla no tumba la corrida: emite cero señales y el vector de
features queda con el hueco explícito. El scorecard maneja faltantes como
categoría propia, nunca imputando la media.

### 2.2 Proveedores

| Proveedor | Entrada → salida | Fuente | Base legal |
|---|---|---|---|
| `geo.geocode` | dirección → lat, lon, precisión | Nominatim/OSM; fallback centroide UPZ | pública |
| `geo.manzana` | lat/lon → cod_manzana, sector, UPZ, localidad | Marco Geoestadístico Nacional, DANE | pública |
| `geo.censo` | manzana → NBI, % educación superior, hacinamiento, tenencia, tamaño de hogar | CNPV 2018 por manzana | pública |
| `geo.estrato` | lat/lon → estrato socioeconómico | Datos Abiertos Bogotá / Catastro | pública |
| `geo.poi` | lat/lon → conteo y distancia a colegios, IES, droguerías | SNIES, OSM | pública |
| `empleador.rues` | NIT o razón social → CIIU, tamaño, antigüedad, estado | RUES / Cámara de Comercio | pública |
| `mercado.tasas` | producto → tasa activa vigente | Superfinanciera | pública |
| `digital.correo` | correo → presencia, perfil profesional | **sintético en el demo** | sintética |
| `encuesta.donante` | perfil → carga financiera, tenencia, canasta | IEFIC + ENPH, imputación | inferida |

Verificar disponibilidad y formato de cada capa el día 1.

### 2.3 Presupuesto de latencia

Objetivo: **lote de 2.000 sujetos en menos de 3 minutos**, con todo lo
geoespacial precalculado. Nada geoespacial se resuelve por sujeto en línea: se
precalcula la tabla `manzana → features` completa para Bogotá (~45k manzanas) y
en corrida el enriquecimiento geo es un `JOIN`. La única llamada externa por
sujeto es la geocodificación, cacheada agresivamente.

---

## 3. Motor 1.5 — Imputación desde encuestas

### 3.1 Planteamiento

Registros **receptores** (afiliados) con X comunes; necesitamos Y que solo
existe en el **donante** (IEFIC). Fusión estadística clásica bajo el supuesto de
independencia condicional Y ⊥ Z | X. Hay que enunciarlo, no esconderlo.

- **X** (comunes): edad, sexo, decil de ingreso, composición del hogar, CIIU,
  localidad y estrato.
- **Y** (a imputar): carga financiera, tenencia por producto, canasta de gasto.

### 3.2 Método: predictive mean matching con hot-deck ponderado

1. Armonizar X entre donante y receptor.
2. Ajustar g(X) → Y_principal con pesos de expansión.
3. Predecir ŷ = g(X) en donante y receptor.
4. Estratificar exacto por (localidad × categoría); k=5 donantes más cercanos.
5. Sortear uno de los 5 proporcional al peso de expansión; copiar Y COMPLETO.
6. La dispersión entre los 5 es el intervalo de incertidumbre.

Hot-deck y no regresión: copiar el vector completo **preserva la estructura
conjunta** entre las Y. **Los pesos de expansión no son opcionales.**

### 3.3 Validación (holdout dentro del donante)

| Qué | Métrica | Umbral |
|---|---|---|
| Tenencia (binaria) | AUC + calibración (Brier) | AUC > 0.68 |
| Carga financiera | Cobertura del intervalo de 5 donantes | ≥ 80% |
| Distribución marginal | KS entre Y imputada e Y real | D < 0.10 |
| Estructura conjunta | ‖ΔR‖ vs baseline de regresiones independientes | menor que baseline |

### 3.4 Sesgo conocido, declarado

IEFIC es urbano y restringido a hogares bancarizados. Mitigaciones: raking a la
distribución de categorías de Colsubsidio; marcar celdas con soporte bajo (n<30)
como confianza reducida y propagarla al `Signal`; nunca usar una señal imputada
como restricción dura.

---

## 4. Motor 2 — La ventana

### 4.1 Generador sintético con verdad de campo

Generamos los datos con un proceso conocido para medir si el modelo lo recupera:
muestrear afiliados con distribuciones reales, asignar estado latente, emitir 36
meses de eventos con tasas Poisson dependientes del estado y estacionalidad real,
generar el evento de necesidad desde un hazard CONOCIDO, censurar por la derecha.

### 4.2 Estados de trayectoria

Estados **por reglas** sobre features de ventana móvil (rápido y auditable). HMM
categórico (`hmmlearn`) solo como objetivo secundario si sobra tiempo el día 3.

### 4.3 Modelo de riesgo en tiempo discreto

Formato **persona-periodo**: una fila por `(subject_id, producto, mes)`.

```
logit h(t | x) = α(t) + β' x(t)
```

`α(t)`: dummies de mes calendario + spline cúbico en antigüedad. `x(t)`:
covariables variables en el tiempo. Ajuste `statsmodels.GLM(Binomial())`, L2
leve. Devuelve hazard mensual calibrado con coeficientes leíbles como razones de
odds.

### 4.4 Extracción de la ventana

Ventana de dos meses (no un día — falsa precisión y frágil en vivo) en el punto
de mayor riesgo acumulado a 60 días.

### 4.5 Métrica de pitch

**Cobertura de eventos contra volumen de contacto**: *"capturamos ~60% de los
eventos usando ~20% de los contactos"*.

---

## 5. Motor 3 — Elegibilidad, scoring y explicación

### 5.1 Reglas duras, declarativas

Ver `backend/src/momento/rules/elegibilidad.yaml`. Motor pequeño y propio con
registro de cada regla disparada. Salida: conjunto elegible + `monto_max` por
producto. El scoring solo ordena dentro de ese conjunto.

### 5.2 Scorecard aditivo

`optbinning` (binning óptimo con WoE) → logística → puntos enteros. Aditivo por
construcción; los faltantes son un bin propio; la tabla de puntos es el artefacto
de auditoría que riesgo ya sabe leer. Las tres señales principales son los tres
aportes de mayor valor absoluto en puntos.

### 5.3 Narrativa restringida

El LLM recibe **solo** el payload de la decisión (producto, monto, plazo, las
tres señales con valor y puntos). Un validador determinista descarta cualquier
generación con una cifra ausente del payload y cae a plantilla. Alucinar un monto
es estructuralmente imposible, no improbable.

---

## 6. Motor 4 — Canal y entrega

Matriz `(estado_trayectoria × grupo_edad × canales_disponibles)` con orden de
preferencia y topes de frecuencia. Hora de envío desde un prior por grupo de
edad. Entrega por WhatsApp Cloud API (template message), SMTP de respaldo,
webhook para push. Clave de idempotencia `(subject_id, producto, ventana)`.

> **Riesgo operativo crítico:** las plantillas de WhatsApp requieren aprobación
> de Meta. **Enviar la plantilla a aprobación el día 1.**

---

## 7. Trazabilidad

Cada oferta emite un manifiesto JSON con *hash* de contenido (ver
`backend/src/momento/trace/manifest.py`): señales, reglas evaluadas, scorecard,
hazard/ventana, narrativa y entrega. Exportable como archivo descargable desde la
UI. Esto es lo que convierte el proyecto de demo a candidato de producción.

---

## 8. Stack y repositorio

Python 3.11 · DuckDB + `spatial` · Polars · GeoPandas · statsmodels ·
scikit-learn · optbinning · hmmlearn (opcional) · FastAPI · WhatsApp Cloud API.
Front en React sobre FastAPI (`frontend/`); Streamlit solo si el equipo es de
dos.

---

## 9. Plan de cinco días

| Día | Trabajo | Entregable verificable |
|---|---|---|
| **1** | Plantilla WhatsApp a aprobación. Schemas. Generador sintético. Descarga y armonización de IEFIC. Precálculo `manzana → features`. | 2.000 afiliados con 36 meses en DuckDB; donante armonizado; plantilla en revisión |
| **2** | Proveedores geo, empleador y mercado. DAG de enriquecimiento con caché. | Lote: 2.000 sujetos, ~40 señales, < 3 min |
| **3** | Imputación donante + notebook de validación. Panel persona-periodo + hazard + ventana. | Ventanas por sujeto y producto; validación §3.3 y métrica §4.5 |
| **4** | Reglas, scorecard, narrativa con validador, política de canal, envío real. UI operador y afiliado. | Tres perfiles end-to-end, mensaje real en el celular, manifiesto exportable |
| **5** | **Congelamiento de código.** Video de 2 min, cinco diapositivas, README. | Entregable subido con margen |

---

## 10. Registro de riesgos

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Plantilla WhatsApp no aprobada a tiempo | Se pierde el golpe final | Enviar día 1; correo y mock de push de respaldo |
| Nombres de variable IEFIC inconsistentes entre años | Medio día perdido | Fijar UN año y armonizar solo ese |
| Capas geo con rutas caídas | Bloquea el día 2 | Verificar y congelar copias en `data/raw` el día 1 |
| Límites de tasa en geocodificación | Lote lento | Caché por dirección; precálculo por manzana; fallback UPZ |
| Sobre-alcance en el HMM | Se come el día 4 | Estados por reglas como camino principal |
| Todo en vivo falla | Demo caído | Solo el envío corre en vivo; todo lo demás precalculado |

---

## 11. Definición de terminado

- [ ] Un lote de 2.000 documentos entra y sale enriquecido en < 3 minutos
- [ ] Cada señal tiene fuente, versión, confianza y base legal
- [ ] Ninguna señal proviene de un buró de crédito
- [ ] Las reglas de capacidad son declarativas y probadas con casos límite
- [ ] Tres perfiles producen tres productos, tres canales y tres fechas distintas
- [ ] Cada oferta expone sus tres señales principales con puntos y fuente
- [ ] La narrativa no puede contener una cifra ausente del payload
- [ ] Un WhatsApp real llega a un celular real
- [ ] El manifiesto de trazabilidad se descarga desde la UI
- [ ] El notebook de validación reproduce las métricas de §3.3 y §4.5
