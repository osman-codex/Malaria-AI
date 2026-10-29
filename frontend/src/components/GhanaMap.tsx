import { useEffect, useMemo, useState } from "react";
import { MapContainer, TileLayer, GeoJSON, Tooltip as LTooltip } from "react-leaflet";
import L from "leaflet";
import type { Feature, Geometry } from "geojson";
import type { RegionStats } from "./types";

const RISK_COLORS: Record<string, string> = {
  low: "#7bc47f",
  moderate: "#f2d14e",
  high: "#ef8f4b",
  "very high": "#d94f3d",
};

export type MapLayer = "risk" | "recent_cases" | "forecast";

// Fix default marker icon paths when bundlers break their URL resolution.
import markerIcon2x from "leaflet/dist/images/marker-icon-2x.png";
import markerIcon from "leaflet/dist/images/marker-icon.png";
import markerShadow from "leaflet/dist/images/marker-shadow.png";
L.Icon.Default.mergeOptions({
  iconRetinaUrl: markerIcon2x,
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
});

export default function GhanaMap({
  geojson,
  layer,
}: {
  geojson: Feature<Geometry, { shapeName: string; stats?: RegionStats }>[];
  layer: MapLayer;
}) {
  const [mapReady, setMapReady] = useState(false);
  const [renderKey, setRenderKey] = useState(0);

  // Signal readiness after mount, and force GeoJSON layer re-creation when
  // data/layer change (react-leaflet does not diff GeoJSON props deeply).
  useEffect(() => {
    const t = setTimeout(() => setMapReady(true), 0);
    return () => clearTimeout(t);
  }, []);

  useEffect(() => {
    setRenderKey((k) => k + 1);
  }, [geojson, layer]);

  function styleFn(feature?: Feature<Geometry, any>) {
    const s: RegionStats | undefined = feature?.properties?.stats;
    let color = "#d7dee4";
    if (s) {
      if (layer === "risk" && s.risk_category) color = RISK_COLORS[s.risk_category] ?? color;
      if (layer === "recent_cases") {
        const v = s.recent_4wk_mean_cases ?? 0;
        const max = Math.max(...geojson.map((f) => f.properties.stats?.recent_4wk_mean_cases ?? 0), 1);
        color = scaleColor(v / max);
      }
      if (layer === "forecast" && s.forecast_median_4wk != null) {
        const max = Math.max(...geojson.map((f) => f.properties.stats?.forecast_median_4wk ?? 0), 1);
        color = scaleColor((s.forecast_median_4wk ?? 0) / max);
      }
    }
    return { fillColor: color, fillOpacity: 0.82, color: "#4a5a66", weight: 1 };
  }

  // Fit map bounds to Ghana once when the map is created.
  function FitBounds() {
    const map = useMap();
    useEffect(() => {
      if (geojson.length) {
        try {
          const gj = L.geoJSON({ type: "FeatureCollection", features: geojson } as any);
          map.fitBounds(gj.getBounds(), { padding: [12, 12] });
        } catch {
          /* keep default centre */
        }
      }
    }, [map, renderKey]);
    return null;
  }

  return (
    <MapContainer
      center={[7.9, -1.1]}
      zoom={6}
      minZoom={5}
      scrollWheelZoom
      className="map-container"
      whenReady={() => setMapReady(true)}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <FitBounds />
      {mapReady &&
        geojson.map((f, i) => (
          <GeoJSON
            key={`${f.properties.shapeName}-${i}-${layer}-${renderKey}`}
            data={f}
            style={styleFn as any}
          >
            <LTooltip sticky>
              <strong>{f.properties.shapeName}</strong>
              {f.properties.stats ? (
                <>
                  <br />
                  Recent 4-wk mean: {f.properties.stats.recent_4wk_mean_cases?.toFixed(0)} cases
                  <br />
                  Historical p90: {f.properties.stats.hist_p90?.toFixed(0)}
                  <br />
                  {f.properties.stats.forecast_median_4wk != null && (
                    <>
                      Forecast median (≤4 wk): {f.properties.stats.forecast_median_4wk?.toFixed(0)}
                      <br />
                    </>
                  )}
                  Risk: {f.properties.stats.risk_category ?? "n/a"}
                </>
              ) : (
                  <>
                  <br />
                  No data
                </>
              )}
            </LTooltip>
          </GeoJSON>
        ))}
    </MapContainer>
  );
}

import { useMap } from "react-leaflet";

function scaleColor(t: number): string {
  // simple sequential ramp: green -> yellow -> red
  const stops = ["#7bc47f", "#c9d55a", "#f2d14e", "#ef8f4b", "#d94f3d"];
  const idx = Math.min(stops.length - 1, Math.max(0, Math.floor(t * stops.length)));
  return stops[idx];
}

export function MapLegend() {
  return (
    <div className="map-legend">
      <span>
        <span className="legend-swatch" style={{ background: RISK_COLORS.low }} /> Low
      </span>
      <span>
        <span className="legend-swatch" style={{ background: RISK_COLORS.moderate }} /> Moderate
      </span>
      <span>
        <span className="legend-swatch" style={{ background: RISK_COLORS.high }} /> High
      </span>
      <span>
        <span className="legend-swatch" style={{ background: RISK_COLORS["very high"] }} /> Very high
      </span>
      <span className="muted">Risk categories are relative to the loaded dataset's own history.</span>
    </div>
  );
}
