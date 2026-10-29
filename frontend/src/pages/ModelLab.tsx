import { Fragment, useCallback, useEffect, useState } from "react";
import { api } from "../api";
import type { DatasetSummary, TrainedModelRow } from "../components/types";
import { Empty, ErrorBox, Loading, OkBox } from "../components/ui";
import { ImportanceBars } from "../components/ui";

export default function ModelLab() {
  const [datasets, setDatasets] = useState<DatasetSummary[]>([]);
  const [models, setModels] = useState<TrainedModelRow[]>([]);
  const [datasetId, setDatasetId] = useState<number | "">("");
  const [modelTypes, setModelTypes] = useState<string[]>(["random_forest", "xgboost", "ridge"]);
  const [horizons, setHorizons] = useState<number[]>([1, 2, 4, 8]);
  const [seed, setSeed] = useState(42);
  const [trainFraction, setTrainFraction] = useState(0.8);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [msg, setMsg] = useState("");
  const [selected, setSelected] = useState<number | null>(null);

  const load = useCallback(async () => {
    const [ds, ms] = await Promise.all([
      api<DatasetSummary[]>("/datasets"),
      api<TrainedModelRow[]>("/models"),
    ]);
    setDatasets(ds.filter((d) => d.record_type === "surveillance"));
    setModels(ms);
    if (ds.length && datasetId === "") setDatasetId(ds[0].id);
  }, [datasetId]);

  useEffect(() => {
    load().catch((e) => setError(e instanceof Error ? e.message : "Load failed"));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function train() {
    if (datasetId === "") return;
    setBusy(true);
    setError("");
    setMsg("");
    try {
      await api("/transmission/train", {
        method: "POST",
        body: JSON.stringify({
          dataset_id: datasetId,
          model_types: modelTypes,
          horizons_weeks: horizons,
          seed,
          train_fraction: trainFraction,
        }),
      });
      setMsg("Training complete. Models saved with full provenance.");
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Training failed");
    } finally {
      setBusy(false);
    }
  }

  async function remove(id: number) {
    if (!confirm("Delete this model and its artifact?")) return;
    await api(`/models/${id}`, { method: "DELETE" });
    await load();
  }

  function toggle<T>(arr: T[], v: T): T[] {
    return arr.includes(v) ? arr.filter((x) => x !== v) : [...arr, v];
  }

  return (
    <div>
      <div className="card">
        <h2>🧪 Model Laboratory</h2>
        <p className="muted">
          Train, compare and manage transmission forecasting models. Validation is chronological (time-series data
          is never split at random). Every model is stored with its dataset, features, preprocessing, seed, software
          versions and metrics so anyone can reproduce it.
        </p>
        <div className="row" style={{ maxWidth: 760 }}>
          <div>
            <label>Dataset</label>
            <select value={datasetId} onChange={(e) => setDatasetId(e.target.value === "" ? "" : Number(e.target.value))}>
              <option value="">— select —</option>
              {datasets.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name}
                </option>
              ))}
            </select>
          </div>
          <div>
            <label>Random seed</label>
            <input type="number" value={seed} onChange={(e) => setSeed(Number(e.target.value))} />
          </div>
          <div>
            <label>Train fraction (temporal)</label>
            <input
              type="number"
              step="0.05"
              min="0.5"
              max="0.95"
              value={trainFraction}
              onChange={(e) => setTrainFraction(Number(e.target.value))}
            />
          </div>
        </div>
        <div className="row" style={{ marginTop: 10, maxWidth: 760 }}>
          <div>
            <label>Models</label>
            {["random_forest", "xgboost", "ridge"].map((m) => (
              <label key={m} style={{ display: "inline-flex", alignItems: "center", gap: 6, marginRight: 14, textTransform: "none" }}>
                <input
                  type="checkbox"
                  style={{ width: "auto" }}
                  checked={modelTypes.includes(m)}
                  onChange={() => setModelTypes(toggle(modelTypes, m))}
                />
                {m}
              </label>
            ))}
          </div>
          <div>
            <label>Horizons (weeks)</label>
            {[1, 2, 4, 8].map((h) => (
              <label key={h} style={{ display: "inline-flex", alignItems: "center", gap: 6, marginRight: 14, textTransform: "none" }}>
                <input
                  type="checkbox"
                  style={{ width: "auto" }}
                  checked={horizons.includes(h)}
                  onChange={() => setHorizons(toggle(horizons, h))}
                />
                +{h}w
              </label>
            ))}
          </div>
          <div style={{ flex: 0 }}>
            <button className="btn" onClick={train} disabled={busy || datasetId === ""}>
              {busy ? "Training…" : "Train"}
            </button>
          </div>
        </div>
        {busy && <Loading />}
        {msg && <OkBox>{msg}</OkBox>}
        {error && <ErrorBox message={error} />}
      </div>

      <div className="card">
        <h3>Saved models</h3>
        {models.length === 0 ? (
          <Empty>No trained models yet.</Empty>
        ) : (
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Name</th>
                <th>MAE</th>
                <th>RMSE</th>
                <th>Seed</th>
                <th>Trained</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {models.map((m) => {
                const metrics = m.metrics as Record<string, number>;
                return (
                  <Fragment key={m.id}>
                    <tr style={{ cursor: "pointer" }} onClick={() => setSelected(selected === m.id ? null : m.id)}>
                      <td>{m.id}</td>
                      <td>{m.name}</td>
                      <td>{metrics?.MAE != null ? metrics.MAE.toFixed(1) : "—"}</td>
                      <td>{metrics?.RMSE != null ? metrics.RMSE.toFixed(1) : "—"}</td>
                      <td>{m.random_seed}</td>
                      <td>{new Date(m.training_date).toLocaleString()}</td>
                      <td onClick={(e) => e.stopPropagation()}>
                        <button className="btn outline" onClick={() => remove(m.id)}>
                          Delete
                        </button>
                      </td>
                    </tr>
                    {selected === m.id && (
                      <tr>
                        <td colSpan={7}>
                          <div style={{ background: "#f8fafb", borderRadius: 8, padding: 14 }}>
                            <h3>Provenance: {m.name}</h3>
                            <p className="mono">
                              type={m.model_type} · target={m.target} · version={m.model_version} ·
                              dataset={m.dataset_id}
                            </p>
                            <p className="mono">
                              validation={JSON.stringify(m.validation)}
                            </p>
                            <p className="mono">software={JSON.stringify(m.software_versions)}</p>
                            <h3>Feature importance (held-out permutation)</h3>
                            {m.feature_importance?.length ? (
                              <ImportanceBars
                                items={m.feature_importance.map((f) => ({ feature: f.feature, value: f.importance }))}
                              />
                            ) : (
                              <p className="muted">No importance data stored.</p>
                            )}
                          </div>
                        </td>
                      </tr>
                    )}
                  </Fragment>
                );
              })}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
