import { useCallback, useEffect, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip as RTooltip,
  ResponsiveContainer,
  CartesianGrid,
  Legend,
} from "recharts";
import { api } from "../api";
import type { DatasetSummary, ForecastRow, ObsPredRow, TrainedModelRow } from "../components/types";
import { DemoBanner, Empty, ErrorBox, Loading, OkBox } from "../components/ui";

type TrainResponse = {
  dataset_id: number;
  dataset_name: string;
  is_synthetic: boolean;
  results: {
    horizons: Record<
      string,
      {
        models?: Record<string, { metrics?: Record<string, number>; error?: string }>;
        best_model?: string;
        best_metrics?: Record<string, number> | null;
        n_train_rows?: number;
        n_test_rows?: number;
        feature_importance?: { feature: string; importance: number }[];
      }
    >;
  };
  saved_model_ids: number[];
};

export default function Transmission() {
  const [datasets, setDatasets] = useState<DatasetSummary[]>([]);
  const [datasetId, setDatasetId] = useState<number | "">("");
  const [train, setTrain] = useState<TrainResponse | null>(null);
  const [models, setModels] = useState<TrainedModelRow[]>([]);
  const [obsPred, setObsPred] = useState<{ rows: ObsPredRow[]; model_type: string; metrics: Record<string, number> } | null>(null);
  const [forecast, setForecast] = useState<ForecastRow[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [region, setRegion] = useState("Ashanti Region");

  useEffect(() => {
    api<DatasetSummary[]>("/datasets").then((rows) => {
      const surv = rows.filter((r) => r.record_type === "surveillance");
      setDatasets(surv);
      if (surv.length) setDatasetId(surv[0].id);
    });
    api<TrainedModelRow[]>("/models").then(setModels).catch(() => {});
  }, []);

  const loadEvaluation = useCallback(async (dsId: number) => {
    try {
      const op = await api<{ rows: ObsPredRow[]; model_type: string; metrics: Record<string, number> }>(
        `/transmission/observed-vs-predicted?dataset_id=${dsId}`
      );
      setObsPred(op);
      const f = await api<{ forecasts: ForecastRow[] }>(`/transmission/forecast?dataset_id=${dsId}`);
      setForecast(f.forecasts);
    } catch {
      setObsPred(null);
      setForecast([]);
    }
  }, []);

  useEffect(() => {
    if (datasetId !== "") loadEvaluation(Number(datasetId));
  }, [datasetId, loadEvaluation]);

  async function runTraining() {
    if (datasetId === "") return;
    setBusy(true);
    setError("");
    setTrain(null);
    try {
      const res = await api<TrainResponse>("/transmission/train", {
        method: "POST",
        body: JSON.stringify({ dataset_id: datasetId, horizons_weeks: [1, 2, 4, 8] }),
      });
      setTrain(res);
      await loadEvaluation(Number(datasetId));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Training failed");
    } finally {
      setBusy(false);
    }
  }

  const regions = Array.from(new Set(forecast.map((f) => f.region))).sort();
  const regionSeries = forecast
    .filter((f) => f.region === region)
    .sort((a, b) => a.horizon_weeks - b.horizon_weeks)
    .map((f) => ({
      horizon: `+${f.horizon_weeks}w`,
      predicted: f.predicted_cases,
      low: f.interval_low,
      high: f.interval_high,
    }));

  const opRows = (obsPred?.rows ?? [])
    .filter((r) => r.region === region)
    .map((r) => ({ week: r.week_start_date, observed: r.observed, predicted: r.predicted }));

  return (
    <div>
      <div className="card">
        <h2>🦟 Transmission AI — Spatiotemporal prediction &amp; forecasting</h2>
        <p className="muted">
          Supervised models predict weekly malaria cases per region using case history (lags 1–4), environmental
          conditions and seasonality. Validation is strictly temporal. Risk categories are relative to the loaded
          dataset's own history, and predictions are associations rather than causal effects.
        </p>
        <div className="row" style={{ maxWidth: 620 }}>
          <div>
            <label>Surveillance dataset</label>
            <select value={datasetId} onChange={(e) => setDatasetId(e.target.value === "" ? "" : Number(e.target.value))}>
              <option value="">— select —</option>
              {datasets.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name} ({d.row_count} rows)
                </option>
              ))}
            </select>
          </div>
          <div style={{ flex: 0 }}>
            <button className="btn" onClick={runTraining} disabled={busy || datasetId === ""}>
              {busy ? "Training…" : "Train / retrain models"}
            </button>
          </div>
        </div>
        {error && <ErrorBox message={error} />}
        {busy && <Loading />}
      </div>

      {train && (
        <div className="card">
          <h3>Latest training run: {train.dataset_name}</h3>
          <DemoBanner show={train.is_synthetic} />
          <table>
            <thead>
              <tr>
                <th>Horizon</th>
                <th>Best model</th>
                <th>MAE</th>
                <th>RMSE</th>
                <th>sMAPE %</th>
                <th>R²*</th>
                <th>Train/test rows</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(train.results.horizons).map(([h, res]) => (
                <tr key={h}>
                  <td>+{h} wk</td>
                  <td>{res.best_model ?? "—"}</td>
                  <td>{fmt(res.best_metrics?.MAE)}</td>
                  <td>{fmt(res.best_metrics?.RMSE)}</td>
                  <td>{fmt(res.best_metrics?.sMAPE_pct)}</td>
                  <td>{fmt(res.best_metrics?.R2)}</td>
                  <td>
                    {res.n_train_rows ?? "—"} / {res.n_test_rows ?? "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="muted">*R² reported for completeness only; MAE/RMSE are primary for count outcomes.</p>
          {train.saved_model_ids.length > 0 && <OkBox>Saved {train.saved_model_ids.length} trained model(s) with full provenance.</OkBox>}
        </div>
      )}

      {obsPred && (
        <div className="card">
          <div className="row" style={{ marginBottom: 8, maxWidth: 480 }}>
            <div>
              <label>Region (validation & forecast)</label>
              <select value={region} onChange={(e) => setRegion(e.target.value)}>
                {Array.from(new Set([...obsPred.rows.map((r) => r.region), ...forecast.map((f) => f.region)]))
                  .sort()
                  .map((r) => (
                    <option key={r}>{r}</option>
                  ))}
              </select>
            </div>
            <div>
              <label>Model</label>
              <input value={obsPred.model_type} disabled />
            </div>
          </div>
          <h3>Held-out validation: observed vs predicted ({region.replace(" Region", "")})</h3>
          <ResponsiveContainer width="100%" height={320}>
            <LineChart data={opRows}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e8edf1" />
              <XAxis dataKey="week" fontSize={10} tickFormatter={(v: string) => v.slice(0, 7)} />
              <YAxis fontSize={11} />
              <RTooltip />
              <Legend />
              <Line type="monotone" dataKey="observed" stroke="#0b6e4f" strokeWidth={2} dot={false} name="Observed" />
              <Line type="monotone" dataKey="predicted" stroke="#1d4ed8" strokeDasharray="5 4" strokeWidth={2} dot={false} name="Predicted" />
            </LineChart>
          </ResponsiveContainer>
          <p className="muted">
            Metrics on the held-out test weeks (all regions): MAE {fmt(obsPred.metrics.MAE)} · RMSE{" "}
            {fmt(obsPred.metrics.RMSE)} · sMAPE {fmt(obsPred.metrics.sMAPE_pct)}%
          </p>
        </div>
      )}

      {regionSeries.length > 0 && (
        <div className="card">
          <h3>Forecast: {region.replace(" Region", "")}</h3>
          <p className="muted">Shaded range is the residual-based interval (not calibrated probabilistic intervals).</p>
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={regionSeries}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e8edf1" />
              <XAxis dataKey="horizon" fontSize={11} />
              <YAxis fontSize={11} />
              <RTooltip />
              <Line type="monotone" dataKey="high" stroke="#cbd5e1" strokeWidth={1} dot={false} name="Interval upper" />
              <Line type="monotone" dataKey="low" stroke="#cbd5e1" strokeWidth={1} dot={false} name="Interval lower" />
              <Line type="monotone" dataKey="predicted" stroke="#ce1126" strokeWidth={2.5} dot name="Predicted cases" />
            </LineChart>
          </ResponsiveContainer>
          <table style={{ marginTop: 12 }}>
            <thead>
              <tr>
                <th>Horizon</th>
                <th>Forecast week</th>
                <th>Predicted cases</th>
                <th>Interval</th>
                <th>Model</th>
              </tr>
            </thead>
            <tbody>
              {forecast
                .filter((f) => f.region === region)
                .sort((a, b) => a.horizon_weeks - b.horizon_weeks)
                .map((f) => (
                  <tr key={f.horizon_weeks}>
                    <td>+{f.horizon_weeks} wk</td>
                    <td>{f.forecast_week}</td>
                    <td>{f.predicted_cases}</td>
                    <td className="mono">
                      [{f.interval_low}, {f.interval_high}]
                    </td>
                    <td>{f.model_type}</td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      )}

      {models.length === 0 && !train && (
        <Empty>No trained models yet. Select a dataset above and train the transmission models.</Empty>
      )}
    </div>
  );
}

function fmt(v: number | undefined | null): string {
  return v == null ? "—" : (Math.round(v * 100) / 100).toString();
}
