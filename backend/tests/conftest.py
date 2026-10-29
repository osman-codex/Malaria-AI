"""Pytest fixtures: isolated temp DB per test session, TestClient factory."""
import os
import sys
import tempfile
from pathlib import Path

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_DIR))

# Isolated settings BEFORE any app import touches get_settings()
_TMP = tempfile.mkdtemp(prefix="ptransmit_test_")
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP}/test.db"
os.environ["DEMO_MODE"] = "true"
os.environ["UPLOAD_DIR"] = str(Path(_TMP) / "uploads")
os.environ["MODEL_DIR"] = str(Path(_TMP) / "models")
os.environ["GEO_DIR"] = str(BACKEND_DIR.parent / "data" / "geo")
os.environ["SECRET_KEY"] = "test-secret-key-for-pytest-only"


@pytest.fixture(scope="session")
def client():
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def auth_headers(client):
    r = client.post("/api/auth/token", data={"username": "demo", "password": "demo1234"})
    assert r.status_code == 200, r.text
    token = r.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(scope="session")
def demo_dataset_id(client, auth_headers) -> int:
    r = client.get("/api/datasets", headers=auth_headers)
    rows = r.json()
    assert rows, "demo dataset should be auto-loaded"
    # Demo mode now also auto-loads a synthetic genomic dataset; the tests in
    # this module need the surveillance dataset specifically.
    surv = [row for row in rows if row["record_type"] == "surveillance" and row["source"] == "synthetic"]
    assert surv, "demo surveillance dataset should be auto-loaded"
    return surv[0]["id"]
