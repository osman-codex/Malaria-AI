import { useEffect, useState } from "react";
import { api } from "../api";
import type { RegionStats } from "../components/types";
import GhanaMap, { MapLegend } from "../components/GhanaMap";
import { DemoBanner, Empty, ErrorBox, Loading, RiskChip } from "../components/ui";
import type { Feature } from "geojson";

type Snapshot = {
  dataset_id: number;
  is_synthetic: boolean;
  last_week: string;
  geojson: { features: Feature<GeoJSON.Geometry, { shapeName: string; stats?: RegionStats }>[] };
};

export default function Spatial() {
  const [snap, setSnap] = useState<Snapshot | null>(null);
  const [layer, setLayer] = useState<"risk" | "recent_cases" | "forecast">("risk");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api<Snapshot>("/spatial/snapshot")
      .then(setSnap)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Loading />;
  if (error) return <ErrorBox message={error} />;
  if (!snap) return <Empty>No data to show yet. Upload a dataset to begin the analysis.</Empty>;

  const stats = snap.geojson.features.map((f) => f.properties.stats).filter((s): s is RegionStats => Boolean(s));
  const envLayersNote = "Environmental suitability & surveillance-coverage layers arrive with Phase 3 (environmental data integration).";

  return (
    <div>
      <div className="card">
        <h2>🗺️ Spatial Intelligence</h2>
        <DemoBanner show={snap.is_synthetic} />
        <div className="row" style={{ maxWidth: 460 }}>
          <div>
            <label>Layer</label>
            <select value={layer} onChange={(e) => setLayer(e.target.value as typeof layer)}>
              <option value="risk">Transmission risk</option>
              <option value="recent_cases">Recent observed cases (4-wk mean)</option>
              <option value="forecast">Predicted transmission (forecast)</option>
            </select>
          </div>
        </div>
        <p className="muted">{envLayersNote}</p>
        <GhanaMap geojson={snap.geojson.features} layer={layer} />
        <MapLegend />
        <p className="muted">
          Boundaries: geoBoundaries gbOpen GHA ADM1 (CC-BY 4.0). Risk categories are relative to the loaded
          dataset's own historical distribution.
        </p>
      </div>

      <div className="card">
        <h3>All regions: current snapshot (week of {snap.last_week})</h3>
        <table>
          <thead>
            <tr>
              <th>Region</th>
              <th>4-wk mean cases</th>
              <th>4-wk total</th>
              <th>Historical p90</th>
              <th>Forecast median (≤4 wk)</th>
              <th>Risk category</th>
            </tr>
          </thead>
          <tbody>
            {stats
              .slice()
              .sort((a, b) => b.recent_4wk_mean_cases - a.recent_4wk_mean_cases)
              .map((s) => (
                <tr key={s.region}>
                  <td>{s.region}</td>
                  <td>{s.recent_4wk_mean_cases.toFixed(1)}</td>
                  <td>{s.recent_4wk_total_cases}</td>
                  <td>{s.hist_p90?.toFixed(0)}</td>
                  <td>{s.forecast_median_4wk != null ? s.forecast_median_4wk.toFixed(0) : "—"}</td>
                  <td>
                    <RiskChip category={s.risk_category} />
                  </td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
