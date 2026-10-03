# 🇬🇭 P-TRANSMIT AI — Ghana Plasmodium Intelligence Platform

An open, locally-hostable research and surveillance **decision-support platform** for
*Plasmodium falciparum* transmission, genomic epidemiology and antimalarial drug
resistance in Ghana.

> **Disclaimer.** This platform is a research and surveillance decision-support system.
> Predictions are not diagnoses and should not independently determine patient treatment
> or public-health action.

---

## What it does (Phase-1 MVP)

| Module | Status | Description |
|---|---|---|
| Dashboard | ✅ | National overview: KPIs, choropleth, forecast, explanations, alerts |
| Transmission AI | ✅ | Supervised models (Random Forest, XGBoost, Ridge) predicting weekly cases per region at 1/2/4/8-week horizons, with temporal validation |
| Spatial Intelligence | ✅ | Interactive Ghana map (16 regions, geoBoundaries ADM1) with risk/observed/forecast layers |
| Forecasting | ✅ | Residual-based uncertainty intervals, assumptions stated |
| Explainable AI | ✅ | SHAP (when available) / perturbation-based per-region contributions — model behaviour, **not** causal effects |
| Early-warning alerts | ✅ | Relative, dataset-derived signals (level, trend, forecast) requiring human review |
| Data Explorer | ✅ | Upload CSV/TSV/XLSX/JSON/GeoJSON, data-quality report, column mapping, Ghana region fuzzy-matching |
| Model Laboratory | ✅ | Train/compare/manage models with full reproducibility provenance |
| Reports | ✅ | Markdown research report with limitations section |
| Plasmodium Genomics | 🧱 Scaffold | Marker catalogue + schema; **awaiting validated data** (no simulated results) |
| Drug Resistance | 🧱 Scaffold | Same governance: genetic marker ≠ phenotypic resistance; **awaiting validated data** |

Scientific governance enforced throughout:
- Synthetic demonstration data are always labelled and never mixed with real data.
- No invented resistance thresholds; interpretation requires researcher-supplied definitions.
- Risk categories are **relative** to the loaded dataset's own history.
- Metrics: MAE/RMSE primary for counts; R² reported for completeness only.
- Validation is strictly temporal (no random splitting of time-series).

---

## Architecture

```
backend/                 FastAPI + SQLAlchemy (SQLite default, PostgreSQL optional)
  app/api/               Routes + auth dependencies
  app/core/              Config, security (bcrypt + JWT)
  app/db/                ORM models (typed core + JSON analytical records)
  app/ml/                Transmission engine (features, training, forecasting, XAI)
  app/services/          Ingestion, synthetic demo data, alerts, genomics, reports
frontend/                React + TypeScript + Vite + Recharts + Leaflet
data/geo/                Ghana ADM1 boundaries (geoBoundaries gbOpen, CC-BY 4.0)
models/                  Trained joblib artifacts + provenance
scripts/                 fetch_geo_data.py, seed helper
backend/tests/           Pytest suite (22 tests)
```

## Quick start (local, no Docker)

Requirements: Python 3.11+, Node 18+.

```bash
# 1. Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --port 8000
# API:            http://127.0.0.1:8000/api/health
# Docs (Swagger): http://127.0.0.1:8000/docs

# 2. Frontend (development, hot reload)
cd frontend
npm install
npm run dev
# UI: http://localhost:5173

# 3. Or serve the built UI from the API
cd frontend && npm run build       # then restart uvicorn
# UI: http://127.0.0.1:8000/app
```

Default accounts (change immediately for any real deployment):
- `admin / ptransmit-admin` (admin)
- `demo / demo1234` (researcher)

## Demonstration workflow (5 minutes)

1. Sign in as `demo / demo1234`. The synthetic demo dataset is auto-loaded and labelled
   **DEMONSTRATION DATA — NOT REAL SURVEILLANCE DATA**.
2. **Model Laboratory** → select the demo dataset → **Train** (defaults: RF + XGBoost +
   Ridge, horizons 1/2/4/8 weeks). Takes ~1 minute.
3. **Dashboard** — map, KPIs, national forecast, per-region explanations appear.
4. **Transmission AI** — inspect held-out observed-vs-predicted curves and metrics.
5. **Alerts** → **Run alert scan** → review signals with evidence; acknowledge/dismiss.
6. **Reports** → generate and download the Markdown research report.
7. **Data Explorer** → upload your own CSV (see schema below).

## Real data: replacing the synthetic dataset

Upload a weekly surveillance table (CSV/XLSX) with columns (synonyms are auto-detected):

| Standard column | Purpose | Synonyms recognised |
|---|---|---|
| `region` | Ghana region (fuzzy-matched to the 16 canonical names) | region_name, admin1, adm1, province |
| `week_start_date` | ISO date of epi-week start | date, week_start, report_date |
| `malaria_cases` | Confirmed cases (count) | mal_cases, cases, confirmed_cases |
| `suspected_cases` | Tests conducted / suspected | tested, suspected |
| `test_positivity_rate` | % | positivity |
| `rainfall_mm`, `temperature_mean_c`, `humidity_pct`, `ndvi` | Environment | rainfall, temp, rh, evi, … |
| `population_illustrative` | Denominator/population weight | population, pop |

Then **Data Explorer** (upload) → **Model Laboratory** (train on the new dataset) →
dashboard/alerts/reports automatically reflect the real data. Suggested district-level
public sources: DHIMS-2 facility aggregate exports, CHIRPS rainfall, ERA5-Land temperature,
MODIS NDVI, WorldPop.

## Adding KCCR / P. falciparum genomic data

The genomic and resistance modules are deliberately modular. Upload a **variant table**
(CSV) with required columns `sample_id, gene, mutation, region, sample_date`
(plus optional district, genotype_quality, phenotyped, phenotype_value) as record type
`genomic` or `resistance`. The platform will compute descriptive counts and, where
sample identifiers exist, marker-positive frequencies per stratum — clearly labelled
as descriptive. No resistance interpretation happens without researcher-supplied
validated definitions. For direct KCCR dataset integration (DB/link), add a connector
module under `backend/app/services/` once a data-access agreement is in place.

## Hosting: one permanent link (frontend + backend together)

The root `Dockerfile` is multi-stage: it builds the React UI and serves it
from the site root next to `/api/*`, so **one URL opens the whole platform**
(no CORS setup, no separate frontend host required).

Recommended free host: **Hugging Face Spaces** (permanent URL, deploys from
this repo, sleeps after ~2 days idle and wakes on visit):

1. Sign up at huggingface.co → create a Space at huggingface.co/new-space
   (name `ptransmit`, SDK **Docker**, hardware CPU basic / free).
2. Create a write-scoped token at huggingface.co/settings/tokens.
3. GitHub → repo **Settings → Secrets and variables → Actions** → new secret
   `HF_TOKEN` = that token.
4. Put your Hugging Face username in
   `.github/workflows/sync-to-hub.yml` (`huggingface_repo_id: <user>/ptransmit`).
5. Push to `main` — the action mirrors the repo, HF builds the image, and the
   platform lives at `https://<user>-ptransmit.hf.space`.

Notes:
- Vercel (or any static host) can remain a second front door: set env var
  `VITE_API_BASE = https://<user>-ptransmit.hf.space` at build time.
- Render alternative: service from repo root, Dockerfile path `Dockerfile`,
  health check `/api/health` (free instances sleep after 15 min idle).
- Fully offline/local: `start-ptransmit.bat` → `http://localhost:4173`.
- Free-tier storage is ephemeral: on restart the clearly-labelled synthetic
  demo data re-seeds automatically; trained models can be re-trained in the
  Model Laboratory.

## Tests

```bash
cd backend
python -m pytest tests/ -q
```

## Roadmap

- **Phase 2** — Genomic module build-out: SNP statistics, diversity (H, MOI), population
  structure; resistance surveillance with researcher-defined thresholds.
- **Phase 3** — Environmental raster ingestion (CHIRPS/ERA5/MODIS), Bayesian spatial
  models, spatiotemporal deep models, calibrated uncertainty, alert thresholds.
- **Phase 4** — Multimodal AI (genomic + clinical + environmental), mechanistic
  transmission-model coupling, PDF report export, multi-user deployment hardening.

## Licence & data credits

- Code: MIT (c) 2026 P-TRANSMIT AI contributors.
- Boundaries: geoBoundaries gbOpen GHA ADM1, CC-BY 4.0.
- Tiles: © OpenStreetMap contributors.
