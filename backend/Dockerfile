# MOMENTO — imagen para Cloud Run.
# La imagen arranca SIN datos: los afiliados se suben manualmente por la UI
# (POST /cargar-excel), que corre el pipeline en caliente y escribe la base en
# una ruta escribible (MOMENTO_DB, en /tmp por defecto).

FROM python:3.11-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src \
    MOMENTO_DB=/tmp/momento.duckdb \
    MOMENTO_PLANTILLA=/app/afiliados.xlsx

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src ./src
COPY afiliados.xlsx .

# Cloud Run inyecta PORT (8080 por defecto).
EXPOSE 8080
CMD ["sh", "-c", "uvicorn momento.api:app --host 0.0.0.0 --port ${PORT:-8080}"]
