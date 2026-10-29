"""Report generation (Markdown for MVP; structure ready for PDF export).

Reports bundle dataset description, data-quality assessment, model provenance,
performance metrics, forecasts and mandatory limitations — everything a
researcher needs for reproducibility.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db.models import Alert, Dataset, TrainedModel


def generate_report(db: Session, dataset_id: int | None = None) -> tuple[str, str]:
    """Build a Markdown report. Returns (filename, markdown)."""
    s = get_settings_lazily()
    now = datetime.now(timezone.utc)
    lines: list[str] = []
    add = lines.append

    add("# P-TRANSMIT AI — Research Report")
    add("")
    add(f"*Generated: {now.strftime('%Y-%m-%d %H:%M UTC')}*")
    add("")
    add(f"> **Disclaimer:** {s.disclaimer}")
    add("")

    q = db.query(Dataset)
    if dataset_id:
        q = q.filter(Dataset.id == dataset_id)
    datasets = q.order_by(Dataset.created_at.desc()).all()

    for ds in datasets:
        label = "DEMONSTRATION DATA — NOT REAL SURVEILLANCE DATA" if ds.is_synthetic else "User-uploaded research data"
        add(f"## Dataset: {ds.name} (id={ds.id})")
        add("")
        add(f"- Record type: `{ds.record_type}` — **{label}**")
        add(f"- Source: `{ds.source}`; rows: {ds.row_count}; columns: {len(ds.columns or [])}")
        if ds.profile:
            issues = ds.profile.get("issues", [])
            add(f"- Data-quality issues: {len(issues)}")
            for i in issues[:10]:
                add(f"  - {i}")
        add("")

    models = db.query(TrainedModel).order_by(TrainedModel.training_date.desc()).all()
    if models:
        add("## Trained models")
        add("")
        add("| Model | Task | Target | Validation | MAE | RMSE | Seed | Version |")
        add("|---|---|---|---|---|---|---|---|")
        for m in models:
            metrics = m.metrics or {}
            val = (m.validation or {}).get("strategy", "temporal split")
            add(
                f"| {m.name} ({m.model_type}) | {m.task} | {m.target} | {val} "
                f"| {metrics.get('MAE', '—')} | {metrics.get('RMSE', '—')} "
                f"| {m.random_seed} | {m.model_version} |"
            )
        add("")

    alerts = db.query(Alert).filter(Alert.status == "open").all()
    if alerts:
        add("## Open research signals (alerts)")
        add("")
        for a in alerts:
            add(f"- **[{a.severity.upper()}] {a.title}** — {a.created_at:%Y-%m-%d} ({a.alert_type})")
            add(f"  - Evidence: `{a.evidence}`")
        add("")

    add("## Limitations")
    add("")
    add("- Predictive associations are not causal effects.")
    add("- Forecast intervals are residual-based approximations, not calibrated probabilistic intervals.")
    add("- Risk categories are relative to the loaded dataset's own historical distribution.")
    add("- Genomic and resistance modules are scaffolds awaiting validated research data.")
    add("- Synthetic demonstration data must never be used for research conclusions.")
    add("")

    fname = f"ptransmit_report_{now.strftime('%Y%m%d_%H%M')}.md"
    return fname, "\n".join(lines)


def get_settings_lazily():
    from app.core.config import get_settings

    return get_settings()
