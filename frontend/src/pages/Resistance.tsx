import { useEffect, useState } from "react";
import { api } from "../api";
import { Empty, ErrorBox, Loading } from "../components/ui";

type ResistanceStatus = {
  module: string;
  status: string;
  message: string;
  required_columns: string[];
  known_markers_catalogue: { gene: string; label: string; drug_class: string; note: string }[];
};

export default function Resistance() {
  const [status, setStatus] = useState<ResistanceStatus | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api<ResistanceStatus>("/resistance/status")
      .then(setStatus)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load"))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Loading />;
  if (error) return <ErrorBox message={error} />;

  return (
    <div>
      <div className="card">
        <h2>💊 Antimalarial Resistance Surveillance</h2>
        <p className="muted">
          Designed for SMART-style surveillance of antimalarial resistance in Ghana: marker frequencies, temporal
          trends, geographic distribution and, once validated labelled outcome data are available, resistance-risk
          models. The platform clearly separates <strong>genetic marker detected</strong> from{" "}
          <strong>phenotypic drug resistance confirmed</strong>.
        </p>
        <Empty>
          <strong>Awaiting validated data / model integration.</strong>
          <p>{status?.message}</p>
          <p className="mono">Required columns: {status?.required_columns.join(", ")}</p>
        </Empty>
      </div>

      <div className="card">
        <h3>Planned outputs (once validated data are loaded)</h3>
        <ul className="muted">
          <li>Marker frequency tables by region and year (descriptive)</li>
          <li>Temporal trend charts for selected variants</li>
          <li>Geographic distribution of resistance-associated markers</li>
          <li>
            Emerging-pattern signals. These appear only with researcher-supplied baseline frequencies and
            thresholds; the platform will not invent resistance thresholds
          </li>
          <li>Integration with treatment-outcome data where ethically approved</li>
        </ul>
      </div>
    </div>
  );
}
