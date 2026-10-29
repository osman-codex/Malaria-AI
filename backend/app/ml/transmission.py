"""Transmission prediction and forecasting engine (MVP, Phase 1).

Scientific design notes
-----------------------
- Supervised framing: for horizon h, the target is malaria_cases at week t+h,
  predicted from case history (lags 1-4), current + lagged environmental
  conditions, seasonality (cyclic week-of-year) and region fixed effects.
- Validation is strictly temporal: models are trained on earlier weeks and
  evaluated on later weeks. No random shuffling of time-series rows.
- Metrics: MAE, RMSE, MAPE (excluding zero-observed weeks), sMAPE and R2.
  R2 is reported for completeness only; for count data MAE/RMSE are primary.
- Uncertainty: prediction intervals are residual-based Gaussian approximations
  (test-set residual standard deviation). They quantify typical model error on
  this dataset, not calibrated probabilistic intervals.
- Risk categories are RELATIVE to the observed historical distribution of the
  loaded dataset (quantiles). The platform never invents absolute thresholds.
- Explanations (SHAP where available, otherwise single-feature perturbation)
  describe model behaviour, NOT causal effects.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.inspection import permutation_importance
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

TARGET = "malaria_cases"
ENV_COLS = ["rainfall_mm", "temperature_mean_c", "humidity_pct", "ndvi"]
CASE_LAGS = [1, 2, 3, 4]
DEFAULT_HORIZONS = [1, 2, 4, 8]
DEFAULT_MODELS = ["random_forest", "xgboost", "ridge"]

try:  # optional, used only when installed
    import shap  # type: ignore
    HAS_SHAP = True
except Exception:  # pragma: no cover
    HAS_SHAP = False


# --------------------------------------------------------------------------- #
# Feature engineering
# --------------------------------------------------------------------------- #
def build_supervised(df: pd.DataFrame, horizon: int) -> tuple[pd.DataFrame, pd.Series, pd.DataFrame]:
    """Build the supervised matrix for lead-horizon prediction.

    Returns (X, y, meta) where meta carries region/week for temporal splitting.
    """
    d = df.copy()
    d["week_start_date"] = pd.to_datetime(d["week_start_date"])
    d = d.sort_values(["region", "week_start_date"])

    parts: list[pd.DataFrame] = []
    for _region, g in d.groupby("region", observed=True):
        g = g.sort_values("week_start_date").copy()
        for lag in CASE_LAGS:
            g[f"cases_lag{lag}"] = g[TARGET].shift(lag)
        for c in ENV_COLS:
            if c in g.columns:
                g[f"{c}_lag1"] = g[c].shift(1)
        week = g["week_start_date"].dt.isocalendar().week.astype(float)
        g["sin_week"] = np.sin(2 * np.pi * week / 52.0)
        g["cos_week"] = np.cos(2 * np.pi * week / 52.0)
        g["target_lead"] = g[TARGET].shift(-horizon)
        parts.append(g)

    s = pd.concat(parts, ignore_index=True)
    needed = [TARGET] + [f"cases_lag{l}" for l in CASE_LAGS] + ["target_lead"]
    s = s.dropna(subset=[c for c in needed if c in s.columns]).reset_index(drop=True)

    base_features = (
        [f"cases_lag{l}" for l in CASE_LAGS]
        + [c for c in ENV_COLS if c in s.columns]
        + [f"{c}_lag1" for c in ENV_COLS if f"{c}_lag1" in s.columns]
        + ["sin_week", "cos_week"]
    )
    if "population_illustrative" in s.columns:
        base_features.append("population_illustrative")

    region_dummies = pd.get_dummies(s["region"], prefix="region", dtype=float)
    X = pd.concat([s[base_features].astype(float), region_dummies], axis=1)
    y = s["target_lead"].astype(float)
    meta = s[["region", "week_start_date", TARGET]].copy()
    meta["week_start_date"] = meta["week_start_date"].dt.strftime("%Y-%m-%d")
    return X, y, meta


def temporal_split(
    X: pd.DataFrame, y: pd.Series, meta: pd.DataFrame, train_fraction: float = 0.8
) -> dict[str, object]:
    """Chronological split on unique weeks (no leakage from the future)."""
    weeks = np.array(sorted(meta["week_start_date"].unique()))
    n_train_weeks = max(1, int(len(weeks) * train_fraction))
    train_weeks = set(weeks[:n_train_weeks])
    is_train = meta["week_start_date"].isin(train_weeks).to_numpy()
    return {
        "X_train": X[is_train],
        "y_train": y[is_train],
        "X_test": X[~is_train],
        "y_test": y[~is_train],
        "meta_test": meta[~is_train].reset_index(drop=True),
        "train_weeks": weeks[:n_train_weeks].tolist(),
        "test_weeks": weeks[n_train_weeks:].tolist(),
    }


# --------------------------------------------------------------------------- #
# Models
# --------------------------------------------------------------------------- #
def _make_model(model_type: str, seed: int):
    if model_type == "random_forest":
        return RandomForestRegressor(
            n_estimators=250, min_samples_leaf=2, random_state=seed, n_jobs=-1
        )
    if model_type == "xgboost":
        from xgboost import XGBRegressor

        return XGBRegressor(
            n_estimators=500,
            learning_rate=0.05,
            max_depth=4,
            subsample=0.9,
            colsample_bytree=0.9,
            reg_lambda=1.0,
            random_state=seed,
            n_jobs=-1,
            tree_method="hist",
            verbosity=0,
        )
    if model_type == "ridge":
        return Pipeline([("scaler", StandardScaler()), ("ridge", Ridge(alpha=1.0))])
    raise ValueError(f"Unknown model type: {model_type}")


def compute_metrics(y_true: np.ndarray, y_pred: np.ndarray) -> dict:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    err = y_pred - y_true
    nonzero = y_true != 0
    mape = float(np.mean(np.abs(err[nonzero] / y_true[nonzero])) * 100) if nonzero.any() else None
    denom = np.abs(y_true) + np.abs(y_pred)
    smape = float(np.mean(2 * np.abs(err) / np.where(denom == 0, 1, denom)) * 100)
    return {
        "n_test": int(len(y_true)),
        "MAE": float(mean_absolute_error(y_true, y_pred)),
        "RMSE": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "MAPE_pct": mape,
        "sMAPE_pct": smape,
        "R2": float(r2_score(y_true, y_pred)) if len(y_true) > 1 else None,
        "residual_std": float(np.std(err, ddof=1)) if len(err) > 1 else 0.0,
        "note": "MAE/RMSE are primary for count outcomes; R2 reported for completeness only.",
    }


def feature_importance(model, X_test: pd.DataFrame, y_test: pd.Series, seed: int, top: int = 12) -> list[dict]:
    """Permutation importance (model-agnostic) on the held-out test weeks."""
    try:
        r = permutation_importance(
            model, X_test, y_test, n_repeats=5, random_state=seed, scoring="neg_mean_absolute_error"
        )
        imp = r.importances_mean
    except Exception:
        imp = getattr(model, "feature_importances_", None)
        if imp is None:
            return []
    order = np.argsort(imp)[::-1][:top]
    return [
        {"feature": str(X_test.columns[i]), "importance": float(imp[i])}
        for i in order
        if imp[i] > 0
    ]


# --------------------------------------------------------------------------- #
# Training entry point
# --------------------------------------------------------------------------- #
def train_transmission_models(
    df: pd.DataFrame,
    horizons: list[int] | None = None,
    model_types: list[str] | None = None,
    seed: int = 42,
    train_fraction: float = 0.8,
    model_dir: str | Path = "models",
    dataset_id: int | None = None,
) -> dict:
    """Train/evaluate models for each horizon. Returns a results dict.

    The best model per horizon (lowest test MAE) is persisted as a joblib
    artifact together with full provenance metadata.
    """
    horizons = horizons or DEFAULT_HORIZONS
    model_types = model_types or DEFAULT_MODELS
    model_dir = Path(model_dir)
    model_dir.mkdir(parents=True, exist_ok=True)

    results: dict = {"horizons": {}, "provenance": {"seed": seed, "train_fraction": train_fraction}, "has_shap": HAS_SHAP}
    software = _software_versions()

    for h in horizons:
        X, y, meta = build_supervised(df, h)
        if len(X) < 30:
            results["horizons"][str(h)] = {"error": f"Insufficient rows after lag construction ({len(X)})."}
            continue
        split = temporal_split(X, y, meta, train_fraction)

        per_model = {}
        best_name, best_mae = None, float("inf")
        best_artifact = None
        for mt in model_types:
            try:
                t0 = time.time()
                model = _make_model(mt, seed)
                model.fit(split["X_train"], split["y_train"])  # type: ignore[arg-type]
                pred = model.predict(split["X_test"])  # type: ignore[arg-type]
                metrics = compute_metrics(split["y_test"].to_numpy(), pred)
                metrics["fit_seconds"] = round(time.time() - t0, 2)
                fi = feature_importance(model, split["X_test"], split["y_test"], seed)
                per_model[mt] = {"metrics": metrics, "feature_importance": fi}
                if metrics["MAE"] < best_mae:
                    best_mae, best_name = metrics["MAE"], mt
                    best_artifact = {
                        "model": model,
                        "model_type": mt,
                        "feature_names": list(X.columns),
                        "horizon": h,
                        "metrics": metrics,
                        "feature_importance": fi,
                        "train_weeks": split["train_weeks"],
                        "test_weeks": split["test_weeks"],
                        "seed": seed,
                        "software": software,
                        "trained_at": pd.Timestamp.now(tz="UTC").isoformat(),
                    }
            except Exception as e:  # keep training other models
                per_model[mt] = {"error": str(e)}

        if best_artifact is not None:
            fname = f"transmission_{best_name}_h{h}_ds{dataset_id or 0}.joblib"
            path = model_dir / fname
            joblib.dump(best_artifact, path)
            best_artifact["artifact_path"] = str(path)

        results["horizons"][str(h)] = {
            "models": per_model,
            "best_model": best_name,
            "best_metrics": best_artifact["metrics"] if best_artifact else None,
            "n_train_rows": int(len(split["X_train"])),
            "n_test_rows": int(len(split["X_test"])),
            "artifact_path": best_artifact["artifact_path"] if best_artifact else None,
            "feature_importance": best_artifact["feature_importance"] if best_artifact else [],
        }
    return results


def _software_versions() -> dict:
    import sklearn

    versions = {"python": platform_python(), "scikit-learn": sklearn.__version__}
    try:
        import xgboost

        versions["xgboost"] = xgboost.__version__
    except Exception:
        pass
    try:
        import pandas

        versions["pandas"] = pandas.__version__
    except Exception:
        pass
    try:
        import numpy

        versions["numpy"] = numpy.__version__
    except Exception:
        pass
    return versions


def platform_python() -> str:
    import sys

    return sys.version.split()[0]


# --------------------------------------------------------------------------- #
# Forecasting from trained artifacts
# --------------------------------------------------------------------------- #
def _latest_feature_row(df: pd.DataFrame, horizon: int) -> pd.DataFrame:
    """Feature vector at the last observed week t for each region."""
    d = df.copy()
    d["week_start_date"] = pd.to_datetime(d["week_start_date"])
    d = d.sort_values(["region", "week_start_date"])
    rows = []
    for region, g in d.groupby("region", observed=True):
        g = g.sort_values("week_start_date").copy()
        for lag in CASE_LAGS:
            g[f"cases_lag{lag}"] = g[TARGET].shift(lag)
        for c in ENV_COLS:
            if c in g.columns:
                g[f"{c}_lag1"] = g[c].shift(1)
        last = g.iloc[-1]
        week = pd.Timestamp(last["week_start_date"]).isocalendar().week
        row = {"region": region, "week_start_date": pd.Timestamp(last["week_start_date"])}
        for feat in (
            [f"cases_lag{l}" for l in CASE_LAGS]
            + [c for c in ENV_COLS if c in g.columns]
            + [f"{c}_lag1" for c in ENV_COLS if f"{c}_lag1" in g.columns]
        ):
            row[feat] = float(last[feat]) if pd.notna(last[feat]) else 0.0
        row["sin_week"] = float(np.sin(2 * np.pi * week / 52.0))
        row["cos_week"] = float(np.cos(2 * np.pi * week / 52.0))
        if "population_illustrative" in g.columns:
            row["population_illustrative"] = float(last["population_illustrative"])
        rows.append(row)
    f = pd.DataFrame(rows)
    f["forecast_week"] = f["week_start_date"] + pd.to_timedelta(7 * horizon, unit="D")
    return f


def _design_matrix(feats: pd.DataFrame, artifact: dict) -> pd.DataFrame:
    """Assemble the prediction matrix, activating each row's region dummy."""
    X = feats.reindex(columns=artifact["feature_names"], fill_value=0.0).astype(float)
    X = X.drop(columns=["forecast_week", "week_start_date"], errors="ignore")
    X = X[artifact["feature_names"]]
    ff = feats.reset_index(drop=True)
    for i, r in ff.iterrows():
        col = f"region_{r['region']}"
        if col in X.columns:
            X.iloc[i, X.columns.get_loc(col)] = 1.0
    return X


def forecast_from_artifacts(
    df: pd.DataFrame, model_dir: str | Path, horizons: list[int] | None = None, dataset_id: int | None = None
) -> list[dict]:
    """Produce forecasts for the next weeks using persisted best models.

    Environmental features are held at their last observed value
    (persistence assumption) and stated in the API response.
    """
    horizons = horizons or DEFAULT_HORIZONS
    model_dir = Path(model_dir)
    hist = df[TARGET].astype(float)

    quantiles = {
        "q50": float(hist.quantile(0.50)),
        "q75": float(hist.quantile(0.75)),
        "q90": float(hist.quantile(0.90)),
    }

    out: list[dict] = []
    for h in horizons:
        # prefer dataset-specific artifact, fall back to shared artifact
        candidates = [f"transmission_*_h{h}_ds{dataset_id or 0}.joblib", f"transmission_*_h{h}_ds*.joblib"]
        path = None
        for pattern in candidates:
            matches = sorted(model_dir.glob(pattern))
            if matches:
                path = matches[-1]
                break
        if path is None:
            continue
        art = joblib.load(path)
        feats = _latest_feature_row(df, h)
        X = _design_matrix(feats, art)
        pred = art["model"].predict(X)
        rstd = float(art["metrics"].get("residual_std", 0.0))

        for i, row in feats.reset_index(drop=True).iterrows():
            p = float(max(0.0, pred[i]))
            category = _risk_category(p, quantiles)
            out.append(
                {
                    "region": row["region"],
                    "horizon_weeks": h,
                    "last_observed_week": str(row["week_start_date"].date()),
                    "forecast_week": str(row["forecast_week"].date()),
                    "predicted_cases": round(p, 1),
                    "interval_low": round(max(0.0, p - 1.96 * rstd), 1),
                    "interval_high": round(p + 1.96 * rstd, 1),
                    "risk_category": category,
                    "model_type": art["model_type"],
                    "interval_method": "residual-based Gaussian approximation (not calibrated probabilistic intervals)",
                }
            )
    return out


def _risk_category(predicted: float, q: dict[str, float]) -> str:
    """Risk category RELATIVE to the dataset's own historical distribution."""
    if predicted >= q["q90"]:
        return "very high"
    if predicted >= q["q75"]:
        return "high"
    if predicted >= q["q50"]:
        return "moderate"
    return "low"


# --------------------------------------------------------------------------- #
# Explanations
# --------------------------------------------------------------------------- #
def explain_forecast(
    df: pd.DataFrame, model_dir: str | Path, horizon: int = 1, dataset_id: int | None = None
) -> dict:
    """Explain the next-week forecast per region.

    Uses SHAP TreeExplainer when available (tree models); otherwise a
    single-feature perturbation heuristic. Both describe model behaviour,
    not causal effects.
    """
    model_dir = Path(model_dir)
    candidates = [f"transmission_*_h{horizon}_ds{dataset_id or 0}.joblib", f"transmission_*_h{horizon}_ds*.joblib"]
    path = None
    for pattern in candidates:
        matches = sorted(model_dir.glob(pattern))
        if matches:
            path = matches[-1]
            break
    if path is None:
        return {"available": False, "reason": "No trained model artifact found for this horizon."}

    art = joblib.load(path)
    feats = _latest_feature_row(df, horizon)
    X = _design_matrix(feats, art)

    method = "single-feature perturbation (model behaviour, not causal effects)"
    contribs: dict[str, list[dict]] = {}
    model = art["model"]
    base_pred = model.predict(X)

    if HAS_SHAP and art["model_type"] in ("random_forest", "xgboost"):
        try:
            inner = model.named_steps.get("ridge") if isinstance(model, Pipeline) else model
            if art["model_type"] == "xgboost":
                explainer = shap.TreeExplainer(inner)
            else:
                explainer = shap.TreeExplainer(inner)
            sv = explainer.shap_values(X)
            method = "SHAP (TreeExplainer) — model behaviour, not causal effects"
            for i, region in enumerate(feats["region"]):
                vals = sv[i] if np.ndim(sv[i]) == 1 else np.asarray(sv).reshape(len(X), -1)[i]
                pairs = sorted(zip(art["feature_names"], np.asarray(vals).ravel()), key=lambda kv: -abs(kv[1]))
                contribs[str(region)] = [
                    {"feature": f, "contribution": round(float(v), 3)} for f, v in pairs[:8]
                ]
        except Exception:
            contribs = {}

    if not contribs:
        # Perturbation fallback: replace one feature with its training-median
        # and record the change in prediction.
        medians = X.median()
        for i, region in enumerate(feats["region"]):
            row0 = X.iloc[[i]]
            base = float(base_pred[i])
            deltas = []
            for f in art["feature_names"]:
                if f.startswith("region_"):
                    continue
                row1 = row0.copy()
                row1[f] = float(medians[f])
                d = float(model.predict(row1)[0]) - base
                deltas.append({"feature": f, "contribution": round(d, 3)})
            deltas.sort(key=lambda kv: -abs(kv["contribution"]))
            contribs[str(region)] = deltas[:8]

    return {
        "available": True,
        "horizon_weeks": horizon,
        "method": method,
        "regions": contribs,
        "predicted_baseline": [round(float(p), 1) for p in base_pred],
    }


def export_forecast_csv(rows: list[dict]) -> str:
    import io

    buf = io.StringIO()
    if not rows:
        return ""
    pd.DataFrame(rows).to_csv(buf, index=False)
    return buf.getvalue()


def json_ready(obj) -> bool:  # pragma: no cover - tiny helper
    try:
        json.dumps(obj)
        return True
    except TypeError:
        return False
