# Build from the REPOSITORY ROOT so both backend/ and data/ are in context:
#   docker build -f backend/Dockerfile -t ptransmit-api .
#
# On Koyeb/Render set:
#   Dockerfile path: backend/Dockerfile
#   Build context / working directory: . (repo root)
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

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
