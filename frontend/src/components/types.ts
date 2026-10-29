export type DatasetSummary = {
  id: number;
  name: string;
  record_type: string;
  source: string;
  is_synthetic: boolean;
  row_count: number;
  columns: string[];
  created_at: string;
};

export type ForecastRow = {
  region: string;
  horizon_weeks: number;
  last_observed_week: string;
  forecast_week: string;
  predicted_cases: number;
  interval_low: number;
  interval_high: number;
  risk_category: string;
  model_type: string;
  interval_method: string;
};

export type ObsPredRow = {
  region: string;
  week_start_date: string;
  observed: number;
  predicted: number;
};

export type AlertRow = {
  id: number;
  alert_type: string;
  severity: string;
  region: string | null;
  title: string;
  evidence: Record<string, unknown>;
  model_ref: string | null;
  confidence: number | null;
  explanation: string;
  status: string;
  created_at: string;
};

export type RegionStats = {
  region: string;
  recent_4wk_mean_cases: number;
  recent_4wk_total_cases: number;
  hist_p90: number;
  forecast_median_4wk: number | null;
  risk_category: string | null;
};

export type RiskBar = { risk_category: string };

export type TrainedModelRow = {
  id: number;
  name: string;
  model_type: string;
  task: string;
  target: string;
  dataset_id: number | null;
  metrics: Record<string, unknown>;
  validation: Record<string, unknown>;
  feature_importance: { feature: string; importance: number }[];
  random_seed: number;
  model_version: string;
  software_versions: Record<string, string>;
  training_date: string;
  artifact_path: string | null;
};
