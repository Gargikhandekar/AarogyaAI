FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ ./backend/
COPY dataset/ ./dataset/
COPY vector_db/ ./vector_db/
COPY scripts/ ./scripts/

WORKDIR /app/backend

ENV PYTHONPATH=/app/backend
ENV DATABASE_URL=sqlite:///./aarogya.db
ENV DATASET_PATH=/app/dataset/medquad_sample.json
ENV FAISS_INDEX_PATH=/app/vector_db/faiss_index

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
