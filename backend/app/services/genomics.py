"""Plasmodium genomic / antimalarial-resistance module (Phase-1 scaffold).

Governance rules implemented here (per master specification, sections 7-8):
- The platform NEVER equates a genetic marker with phenotypic resistance.
- Interpretation thresholds must be supplied by the researcher; none are invented.
- With no uploaded genomic data, every endpoint returns an explicit
  "awaiting validated data" response instead of simulated results.
- When a variant table IS uploaded, this module computes only descriptive
  statistics (counts and, when sample identifiers are present, frequencies)
  and labels them as descriptive, not diagnostic.

Expected uploaded table columns (CSV/TSV/XLSX):
    sample_id, gene, mutation, region, sample_date
Optional: district, genotype_quality, phenotyped (0/1), phenotype_value
"""
from __future__ import annotations

import pandas as pd

# Catalogue of published resistance-associated loci. This is a vocabulary of
# marker NAMES for data harmonisation — NOT an interpretation matrix.
KNOWN_RESISTANCE_MARKERS: list[dict] = [
    {"gene": "kelch13", "label": "K13 propeller", "drug_class": "artemisinin",
     "note": "Validated nonsynonymous propeller mutations are associated with artemisinin partial resistance; the operational definition must be supplied by the researcher."},
    {"gene": "pfmdr1", "label": "PfMDR1", "drug_class": "aminoquinoline / artemisinin partner drugs",
     "note": "Copy-number and point mutations have been associated with partner-drug selection; interpretation is context-dependent."},
    {"gene": "pfcrt", "label": "PfCRT", "drug_class": "chloroquine / piperaquine",
     "note": "Historically associated with chloroquine resistance; piperaquine associations are region-specific."},
    {"gene": "pfdhfr", "label": "PfDHFR", "drug_class": "antifolates (pyrimethamine)",
     "note": "Quintuple-mutant definitions are study-specific."},
    {"gene": "pfdhps", "label": "PfDHPS", "drug_class": "antifolates (sulfadoxine)",
     "note": "Part of SP resistance definitions; A581G has been linked to SP failure in pregnancy in some settings."},
    {"gene": "pfcytb", "label": "PfCYTb", "drug_class": "atovaquone",
     "note": "Y268 codon mutations associated with atovaquone treatment failure."},
    {"gene": "pfk13-cnv", "label": "K13 copy number", "drug_class": "artemisinin",
     "note": "Copy-number variation requires specialised assays; not inferred from SNP calls."},
]

REQUIRED_COLUMNS = ["sample_id", "gene", "mutation", "region", "sample_date"]


def awaiting_data_response(module: str) -> dict:
    """Standard response when no validated genomic data are loaded."""
    return {
        "module": module,
        "status": "awaiting_validated_data",
        "message": (
            "No genomic dataset has been loaded. This module implements no simulated "
            "results. Upload a variant table (sample_id, gene, mutation, region, "
            "sample_date) through Data Explorer, or connect a KCCR genomic dataset."
        ),
        "required_columns": REQUIRED_COLUMNS,
        "known_markers_catalogue": KNOWN_RESISTANCE_MARKERS,
    }


def validate_variant_table(df: pd.DataFrame) -> dict:
    """Check schema of an uploaded variant table before acceptance."""
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    return {
        "valid": len(missing) == 0,
        "missing_required_columns": missing,
        "n_rows": int(len(df)),
        "columns_detected": list(df.columns),
    }


def marker_frequencies(df: pd.DataFrame) -> dict:
    """Descriptive marker statistics for an uploaded variant table.

    Frequencies (marker-positive samples / genotyped samples per stratum) are
    computed ONLY when sample_id exists, so the denominator is meaningful.
    Otherwise raw counts are reported. Output is descriptive only.
    """
    d = df.copy()
    has_samples = "sample_id" in d.columns and d["sample_id"].notna().any()

    by_region = _stratify(d, ["region"], has_samples)
    by_region_time = None
    if "sample_date" in d.columns:
        dt = pd.to_datetime(d["sample_date"], errors="coerce")
        if dt.notna().any():
            d = d.assign(_year=dt.dt.year)
            by_region_time = _stratify(d, ["region", "_year"], has_samples)

    marker_totals = (
        d.groupby(["gene", "mutation"], dropna=False).size().reset_index(name="n_calls")
        .sort_values("n_calls", ascending=False)
        .head(50)
        .to_dict(orient="records")
    )

    return {
        "status": "descriptive_statistics_only",
        "interpretation": (
            "These are descriptive counts"
            + (" and frequencies of marker-positive samples among genotyped samples." if has_samples else ". No sample identifiers were available, so no frequencies are computed.")
            + " A detected genetic marker is NOT phenotypic drug resistance."
        ),
        "n_rows": int(len(d)),
        "n_samples": int(d["sample_id"].nunique()) if has_samples else None,
        "by_region": by_region,
        "by_region_year": by_region_time,
        "top_markers": marker_totals,
        "unusual_increase_note": (
            "Emerging-resistance trend detection requires validated baseline frequencies "
            "and thresholds supplied by the researcher; not computed by default."
        ),
    }


def _stratify(d: pd.DataFrame, by: list[str], has_samples: bool) -> list[dict]:
    by = [c for c in by if c in d.columns]
    if not by:
        return []
    total = d.groupby(by, dropna=False).agg(
        n_calls=("gene", "size"),
        **({"n_samples": ("sample_id", "nunique")} if has_samples else {}),
    )
    pos = (
        d.drop_duplicates(subset=(["sample_id"] + by) if has_samples else None)
        .groupby(by, dropna=False)
        .agg(n_marker_positive_samples=("gene", "size"))
    )
    merged = total.join(pos, how="outer").reset_index().fillna({"n_marker_positive_samples": 0})
    if has_samples and "n_samples" in merged.columns:
        merged["frequency"] = (merged["n_marker_positive_samples"] / merged["n_samples"]).round(4)
    return merged.to_dict(orient="records")


# ------------------------------------------------------------------------- #
# Synthetic DEMONSTRATION variant table + chart payload (clearly labelled)
# ------------------------------------------------------------------------- #

# Illustrative per-gene baseline marker frequencies (dimensionless, chosen
# only to make demo charts informative; NOT published estimates).
_DEMO_GENE_BASE: dict[str, float] = {
    "pfcrt": 0.32,
    "pfmdr1": 0.24,
    "pfdhfr": 0.18,
    "pfdhps": 0.11,
    "kelch13": 0.05,
    "pfcytb": 0.02,
}

_DEMO_MUTATIONS: dict[str, list[str]] = {
    "pfcrt": ["CVMNK at 72-76 (wild)", "CVIET at 72-76", "K76T"],
    "pfmdr1": ["N86Y", "Y184F", "D1246Y"],
    "pfdhfr": ["N51I", "C59R", "S108N", "A16V"],
    "pfdhps": ["A437G", "K540E", "A581G"],
    "kelch13": ["C469Y", "A675V", "R561H", "wild-type"],
    "pfcytb": ["Y268S", "wild-type"],
}

_DEMO_REGIONS = [
    "Ashanti Region", "Greater Accra Region", "Northern Region", "Eastern Region",
    "Volta Region", "Western Region", "Central Region", "Bono Region",
    "Upper East Region", "Upper West Region", "Oti Region", "Bono East Region",
]


def generate_demo_variants(n_samples: int = 960, seed: int = 7) -> pd.DataFrame:
    """Simulate a Plasmodium falciparum variant-call table for demo charts.

    Synthetic by construction: sample ids, regions, gene/mutation picks and
    dates are all drawn from made-up baselines above. The only purpose is to
    exercise the visualisations during software demonstrations.
    """
    import numpy as np

    rng = np.random.default_rng(seed)
    years = [2023, 2024, 2025, 2026]
    # Some marker frequencies drift upward over time (demo trend story).
    drift = {"kelch13": 0.022, "pfdhps": 0.015, "pfcrt": -0.01, "pfmdr1": 0.004,
             "pfdhfr": 0.002, "pfcytb": 0.001}

    # A couple of regions run "hotter" for storytelling.
    region_boost = {"Northern Region": 1.5, "Upper East Region": 1.4, "Ashanti Region": 1.15}

    rows: list[dict] = []
    for i in range(n_samples):
        region = _DEMO_REGIONS[int(rng.integers(0, len(_DEMO_REGIONS)))]
        year = years[int(rng.integers(0, len(years)))]
        t_idx = years.index(year)
        boost = region_boost.get(region, 1.0)
        n_markers = 1 + int(rng.poisson(0.7))
        genes = rng.choice(list(_DEMO_GENE_BASE.keys()), size=n_markers, replace=False,
                           p=np.array(list(_DEMO_GENE_BASE.values())) / sum(_DEMO_GENE_BASE.values()))
        sample_id = f"DEM-{year}-{i:05d}"
        month = int(rng.integers(1, 13))
        day = int(rng.integers(1, 29))
        for g in genes:
            base = min(0.95, max(0.01, _DEMO_GENE_BASE[g] + drift[g] * t_idx)) * boost
            muts = _DEMO_MUTATIONS[g]
            # First entry treated as the common wild-type-ish call
            probs = np.array([0.55 if k == 0 else 0.45 / (len(muts) - 1) for k in range(len(muts))])
            probs = np.where(np.isin(muts, ["wild-type", "CVMNK at 72-76 (wild)"]), probs * 0.4, probs)
            probs = probs / probs.sum()
            mut = str(rng.choice(muts, p=probs))
            carry = bool(rng.random() < base)
            rows.append({
                "sample_id": sample_id,
                "gene": g,
                "mutation": mut if carry else muts[0] if rng.random() < 0.8 else mut,
                "region": region,
                "sample_date": f"{year}-{month:02d}-{day:02d}",
                "genotype_quality": round(float(rng.uniform(20, 60)), 1),
            })
    return pd.DataFrame(rows)


def chart_payload(df: pd.DataFrame) -> dict:
    """Chart-ready aggregations of a variant table (descriptive only).

    Returns four series used by the UI:
    - by_gene: total marker calls per gene
    - by_region_top: marker-positive sample share per region (top 12)
    - trend_by_year: marker-positive share per year for watchlist genes
    - top_mutations: most frequent gene/mutation pairs
    """
    d = df.copy()
    has_samples = "sample_id" in d.columns and d["sample_id"].notna().any()

    by_gene = (
        d.groupby("gene").size().reset_index(name="n_calls")
        .sort_values("n_calls", ascending=False)
        .to_dict(orient="records")
    )

    by_region = []
    if has_samples and "region" in d.columns:
        samples = d.drop_duplicates(subset=["sample_id", "region"])
        totals = samples.groupby("region")["sample_id"].nunique().rename("n_samples")
        pos = d.drop_duplicates(subset=["sample_id", "region"]).groupby("region")["sample_id"].nunique()
        watch = ["kelch13", "pfdhps", "pfmdr1"]
        pos_watch = (
            d[d["gene"].isin(watch)].drop_duplicates(subset=["sample_id", "region"])
            .groupby("region")["sample_id"].nunique().rename("n_watch_positive")
        )
        frame = totals.to_frame().join(pos_watch, how="left").fillna({"n_watch_positive": 0})
        frame = frame.reset_index()
        frame = frame[frame["n_samples"] > 0].copy()
        frame["watch_share_pct"] = (100 * frame["n_watch_positive"] / frame["n_samples"]).round(1)
        by_region = (
            frame.sort_values("watch_share_pct", ascending=False)
            .head(12)[["region", "n_samples", "n_watch_positive", "watch_share_pct"]]
            .to_dict(orient="records")
        )

    trend_by_year = []
    if has_samples and "sample_date" in d.columns:
        d["year"] = pd.to_datetime(d["sample_date"], errors="coerce").dt.year
        d = d.dropna(subset=["year"])
        d["year"] = d["year"].astype(int)
        watch = ["kelch13", "pfdhps", "pfcrt", "pfmdr1"]
        for gene in watch:
            sub = d[d["gene"] == gene]
            if sub.empty:
                continue
            samples = d.drop_duplicates(subset=["sample_id", "year"])
            denom = samples.groupby("year")["sample_id"].nunique()
            num = sub.drop_duplicates(subset=["sample_id", "year"]).groupby("year")["sample_id"].nunique()
            share = (100 * num / denom).dropna().round(2)
            trend_by_year.append({
                "gene": gene,
                "points": [{"year": int(y), "share_pct": float(v)} for y, v in share.items()],
            })

    top_mutations = (
        d.groupby(["gene", "mutation"]).size().reset_index(name="n_calls")
        .sort_values("n_calls", ascending=False)
        .head(12)
        .to_dict(orient="records")
    )

    return {
        "status": "descriptive_statistics_only",
        "interpretation": (
            "All charts show descriptive marker counts and shares of genotyped samples. "
            "A detected genetic marker is NOT phenotypic drug resistance."
        ),
        "by_gene": by_gene,
        "by_region_top": by_region,
        "trend_by_year": trend_by_year,
        "top_mutations": top_mutations,
    }
