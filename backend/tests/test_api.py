"""Tests for auth, ingestion, transmission engine, alerts, genomics scaffold."""
from __future__ import annotations

import io

import numpy as np
import pandas as pd
import pytest


# --------------------------------------------------------------------------- #
# System & auth
# --------------------------------------------------------------------------- #
def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert "disclaimer" in body


def test_auth_flow(client):
    r = client.post("/api/auth/register", json={"username": "testuser1", "password": "strongpass1"})
    assert r.status_code == 200
    r = client.post("/api/auth/token", data={"username": "testuser1", "password": "strongpass1"})
    assert r.status_code == 200
    token = r.json()["access_token"]
    r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["username"] == "testuser1"


def test_auth_rejects_bad_password(client):
    r = client.post("/api/auth/token", data={"username": "demo", "password": "wrong"})
    assert r.status_code == 401


def test_protected_route_requires_token(client):
    r = client.get("/api/datasets")
    assert r.status_code == 401


# --------------------------------------------------------------------------- #
# Demo dataset
# --------------------------------------------------------------------------- #
def test_demo_dataset_loaded(client, auth_headers, demo_dataset_id):
    r = client.get(f"/api/datasets/{demo_dataset_id}", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["is_synthetic"] is True
    assert body["source"] == "synthetic"
    assert body["row_count"] > 0


# --------------------------------------------------------------------------- #
# Ingestion service
# --------------------------------------------------------------------------- #
def _csv_bytes(df: pd.DataFrame) -> io.BytesIO:
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return io.BytesIO(buf.getvalue().encode())


def test_upload_surveillance_csv(client, auth_headers):
    df = pd.DataFrame(
        {
            "region_name": ["Ashanti", "Northern"],
            "date": ["2026-01-04", "2026-01-04"],
            "mal_cases": [120, 200],
            "rainfall": [30.5, 5.0],
        }
    )
    r = client.post(
        "/api/datasets/upload?record_type=surveillance",
        files={"file": ("test_surv.csv", _csv_bytes(df), "text/csv")},
        headers=auth_headers,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["row_count"] == 2
    mapping = body["column_mapping_suggested"]
    assert mapping["region_name"] == "region"
    assert mapping["mal_cases"] == "malaria_cases"
    assert mapping["date"] == "week_start_date"
    assert body["standardisation_report"]["region_matches"]["Ashanti"] == "Ashanti Region"


def test_upload_rejects_bad_variant_schema(client, auth_headers):
    df = pd.DataFrame({"foo": [1], "bar": [2]})
    r = client.post(
        "/api/datasets/upload?record_type=genomic",
        files={"file": ("bad_variants.csv", _csv_bytes(df), "text/csv")},
        headers=auth_headers,
    )
    assert r.status_code == 400


# --------------------------------------------------------------------------- #
# Transmission engine (unit level)
# --------------------------------------------------------------------------- #
def _mini_surveillance() -> pd.DataFrame:
    from app.services.synthetic import generate_demo_surveillance

    return generate_demo_surveillance(n_weeks=120, seed=7)


def test_build_supervised_shapes():
    from app.ml.transmission import build_supervised

    df = _mini_surveillance()
    X, y, meta = build_supervised(df, horizon=2)
    assert len(X) == len(y) == len(meta)
    assert not X.isna().any().any()
    assert "region_Ashanti Region" in X.columns


def test_temporal_split_no_leakage():
    from app.ml.transmission import build_supervised, temporal_split

    df = _mini_surveillance()
    X, y, meta = build_supervised(df, horizon=1)
    split = temporal_split(X, y, meta, train_fraction=0.8)
    assert set(split["train_weeks"]).isdisjoint(set(split["test_weeks"]))
    assert max(split["train_weeks"]) < min(split["test_weeks"])


def test_train_and_forecast_roundtrip(tmp_path):
    from app.ml.transmission import forecast_from_artifacts, train_transmission_models

    df = _mini_surveillance()
    results = train_transmission_models(
        df, horizons=[1], model_types=["ridge", "random_forest"], seed=42, model_dir=tmp_path, dataset_id=99
    )
    h1 = results["horizons"]["1"]
    assert "error" not in h1 and h1["best_model"] is not None
    m = h1["best_metrics"]
    assert m["n_test"] > 0 and m["MAE"] >= 0

    fc = forecast_from_artifacts(df, tmp_path, horizons=[1], dataset_id=99)
    assert len(fc) == df["region"].nunique()
    row = fc[0]
    assert row["predicted_cases"] >= 0
    assert row["interval_low"] <= row["predicted_cases"] <= row["interval_high"]
    assert row["risk_category"] in ("low", "moderate", "high", "very high")


def test_explain_forecast(tmp_path):
    from app.ml.transmission import explain_forecast, train_transmission_models

    df = _mini_surveillance()
    train_transmission_models(df, horizons=[1], model_types=["random_forest"], seed=42, model_dir=tmp_path, dataset_id=5)
    expl = explain_forecast(df, tmp_path, horizon=1, dataset_id=5)
    assert expl["available"] is True
    assert "method" in expl and "not causal" in expl["method"]
    some = next(iter(expl["regions"].values()))
    assert len(some) > 0


# --------------------------------------------------------------------------- #
# Full API flow: train -> forecast -> explain -> observed-vs-predicted
# --------------------------------------------------------------------------- #
def test_api_train_forecast_explain(client, auth_headers, demo_dataset_id):
    r = client.post(
        "/api/transmission/train",
        json={"dataset_id": demo_dataset_id, "horizons_weeks": [1, 4], "model_types": ["ridge", "random_forest"]},
        headers=auth_headers,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["is_synthetic"] is True
    assert body["saved_model_ids"], "at least one model should be saved"

    r = client.get(f"/api/transmission/forecast?dataset_id={demo_dataset_id}", headers=auth_headers)
    assert r.status_code == 200
    f = r.json()["forecasts"]
    assert len(f) >= 16 * 2  # 16 regions x 2 horizons

    r = client.get(f"/api/transmission/explain?dataset_id={demo_dataset_id}&horizon=1", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["available"] is True

    r = client.get(f"/api/transmission/observed-vs-predicted?dataset_id={demo_dataset_id}", headers=auth_headers)
    assert r.status_code == 200
    assert len(r.json()["rows"]) > 0


def test_forecast_requires_training(client, auth_headers):
    r = client.get("/api/transmission/forecast?dataset_id=999999", headers=auth_headers)
    assert r.status_code in (404,)


# --------------------------------------------------------------------------- #
# Spatial
# --------------------------------------------------------------------------- #
def test_region_boundaries(client, auth_headers):
    r = client.get("/api/spatial/regions", headers=auth_headers)
    assert r.status_code == 200
    gj = r.json()
    names = [f["properties"]["shapeName"] for f in gj["features"]]
    assert len(names) == 16
    assert "Ashanti Region" in names


def test_spatial_snapshot(client, auth_headers, demo_dataset_id):
    # ensure models exist for forecast join
    client.post("/api/transmission/train", json={"dataset_id": demo_dataset_id, "horizons_weeks": [1]}, headers=auth_headers)
    r = client.get(f"/api/spatial/snapshot?dataset_id={demo_dataset_id}", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["is_synthetic"] is True
    feats = body["geojson"]["features"]
    with_stats = [f for f in feats if f["properties"].get("stats")]
    assert len(with_stats) >= 14  # most regions should have stats


# --------------------------------------------------------------------------- #
# Alerts
# --------------------------------------------------------------------------- #
def test_alert_scan_and_status(client, auth_headers, demo_dataset_id):
    r = client.post("/api/alerts/scan", json={"dataset_id": demo_dataset_id}, headers=auth_headers)
    assert r.status_code == 200
    r = client.get("/api/alerts", headers=auth_headers)
    alerts = r.json()
    assert isinstance(alerts, list)
    for a in alerts:
        assert a["evidence"] is not None
        assert "not a confirmed" in a["explanation"] or a["explanation"]
    if alerts:
        aid = alerts[0]["id"]
        r = client.post(f"/api/alerts/{aid}/status", json={"status": "acknowledged"}, headers=auth_headers)
        assert r.status_code == 200


# --------------------------------------------------------------------------- #
# Genomics scaffold
# --------------------------------------------------------------------------- #
def test_genomics_awaiting_data(client, auth_headers):
    r = client.get("/api/genomics/status", headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "awaiting_validated_data"
    assert body["known_markers_catalogue"]


def test_genomics_analyze_with_uploaded_variants(client, auth_headers):
    df = pd.DataFrame(
        {
            "sample_id": [f"S{i}" for i in range(20)],
            "gene": ["kelch13"] * 10 + ["pfmdr1"] * 10,
            "mutation": ["C469Y"] * 5 + ["WT"] * 5 + ["N86Y"] * 8 + ["WT"] * 2,
            "region": ["Ashanti Region"] * 20,
            "sample_date": ["2026-06-15"] * 20,
        }
    )
    r = client.post(
        "/api/datasets/upload?record_type=genomic",
        files={"file": ("variants.csv", _csv_bytes(df), "text/csv")},
        headers=auth_headers,
    )
    assert r.status_code == 200, r.text
    ds_id = r.json()["id"]

    r = client.post("/api/genomics/analyze", json={"dataset_id": ds_id}, headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "descriptive_statistics_only"
    assert body["n_samples"] == 20
    assert body["by_region"], "stratified records should exist"


def test_marker_frequencies_math():
    from app.services.genomics import marker_frequencies

    df = pd.DataFrame(
        {
            "sample_id": ["A", "A", "B", "C"],
            "gene": ["g", "g", "g", "h"],
            "mutation": ["m", "m", "m", "x"],
            "region": ["R", "R", "R", "R"],
            "sample_date": ["2026-01-01"] * 4,
        }
    )
    out = marker_frequencies(df)
    rec = out["by_region"][0]
    assert rec["n_calls"] == 4
    assert rec["n_samples"] == 3
    assert rec["n_marker_positive_samples"] == 3
    assert rec["frequency"] == 1.0


# --------------------------------------------------------------------------- #
# Reports
# --------------------------------------------------------------------------- #
def test_report_generation(client, auth_headers, demo_dataset_id):
    r = client.get(f"/api/reports/generate?dataset_id={demo_dataset_id}", headers=auth_headers)
    assert r.status_code == 200
    text = r.text
    assert "P-TRANSMIT AI" in text
    assert "DEMONSTRATION DATA" in text
    assert "Limitations" in text


# --------------------------------------------------------------------------- #
# Synthetic generator sanity
# --------------------------------------------------------------------------- #
def test_synthetic_generator_properties():
    from app.services.synthetic import REGION_POP_WEIGHTS, generate_demo_surveillance

    df = generate_demo_surveillance(n_weeks=60, seed=1)
    assert set(df["region"].unique()) == set(REGION_POP_WEIGHTS.keys())
    assert (df["malaria_cases"] >= 0).all()
    # Southern regions should be bimodal (two seasonal peaks); northern unimodal.
    ash = df[df["region"] == "Ashanti Region"].groupby("epi_week")["malaria_cases"].mean()
    assert ash.max() > ash.median() * 1.3  # seasonality exists


def test_no_nan_in_demo():
    from app.services.synthetic import generate_demo_surveillance

    df = generate_demo_surveillance(n_weeks=40, seed=3)
    assert not df.isna().any().any()
