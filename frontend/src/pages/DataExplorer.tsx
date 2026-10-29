import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../api";
import type { DatasetSummary } from "../components/types";
import { Empty, ErrorBox, Loading, OkBox } from "../components/ui";

type DatasetDetail = DatasetSummary & {
  dtypes: Record<string, string>;
  profile: {
    n_rows: number;
    missing_by_column: Record<string, number>;
    duplicate_rows: number;
    issues: string[];
    numeric_summary: Record<string, { min: number; mean: number; max: number }>;
  };
  column_mapping: Record<string, string>;
  data?: Record<string, unknown>[];
};

export default function DataExplorer() {
  const [datasets, setDatasets] = useState<DatasetSummary[]>([]);
  const [selected, setSelected] = useState<number | null>(null);
  const [detail, setDetail] = useState<DatasetDetail | null>(null);
  const [error, setError] = useState("");
  const [msg, setMsg] = useState("");
  const [uploading, setUploading] = useState(false);
  const [recordType, setRecordType] = useState("surveillance");
  const fileRef = useRef<HTMLInputElement>(null);

  const loadList = useCallback(async () => {
    const rows = await api<DatasetSummary[]>("/datasets");
    setDatasets(rows);
    return rows;
  }, []);

  useEffect(() => {
    loadList().catch((e) => setError(e instanceof Error ? e.message : "Load failed"));
  }, [loadList]);

  const open = useCallback(async (id: number) => {
    setError("");
    setMsg("");
    setSelected(id);
    setDetail(null);
    try {
      const d = await api<DatasetDetail>(`/datasets/${id}?include_data=true`);
      setDetail(d);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to open dataset");
    }
  }, []);

  async function upload(file: File) {
    setUploading(true);
    setError("");
    setMsg("");
    try {
      const fd = new FormData();
      fd.append("file", file);
      const res = await api<{ id: number; row_count: number; column_mapping_suggested: Record<string, string> }>(
        `/datasets/upload?record_type=${recordType}`,
        { method: "POST", body: fd }
      );
      setMsg(`Uploaded “${file.name}” (${res.row_count} rows). Suggested mapping: ${JSON.stringify(res.column_mapping_suggested)}`);
      await loadList();
      await open(res.id);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  }

  async function remove(id: number) {
    if (!confirm("Delete this dataset? This cannot be undone.")) return;
    await api(`/datasets/${id}`, { method: "DELETE" });
    setSelected(null);
    setDetail(null);
    await loadList();
  }

  return (
    <div>
      <div className="card">
        <h2>📊 Data Explorer</h2>
        <p className="muted">
          Upload CSV, TSV, Excel, JSON or GeoJSON attribute tables. The platform profiles data quality, suggests
          column mappings to standard variables and fuzzy-matches Ghana's 16 regions. Nothing is imputed silently,
          and missing values are always reported.
        </p>
        <div className="row" style={{ maxWidth: 560 }}>
          <div>
            <label>Record type</label>
            <select value={recordType} onChange={(e) => setRecordType(e.target.value)}>
              <option value="surveillance">Surveillance (weekly cases + environment)</option>
              <option value="environmental">Environmental</option>
              <option value="clinical">Clinical</option>
              <option value="genomic">Genomic variant table</option>
              <option value="resistance">Resistance marker table</option>
            </select>
          </div>
          <div>
            <label>File</label>
            <input
              ref={fileRef}
              type="file"
              accept=".csv,.tsv,.txt,.xlsx,.xls,.json,.geojson"
              onChange={(e) => e.target.files?.[0] && upload(e.target.files[0])}
              disabled={uploading}
            />
          </div>
          {uploading && <Loading />}
        </div>
        {msg && <OkBox>{msg}</OkBox>}
        {error && <ErrorBox message={error} />}
      </div>

      <div className="card">
        <h3>Datasets</h3>
        {datasets.length === 0 ? (
          <Empty>No datasets yet. Upload a file to begin the analysis.</Empty>
        ) : (
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Type</th>
                <th>Source</th>
                <th>Rows</th>
                <th>Uploaded</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {datasets.map((d) => (
                <tr key={d.id} style={{ cursor: "pointer" }} onClick={() => open(d.id)}>
                  <td>{d.id}</td>
                  <td>{d.name}</td>
                  <td>
                    <span className="chip neutral">{d.record_type}</span>{" "}
                    {d.is_synthetic && <span className="chip warning">SYNTHETIC</span>}
                  </td>
                  <td>{d.source}</td>
                  <td>{d.row_count}</td>
                  <td>{new Date(d.created_at).toLocaleDateString()}</td>
                  <td onClick={(e) => e.stopPropagation()}>
                    <button className="btn outline" onClick={() => remove(d.id)}>
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {detail && (
        <>
          <div className="card">
            <h3>Data quality: {detail.name}</h3>
            {detail.profile.issues?.length ? (
              <ul className="muted">
                {detail.profile.issues.map((i, k) => (
                  <li key={k}>{i}</li>
                ))}
              </ul>
            ) : (
              <OkBox>No data-quality issues detected.</OkBox>
            )}
            <p className="muted">
              {detail.profile.n_rows} rows × {Object.keys(detail.dtypes).length} columns ·{" "}
              {detail.profile.duplicate_rows} duplicate rows
            </p>
            <details>
              <summary className="muted" style={{ cursor: "pointer" }}>
                Numeric summary &amp; missingness
              </summary>
              <table style={{ marginTop: 8 }}>
                <thead>
                  <tr>
                    <th>Column</th>
                    <th>Type</th>
                    <th>Missing</th>
                    <th>Min</th>
                    <th>Mean</th>
                    <th>Max</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.keys(detail.dtypes).map((c) => {
                    const ns = detail.profile.numeric_summary?.[c];
                    return (
                      <tr key={c}>
                        <td className="mono">{c}</td>
                        <td>{detail.dtypes[c]}</td>
                        <td>{detail.profile.missing_by_column?.[c] ?? 0}</td>
                        <td>{ns ? ns.min.toPrecision(4) : "—"}</td>
                        <td>{ns ? ns.mean.toPrecision(4) : "—"}</td>
                        <td>{ns ? ns.max.toPrecision(4) : "—"}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </details>
          </div>

          {detail.data && detail.data.length > 0 && (
            <div className="card">
              <h3>Preview (first 20 rows)</h3>
              <div style={{ overflowX: "auto" }}>
                <table>
                  <thead>
                    <tr>
                      {Object.keys(detail.data![0]).map((c) => (
                        <th key={c}>{c}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {detail.data!.slice(0, 20).map((row, i) => (
                      <tr key={i}>
                        {Object.keys(detail.data![0]).map((c) => (
                          <td key={c} className="mono">
                            {String(row[c] ?? "")}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
