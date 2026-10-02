"""Data ingestion: parse, profile, validate and standardise uploaded tables.

Supported formats: CSV, TSV, Excel (.xlsx), JSON (records or GeoJSON-like with
a `features` array), GeoJSON (attribute table; geometry dropped for analysis).

Scientific governance rules enforced here:
- No value imputation happens silently; missing values are reported, never invented.
- Region names are fuzzy-matched to Ghana's 16 administrative regions and the
  mapping is reported back to the user.
"""
from __future__ import annotations

import io
import json
from datetime import date

import numpy as np
import pandas as pd

CANONICAL_REGIONS = [
    "Ahafo Region",
    "Ashanti Region",
    "Bono East Region",
    "Bono Region",
    "Central Region",
    "Eastern Region",
    "Greater Accra Region",
    "North East Region",
    "Northern Region",
    "Oti Region",
    "Savannah Region",
    "Upper East Region",
    "Upper West Region",
    "Volta Region",
    "Western North Region",
    "Western Region",
]

_REGION_LOOKUP = {r.replace(" Region", "").lower(): r for r in CANONICAL_REGIONS}

COLUMN_SYNONYMS: dict[str, list[str]] = {
    "region": ["region", "region_name", "admin1", "adm1", "province", "regionname"],
    "district": ["district", "district_name", "admin2", "adm2", "districtname"],
    "week_start_date": ["week_start_date", "date", "week", "week_start", "epi_week_start", "sample_date", "report_date"],
    "malaria_cases": ["malaria_cases", "mal_cases", "cases", "confirmed_cases", "malaria_case_count", "positive_cases"],
    "suspected_cases": ["suspected_cases", "suspected", "tested", "total_tested"],
    "test_positivity_rate": ["test_positivity_rate", "positivity", "test_positivity", "slide_positivity"],
    "rainfall_mm": ["rainfall_mm", "rainfall", "rain", "precip", "precipitation", "precip_mm", "chirps_rainfall"],
    "temperature_mean_c": ["temperature_mean_c", "temperature", "temp", "temp_mean", "temperature_c", "tmean"],
    "humidity_pct": ["humidity_pct", "humidity", "relative_humidity", "rh"],
    "ndvi": ["ndvi", "evi", "vegetation_index"],
    "population_illustrative": ["population_illustrative", "population", "pop", "pop_density"],
    "year": ["year", "yr"],
    "epi_week": ["epi_week", "week_number", "epidemiological_week"],
}

GENOMIC_SYNONYMS: dict[str, list[str]] = {
    "sample_id": ["sample_id", "sampleid", "sid", "specimen_id"],
    "gene": ["gene", "locus", "target_gene"],
    "mutation": ["mutation", "variant", "aa_change", "snp", "allele"],
    "region": COLUMN_SYNONYMS["region"],
    "district": COLUMN_SYNONYMS["district"],
    "sample_date": ["sample_date", "date", "collection_date", "sampling_date"],
}


class IngestionError(ValueError):
    pass


def read_table(filename: str, raw: bytes) -> tuple[pd.DataFrame, str]:
    """Parse an uploaded file into a DataFrame. Returns (df, format)."""
    name = filename.lower()
    if name.endswith((".csv", ".txt")):
        return pd.read_csv(io.BytesIO(raw)), "csv"
    if name.endswith((".tsv",)):
        return pd.read_csv(io.BytesIO(raw), sep="\t"), "tsv"
    if name.endswith((".xlsx", ".xls")):
        return pd.read_excel(io.BytesIO(raw)), "excel"
    if name.endswith((".json", ".geojson")):
        payload = json.loads(raw.decode("utf-8", errors="replace"))
        if isinstance(payload, dict) and "features" in payload:
            rows = [f.get("properties", {}) for f in payload["features"]]
            return pd.DataFrame(rows), "geojson"
        if isinstance(payload, list):
            return pd.DataFrame(payload), "json"
        raise IngestionError("JSON must be a list of records or GeoJSON with a 'features' array.")
    raise IngestionError(f"Unsupported file format: {filename}")


def suggest_column_mapping(columns: list[str], record_type: str = "surveillance") -> dict[str, str]:
    """Heuristic mapping of user columns to standard variable names."""
    mapping: dict[str, str] = {}
    norm = {c: c.strip().lower().replace(" ", "_").replace("-", "_") for c in columns}
    synonyms_by_std = GENOMIC_SYNONYMS if record_type in ("genomic", "resistance") else COLUMN_SYNONYMS
    for std, synonyms in synonyms_by_std.items():
        for user_col, low in norm.items():
            if low in synonyms and user_col not in mapping.values():
                mapping[user_col] = std
                break
    return mapping


def normalise_region(value: str) -> tuple[str | None, bool]:
    """Match a region label to a canonical Ghana region. Returns (canonical, exact)."""
    if not isinstance(value, str):
        return None, False
    key = value.strip().lower().replace(" region", "").replace("region", "").strip()
    canon = _REGION_LOOKUP.get(key)
    if canon:
        return canon, value.strip() == canon
    return None, False


def standardise(df: pd.DataFrame, mapping: dict[str, str] | None = None) -> tuple[pd.DataFrame, dict]:
    """Apply the user-approved column mapping and coerce standard types.

    Returns (standardised_df, report). Never drops or imputes rows silently.
    """
    report: dict = {"renamed": {}, "region_matches": {}, "unmatched_regions": [], "type_coercions": {}}
    if mapping:
        df = df.rename(columns={k: v for k, v in mapping.items() if k in df.columns})
        report["renamed"] = {k: v for k, v in mapping.items() if k in df.columns}

    if "region" in df.columns:
        canon_series, unmatched, matches = [], set(), {}
        for v in df["region"]:
            canon, exact = normalise_region(v) if v is not None else (None, False)
            canon_series.append(canon if canon else v)
            if canon:
                matches[str(v)] = canon
                if not exact:
                    report["region_matches"][str(v)] = canon
            else:
                if isinstance(v, str):
                    unmatched.add(v)
        df = df.assign(region=canon_series)
        report["unmatched_regions"] = sorted(unmatched)

    if "week_start_date" in df.columns:
        parsed = pd.to_datetime(df["week_start_date"], errors="coerce", format="mixed", utc=True)
        n_bad = int(parsed.isna().sum())
        df = df.assign(week_start_date=parsed.dt.strftime("%Y-%m-%d"))
        report["type_coercions"]["week_start_date"] = {"unparseable": n_bad}

    for col in ("malaria_cases", "suspected_cases", "epi_week", "year", "population_illustrative"):
        if col in df.columns:
            before_nonnull = int(df[col].notna().sum())
            coerced = pd.to_numeric(df[col], errors="coerce")
            report["type_coercions"][col] = {
                "coerced_to_numeric": before_nonnull - int(coerced.notna().sum())
            }
            df = df.assign(**{col: coerced})

    for col in ("test_positivity_rate", "rainfall_mm", "temperature_mean_c", "humidity_pct", "ndvi"):
        if col in df.columns:
            df = df.assign(**{col: pd.to_numeric(df[col], errors="coerce")})

    return df, report


def profile_dataframe(df: pd.DataFrame) -> dict:
    """Data-quality report: missingness, duplicates, dtypes, numeric ranges."""
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    profile: dict = {
        "n_rows": int(len(df)),
        "n_columns": int(df.shape[1]),
        "columns": {c: str(t) for c, t in df.dtypes.items()},
        "missing_by_column": {c: int(df[c].isna().sum()) for c in df.columns},
        "duplicate_rows": int(df.duplicated().sum()),
        "numeric_summary": {
            c: {
                "min": None if df[c].dropna().empty else float(df[c].min()),
                "mean": None if df[c].dropna().empty else float(df[c].mean()),
                "max": None if df[c].dropna().empty else float(df[c].max()),
            }
            for c in numeric_cols
        },
        "generated_on": str(date.today()),
    }
    issues: list[str] = []
    if profile["duplicate_rows"] > 0:
        issues.append(f"{profile['duplicate_rows']} duplicate row(s) detected.")
    for c, m in profile["missing_by_column"].items():
        if m > 0:
            issues.append(f"Column '{c}' has {m} missing value(s).")
    profile["issues"] = issues
    return profile
