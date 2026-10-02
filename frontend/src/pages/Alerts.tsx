import { useCallback, useEffect, useState } from "react";
import { api } from "../api";
import type { AlertRow } from "../components/types";
import { Empty, ErrorBox, Loading, OkBox, SeverityChip } from "../components/ui";

export default function Alerts() {
  const [alerts, setAlerts] = useState<AlertRow[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [msg, setMsg] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setAlerts(await api<AlertRow[]>("/alerts"));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load alerts");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function scan() {
    setMsg("");
    setError("");
    try {
      const r = await api<{ new_alerts: number }>("/alerts/scan", { method: "POST", body: JSON.stringify({}) });
      setMsg(r.new_alerts > 0 ? `${r.new_alerts} new signal(s) generated.` : "Scan complete. No new signals beyond the open alerts you already have.");
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Scan failed");
    }
  }

  async function setStatus(id: number, status: string) {
    await api(`/alerts/${id}/status`, { method: "POST", body: JSON.stringify({ status }) });
    await load();
  }

  if (loading) return <Loading />;
  if (error && alerts.length === 0) return <ErrorBox message={error} />;

  return (
    <div>
      <div className="card">
        <h2>⚠ Early Warning System</h2>
        <p className="muted">
          Alerts are <strong>model-generated research and surveillance signals that need human and public-health
          review</strong>, never confirmed outbreaks and never confirmed drug resistance. Signals are relative to the
          loaded dataset's own historical distribution.
        </p>
        <div className="row" style={{ maxWidth: 420 }}>
          <div style={{ flex: 0 }}>
            <button className="btn" onClick={scan}>
              Run alert scan
            </button>
          </div>
          {msg && <div style={{ flex: 1 }}><OkBox>{msg}</OkBox></div>}
        </div>
        {error && <ErrorBox message={error} />}
      </div>

      {alerts.length === 0 && <Empty>No alerts recorded. Train models, forecast, then run a scan.</Empty>}

      {alerts.map((a) => (
        <div key={a.id} className={`alert-card ${a.severity}`}>
          <div style={{ display: "flex", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
            <div>
              <SeverityChip severity={a.severity} />{" "}
              <span className="chip neutral">{a.alert_type}</span> <strong>{a.title}</strong>
            </div>
            <div>
              {a.status === "open" ? (
                <>
                  <button className="btn outline" style={{ marginRight: 8 }} onClick={() => setStatus(a.id, "acknowledged")}>
                    Acknowledge
                  </button>
                  <button className="btn outline" onClick={() => setStatus(a.id, "dismissed")}>
                    Dismiss
                  </button>
                </>
              ) : (
                <span className="chip neutral">{a.status}</span>
              )}
            </div>
          </div>
          <div className="meta">
            {new Date(a.created_at).toLocaleString()} · {a.region ?? "national"} · model ref: {a.model_ref ?? "—"} ·
            confidence: {a.confidence ?? "not computed"}
          </div>
          <div className="evidence">{JSON.stringify(a.evidence)}</div>
          <p className="muted" style={{ marginBottom: 0 }}>{a.explanation}</p>
        </div>
      ))}
    </div>
  );
}
