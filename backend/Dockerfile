# MOMENTO — imagen para Cloud Run.
# Estrategia: DuckDB es embebido y las ofertas se precalculan, así que se
# hornea la base sintética dentro de la imagen en tiempo de build. El runtime
# solo sirve la API (lectura), por eso es una imagen mínima.

# ---- Etapa 1: carga los afiliados del Excel y corre el pipeline ----
FROM python:3.11-slim AS builder
WORKDIR /app
ENV PYTHONPATH=/app/src
COPY requirements-build.txt .
RUN pip install --no-cache-dir -r requirements-build.txt
COPY src ./src
COPY scripts ./scripts
COPY afiliados.xlsx .
# Los afiliados vienen del Excel; sus eventos se simulan para el timing.
RUN python scripts/cargar_excel.py afiliados.xlsx \
        --db data/synthetic/momento.duckdb --as-of 2026-07-01

# ---- Etapa 2: runtime mínimo (solo la API) ----
FROM python:3.11-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    MOMENTO_DB=/app/data/synthetic/momento.duckdb
RUN pip install --no-cache-dir "fastapi>=0.110" "uvicorn[standard]>=0.29" "duckdb>=0.10"
COPY src ./src
COPY --from=builder /app/data ./data
# Cloud Run inyecta PORT (8080 por defecto).
EXPOSE 8080
CMD ["sh", "-c", "uvicorn momento.api:app --host 0.0.0.0 --port ${PORT:-8080}"]
