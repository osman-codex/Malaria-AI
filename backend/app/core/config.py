"""Application configuration (12-factor, env-driven)."""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent.parent  # backend/
BASE_DIR.parent.joinpath("data").mkdir(exist_ok=True)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Ghana Plasmodium Intelligence Platform (P-TRANSMIT AI)"
    app_version: str = "0.1.0"
    demo_mode: bool = True  # when True the demo dataset is auto-loaded and labelled

    database_url: str = f"sqlite:///{BASE_DIR / 'data' / 'ptransmit.db'}"
    secret_key: str = "CHANGE-ME-in-production-set-SECRET_KEY-env-var"
    access_token_expire_minutes: int = 60 * 8
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:4173,http://127.0.0.1:4173"

    max_upload_mb: int = 50
    upload_dir: str = str(BASE_DIR / "data" / "uploads")
    model_dir: str = str(BASE_DIR.parent / "models")
    geo_dir: str = str(BASE_DIR.parent / "data" / "geo")
    demo_data_dir: str = str(BASE_DIR.parent / "data" / "demonstration")

    disclaimer: str = (
        "This platform is a research and surveillance decision-support system. "
        "Predictions are not diagnoses and should not independently determine "
        "patient treatment or public-health action."
    )


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    for p in (s.upload_dir, s.model_dir):
        Path(p).mkdir(parents=True, exist_ok=True)
    return s
