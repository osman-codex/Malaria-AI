"""Synthetic DEMONSTRATION dataset generator (software testing only).

These data are simulated from a seasonal, environmentally-driven model and are
NOT real Ghana surveillance data. Every record carries source='synthetic' and
is_synthetic=True so the UI can display the mandatory
"DEMONSTRATION DATA — NOT REAL SURVEILLANCE DATA" banner.

The seasonal patterns are qualitatively inspired by published descriptions of
Ghanaian malaria seasonality (bimodal rains in the south, unimodal in the
north) but the values are simulated and carry no scientific authority.

For demonstration purposes, the final weeks include a scripted "late-season
upswing" in a few regions so that the early-warning engine, risk categories
and forecast comparisons have visible signals to display. This upswing is a
storytelling device for the demo — it is inserted after simulation and clearly
part of the synthetic scenario, not real epidemiology.
"""
from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd

# Illustrative relative population weights by region (approximate, for shaping
# simulated case counts only — not census figures).
REGION_POP_WEIGHTS: dict[str, float] = {
    "Greater Accra Region": 5.5,
    "Ashanti Region": 6.2,
    "Eastern Region": 3.4,
    "Western Region": 2.6,
    "Central Region": 2.7,
    "Volta Region": 2.1,
    "Northern Region": 2.4,
    "Upper East Region": 1.4,
    "Upper West Region": 0.95,
    "Bono Region": 1.6,
    "Bono East Region": 1.5,
    "Ahafo Region": 0.83,
    "Oti Region": 1.0,
    "Western North Region": 1.0,
    "Savannah Region": 0.76,
    "North East Region": 0.95,
}

# Regions with unimodal rainfall regime (north of ~8°N).
NORTHERN_REGIONS = {
    "Northern Region",
    "Upper East Region",
    "Upper West Region",
    "Savannah Region",
    "North East Region",
}

# Illustrative baseline transmission intensity factor (dimensionless).
REGION_BASELINE: dict[str, float] = {
    "Greater Accra Region": 0.45,
    "Ashanti Region": 0.85,
    "Eastern Region": 0.9,
    "Western Region": 0.8,
    "Central Region": 0.85,
    "Volta Region": 0.9,
    "Northern Region": 1.35,
    "Upper East Region": 1.4,
    "Upper West Region": 1.3,
    "Bono Region": 1.0,
    "Bono East Region": 1.1,
    "Ahafo Region": 1.0,
    "Oti Region": 1.15,
    "Western North Region": 1.05,
    "Savannah Region": 1.3,
    "North East Region": 1.35,
}

# Scripted demo scenario: late-series upswing (outbreak storytelling).
# region -> (start_weeks_before_end, multiplier_growth_per_week)
UPSWING_SCENARIO: dict[str, tuple[int, float]] = {
    "Northern Region": (10, 1.32),   # strong sustained rise
    "Upper East Region": (8, 1.28),  # strong rise
    "Ashanti Region": (6, 1.22),     # moderate rise in the biggest region
    "Greater Accra Region": (5, 1.18),  # mild urban rise
}

STANDARD_COLUMNS = [
    "region",
    "week_start_date",
    "epi_week",
    "year",
    "malaria_cases",
    "suspected_cases",
    "test_positivity_rate",
    "rainfall_mm",
    "temperature_mean_c",
    "humidity_pct",
    "ndvi",
    "population_illustrative",
]


def generate_demo_surveillance(
    n_weeks: int = 160,
    seed: int = 42,
    end_date: date | None = None,
) -> pd.DataFrame:
    """Simulate weekly region-level malaria surveillance + environment."""
    rng = np.random.default_rng(seed)
    end = pd.Timestamp(end_date or date.today()).to_period("W-SUN").start_time
    weeks = pd.date_range(end=end, periods=n_weeks, freq="W-SUN")

    frames: list[pd.DataFrame] = []
    for region, pop_w in REGION_POP_WEIGHTS.items():
        northern = region in NORTHERN_REGIONS
        baseline = REGION_BASELINE[region]
        n = len(weeks)
        doy = np.array([d.dayofyear for d in weeks], dtype=float)

        if northern:  # unimodal: peak ~Aug-Sep
            rain_season = np.clip(np.sin(np.pi * ((doy - 120) / 200.0)), 0, 1.2)
        else:  # bimodal: major peak ~May-Jun, minor ~Oct
            major = np.exp(-0.5 * ((doy - 160) / 30.0) ** 2)
            minor = 0.45 * np.exp(-0.5 * ((doy - 285) / 26.0) ** 2)
            rain_season = major + minor

        rain_noise = rng.gamma(shape=3.0, scale=0.35, size=n)
        rainfall = np.clip(55.0 * rain_season * rain_noise, 0, 220)

        tbase = 26.5 if northern else 27.0
        temperature = tbase - 1.6 * np.cos(2 * np.pi * (doy - 40) / 365.0) + rng.normal(0, 0.6, n)
        humidity = np.clip(62 + 0.22 * rainfall + rng.normal(0, 3, n), 35, 98)
        ndvi = np.clip(0.30 + 0.0035 * rainfall + rng.normal(0, 0.03, n), 0.08, 0.85)

        # Environmental suitability drives transmission with a lag
        # (rainfall -> breeding sites -> cases ~3 weeks later).
        rain_lag = np.roll(rainfall, 3)
        rain_lag[:3] = rainfall[:3]
        temp_suit = np.exp(-((temperature - 27.0) ** 2) / (2 * 4.5**2))
        suit = 0.55 + 0.0038 * rain_lag + 0.9 * temp_suit * (0.4 + 0.0030 * rain_lag)

        scale = baseline * pop_w * 6.0
        lam = scale * suit
        # Over-dispersed counts
        cases = rng.negative_binomial(n=6.0, p=6.0 / (6.0 + lam))
        cases = np.clip(cases, 0, None).astype(float)

        # --- Scripted late-season upswing (demo scenario) -----------------
        if region in UPSWING_SCENARIO:
            start_back, growth = UPSWING_SCENARIO[region]
            k = n - start_back  # index where upswing begins
            mult = growth ** np.arange(1, n - k + 1, dtype=float)
            cases[k:] = cases[k:] * mult
            # keep whole numbers
            cases = np.clip(np.round(cases), 0, None)

        cases = cases.astype(int)

        tests = np.clip((cases / rng.uniform(0.25, 0.55, n)).astype(int), cases, None)
        suspected = np.clip((tests * rng.uniform(1.05, 1.5, n)).astype(int), tests, None)
        positivity = np.where(suspected > 0, cases / np.maximum(suspected, 1) * 100.0, 0.0)

        frames.append(
            pd.DataFrame(
                {
                    "region": region,
                    "week_start_date": weeks.strftime("%Y-%m-%d"),
                    "epi_week": weeks.isocalendar().week.values,
                    "year": weeks.year,
                    "malaria_cases": cases,
                    "suspected_cases": suspected,
                    "test_positivity_rate": np.round(positivity, 1),
                    "rainfall_mm": np.round(rainfall, 1),
                    "temperature_mean_c": np.round(temperature, 1),
                    "humidity_pct": np.round(humidity, 1),
                    "ndvi": np.round(ndvi, 3),
                    "population_illustrative": pop_w,
                }
            )
        )

    df = pd.concat(frames, ignore_index=True)
    return df[STANDARD_COLUMNS]


def summarize_for_profile(df: pd.DataFrame) -> dict:
    """Lightweight dataset profile for the data-quality report."""
    profile: dict = {
        "n_rows": int(len(df)),
        "n_columns": int(df.shape[1]),
        "missing_by_column": {c: int(df[c].isna().sum()) for c in df.columns},
        "duplicate_rows": int(df.duplicated().sum()),
    }
    num = df.select_dtypes(include=[np.number])
    profile["numeric_summary"] = {
        c: {
            "min": float(num[c].min()),
            "mean": float(num[c].mean()),
            "max": float(num[c].max()),
        }
        for c in num.columns
    }
    return profile
