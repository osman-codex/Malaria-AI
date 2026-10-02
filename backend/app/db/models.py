"""SQLAlchemy ORM models for the P-TRANSMIT AI platform.

Analytical datasets are stored as JSON records in typed tables so that the
platform can ingest arbitrary research CSVs without schema migration, while
the core entities (users, datasets, models, alerts) remain strongly typed.
"""
from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(32), default="researcher")  # admin | researcher | viewer
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    datasets: Mapped[list["Dataset"]] = relationship(back_populates="owner")


class Dataset(Base):
    """An uploaded or generated analytical dataset.

    `record_type` in {surveillance, environmental, genomic, resistance, clinical}
    `data` holds the row-level records as a JSON list.
    `is_synthetic` marks generated demonstration data; the UI must display the
    DEMONSTRATION banner whenever this is true or demo_mode is on.
    """

    __tablename__ = "datasets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    record_type: Mapped[str] = mapped_column(String(32), index=True)
    source: Mapped[str] = mapped_column(String(255), default="upload")  # upload | synthetic | external
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=True)
    row_count: Mapped[int] = mapped_column(Integer, default=0)
    columns: Mapped[list] = mapped_column(JSON, default=list)
    dtypes: Mapped[dict] = mapped_column(JSON, default=dict)
    profile: Mapped[dict] = mapped_column(JSON, default=dict)  # data-quality report
    column_mapping: Mapped[dict] = mapped_column(JSON, default=dict)  # user var -> standard var
    data: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    owner: Mapped[User | None] = relationship(back_populates="datasets")


class TrainedModel(Base):
    """A trained, persisted ML model plus full provenance for reproducibility."""

    __tablename__ = "trained_models"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    model_type: Mapped[str] = mapped_column(String(64))  # random_forest | xgboost | ridge
    task: Mapped[str] = mapped_column(String(32), default="transmission_forecast")
    dataset_id: Mapped[int | None] = mapped_column(ForeignKey("datasets.id"), nullable=True)
    target: Mapped[str] = mapped_column(String(128))
    features: Mapped[list] = mapped_column(JSON, default=list)
    preprocessing: Mapped[dict] = mapped_column(JSON, default=dict)
    validation: Mapped[dict] = mapped_column(JSON, default=dict)  # split strategy + metrics
    metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    feature_importance: Mapped[list] = mapped_column(JSON, default=list)  # [{feature, importance}]
    horizons_weeks: Mapped[list] = mapped_column(JSON, default=list)
    random_seed: Mapped[int] = mapped_column(Integer, default=42)
    model_version: Mapped[str] = mapped_column(String(32), default="v1")
    software_versions: Mapped[dict] = mapped_column(JSON, default=dict)
    training_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    artifact_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)


class Alert(Base):
    """A model-generated research/surveillance signal (never a confirmed event)."""

    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    alert_type: Mapped[str] = mapped_column(String(64))  # transmission | forecast | genomic | resistance
    severity: Mapped[str] = mapped_column(String(16), default="info")  # info | warning | critical
    region: Mapped[str | None] = mapped_column(String(128), nullable=True)
    district: Mapped[str | None] = mapped_column(String(128), nullable=True)
    title: Mapped[str] = mapped_column(String(255))
    evidence: Mapped[dict] = mapped_column(JSON, default=dict)
    model_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    explanation: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(32), default="open")  # open | acknowledged | dismissed
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64))
    action: Mapped[str] = mapped_column(String(255))
    detail: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
