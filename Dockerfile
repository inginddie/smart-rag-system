# Multi-stage build para optimizar el tamaño de la imagen
FROM python:3.11-slim as builder

# Instalar dependencias del sistema necesarias para compilación
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Configurar pip para mejor cacheo
ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

# Copiar requirements y instalar dependencias
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# Imagen de producción
FROM python:3.11-slim

# Metadatos
LABEL maintainer="RAG System" \
      description="Sistema RAG Avanzado con Gradio UI" \
      version="1.0"

# Variables de entorno
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/home/appuser/.local/bin:${PATH}" \
    DOCUMENTS_PATH=/app/data/documents \
    VECTOR_DB_PATH=/app/data/vector_db \
    TRACE_DB_PATH=/app/data/traces.db

# Instalar dependencias del sistema runtime
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Crear usuario no-root para seguridad
RUN useradd --create-home --shell /bin/bash appuser

# Copiar dependencias instaladas desde builder
COPY --from=builder /root/.local /home/appuser/.local

# Configurar directorio de trabajo
WORKDIR /app

# Copiar código fuente
COPY --chown=appuser:appuser . .

# Crear directorios necesarios
RUN mkdir -p data/documents data/vector_db logs && \
    chown -R appuser:appuser /app

# Cambiar a usuario no-root
USER appuser

# Exponer puertos
EXPOSE 7860 8000

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:7860 || exit 1

# Comando por defecto
CMD ["python", "main.py", "--mode", "ui", "--port", "7860"]
