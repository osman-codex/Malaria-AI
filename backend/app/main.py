"""P-TRANSMIT AI FastAPI application factory."""
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import get_settings
from app.api import api_routes


@asynccontextmanager
async def lifespan(application: FastAPI):
    api_routes.bootstrap()
    yield


def create_app() -> FastAPI:
    s = get_settings()
    app = FastAPI(
        title=s.app_name,
        version=s.app_version,
        description=(
            "Research and surveillance decision-support platform for "
            "Plasmodium falciparum transmission, genomic epidemiology and "
            "antimalarial drug resistance in Ghana. "
            f"**Disclaimer:** {s.disclaimer}"
        ),
        lifespan=lifespan,
    )

    origins = [o.strip() for o in s.cors_origins.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_origin_regex=r"^https://[a-z0-9-]+\.vercel\.app$",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_routes.router, prefix="/api")

    @app.get("/api/health", tags=["system"])
    def health() -> dict:
        return {
            "status": "ok",
            "app": s.app_name,
            "version": s.app_version,
            "demo_mode": s.demo_mode,
            "disclaimer": s.disclaimer,
        }

    # Optional: serve the built frontend if present (frontend/dist)
    dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
    if dist.exists():
        app.mount("/app", StaticFiles(directory=str(dist), html=True), name="frontend")

        @app.get("/app/{full_path:path}", include_in_schema=False)
        def spa(full_path: str):
            target = dist / full_path
            if full_path and target.is_file():
                return FileResponse(target)
            return FileResponse(dist / "index.html")

    return app


app = create_app()
