"""Early-warning alert engine (research signals — never confirmed events).

All alerts generated here are model-derived surveillance signals that require
human/public-health review. Each alert carries date, location, evidence,
model reference, confidence/uncertainty note and an explanation.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from app.db.models import Alert


def generate_alerts(db: Session, df: pd.DataFrame, forecast_rows: list[dict], model_ref: str | None) -> list[Alert]:
    """Scan surveillance data + forecasts and persist any signals found.

    Rules (relative, dataset-derived — no invented absolute thresholds):
    1. Level alert  — last 4 weeks' mean above the historical 90th percentile.
    2. Trend alert  — positive slope over last 8 weeks that is unusually steep
       vs the same region's historical 8-week slope distribution (>= p90).
    3. Forecast alert — median forecast for weeks 1-4 exceeds the same p90.
    """
    alerts: list[Alert] = []
    d = df.copy()
    d["week_start_date"] = pd.to_datetime(d["week_start_date"])
    d = d.sort_values(["region", "week_start_date"])

    for region, g in d.groupby("region", observed=True):
        series = g.set_index("week_start_date")["malaria_cases"].astype(float)
        if len(series) < 30:
            continue
        p90 = float(series.quantile(0.90))
        recent = series.iloc[-4:]

        # 1. Level alert
        if float(recent.mean()) > p90:
            alerts.append(
                Alert(
                    alert_type="transmission",
                    severity="warning",
                    region=region,
                    title=f"Unusual increase in observed transmission — {region}",
                    evidence={
                        "last_4_week_mean": round(float(recent.mean()), 1),
                        "historical_p90": round(p90, 1),
                        "last_week": str(series.index[-1].date()),
                    },
                    model_ref=model_ref,
                    confidence=None,
                    explanation=(
                        "The mean of the last 4 observed weeks exceeds the 90th percentile of "
                        "this region's own historical distribution in the loaded dataset. This is a "
                        "relative, data-derived signal, not a confirmed outbreak."
                    ),
                )
            )

        # 2. Trend alert
        if len(series) >= 8:
            recent8 = series.iloc[-8:]
            slope = float(np.polyfit(range(8), recent8.to_numpy(), 1)[0])
            hist_slopes = _historical_slopes(series, window=8)
            if hist_slopes:
                thr = float(np.quantile(hist_slopes, 0.90))
                if slope > thr > 0:
                    alerts.append(
                        Alert(
                            alert_type="trend",
                            severity="warning",
                            region=region,
                            title=f"Steep upward trend detected — {region}",
                            evidence={
                                "recent_8week_slope_per_week": round(slope, 2),
                                "historical_slope_p90": round(thr, 2),
                                "window_end": str(series.index[-1].date()),
                            },
                            model_ref=model_ref,
                            confidence=None,
                            explanation=(
                                "The most recent 8-week slope exceeds the 90th percentile of all "
                                "historical 8-week slopes for this region in the loaded dataset."
                            ),
                        )
                    )

    # 3. Forecast alerts (next 4 weeks aggregate)
    fdf = pd.DataFrame(forecast_rows)
    if not fdf.empty:
        f4 = fdf[(fdf["horizon_weeks"] >= 1) & (fdf["horizon_weeks"] <= 4)]
        agg = f4.groupby("region")["predicted_cases"].median()
        for region, med in agg.items():
            g = d[d["region"] == region]["malaria_cases"].astype(float)
            if len(g) < 30:
                continue
            p90 = float(g.quantile(0.90))
            if med > p90:
                alerts.append(
                    Alert(
                        alert_type="forecast",
                        severity="info",
                        region=region,
                        title=f"Model predicts elevated transmission (next 4 weeks) — {region}",
                        evidence={
                            "median_predicted_weekly_cases": round(float(med), 1),
                            "historical_p90": round(p90, 1),
                        },
                        model_ref=model_ref,
                        confidence=None,
                        explanation=(
                            "Median model prediction for the next 4 weeks exceeds the historical "
                            "90th percentile of observed weekly cases in the loaded dataset. "
                            "Predictions carry uncertainty and assume environmental persistence."
                        ),
                    )
                )

    # Deduplicate: skip if an open alert with the same type+region already exists
    existing = {
        (a.alert_type, a.region)
        for a in db.query(Alert).filter(Alert.status == "open").all()
    }
    fresh = [a for a in alerts if (a.alert_type, a.region) not in existing]
    db.add_all(fresh)
    db.commit()
    for a in fresh:
        db.refresh(a)
    return fresh


def _historical_slopes(series: pd.Series, window: int = 8) -> list[float]:
    """All consecutive non-overlapping-step slopes over the historical series."""
    vals = series.to_numpy()
    slopes = []
    step = window // 2
    for i in range(0, len(vals) - window + 1, step):
        slopes.append(float(np.polyfit(range(window), vals[i : i + window], 1)[0]))
    return slopes
