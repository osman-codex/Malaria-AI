import { useState } from "react";
import { apiText } from "../api";
import { Empty, ErrorBox, Loading } from "../components/ui";

export default function Reports() {
  const [markdown, setMarkdown] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function generate() {
    setBusy(true);
    setError("");
    try {
      const text = await apiText("/reports/generate");
      setMarkdown(text);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Report generation failed");
    } finally {
      setBusy(false);
    }
  }

  function download() {
    const blob = new Blob([markdown], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `ptransmit_report_${new Date().toISOString().slice(0, 16).replace(/[:T]/g, "")}.md`;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div>
      <div className="card">
        <h2>📑 Reports</h2>
        <p className="muted">
          Generates a reproducibility-oriented research report: dataset description, data-quality assessment,
          trained models with metrics, open research signals and mandatory limitations.
        </p>
        <button className="btn" onClick={generate} disabled={busy}>
          {busy ? "Generating…" : "Generate report"}
        </button>
        {error && <ErrorBox message={error} />}
      </div>

      {markdown && (
        <div className="card">
          <h3>Report preview</h3>
          <button className="btn outline" onClick={download} style={{ marginBottom: 12 }}>
            ⬇ Download .md
          </button>
          <pre style={{ whiteSpace: "pre-wrap", maxHeight: 600, overflowY: "auto" }}>{markdown}</pre>
        </div>
      )}
      {!markdown && !busy && <Empty>Generate a report to preview it here.</Empty>}
    </div>
  );
}
