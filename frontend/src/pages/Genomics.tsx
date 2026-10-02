import { useEffect, useState } from "react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip as RTooltip, ResponsiveContainer,
  CartesianGrid, Legend, LineChart, Line, Cell,
} from "recharts";
import { api } from "../api";
import { DemoBanner, Empty, ErrorBox, Loading, OkBox } from "../components/ui";

type GenomicsStatus = {
  module: string;
  status: string;
  message: string;
  required_columns: string[];
  known_markers_catalogue: { gene: string; label: string; drug_class: string; note: string }[];
};

type AnalyzeResponse = {
  dataset?: { id: number; name: string };
  is_synthetic?: boolean;
  status: string;
  interpretation: string;
  n_rows: number;
  n_samples: number | null;
  by_region: Record<string, unknown>[];
  top_markers: { gene: string; mutation: string; n_calls: number }[];
};

type ChartsResponse = {
  dataset_name: string;
  is_synthetic: boolean;
  status: string;
  interpretation: string;
  by_gene: { gene: string; n_calls: number }[];
  by_region_top: { region: string; n_samples: number; n_watch_positive: number; watch_share_pct: number }[];
  trend_by_year: { gene: string; points: { year: number; share_pct: number }[] }[];
  top_mutations: { gene: string; mutation: string; n_calls: number }[];
};

const GENE_COLORS: Record<string, string> = {
  kelch13: "#8f141b",
  pfcrt: "#0b6e4f",
  pfmdr1: "#1d4ed8",
  pfdhfr: "#d4a017",
  pfdhps: "#b45309",
  pfcytb: "#5b6b76",
};

export default function Genomics() {
  const [status, setStatus] = useState<GenomicsStatus | null>(null);
  const [analysis, setAnalysis] = useState<AnalyzeResponse | null>(null);
  const [charts, setCharts] = useState<ChartsResponse | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [focusGene, setFocusGene] = useState<string>("kelch13");

  useEffect(() => {
    Promise.all([
      api<GenomicsStatus>("/genomics/status"),
      api<AnalyzeResponse>("/genomics/analyze", { method: "POST", body: JSON.stringify({}) }),
      api<ChartsResponse>("/genomics/charts").catch(() => null),
    ])
      .then(([s, a, c]) => {
        setStatus(s);
        setAnalysis(a);
        setCharts(c);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Loading />;
  if (error) return <ErrorBox message={error} />;

  const hasData = analysis?.status === "descriptive_statistics_only";

  return (
    <div>
      <div className="card">
        <h2>🧬 Plasmodium Genomics &amp; AMR Surveillance</h2>
        {hasData ? (
          <OkBox>
            Showing descriptive statistics from “{analysis?.dataset?.name}” ({analysis?.n_rows} variant calls,{" "}
            {analysis?.n_samples ?? "—"} samples). A detected genetic marker is <strong>not</strong> phenotypic
            drug resistance.
          </OkBox>
        ) : (
          <Empty>
            <strong>Waiting for a validated genomic dataset.</strong>
            <p>{status?.message}</p>
            <p className="mono">Required columns: {status?.required_columns.join(", ")}</p>
          </Empty>
        )}
      </div>

      {charts && charts.status === "descriptive_statistics_only" && (
        <>
          {charts.is_synthetic && <DemoBanner show />}

          <div className="grid2">
            <div className="card">
              <h3>Marker calls by gene</h3>
              <p className="muted">
                Every bar counts variant calls assigned to a resistance-associated gene in the demo variant table.
              </p>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={charts.by_gene} margin={{ left: 0, right: 8, bottom: 4 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e8edf1" />
                  <XAxis dataKey="gene" fontSize={11} />
                  <YAxis fontSize={11} />
                  <RTooltip />
                  <Bar dataKey="n_calls" name="Variant calls" radius={[4, 4, 0, 0]}>
                    {charts.by_gene.map((g) => (
                      <Cell key={g.gene} fill={GENE_COLORS[g.gene] ?? "#0b6e4f"} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="card">
              <h3>Watchlist marker share by region</h3>
              <p className="muted">
                Share of genotyped samples per region carrying at least one kelch13, pfdhps or pfmdr1 marker.
                Higher shares justify closer monitoring, nothing more.
              </p>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart
                  data={charts.by_region_top}
                  layout="vertical"
                  margin={{ left: 30, right: 16 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#e8edf1" />
                  <XAxis type="number" fontSize={11} unit="%" />
                  <YAxis type="category" dataKey="region" fontSize={10} width={120} tickFormatter={(v: string) => v.replace(" Region", "")} />
                  <RTooltip formatter={(v: number) => `${v}%`} />
                  <Bar dataKey="watch_share_pct" name="Samples with watchlist marker" fill="#8f141b" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="card">
            <div className="row" style={{ marginBottom: 6, maxWidth: 520 }}>
              <div>
                <label>Focus gene (temporal trend)</label>
                <select value={focusGene} onChange={(e) => setFocusGene(e.target.value)}>
                  {charts.trend_by_year.map((t) => (
                    <option key={t.gene} value={t.gene}>
                      {t.gene}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label>All genes (compare)</label>
                <input value="see all lines below" disabled />
              </div>
            </div>
            <h3>Marker-positive share over time (%)</h3>
            <p className="muted">
              Rising lines signal growing marker presence in sequenced samples. Trends are descriptive; they do not
              confirm drug resistance.
            </p>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart margin={{ left: 0, right: 12, top: 8 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e8edf1" />
                <XAxis
                  dataKey="year"
                  type="number"
                  domain={["dataMin", "dataMax"]}
                  tickFormatter={(v: number) => String(v)}
                  fontSize={11}
                  allowDuplicatedCategory={false}
                />
                <YAxis fontSize={11} unit="%" />
                <RTooltip formatter={(v: number) => `${v}%`} labelFormatter={(l) => `Year ${l}`} />
                <Legend />
                {charts.trend_by_year.map((t) => (
                  <Line
                    key={t.gene}
                    data={t.points}
                    dataKey="share_pct"
                    name={t.gene}
                    type="monotone"
                    stroke={GENE_COLORS[t.gene] ?? "#334155"}
                    strokeWidth={t.gene === focusGene ? 3 : 1.4}
                    dot={t.gene === focusGene}
                    opacity={t.gene === focusGene ? 1 : 0.55}
                  />
                ))}
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="card">
            <h3>Most frequent mutations</h3>
            <p className="muted">Top gene and mutation pairs by number of calls in the demo table.</p>
            <ResponsiveContainer width="100%" height={320}>
              <BarChart data={charts.top_mutations} layout="vertical" margin={{ left: 40, right: 16 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e8edf1" />
                <XAxis type="number" fontSize={11} />
                <YAxis
                  type="category"
                  dataKey="mutation"
                  fontSize={9.5}
                  width={180}
                  tickFormatter={(v: string) => (v.length > 24 ? v.slice(0, 23) + "…" : v)}
                />
                <RTooltip />
                <Bar dataKey="n_calls" name="Calls" radius={[0, 4, 4, 0]}>
                  {charts.top_mutations.map((m, i) => (
                    <Cell key={i} fill={GENE_COLORS[m.gene] ?? "#0b6e4f"} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="card">
            <h3>Regional frequency table</h3>
            <table>
              <thead>
                <tr>
                  <th>Region</th>
                  <th>Calls</th>
                  <th>Samples</th>
                  <th>Marker-positive samples</th>
                  <th>Frequency</th>
                </tr>
              </thead>
              <tbody>
                {analysis?.by_region.map((r, i) => (
                  <tr key={i}>
                    <td>{String(r.region ?? "—")}</td>
                    <td>{String(r.n_calls ?? "—")}</td>
                    <td>{String(r.n_samples ?? "—")}</td>
                    <td>{String(r.n_marker_positive_samples ?? "—")}</td>
                    <td>{r.frequency != null ? String(r.frequency) : "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            <p className="muted">{analysis?.interpretation}</p>
          </div>
        </>
      )}

      <div className="card">
        <h3>Validated marker catalogue (vocabulary, not an interpretation matrix)</h3>
        <p className="muted">
          The platform does not invent resistance thresholds. Interpretation definitions must come from the
          researcher, for example from WHO or published operational definitions.
        </p>
        <table>
          <thead>
            <tr>
              <th>Gene</th>
              <th>Label</th>
              <th>Drug class</th>
              <th>Note</th>
            </tr>
          </thead>
          <tbody>
            {status?.known_markers_catalogue.map((m) => (
              <tr key={m.gene}>
                <td className="mono">{m.gene}</td>
                <td>{m.label}</td>
                <td>{m.drug_class}</td>
                <td className="muted">{m.note}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="card">
        <h3>Planned integrations (Phase 2 and beyond)</h3>
        <ul className="muted">
          <li>SNP analysis, genetic diversity (heterozygosity, MOI), population structure (PCA/ADMIXTURE-style plots)</li>
          <li>Genetic distance and clustering visualisations</li>
          <li>Temporal and geographic distribution of resistance-associated variants</li>
          <li>KCCR genomic dataset connector (requires a data access agreement)</li>
        </ul>
      </div>
    </div>
  );
}
