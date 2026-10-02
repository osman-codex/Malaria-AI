"""Download Ghana administrative boundaries (ADM1) from geoBoundaries gbOpen.

Usage:  python scripts/fetch_geo_data.py

Source: geoBoundaries (https://www.geoboundaries.org), gbOpen licence (CC-BY 4.0).
Saves the full file and a lightweight simplified version used by the web map.
"""
from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GEO_DIR = ROOT / "data" / "geo"
GEO_DIR.mkdir(parents=True, exist_ok=True)

URLS = [
    "https://media.githubusercontent.com/media/wmgeolab/geoBoundaries/main/releaseData/gbOpen/GHA/ADM1/geoBoundaries-GHA-ADM1.geojson",
    "https://raw.githubusercontent.com/wmgeolab/geoBoundaries/main/releaseData/gbOpen/GHA/ADM1/geoBoundaries-GHA-ADM1.geojson",
]


def fetch() -> bytes:
    last_err: Exception | None = None
    for url in URLS:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            data = urllib.request.urlopen(req, timeout=90).read()
            json.loads(data)  # validate
            return data
        except Exception as e:  # noqa: BLE001
            last_err = e
    raise RuntimeError(f"Could not download Ghana ADM1 boundaries: {last_err}")


def simplify(coords, tol: float = 0.004):
    """Cheap vertex decimation, keeps first/last point of each ring."""
    if isinstance(coords[0][0], (int, float)):
        return [
            c
            for i, c in enumerate(coords)
            if i == 0
            or i == len(coords) - 1
            or (abs(c[0] - coords[i - 1][0]) + abs(c[1] - coords[i - 1][1])) > tol
        ]
    return [simplify(c, tol) for c in coords]


def main() -> None:
    data = fetch()
    full = GEO_DIR / "ghana_adm1.geojson"
    full.write_bytes(data)
    print(f"saved {full} ({len(data)//1024} KB)")

    gj = json.loads(data)
    for f in gj["features"]:
        g = f["geometry"]
        if g["type"] == "Polygon":
            g["coordinates"] = [simplify(g["coordinates"])]
        elif g["type"] == "MultiPolygon":
            g["coordinates"] = [[simplify(p) for p in g["coordinates"]]]
    light = GEO_DIR / "ghana_adm1_simplified.geojson"
    light.write_text(json.dumps(gj, separators=(",", ":")), encoding="utf-8")
    print(f"saved {light} ({light.stat().st_size//1024} KB)")

    names = [f["properties"]["shapeName"] for f in gj["features"]]
    print(f"{len(names)} regions: {', '.join(sorted(names))}")


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
