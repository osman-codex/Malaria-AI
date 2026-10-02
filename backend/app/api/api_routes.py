"""All API routes for the P-TRANSMIT AI platform."""
from __future__ import annotations

import json
import platform
import sys
from pathlib import Path

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import PlainTextResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import Body
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.core.config import get_settings
from app.core.security import create_access_token, hash_password, verify_password
from app.db.models import Alert, AuditLog, Dataset, TrainedModel, User
from app.db.session import Base, engine, get_db
from app.ml import transmission as ml
from app.services import alerts as alerts_svc
from app.services import genomics as genomics_svc
from app.services import ingestion as ing
from app.services import reports as reports_svc
from app.services import synthetic as syn

router = APIRouter()


def audit(db: Session, username: str, action: str, detail: str = "") -> None:
    db.add(AuditLog(username=username, action=action, detail=detail))
    db.commit()


# --------------------------------------------------------------------------- #
# System
# --------------------------------------------------------------------------- #
@router.get("/system/info", tags=["system"])
def system_info() -> dict:
    s = get_settings()
    return {
        "app": s.app_name,
        "version": s.app_version,
        "demo_mode": s.demo_mode,
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "disclaimer": s.disclaimer,
    }


# --------------------------------------------------------------------------- #
# Auth
# --------------------------------------------------------------------------- #
@router.post("/auth/register", tags=["auth"])
def register(payload: dict = Body(...), db: Session = Depends(get_db)) -> dict:
    username = str(payload.get("username", "")).strip()
    password = str(payload.get("password", ""))
    if len(username) < 3 or len(password) < 8:
        raise HTTPException(400, "Username >= 3 chars and password >= 8 chars required.")
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(409, "Username already exists.")
    user = User(username=username, hashed_password=hash_password(password), role="researcher")
    db.add(user)
    db.commit()
    return {"id": user.id, "username": user.username, "role": user.role}


@router.post("/auth/token", tags=["auth"])
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)) -> dict:
    s = get_settings()
    user = db.query(User).filter(User.username == form.username).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(401, "Incorrect username or password.")
    token = create_access_token(user.username, s.secret_key, s.access_token_expire_minutes, {"role": user.role})
    audit(db, user.username, "login")
    return {"access_token": token, "token_type": "bearer", "role": user.role, "username": user.username}


@router.get("/auth/me", tags=["auth"])
def me(user: User = Depends(get_current_user)) -> dict:
    return {"username": user.username, "role": user.role, "id": user.id}


@router.post("/auth/demo", tags=["auth"])
def demo_login(db: Session = Depends(get_db)) -> dict:
    """One-click guest access for demonstrations — no credentials required.

    Reuses the shared read-only 'demo' account and returns a normal bearer
    token. Only meaningful when demo_mode is enabled; in production the
    endpoint is disabled so anonymous token minting cannot happen.
    """
    s = get_settings()
    if not s.demo_mode:
        raise HTTPException(403, "Demo access is disabled (demo_mode off).")
    user = db.query(User).filter(User.username == "demo").first()
    if not user:
        raise HTTPException(503, "Demo account missing; restart the backend to bootstrap it.")
    token = create_access_token(user.username, s.secret_key, s.access_token_expire_minutes, {"role": user.role})
    audit(db, user.username, "login", "demo one-click access")
    return {"access_token": token, "token_type": "bearer", "role": user.role, "username": user.username}


# --------------------------------------------------------------------------- #
# Bootstrap admin (dev convenience; runs once)
# --------------------------------------------------------------------------- #
def bootstrap() -> None:
    """Create tables, seed default users and (optionally) the demo dataset.
    Called from the app lifespan in main.py.
    """
    s = get_settings()
    Base.metadata.create_all(engine)
    from sqlalchemy.orm import Session as SqlaSession

    with SqlaSession(engine) as db:
        if not db.query(User).first():
            admin = User(username="admin", hashed_password=hash_password("ptransmit-admin"), role="admin")
            demo = User(username="demo", hashed_password=hash_password("demo1234"), role="researcher")
            db.add_all([admin, demo])
            db.commit()
        if s.demo_mode and not db.query(Dataset).filter(Dataset.source == "synthetic").first():
            _load_demo_dataset(db)
        else:
            _load_demo_genomics(db)


def _load_demo_dataset(db: Session) -> Dataset:
    s = get_settings()
    df = syn.generate_demo_surveillance()
    profile = ing.profile_dataframe(df)
    ds = Dataset(
        name="DEMO — Synthetic Ghana weekly surveillance (illustrative only)",
        record_type="surveillance",
        source="synthetic",
        is_synthetic=True,
        row_count=int(len(df)),
        columns=list(df.columns),
        dtypes={c: str(t) for c, t in df.dtypes.items()},
        profile=profile,
        data=df.to_dict(orient="records"),
    )
    db.add(ds)
    db.commit()
    db.refresh(ds)
    _load_demo_genomics(db)
    return ds


def _load_demo_genomics(db: Session) -> Dataset | None:
    """Load the synthetic Plasmodium variant table used for demo charts.

    Clearly labelled synthetic: it exists so the genomics screens have
    something to display during demonstrations. Values are simulated and
    carry no scientific authority.
    """
    if db.query(Dataset).filter(Dataset.record_type == "genomic", Dataset.source == "synthetic").first():
        return None
    df = genomics_svc.generate_demo_variants()
    profile = ing.profile_dataframe(df)
    ds = Dataset(
        name="DEMO — Synthetic Plasmodium variant calls (illustrative only)",
        record_type="genomic",
        source="synthetic",
        is_synthetic=True,
        row_count=int(len(df)),
        columns=list(df.columns),
        dtypes={c: str(t) for c, t in df.dtypes.items()},
        profile=profile,
        data=df.to_dict(orient="records"),
    )
    db.add(ds)
    db.commit()
    db.refresh(ds)
    return ds


# --------------------------------------------------------------------------- #
# Datasets
# --------------------------------------------------------------------------- #
@router.get("/datasets", tags=["data"])
def list_datasets(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> list[dict]:
    rows = db.query(Dataset).order_by(Dataset.created_at.desc()).all()
    return [
        {
            "id": d.id,
            "name": d.name,
            "record_type": d.record_type,
            "source": d.source,
            "is_synthetic": d.is_synthetic,
            "row_count": d.row_count,
            "columns": d.columns,
            "created_at": d.created_at.isoformat(),
        }
        for d in rows
    ]


@router.get("/datasets/{dataset_id}", tags=["data"])
def get_dataset(
    dataset_id: int,
    include_data: bool = Query(False),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    d = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not d:
        raise HTTPException(404, "Dataset not found.")
    out = {
        "id": d.id,
        "name": d.name,
        "record_type": d.record_type,
        "source": d.source,
        "is_synthetic": d.is_synthetic,
        "row_count": d.row_count,
        "columns": d.columns,
        "dtypes": d.dtypes,
        "profile": d.profile,
        "column_mapping": d.column_mapping,
    }
    if include_data:
        out["data"] = d.data
    return out


@router.post("/datasets/upload", tags=["data"])
async def upload_dataset(
    file: UploadFile = File(...),
    record_type: str = Query("surveillance"),
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin", "researcher")),
) -> dict:
    s = get_settings()
    raw = await file.read()
    if len(raw) > s.max_upload_mb * 1024 * 1024:
        raise HTTPException(413, f"File exceeds {s.max_upload_mb} MB limit.")
    safe_name = Path(file.filename or "upload").name
    dest = Path(s.upload_dir) / f"{pd.Timestamp.now().strftime('%Y%m%d%H%M%S')}_{safe_name}"
    dest.write_bytes(raw)

    try:
        df, fmt = ing.read_table(safe_name, raw)
    except ing.IngestionError as e:
        raise HTTPException(400, str(e))
    if df.empty:
        raise HTTPException(400, "Uploaded file contains no rows.")

    suggested = ing.suggest_column_mapping(list(df.columns), record_type=record_type)
    df_std, report = ing.standardise(df, suggested)
    profile = ing.profile_dataframe(df_std)

    is_genomic = record_type in ("genomic", "resistance")
    if is_genomic:
        check = genomics_svc.validate_variant_table(df_std)
        if not check["valid"]:
            raise HTTPException(
                400,
                {
                    "error": "Variant table does not meet the required schema.",
                    **check,
                },
            )

    ds = Dataset(
        name=safe_name,
        record_type=record_type,
        source="upload",
        is_synthetic=False,
        filename=str(dest),
        row_count=int(len(df_std)),
        columns=list(df_std.columns),
        dtypes={c: str(t) for c, t in df_std.dtypes.items()},
        profile=profile,
        column_mapping=suggested,
        data=df_std.to_dict(orient="records"),
        created_by=user.id,
    )
    db.add(ds)
    db.commit()
    db.refresh(ds)
    audit(db, user.username, "dataset.upload", f"dataset={ds.id} file={safe_name} rows={ds.row_count}")
    return {
        "id": ds.id,
        "name": ds.name,
        "record_type": ds.record_type,
        "row_count": ds.row_count,
        "columns": ds.columns,
        "column_mapping_suggested": suggested,
        "standardisation_report": report,
        "profile": profile,
        "genomic_schema_check": genomics_svc.validate_variant_table(df_std) if is_genomic else None,
    }


@router.post("/datasets/{dataset_id}/remap", tags=["data"])
def remap_columns(
    dataset_id: int,
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin", "researcher")),
) -> dict:
    """Apply a user-approved column mapping and re-standardise a dataset."""
    d = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not d:
        raise HTTPException(404, "Dataset not found.")
    mapping = payload.get("mapping", {})
    df = pd.DataFrame(d.data)
    df_std, report = ing.standardise(df, mapping)
    d.column_mapping = mapping
    d.columns = list(df_std.columns)
    d.dtypes = {c: str(t) for c, t in df_std.dtypes.items()}
    d.profile = ing.profile_dataframe(df_std)
    d.data = df_std.to_dict(orient="records")
    db.commit()
    audit(db, user.username, "dataset.remap", f"dataset={d.id}")
    return {"id": d.id, "columns": d.columns, "report": report, "profile": d.profile}


@router.delete("/datasets/{dataset_id}", tags=["data"])
def delete_dataset(
    dataset_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin", "researcher")),
) -> dict:
    d = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not d:
        raise HTTPException(404, "Dataset not found.")
    if d.filename and Path(d.filename).exists():
        Path(d.filename).unlink(missing_ok=True)
    db.delete(d)
    db.commit()
    audit(db, user.username, "dataset.delete", f"dataset={dataset_id}")
    return {"deleted": dataset_id}


# --------------------------------------------------------------------------- #
# Transmission AI: train, evaluate, forecast, explain
# --------------------------------------------------------------------------- #
@router.post("/transmission/train", tags=["transmission"])
def train_models(
    payload: dict = Body(default={}),
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin", "researcher")),
) -> dict:
    s = get_settings()
    dataset_id = payload.get("dataset_id")
    horizons = payload.get("horizons_weeks") or ml.DEFAULT_HORIZONS
    model_types = payload.get("model_types") or ml.DEFAULT_MODELS
    seed = int(payload.get("seed", 42))
    train_fraction = float(payload.get("train_fraction", 0.8))

    ds = _get_surveillance_dataset(db, dataset_id)
    df = pd.DataFrame(ds.data)
    df = _coerce_surveillance(df)

    results = ml.train_transmission_models(
        df,
        horizons=horizons,
        model_types=model_types,
        seed=seed,
        train_fraction=train_fraction,
        model_dir=s.model_dir,
        dataset_id=ds.id,
    )

    saved: list[int] = []
    for h, res in results["horizons"].items():
        if "error" in res or not res.get("best_model"):
            continue
        tm = TrainedModel(
            name=f"Transmission h={h}w — {res['best_model']}",
            model_type=res["best_model"],
            task="transmission_forecast",
            dataset_id=ds.id,
            target=ml.TARGET,
            features=[f["feature"] for f in res.get("feature_importance", [])],
            preprocessing={"lag_features": ml.CASE_LAGS, "env_lag1": True, "seasonality": "cyclic week-of-year"},
            validation={
                "strategy": "temporal split",
                "train_fraction": train_fraction,
                "n_train_rows": res.get("n_train_rows"),
                "n_test_rows": res.get("n_test_rows"),
                "note": "Chronological split on weeks; models trained on earlier weeks only.",
            },
            metrics=res["best_metrics"],
            feature_importance=res.get("feature_importance", []),
            horizons_weeks=[int(h)],
            random_seed=seed,
            model_version="v1",
            software_versions=ml._software_versions(),
            artifact_path=res.get("artifact_path"),
            created_by=user.id,
        )
        db.add(tm)
        db.commit()
        db.refresh(tm)
        saved.append(tm.id)

    audit(db, user.username, "transmission.train", f"dataset={ds.id} horizons={horizons}")
    return {
        "dataset_id": ds.id,
        "dataset_name": ds.name,
        "is_synthetic": ds.is_synthetic,
        "results": results,
        "saved_model_ids": saved,
    }


@router.get("/transmission/forecast", tags=["transmission"])
def get_forecast(
    dataset_id: int | None = Query(None),
    horizons: str = Query("1,2,4,8"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    s = get_settings()
    ds = _get_surveillance_dataset(db, dataset_id)
    df = _coerce_surveillance(pd.DataFrame(ds.data))
    rows = ml.forecast_from_artifacts(
        df, s.model_dir, horizons=[int(x) for x in horizons.split(",") if x.strip()], dataset_id=ds.id
    )
    if not rows:
        raise HTTPException(
            404,
            "No trained model artifacts found. Train the transmission models first (Model Laboratory or POST /transmission/train).",
        )
    return {
        "dataset_id": ds.id,
        "is_synthetic": ds.is_synthetic,
        "assumptions": "Environmental covariates held at last observed value (persistence).",
        "forecasts": rows,
    }


@router.get("/transmission/explain", tags=["transmission"])
def get_explanation(
    horizon: int = Query(1),
    dataset_id: int | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    s = get_settings()
    ds = _get_surveillance_dataset(db, dataset_id)
    df = _coerce_surveillance(pd.DataFrame(ds.data))
    expl = ml.explain_forecast(df, s.model_dir, horizon=horizon, dataset_id=ds.id)
    expl["is_synthetic"] = ds.is_synthetic
    expl["note"] = "Explanations describe model behaviour, NOT causal effects."
    return expl


@router.get("/transmission/observed-vs-predicted", tags=["transmission"])
def observed_vs_predicted(
    dataset_id: int | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    """Held-out test-week predictions from the h=1 artifact, for validation plots."""
    s = get_settings()
    ds = _get_surveillance_dataset(db, dataset_id)
    df = _coerce_surveillance(pd.DataFrame(ds.data))
    horizon = 1
    path = _best_artifact(s.model_dir, horizon, ds.id)
    if not path:
        raise HTTPException(404, "No trained h=1 model artifact found. Train models first.")
    import joblib

    art = joblib.load(path)
    X, y, meta = ml.build_supervised(df, horizon)
    split = ml.temporal_split(X, y, meta)
    pred = art["model"].predict(split["X_test"])
    rows = [
        {
            "region": m["region"],
            "week_start_date": m["week_start_date"],
            "observed": float(o),
            "predicted": round(float(p), 1),
        }
        for m, o, p in zip(split["meta_test"].to_dict(orient="records"), split["y_test"].to_numpy(), pred)
    ]
    return {
        "dataset_id": ds.id,
        "is_synthetic": ds.is_synthetic,
        "model_type": art["model_type"],
        "metrics": art["metrics"],
        "rows": rows,
    }


# --------------------------------------------------------------------------- #
# Spatial
# --------------------------------------------------------------------------- #
@router.get("/spatial/regions", tags=["spatial"])
def region_boundaries(user: User = Depends(get_current_user)) -> dict:
    """Real Ghana ADM1 boundaries (geoBoundaries gbOpen, CC-BY 4.0)."""
    s = get_settings()
    path = Path(s.geo_dir) / "ghana_adm1_simplified.geojson"
    if not path.exists():
        path = Path(s.geo_dir) / "ghana_adm1.geojson"
    if not path.exists():
        raise HTTPException(503, "Ghana boundary file missing. Run scripts/fetch_geo_data.py")
    return json.loads(path.read_text(encoding="utf-8"))


@router.get("/spatial/snapshot", tags=["spatial"])
def spatial_snapshot(
    dataset_id: int | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    """Join latest observed + forecast stats onto region boundaries."""
    s = get_settings()
    ds = _get_surveillance_dataset(db, dataset_id)
    df = _coerce_surveillance(pd.DataFrame(ds.data))
    df["week_start_date"] = pd.to_datetime(df["week_start_date"])

    last_week = df["week_start_date"].max()
    recent = df[df["week_start_date"] > last_week - pd.Timedelta(weeks=4)]
    stats = recent.groupby("region")["malaria_cases"].agg(["mean", "sum"]).reset_index()
    stats.columns = ["region", "recent_4wk_mean_cases", "recent_4wk_total_cases"]
    hist_p90 = df.groupby("region")["malaria_cases"].quantile(0.90).rename("hist_p90").reset_index()
    stats = stats.merge(hist_p90, on="region", how="left")

    try:
        frows = ml.forecast_from_artifacts(df, s.model_dir, horizons=[1, 2, 4], dataset_id=ds.id)
        fdf = pd.DataFrame(frows)
        fagg = (
            fdf[fdf["horizon_weeks"] <= 4]
            .groupby("region")["predicted_cases"]
            .median()
            .rename("forecast_median_4wk")
            .reset_index()
        )
        stats = stats.merge(fagg, on="region", how="left")
    except Exception:
        stats["forecast_median_4wk"] = None

    stats["risk_category"] = stats.apply(
        lambda r: ml._risk_category(r["recent_4wk_mean_cases"], {"q50": r["hist_p90"] * 0.75, "q75": r["hist_p90"] * 0.9, "q90": r["hist_p90"]})
        if pd.notna(r["hist_p90"]) and r["hist_p90"] > 0
        else None,
        axis=1,
    )

    gj = json.loads((Path(s.geo_dir) / "ghana_adm1_simplified.geojson").read_text(encoding="utf-8"))
    stats_records = stats.to_dict(orient="records")
    by_region = {r["region"]: r for r in stats_records}

    for f in gj["features"]:
        nm = f["properties"]["shapeName"]
        st = by_region.get(nm)
        f["properties"]["stats"] = st
    return {
        "dataset_id": ds.id,
        "is_synthetic": ds.is_synthetic,
        "last_week": str(last_week.date()),
        "geojson": gj,
    }


# --------------------------------------------------------------------------- #
# Alerts
# --------------------------------------------------------------------------- #
@router.get("/alerts", tags=["alerts"])
def list_alerts(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> list[dict]:
    rows = db.query(Alert).order_by(Alert.created_at.desc()).limit(200).all()
    return [
        {
            "id": a.id,
            "alert_type": a.alert_type,
            "severity": a.severity,
            "region": a.region,
            "district": a.district,
            "title": a.title,
            "evidence": a.evidence,
            "model_ref": a.model_ref,
            "confidence": a.confidence,
            "explanation": a.explanation,
            "status": a.status,
            "created_at": a.created_at.isoformat(),
        }
        for a in rows
    ]


@router.post("/alerts/scan", tags=["alerts"])
def scan_alerts(
    payload: dict = Body(default={}),
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin", "researcher")),
) -> dict:
    ds = _get_surveillance_dataset(db, payload.get("dataset_id"))
    df = _coerce_surveillance(pd.DataFrame(ds.data))
    s = get_settings()
    try:
        frows = ml.forecast_from_artifacts(df, s.model_dir, horizons=[1, 2, 4], dataset_id=ds.id)
    except Exception:
        frows = []
    model_ref = f"transmission artifact ds{ds.id} h<=4"
    fresh = alerts_svc.generate_alerts(db, df, frows, model_ref)
    audit(db, user.username, "alerts.scan", f"dataset={ds.id} new={len(fresh)}")
    return {"new_alerts": len(fresh), "alerts": [{"id": a.id, "title": a.title} for a in fresh]}


@router.post("/alerts/{alert_id}/status", tags=["alerts"])
def set_alert_status(
    alert_id: int,
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin", "researcher")),
) -> dict:
    a = db.query(Alert).filter(Alert.id == alert_id).first()
    if not a:
        raise HTTPException(404, "Alert not found.")
    status = payload.get("status")
    if status not in ("open", "acknowledged", "dismissed"):
        raise HTTPException(400, "status must be open|acknowledged|dismissed")
    a.status = status
    db.commit()
    audit(db, user.username, "alerts.status", f"alert={alert_id} status={status}")
    return {"id": a.id, "status": a.status}


# --------------------------------------------------------------------------- #
# Genomics / resistance (scaffold)
# --------------------------------------------------------------------------- #
@router.get("/genomics/status", tags=["genomics"])
def genomics_status(user: User = Depends(get_current_user)) -> dict:
    return genomics_svc.awaiting_data_response("Plasmodium Genomics")


@router.get("/resistance/status", tags=["genomics"])
def resistance_status(user: User = Depends(get_current_user)) -> dict:
    return genomics_svc.awaiting_data_response("Antimalarial Resistance")


@router.post("/genomics/analyze", tags=["genomics"])
def analyze_genomics(
    payload: dict = Body(default={}),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    ds_id = payload.get("dataset_id")
    q = db.query(Dataset).filter(Dataset.record_type.in_(("genomic", "resistance")))
    if ds_id:
        q = q.filter(Dataset.id == ds_id)
    ds = q.order_by(Dataset.created_at.desc()).first()
    if not ds:
        return genomics_svc.awaiting_data_response("Plasmodium Genomics")
    df = pd.DataFrame(ds.data)
    return {"dataset": {"id": ds.id, "name": ds.name}, "is_synthetic": ds.is_synthetic, **genomics_svc.marker_frequencies(df)}


@router.get("/genomics/charts", tags=["genomics"])
def genomics_charts(
    dataset_id: int | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    """Chart-ready genomic surveillance series (descriptive only)."""
    q = db.query(Dataset).filter(Dataset.record_type.in_(("genomic", "resistance")))
    if dataset_id:
        q = q.filter(Dataset.id == dataset_id)
    ds = q.order_by(Dataset.created_at.desc()).first()
    if not ds:
        raise HTTPException(404, "No genomic dataset loaded. Upload a variant table or enable demo mode.")
    df = pd.DataFrame(ds.data)
    return {
        "dataset_id": ds.id,
        "dataset_name": ds.name,
        "is_synthetic": ds.is_synthetic,
        **genomics_svc.chart_payload(df),
    }


# --------------------------------------------------------------------------- #
# Model laboratory
# --------------------------------------------------------------------------- #
@router.get("/models", tags=["models"])
def list_models(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> list[dict]:
    rows = db.query(TrainedModel).order_by(TrainedModel.training_date.desc()).all()
    return [
        {
            "id": m.id,
            "name": m.name,
            "model_type": m.model_type,
            "task": m.task,
            "target": m.target,
            "dataset_id": m.dataset_id,
            "metrics": m.metrics,
            "validation": m.validation,
            "feature_importance": m.feature_importance,
            "random_seed": m.random_seed,
            "model_version": m.model_version,
            "software_versions": m.software_versions,
            "training_date": m.training_date.isoformat(),
            "artifact_path": m.artifact_path,
        }
        for m in rows
    ]


@router.delete("/models/{model_id}", tags=["models"])
def delete_model(
    model_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_role("admin", "researcher")),
) -> dict:
    m = db.query(TrainedModel).filter(TrainedModel.id == model_id).first()
    if not m:
        raise HTTPException(404, "Model not found.")
    if m.artifact_path and Path(m.artifact_path).exists():
        Path(m.artifact_path).unlink(missing_ok=True)
    db.delete(m)
    db.commit()
    audit(db, user.username, "model.delete", f"model={model_id}")
    return {"deleted": model_id}


# --------------------------------------------------------------------------- #
# Reports
# --------------------------------------------------------------------------- #
@router.get("/reports/generate", tags=["reports"])
def generate_report(
    dataset_id: int | None = Query(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> PlainTextResponse:
    fname, markdown = reports_svc.generate_report(db, dataset_id)
    audit(db, user.username, "report.generate", fname)
    return PlainTextResponse(
        markdown,
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'},
    )


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _get_surveillance_dataset(db: Session, dataset_id: int | None) -> Dataset:
    q = db.query(Dataset).filter(Dataset.record_type == "surveillance")
    if dataset_id:
        ds = q.filter(Dataset.id == dataset_id).first()
        if not ds:
            raise HTTPException(404, "Dataset not found.")
        return ds
    ds = q.order_by(Dataset.created_at.desc()).first()
    if not ds:
        raise HTTPException(404, "No surveillance dataset available. Upload one or enable demo mode.")
    return ds


def _coerce_surveillance(df: pd.DataFrame) -> pd.DataFrame:
    required = {"region", "week_start_date", "malaria_cases"}
    missing = required - set(df.columns)
    if missing:
        raise HTTPException(422, f"Surveillance dataset missing required columns: {sorted(missing)}")
    df = df.copy()
    df["week_start_date"] = pd.to_datetime(df["week_start_date"], errors="coerce")
    df["malaria_cases"] = pd.to_numeric(df["malaria_cases"], errors="coerce")
    df = df.dropna(subset=["week_start_date", "malaria_cases", "region"])
    df["region"] = df["region"].astype(str)
    return df


def _best_artifact(model_dir: Path, horizon: int, dataset_id: int):
    model_dir = Path(model_dir)
    for pattern in (f"transmission_*_h{horizon}_ds{dataset_id or 0}.joblib", f"transmission_*_h{horizon}_ds*.joblib"):
        matches = sorted(model_dir.glob(pattern))
        if matches:
            return matches[-1]
    return None
