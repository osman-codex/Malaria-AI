# Lives at the REPOSITORY ROOT on purpose: Render / Koyeb / Hugging Face
# Spaces all default to `Dockerfile` at the root, so no path config is needed.
#   docker build -t ptransmit-api .
#
# One image serves EVERYTHING: FastAPI on /api/*, built React UI at /.

# ---- Stage 1: build the React frontend ----------------------------------
FROM node:20-slim AS web
WORKDIR /web
# No package-lock.json in the repo, so npm install (not npm ci)
COPY frontend/package.json ./
RUN npm install --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

# ---- Stage 2: API + built UI --------------------------------------------
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

# main.py resolves the UI at <parents[2]>/frontend/dist == /frontend/dist
COPY --from=web /web/dist /frontend/dist

# Storage stays inside the container FS. Free tiers are ephemeral: the SQLite
# DB re-seeds with clearly labelled demo data on every restart (fine for demos).
# PORT: HF Spaces expects 7860 (default below); Render/others override at runtime.
ENV PYTHONUNBUFFERED=1 \
    GEO_DIR=/app/data/geo \
    MODEL_DIR=/app/models \
    PORT=7860

EXPOSE 7860
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
