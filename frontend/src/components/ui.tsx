import { RiskBar } from "./types";

export function RiskChip({ category }: { category: string | null | undefined }) {
  if (!category) return <span className="chip neutral">n/a</span>;
  const cls = category.toLowerCase().replace(/\s+/g, "");
  return <span className={`chip ${cls}`}>{category.toUpperCase()}</span>;
}

export function SeverityChip({ severity }: { severity: string }) {
  return <span className={`chip ${severity}`}>{severity.toUpperCase()}</span>;
}

export function DemoBanner({ show }: { show: boolean | null | undefined }) {
  if (!show) return null;
  return (
    <div className="demo-banner">
      <div>⚠️ DEMONSTRATION DATA: NOT REAL SURVEILLANCE DATA. Synthetic values for software testing only.</div>
    </div>
  );
}

export function Empty({ children }: { children: React.ReactNode }) {
  return <div className="empty">{children}</div>;
}

export function Loading() {
  return <div className="spinner">Loading…</div>;
}

export function ErrorBox({ message }: { message: string }) {
  return <div className="error-box">⚠ {message}</div>;
}

export function OkBox({ children }: { children: React.ReactNode }) {
  return <div className="ok-box">{children}</div>;
}

/** Horizontal bar list for feature importances / explanations. */
export function ImportanceBars({
  items,
  max,
  signed,
}: {
  items: { feature: string; value: number }[];
  max?: number;
  signed?: boolean;
}) {
  const m = max ?? Math.max(...items.map((i) => Math.abs(i.value)), 1e-9);
  return (
    <div>
      {items.map((i) => {
        const width = (Math.abs(i.value) / m) * 100;
        const negative = signed && i.value < 0;
        return (
          <div className="bar-row" key={i.feature}>
            <div className="bar-label" title={i.feature}>
              {i.feature}
            </div>
            <div className="bar-track">
              <div className={`bar-fill${negative ? " neg" : ""}`} style={{ width: `${width}%` }} />
            </div>
            <div className="mono" style={{ width: 74, textAlign: "right" }}>
              {i.value >= 0 && !signed ? "" : ""}
              {i.value.toFixed(3)}
            </div>
          </div>
        );
      })}
    </div>
  );
}

export function riskLabel(r: RiskBar | undefined) {
  return r ? r.risk_category : "n/a";
}
