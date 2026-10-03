# Lives at the REPOSITORY ROOT on purpose: Render / Koyeb / Hugging Face
# Spaces all default to `Dockerfile` at the root, so no path config is needed.
#   docker build -t ptransmit-api .
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc g++ libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app

# Ghana ADM1 boundaries used by the spatial endpoints (tracked in git)
COPY data/geo ./data/geo

# Point the app at the copied data; storage stays inside the container FS.
# (Koyeb free-tier storage is ephemeral: the SQLite DB re-seeds with clearly
# labelled demo data on every restart, which is fine for demonstrations.)
ENV PYTHONUNBUFFERED=1 \
    GEO_DIR=/app/data/geo \
    MODEL_DIR=/app/models

# Render/Koyeb inject $PORT (Render defaults to 10000); fall back to 8000 locally.
EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
