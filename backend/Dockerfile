# API image. Build from the project root:  docker build -f backend/Dockerfile .
FROM python:3.11-slim

# Set to true for dense retrieval (RETRIEVER=faiss); adds CPU-only PyTorch (~1 GB).
ARG WITH_EMBEDDINGS=false

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY backend/requirements*.txt backend/
RUN pip install -r backend/requirements.txt \
 && if [ "$WITH_EMBEDDINGS" = "true" ]; then \
      pip install torch --index-url https://download.pytorch.org/whl/cpu \
      && pip install -r backend/requirements-embeddings.txt; \
    fi

COPY backend/ backend/
COPY scripts/ scripts/

# Runtime data (SQLite DB) lives in a volume; the dataset and index are mounted.
RUN useradd --create-home app && mkdir -p data vector_db && chown -R app data vector_db
USER app

WORKDIR /app/backend
ENV DATABASE_URL=sqlite:////app/data/aarogya.db \
    DATASET_PATH=dataset/medquad.json

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
