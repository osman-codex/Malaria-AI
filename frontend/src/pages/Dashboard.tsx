import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip as RTooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import { api } from "../api";
import type { AlertRow, ForecastRow, RegionStats } from "../components/types";
import { DemoBanner, Empty, ErrorBox, ImportanceBars, Loading, RiskChip, SeverityChip } from "../components/ui";
import GhanaMap, { MapLegend } from "../components/GhanaMap";
import type { Feature } from "geojson";

type Snapshot = {
  dataset_id: number;
  is_synthetic: boolean;
  last_week: string;
  geojson: {
    features: Feature<GeoJSON.Geometry, { shapeName: string; stats?: RegionStats }>[];
  };
};

export default function Dashboard() {
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null);
  const [forecasts, setForecasts] = useState<ForecastRow[]>([]);
  const [alerts, setAlerts] = useState<AlertRow[]>([]);
  const [expl, setExpl] = useState<{ regions: Record<string, { feature: string; contribution: number }[]>; method: string } | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [layer, setLayer] = useState<"risk" | "recent_cases" | "forecast">("risk");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const snap = await api<Snapshot>("/spatial/snapshot");
      setSnapshot(snap);
      try {
        const f = await api<{ forecasts: ForecastRow[] }>("/transmission/forecast");
        setForecasts(f.forecasts);
        const e = await api<{ regions: Record<string, { feature: string; contribution: number }[]>; method: string }>(
          "/transmission/explain"
        );
        setExpl(e);
      } catch {
        /* models not trained yet — dashboard still renders observed data */
      }
      setAlerts(await api<AlertRow[]>("/alerts"));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load dashboard");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  if (loading) return <Loading />;
  if (error) return <ErrorBox message={error} />;
  if (!snapshot) return <Empty>No data to show yet. Upload a dataset to begin the analysis.</Empty>;

  const stats: RegionStats[] = snapshot.geojson.features
    .map((f) => f.properties.stats)
    .filter((s): s is RegionStats => Boolean(s));
  const totalRecent = stats.reduce((a, s) => a + (s.recent_4wk_total_cases ?? 0), 0);
  const veryHigh = stats.filter((s) => s.risk_category === "very high").length;
  const high = stats.filter((s) => s.risk_category === "high").length;
  const f1 = forecasts.filter((f) => f.horizon_weeks === 1);
  const nationalNextWeek = f1.length ? f1.reduce((a, f) => a + f.predicted_cases, 0) : null;

  const region = "Ashanti Region";
  const ashantiExpl = expl?.regions?.[region] ?? [];

  return (
    <div>
      <DemoBanner show={snapshot.is_synthetic} />
      <div className="kpis">
        <div className="kpi">
          <div className="label">Latest data week</div>
          <div className="value" style={{ fontSize: "1.05rem" }}>{snapshot.last_week}</div>
          <div className="hint">from loaded dataset</div>
        </div>
        <div className="kpi accent-info">
          <div className="label">Recent 4-wk cases (national)</div>
          <div className="value">{totalRecent.toLocaleString()}</div>
          <div className="hint">sum across regions</div>
        </div>
        <div className="kpi accent-gold">
          <div className="label">National forecast (next week)</div>
          <div className="value">{nationalNextWeek != null ? Math.round(nationalNextWeek).toLocaleString() : "—"}</div>
          <div className="hint">model prediction, not observed</div>
        </div>
        <div className="kpi accent-red">
          <div className="label">Regions at elevated risk</div>
          <div className="value">
            {veryHigh} <span className="muted">very high</span> · {high} <span className="muted">high</span>
          </div>
          <div className="hint">relative to dataset history</div>
        </div>
      </div>

      <div className="grid-map">
        <div className="card">
          <h2>Ghana Malaria Transmission Intelligence</h2>
          <div className="row" style={{ marginBottom: 10, maxWidth: 420 }}>
            <div>
              <label>Map layer</label>
              <select value={layer} onChange={(e) => setLayer(e.target.value as typeof layer)}>
                <option value="risk">Transmission risk category</option>
                <option value="recent_cases">Recent 4-week case mean</option>
                <option value="forecast">Forecast median (≤4 weeks)</option>
              </select>
            </div>
          </div>
          <GhanaMap geojson={snapshot.geojson.features} layer={layer} />
          <MapLegend />
        </div>

        <div>
          <div className="card">
            <h3>Regional risk summary</h3>
            {stats.length === 0 && <Empty>No data to show yet. Upload a dataset to begin the analysis.</Empty>}
            <table>
              <thead>
                <tr>
                  <th>Region</th>
                  <th>4-wk mean</th>
                  <th>Risk</th>
                </tr>
              </thead>
              <tbody>
                {stats
                  .slice()
                  .sort((a, b) => b.recent_4wk_mean_cases - a.recent_4wk_mean_cases)
                  .slice(0, 8)
                  .map((s) => (
                    <tr key={s.region}>
                      <td>{s.region.replace(" Region", "")}</td>
                      <td>{s.recent_4wk_mean_cases.toFixed(0)}</td>
                      <td>
                        <RiskChip category={s.risk_category} />
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>

          <div className="card">
            <h3>Open research signals</h3>
            {alerts.length === 0 && <p className="muted">No open alerts. Run a scan after training models.</p>}
            {alerts.slice(0, 4).map((a) => (
              <div key={a.id} className={`alert-card ${a.severity}`}>
                <SeverityChip severity={a.severity} /> <strong>{a.title}</strong>
                <div className="meta">{new Date(a.created_at).toLocaleDateString()} · {a.alert_type}</div>
              </div>
            ))}
            <Link className="btn outline" to="/alerts" style={{ marginTop: 8, display: "inline-block" }}>
              View all alerts
            </Link>
          </div>
        </div>
      </div>

      <div className="grid2">
        <div className="card">
          <h3>Forecast by region (next week)</h3>
          {f1.length === 0 ? (
            <Empty>No trained models. Open the Model Laboratory to train the transmission model.</Empty>
          ) : (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={f1} margin={{ left: 0, right: 8 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e8edf1" />
                <XAxis dataKey="region" tickFormatter={(v: string) => v.replace(" Region", "")} angle={-35} textAnchor="end" height={70} fontSize={11} />
                <YAxis fontSize={11} />
                <RTooltip formatter={(v: number) => Math.round(v).toLocaleString()} labelFormatter={(v: string) => v.replace(" Region", "")} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>

        <div className="card">
          <h3>Why? Top contributors for {region.replace(" Region", "")}</h3>
          <p className="muted">{expl?.method ?? "Train models to generate explanations of model behaviour (not causal effects)."}</p>
          {ashantiExpl.length > 0 ? (
            <ImportanceBars items={ashantiExpl.map((x) => ({ feature: x.feature, value: x.contribution }))} signed />
          ) : (
            <Empty>Train models first (Model Laboratory), then explanations appear here.</Empty>
          )}
        </div>
      </div>
    </div>
  );
}
