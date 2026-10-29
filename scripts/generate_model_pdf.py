#!/usr/bin/env python3
"""Generate a PDF document with comprehensive information about the P-TRANSMIT AI model."""

from fpdf import FPDF
from datetime import datetime
from pathlib import Path

FONT_DIR = Path("C:/Users/iddri/AppData/Local/Programs/Python/Python312/Lib/site-packages/matplotlib/mpl-data/fonts/ttf")


class ModelPDF(FPDF):
    def __init__(self):
        super().__init__()
        # Unicode-capable fonts
        self.add_font("DejaVu", "", str(FONT_DIR / "DejaVuSans.ttf"), uni=True)
        self.add_font("DejaVu", "B", str(FONT_DIR / "DejaVuSans-Bold.ttf"), uni=True)
        self.add_font("DejaVu", "I", str(FONT_DIR / "DejaVuSans-Oblique.ttf"), uni=True)
        self.add_font("DejaVu", "BI", str(FONT_DIR / "DejaVuSans-BoldOblique.ttf"), uni=True)

    def header(self):
        if self.page_no() > 1:
            self.set_font("DejaVu", "I", 8)
            self.set_text_color(100, 100, 100)
            self.cell(0, 10, "P-TRANSMIT AI — Model Information Document", align="L")
            self.cell(0, 10, f"Page {self.page_no()}", align="R", new_x="LMARGIN", new_y="NEXT")
            self.line(10, 18, 200, 18)
            self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("DejaVu", "I", 7)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, "Research and surveillance decision-support system — not a diagnostic device", align="C")

    def chapter_title(self, title):
        self.set_font("DejaVu", "B", 14)
        self.set_text_color(11, 110, 79)
        self.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(11, 110, 79)
        self.set_line_width(0.5)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def section_title(self, title):
        self.set_font("DejaVu", "B", 11)
        self.set_text_color(11, 74, 56)
        self.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def body_text(self, text):
        self.set_font("DejaVu", "", 10)
        self.set_text_color(34, 48, 58)
        self.multi_cell(0, 5.5, text)
        self.ln(2)

    def bullet_point(self, text, indent=10):
        self.set_font("DejaVu", "", 10)
        self.set_text_color(34, 48, 58)
        self.cell(indent, 5.5, "")
        self.cell(5, 5.5, "•")
        self.multi_cell(190 - indent - 5, 5.5, text)

    def info_box(self, title, content, color=(255, 243, 243), border_color=(179, 32, 42)):
        self.set_fill_color(*color)
        self.set_draw_color(*border_color)
        y_start = self.get_y()
        self.set_font("DejaVu", "B", 10)
        self.set_text_color(*border_color)
        self.cell(0, 6, title, new_x="LMARGIN", new_y="NEXT")
        self.set_font("DejaVu", "", 9)
        self.set_text_color(122, 19, 24)
        self.multi_cell(0, 5, content)
        y_end = self.get_y()
        self.set_fill_color(*color)
        self.rect(10, y_start, 190, y_end - y_start, "F")
        self.set_draw_color(*border_color)
        self.set_line_width(0.5)
        self.rect(10, y_start, 190, y_end - y_start, "D")
        self.ln(4)

    def make_table_header(self, cols, widths):
        self.set_font("DejaVu", "B", 10)
        self.set_fill_color(11, 110, 79)
        self.set_text_color(255, 255, 255)
        for i, (col, w) in enumerate(zip(cols, widths)):
            if i == len(cols) - 1:
                self.cell(w, 7, col, border=1, fill=True, new_x="LMARGIN", new_y="NEXT")
            else:
                self.cell(w, 7, col, border=1, fill=True, new_x="RIGHT", new_y="TOP")

    def make_table_row(self, cells, widths, height=6):
        self.set_font("DejaVu", "", 9)
        self.set_text_color(34, 48, 58)
        for i, (cell, w) in enumerate(zip(cells, widths)):
            if i == len(cells) - 1:
                self.cell(w, height, str(cell), border=1, new_x="LMARGIN", new_y="NEXT")
            else:
                self.cell(w, height, str(cell), border=1, new_x="RIGHT", new_y="TOP")


def create_pdf():
    pdf = ModelPDF()
    pdf.set_auto_page_break(auto=True, margin=20)
    pdf.add_page()

    # ========== COVER PAGE ==========
    pdf.set_fill_color(11, 110, 79)
    pdf.rect(10, 30, 190, 60, "F")

    pdf.set_y(38)
    pdf.set_font("DejaVu", "", 9)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(0, 5, "GHANA PLASMODIUM INTELLIGENCE PLATFORM", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("DejaVu", "B", 22)
    pdf.cell(0, 12, "P-TRANSMIT AI", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("DejaVu", "", 11)
    pdf.cell(0, 6, "The AI Model — Information Document", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("DejaVu", "I", 9)
    pdf.cell(0, 5, "Purpose, Development & Technical Overview", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.ln(25)

    meta_items = [
        ("Document Type", "AI Model Information & Technical Overview"),
        ("Platform Version", "0.1.0 — Phase-1 MVP"),
        ("Date", datetime.now().strftime("%d %B %Y")),
        ("Model Family", "Supervised Tabular Regression"),
        ("Algorithms", "Random Forest, XGBoost, Ridge Regression"),
        ("Target Variable", "Weekly confirmed malaria cases per region"),
        ("Forecast Horizons", "1, 2, 4, and 8 weeks ahead"),
        ("Coverage", "Ghana — 16 administrative regions (ADM1)"),
        ("Validation Method", "Strictly chronological (temporal) hold-out"),
        ("Code Location", "backend/app/ml/transmission.py"),
        ("License", "MIT (code) · geoBoundaries CC-BY 4.0 (boundaries)"),
    ]

    for label, value in meta_items:
        pdf.set_font("DejaVu", "B", 10)
        pdf.set_text_color(80, 80, 80)
        pdf.cell(55, 7, label + ":", align="R")
        pdf.set_font("DejaVu", "", 10)
        pdf.set_text_color(34, 48, 58)
        pdf.cell(0, 7, "  " + value, new_x="LMARGIN", new_y="NEXT")

    pdf.ln(10)

    pdf.info_box(
        "IMPORTANT DISCLAIMER",
        "P-TRANSMIT AI is a research and surveillance decision-support system. "
        "Model predictions are NOT diagnoses and must not independently determine "
        "patient treatment or public-health action. All outputs require review by "
        "qualified public-health researchers and officers. Demonstration data are "
        "synthetic and always labelled as such. This document is for informational "
        "purposes about the model architecture and capabilities.",
        color=(255, 243, 243),
        border_color=(179, 32, 42),
    )

    # ========== PAGE 2: OVERVIEW ==========
    pdf.add_page()
    pdf.chapter_title("1. Overview")

    pdf.section_title("1.1 What is P-TRANSMIT AI?")
    pdf.body_text(
        "P-TRANSMIT AI is an open, locally-hostable decision-support platform for "
        "Plasmodium falciparum transmission, genomic epidemiology, and antimalarial "
        "drug resistance surveillance in Ghana. It is designed for public-health "
        "researchers and officers who need forward-looking, region-level insights "
        "from weekly surveillance data."
    )

    pdf.body_text(
        "The platform ingests weekly surveillance data (confirmed cases plus optional "
        "environmental covariates such as rainfall, temperature, humidity, and vegetation "
        "index), trains and compares supervised forecasting models, produces per-region "
        "forecasts with uncertainty ranges, explains what drove each prediction, and "
        "raises relative early-warning signals for human review."
    )

    pdf.section_title("1.2 Platform Modules")
    modules = [
        ("Dashboard", "National KPIs, choropleth map, national forecast, per-region explanations, alerts overview."),
        ("Transmission AI", "Trains models, shows held-out observed-vs-predicted curves and metrics per horizon."),
        ("Spatial Intelligence", "Interactive map of Ghana's 16 regions with risk / observed / forecast layers."),
        ("Forecasting", "1/2/4/8-week forecasts with residual-based uncertainty intervals and stated assumptions."),
        ("Explainable AI", "SHAP (when available) or perturbation-based per-region contributions — model behaviour, not causality."),
        ("Early-warning Alerts", "Level / trend / forecast signals relative to the dataset's own history; human review required."),
        ("Data Explorer", "CSV/TSV/XLSX/JSON upload, data-quality report, column mapping, Ghana region fuzzy-matching."),
        ("Model Laboratory", "Train/compare/manage models with full reproducibility provenance."),
        ("Reports", "Markdown research report including a limitations section."),
        ("Genomics / Resistance", "Scaffold modules awaiting validated data (no simulated results)."),
    ]

    for name, desc in modules:
        pdf.set_font("DejaVu", "B", 10)
        pdf.set_text_color(11, 110, 79)
        pdf.cell(0, 6, name, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("DejaVu", "", 10)
        pdf.set_text_color(34, 48, 58)
        pdf.multi_cell(0, 5.5, desc)
        pdf.ln(1)

    # ========== PAGE 3: THE AI MODEL ==========
    pdf.add_page()
    pdf.chapter_title("2. The AI Model")

    pdf.section_title("2.1 Model Architecture — Ten Layers")
    pdf.body_text(
        "The 'AI model' is not a single neural network. It is a pipeline of ten layers, "
        "each with a specific job. Together they transform raw weekly surveillance rows "
        "into forecasts, explanations, and early-warning signals."
    )

    layers = [
        (
            "Layer 1 — Data",
            "Standardised weekly rows: one row per region per epi-week. Required columns: region, week_start_date, malaria_cases. Optional covariates include rainfall, temperature, humidity, NDVI, population, suspected cases, and test positivity rate.",
        ),
        (
            "Layer 2 — Features",
            "For every region-week, the engine constructs: case history lags (1-4 weeks), current + lagged environmental conditions, cyclic seasonality encoding (sin/cos of week-of-year), and region fixed-effect dummies. The target is cases at week t+h (the forecast horizon).",
        ),
        (
            "Layer 3 — Models",
            "Three competing algorithms train per horizon: Ridge (regularised linear baseline), Random Forest (250 trees, bagged ensemble), and XGBoost (500 boosted trees). The best model per horizon is selected by lowest test MAE.",
        ),
        (
            "Layer 4 — Validation",
            "Strictly chronological split: earliest 80% of weeks for training, latest 20% for testing. Train and test weeks are disjoint — no future information can leak backward. This is verified by automated tests.",
        ),
        (
            "Layer 5 — Metrics",
            "MAE and RMSE are primary metrics for case counts. MAPE, sMAPE, and R-squared are also reported. R-squared is explicitly noted as 'for completeness only' — low R-squared is normal for noisy count data.",
        ),
        (
            "Layer 6 — Forecast",
            "At the last observed week, the engine builds one feature row per region and predicts cases h weeks ahead. Environmental features are held at their last observed value (persistence assumption), which is stated in every forecast response.",
        ),
        (
            "Layer 7 — Uncertainty",
            "Each forecast carries interval_low and interval_high = prediction +/- 1.96 * residual_std. These are residual-based Gaussian approximations from held-out test errors — NOT calibrated probabilistic intervals.",
        ),
        (
            "Layer 8 — Risk",
            "Risk categories are RELATIVE to the loaded dataset's own historical distribution. Predicted >= 90th percentile = 'very high'; >= 75th = 'high'; >= 50th = 'moderate'; else 'low'. These are not national clinical thresholds.",
        ),
        (
            "Layer 9 — Explainability",
            "Per-region explanations show top 8 features driving each prediction. Uses SHAP TreeExplainer when available (tree models), otherwise single-feature perturbation. Positive = pushed prediction up; negative = pulled down. Describes model behaviour, NOT causal effects.",
        ),
        (
            "Layer 10 — Alerts",
            "Three deterministic rules scan every region (minimum 30 weeks history): Level alert (last 4 weeks mean > historical p90), Trend alert (8-week slope > 90th percentile of historical slopes), and Forecast alert (median 1-4 week prediction > p90). All require human review.",
        ),
    ]

    for title, desc in layers:
        pdf.set_font("DejaVu", "B", 10)
        pdf.set_text_color(11, 110, 79)
        pdf.cell(0, 6, title, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("DejaVu", "", 9.5)
        pdf.set_text_color(34, 48, 58)
        pdf.multi_cell(0, 5, desc)
        pdf.ln(2)

    # ========== PAGE 4: ALGORITHMS ==========
    pdf.add_page()
    pdf.chapter_title("3. Machine Learning Algorithms")

    pdf.section_title("3.1 Ridge Regression (Baseline)")
    pdf.body_text(
        "A regularised linear model using StandardScaler + Ridge (alpha=1.0). "
        "Learns one weight per feature, making it fully interpretable. It captures "
        "linear relationships only but serves as an honest, stable baseline. "
        "Training is fast and the model rarely overfits. If non-linear methods do "
        "not substantially beat Ridge, it suggests the predictive signal is "
        "predominantly linear."
    )

    pdf.section_title("3.2 Random Forest")
    pdf.body_text(
        "An ensemble of 250 decision trees using bagging (bootstrap aggregating). "
        "Key parameters: min_samples_leaf=2, random_state fixed for reproducibility, "
        "n_jobs=-1 for parallel training. Random Forest captures non-linear relationships "
        "and interactions (e.g., rainfall × season × region effects) and is robust to "
        "outliers. It is less interpretable than Ridge but more stable than boosting "
        "on small datasets."
    )

    pdf.section_title("3.3 XGBoost (Gradient Boosting)")
    pdf.body_text(
        "A gradient boosting machine with 500 trees, learning rate 0.05, max depth 4, "
        "subsample 0.9, colsample_bytree 0.9, and L2 regularization (lambda=1.0). "
        "Uses histogram-based tree construction for speed. XGBoost usually performs "
        "best on tabular data but is the most sensitive to hyperparameter settings and "
        "data quality. Trees are added sequentially, each correcting the previous tree's "
        "errors."
    )

    pdf.section_title("3.4 Model Selection")
    pdf.body_text(
        "One model is trained per algorithm per horizon, producing up to 12 model fits "
        "per training run (3 algorithms × 4 horizons). For each horizon, the model with "
        "the lowest test-set MAE is selected as the 'best' and persisted as a joblib "
        "artifact with full provenance metadata. A fixed random seed (default 42, "
        "user-settable) ensures reproducibility across runs."
    )

    # ========== PAGE 5: FEATURES ==========
    pdf.add_page()
    pdf.chapter_title("4. Feature Engineering")

    pdf.section_title("4.1 Feature Groups")
    pdf.body_text(
        "The model does not see raw data directly. For each region-week, the following "
        "features are constructed:"
    )

    features = [
        (
            "Case History (Lags)",
            "cases_lag1 through cases_lag4 — confirmed malaria cases in each of the previous 1-4 weeks for the same region. These are typically the strongest predictors because recent transmission momentum is highly predictive of near-future cases.",
        ),
        (
            "Environment (Current)",
            "rainfall_mm, temperature_mean_c, humidity_pct, ndvi — current-week environmental conditions. These are known correlates of malaria transmission dynamics.",
        ),
        (
            "Environment (Lagged)",
            "rainfall_lag1, temperature_lag1, humidity_lag1, ndvi_lag1 — same environmental variables from one week prior, capturing delayed effects.",
        ),
        (
            "Seasonality",
            "sin_week and cos_week — cyclic encoding of ISO week-of-year using sine and cosine transformations with period 52. This allows the model to learn seasonal patterns without discontinuities at year boundaries.",
        ),
        (
            "Region Fixed Effects",
            "One-hot encoded dummy variables (region_Ashanti, region_Brong_Ahafo, etc.) — 16 binary indicators, one per Ghana region. This allows a single global model to capture each region's baseline transmission level.",
        ),
        (
            "Population (Optional)",
            "population_illustrative — when present, used as a denominator or weighting factor.",
        ),
    ]

    for title, desc in features:
        pdf.set_font("DejaVu", "B", 10)
        pdf.set_text_color(34, 48, 58)
        pdf.cell(0, 6, title, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("DejaVu", "", 9.5)
        pdf.set_text_color(80, 80, 80)
        pdf.multi_cell(0, 5, desc)
        pdf.ln(1.5)

    pdf.section_title("4.2 Target Construction")
    pdf.body_text(
        "For forecast horizon h (where h is 1, 2, 4, or 8 weeks), the target variable "
        "is constructed by shifting the malaria_cases column backward by h weeks "
        "(shift(-h)). This means: at week t, the model learns to predict cases at week "
        "t+h. Rows where the target cannot be computed (because h weeks of future data "
        "don't exist) are excluded from training."
    )

    pdf.section_title("4.3 Data Requirements")
    pdf.body_text(
        "The minimum viable dataset needs: (1) region names matching Ghana's 16 "
        "administrative regions, (2) week_start_date in ISO date format, and (3) "
        "malaria_cases as integer counts. The Data Explorer auto-detects column synonyms "
        "and fuzzy-matches region names. A minimum of 30 weeks of history per region is "
        "needed for meaningful alert generation, and the first 4+ weeks per region are "
        "consumed by lag construction."
    )

    # ========== PAGE 6: VALIDATION ==========
    pdf.add_page()
    pdf.chapter_title("5. Validation & Metrics")

    pdf.section_title("5.1 Temporal Validation Strategy")
    pdf.body_text(
        "The platform uses a strictly chronological train-test split — never random. "
        "The earliest 80% of unique weeks (configurable as 'train fraction') form the "
        "training set; the latest 20% form the test set. Train weeks and test weeks are "
        "guaranteed to be disjoint, and the maximum training week is always less than the "
        "minimum test week. This is verified by automated tests that assert no data "
        "leakage occurs."
    )

    pdf.body_text(
        "This approach approximates how the model would perform in production: it learns "
        "from the past and is evaluated on the future. Random shuffling of time-series "
        "data is never performed, as it would allow the model to 'see' future patterns "
        "during training."
    )

    pdf.section_title("5.2 Performance Metrics")
    pdf.make_table_header(
        ["Metric", "Formula / Definition", "How to Interpret"],
        [35, 60, 95],
    )

    metrics = [
        ("MAE", "Mean Absolute Error: avg|pred-obs|", "Typical error in cases/week. Compare to region's case scale."),
        ("RMSE", "Root Mean Squared Error: sqrt(avg(err²))", "Like MAE but penalises large misses. Large gap vs MAE = occasional bad predictions."),
        ("MAPE", "Mean Abs Pct Error (non-zero weeks)", "Percentage error. Unstable near zero; excluded on zero weeks."),
        ("sMAPE", "Symmetric Mean Abs Pct Error", "Bounded percentage variant for cross-region comparison."),
        ("R²", "Coefficient of determination", "For completeness only. Low R² normal for noisy count data."),
        ("Residual Std", "Std dev of test-set residuals", "Sizes uncertainty intervals. Larger = wider forecast bands."),
    ]

    for row in metrics:
        pdf.make_table_row(row, [35, 60, 95])

    pdf.ln(5)

    pdf.info_box(
        "METRIC GUIDANCE",
        "Always judge models by MAE and RMSE in case units, per horizon. Longer horizons "
        "(8 weeks) are inherently harder than shorter ones (1 week), so expect their errors "
        "to be larger. A large gap between RMSE and MAE signals occasional large misses — "
        "inspect the observed-vs-predicted curves for spike weeks. Low or negative R-squared "
        "is common and not alarming; MAE/RMSE are the primary metrics for count outcomes.",
        color=(255, 248, 230),
        border_color=(212, 160, 23),
    )

    # ========== PAGE 7: FORECASTING ==========
    pdf.add_page()
    pdf.chapter_title("6. Forecasting System")

    pdf.section_title("6.1 How Forecasts Are Produced")
    pdf.body_text("Once models are trained and persisted as joblib artifacts, the forecasting system works as follows:")

    steps = [
        "At the last observed week (t), the engine constructs one feature row per region using actual historical values for case lags and the most recent environmental data.",
        "Seasonality features (sin_week, cos_week) are computed from the calendar for the forecast week.",
        "Each persisted best model (one per horizon: 1, 2, 4, 8 weeks) predicts the case count for its respective horizon.",
        "Environmental features are held at their last observed value — this is the 'persistence assumption' and is explicitly stated in every forecast response.",
        "Predictions are clipped at zero (case counts cannot be negative).",
        "Uncertainty intervals are computed as prediction +/- 1.96 × residual_std, where residual_std comes from the model's test-set errors.",
    ]

    for i, step in enumerate(steps, 1):
        pdf.set_font("DejaVu", "B", 10)
        pdf.set_text_color(11, 110, 79)
        pdf.cell(0, 6, f"Step {i}:", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("DejaVu", "", 10)
        pdf.set_text_color(34, 48, 58)
        pdf.multi_cell(0, 5.5, step)
        pdf.ln(1)

    pdf.section_title("6.2 Environmental Persistence Assumption")
    pdf.body_text(
        "A critical limitation: the forecasting system does not know future weather. "
        "When producing a forecast for week t+h, all environmental covariates (rainfall, "
        "temperature, humidity, NDVI) are held constant at their last observed value from "
        "week t. This means: genuine weather shocks (unseasonal heavy rain, heat waves, "
        "etc.) will NOT be anticipated by the model. The assumptions are clearly stated "
        "in every API response and dashboard display."
    )

    pdf.section_title("6.3 Uncertainty Intervals")
    pdf.body_text(
        "Each forecast row includes interval_low and interval_high computed as: "
        "prediction +/- 1.96 × residual_std (with the lower bound clipped at zero). "
        "The residual_std is the standard deviation of the model's errors on held-out "
        "test weeks — i.e., 'how wrong this model has actually been on unseen data.'"
    )

    pdf.body_text(
        "These intervals are explicitly labelled as 'residual-based Gaussian approximation "
        "(not calibrated probabilistic intervals).' They show the model's typical error "
        "range but are NOT 95% probability guarantees. Treat values near the upper bound "
        "as 'worth watching' rather than as certain outcomes."
    )

    # ========== PAGE 8: EXPLAINABILITY ==========
    pdf.add_page()
    pdf.chapter_title("7. Explainable AI")

    pdf.section_title("7.1 Global Feature Importance")
    pdf.body_text(
        "The platform computes permutation importance on held-out test weeks (5 repeats, "
        "scored by MAE change) to rank which features the model relies on overall. The "
        "top 12 features are displayed. Permutation importance is model-agnostic: it "
        "measures how much prediction accuracy drops when a feature's values are randomly "
        "shuffled, breaking its relationship with the target."
    )

    pdf.section_title("7.2 Per-Region Explanations")
    pdf.body_text("For each region, the dashboard shows the top 8 features driving that region's current prediction as signed bars. The method works as follows:")

    expl_steps = [
        "A base prediction is computed for the region using all feature values.",
        "For each non-region feature, that feature is replaced with its training-set median value.",
        "The model re-predicts with the replaced feature.",
        "The difference from the base prediction is recorded as that feature's contribution.",
        "Contributions are sorted by absolute magnitude; top 8 are displayed.",
        "Positive contributions pushed the prediction UP; negative contributions pulled it DOWN.",
    ]

    for i, step in enumerate(expl_steps, 1):
        pdf.set_font("DejaVu", "", 10)
        pdf.set_text_color(34, 48, 58)
        pdf.cell(8, 5.5, f"{i}.")
        pdf.multi_cell(182, 5.5, step)
        pdf.ln(0.5)

    pdf.ln(2)

    pdf.section_title("7.3 SHAP Integration (Optional)")
    pdf.body_text(
        "When the optional 'shap' Python package is installed, tree-based models "
        "(Random Forest and XGBoost) use SHAP TreeExplainer instead of the perturbation "
        "heuristic. SHAP (SHapley Additive exPlanations) provides game-theory-based "
        "feature attributions with stronger theoretical foundations. The method used is "
        "always displayed alongside the explanations."
    )

    pdf.info_box(
        "CRITICAL INTERPRETATION NOTE",
        "Explanations describe MODEL BEHAVIOUR, NOT CAUSAL EFFECTS. If 'rainfall' shows "
        "a positive contribution, it means the model leaned on rainfall for this prediction "
        "— it does NOT mean rainfall caused the increase in cases. Always use explanations "
        "for sanity-checking (is the model reacting to recent cases, rainfall, or season?) "
        "rather than as evidence of causation.",
        color=(255, 248, 230),
        border_color=(212, 160, 23),
    )

    # ========== PAGE 9: ALERTS ==========
    pdf.add_page()
    pdf.chapter_title("8. Early-Warning Alert System")

    pdf.section_title("8.1 Alert Rules")
    pdf.body_text(
        "Three deterministic rules scan every region with at least 30 weeks of history. "
        "All rules are relative to the loaded dataset's own historical distribution — "
        "no absolute thresholds are invented."
    )

    pdf.make_table_header(["Rule", "Severity", "Trigger Condition"], [25, 18, 147])

    rules = [
        (
            "Level",
            "Warning",
            "Mean of the last 4 observed weeks EXCEEDS the region's historical 90th percentile of weekly cases. Flags unusually high current transmission relative to the region's own past.",
        ),
        (
            "Trend",
            "Warning",
            "Least-squares slope of the last 8 weeks EXCEEDS the 90th percentile of all historical 8-week slopes for that region, AND the threshold is positive. Flags unusually steep upward trends.",
        ),
        (
            "Forecast",
            "Info",
            "Median model prediction for weeks 1-4 EXCEEDS the region's historical 90th percentile. Flags when the model expects elevated transmission based on current conditions and trends.",
        ),
    ]

    for row in rules:
        pdf.make_table_row(row, [25, 18, 147], height=12)

    pdf.ln(5)

    pdf.section_title("8.2 Alert Workflow")
    steps_alerts = [
        "Alerts are generated by running an 'alert scan' which applies all three rules to every region.",
        "Each alert stores: date, region, severity, alert type, evidence numbers (the specific values that fired the rule), model reference, and a plain-language explanation.",
        "Duplicate suppression: if an open alert of the same type and region already exists, a new scan will NOT create a duplicate.",
        "Workflow states: Open → Acknowledged (kept on radar) or Dismissed (not actionable). A human always makes this decision.",
        "Alerts are research signals, NOT confirmed outbreaks. They require human and public-health review before any action.",
    ]

    for i, step in enumerate(steps_alerts, 1):
        pdf.set_font("DejaVu", "", 10)
        pdf.set_text_color(34, 48, 58)
        pdf.cell(8, 5.5, f"{i}.")
        pdf.multi_cell(182, 5.5, step)
        pdf.ln(1)

    # ========== PAGE 10: GOVERNANCE ==========
    pdf.add_page()
    pdf.chapter_title("9. Scientific Governance")

    pdf.section_title("9.1 Principles Enforced in Code")
    principles = [
        "Synthetic demonstration data are always labelled clearly and never mixed with real data. The demo dataset name includes 'DEMONSTRATION DATA — NOT REAL SURVEILLANCE DATA.'",
        "No invented thresholds. Risk categories are relative to the loaded dataset's own history. Resistance interpretation requires researcher-supplied definitions — the platform never assigns clinical meaning to genetic markers.",
        "Strictly temporal validation. Time-series rows are never shuffled. Train weeks always precede test weeks. This is verified by automated tests.",
        "MAE and RMSE are primary metrics for count outcomes. R-squared is reported for completeness only and explicitly noted as such.",
        "Explanations describe model behaviour, not causal effects. The method text always ends with this clarification.",
        "Alerts are research signals, not confirmed outbreaks. They require human and public-health review. No automatic actions are taken based on alerts.",
        "Genetic marker does not equal phenotypic drug resistance. The genomics and resistance modules are descriptive scaffolds awaiting validated data.",
        "Audit logs record logins, dataset operations, training runs, and report generation for traceability.",
    ]

    for p in principles:
        pdf.bullet_point(p)
        pdf.ln(1.5)

    pdf.ln(3)

    pdf.section_title("9.2 Data Provenance & Reproducibility")
    pdf.body_text(
        "Every trained model artifact (saved as a .joblib file) contains complete provenance "
        "metadata: the exact feature list used, train/test week ranges, random seed, software "
        "versions (Python, scikit-learn, XGBoost, pandas, numpy), and UTC training timestamp. "
        "This makes every training run fully reproducible — running the same data with the same "
        "seed produces identical results."
    )

    pdf.body_text(
        "Artifact files follow the naming convention: transmission_{model_type}_h{horizon}_ds{dataset_id}.joblib. "
        "Each contains the fitted model, model type, horizon, feature names, all metrics, "
        "feature importance rankings, train/test week lists, seed, software versions, and "
        "training timestamp."
    )

    # ========== PAGE 11: TECHNICAL ==========
    pdf.add_page()
    pdf.chapter_title("10. Technical Architecture")

    pdf.section_title("10.1 Technology Stack")
    tech_items = [
        ("Backend / API", "Python 3.12, FastAPI, SQLAlchemy (SQLite default, PostgreSQL optional), scikit-learn, XGBoost, pandas, numpy, joblib"),
        ("Frontend", "React 18, TypeScript, Vite, Recharts (charts), Leaflet (interactive maps)"),
        ("Geography", "geoBoundaries gbOpen GHA ADM1 boundaries (16 regions), CC-BY 4.0 license, simplified for web map rendering"),
        ("Model Artifacts", "joblib format containing fitted estimators + full provenance metadata"),
        ("Deployment", "Single Docker image serving both API (/api/*) and built React UI (/) from one port. Alternatively, separate backend + frontend for development."),
    ]

    for label, desc in tech_items:
        pdf.set_font("DejaVu", "B", 10)
        pdf.set_text_color(11, 74, 56)
        pdf.cell(40, 6, label + ":")
        pdf.set_font("DejaVu", "", 10)
        pdf.set_text_color(34, 48, 58)
        pdf.multi_cell(150, 5.5, desc)
        pdf.ln(2)

    pdf.section_title("10.2 API Endpoints")
    endpoints = [
        ("GET /api/health", "Health check — returns status, app name, version, demo mode flag, and disclaimer."),
        ("GET /api/datasets", "List all uploaded datasets with metadata and data-quality reports."),
        ("POST /api/datasets/upload", "Upload CSV/XLSX/JSON surveillance or genomic data with auto-detection of columns and region matching."),
        ("GET /api/models", "List trained models with metrics and provenance."),
        ("POST /api/models/train", "Train transmission models on a dataset — returns results per horizon per model."),
        ("GET /api/forecasts", "Retrieve forecasts for selected horizons using persisted best models."),
        ("GET /api/explain", "Get per-region feature contributions for the current forecast."),
        ("GET /api/alerts", "List all alerts with status, severity, evidence, and explanations."),
        ("POST /api/alerts/scan", "Run alert scan — applies all rules to current data and creates new alerts."),
        ("GET /api/reports/generate", "Generate a Markdown research report with dataset info, models, alerts, and limitations."),
    ]

    for endpoint, desc in endpoints:
        pdf.set_font("DejaVu", "B", 9.5)
        pdf.set_text_color(34, 48, 58)
        pdf.cell(55, 5.5, endpoint)
        pdf.set_font("DejaVu", "", 9.5)
        pdf.set_text_color(80, 80, 80)
        pdf.multi_cell(135, 5.5, desc)
        pdf.ln(1)

    # ========== PAGE 12: DEVELOPMENT ==========
    pdf.add_page()
    pdf.chapter_title("11. Development & Roadmap")

    pdf.section_title("11.1 Current State (Phase 1 MVP)")
    pdf.body_text(
        "The current version (0.1.0) is a Phase-1 Minimum Viable Product focused on "
        "malaria transmission forecasting for Ghana's 16 regions. It provides a complete "
        "pipeline from data upload through model training, forecasting, explainability, "
        "and alerting — all running locally or on free hosting tiers."
    )

    pdf.body_text(
        "The genomics and drug resistance modules exist as scaffolds: they accept variant "
        "table uploads and compute descriptive statistics (marker counts, frequencies per "
        "stratum) but do NOT perform resistance interpretation. This is intentional governance — "
        "no resistance claims are made without researcher-supplied validated definitions."
    )

    pdf.section_title("11.2 Known Limitations")
    limitations = [
        "Environmental persistence: forecasts hold weather/vegetation at last observed values; genuine rainfall shocks will not be anticipated.",
        "Direct (non-recursive) horizons: each horizon is a separate model; an 8-week forecast does not internally compound the 1-4 week forecasts.",
        "Intervals are uncalibrated Gaussian approximations from test residuals, not true probabilistic forecasts.",
        "Regional dummy coverage: a region absent at training time gets no dedicated dummy — all 16 regions should have history before real use.",
        "Minimum history requirements: alert rules need ≥ 30 weeks; lag construction consumes the first 4+ weeks per region.",
        "Demo data are synthetic with a scripted late-season upswing to exercise alerts — they are always labelled and must never be used for research conclusions.",
        "Genomics/Resistance modules are descriptive scaffolds awaiting validated data; detected markers are not phenotypic resistance.",
        "Free-tier hosting has ephemeral storage — trained models and uploaded accounts do not survive restarts (local storage in models/ persists).",
    ]

    for i, lim in enumerate(limitations, 1):
        pdf.set_font("DejaVu", "", 10)
        pdf.set_text_color(34, 48, 58)
        pdf.cell(8, 5.5, f"{i}.")
        pdf.multi_cell(182, 5.5, lim)
        pdf.ln(1.5)

    pdf.section_title("11.3 Future Roadmap")
    roadmap = [
        ("Phase 2", "Genomic module build-out: SNP statistics, diversity indices (H, MOI), population structure analysis; resistance surveillance with researcher-defined thresholds."),
        ("Phase 3", "Environmental raster ingestion (CHIRPS rainfall, ERA5-Land temperature, MODIS NDVI), Bayesian spatial models, spatiotemporal deep learning models, calibrated uncertainty quantification, configurable alert thresholds."),
        ("Phase 4", "Multimodal AI combining genomic + clinical + environmental data, mechanistic transmission model coupling, PDF report export, multi-user deployment hardening with role-based access control."),
    ]

    for phase, desc in roadmap:
        pdf.set_font("DejaVu", "B", 10)
        pdf.set_text_color(11, 110, 79)
        pdf.cell(0, 6, phase, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("DejaVu", "", 10)
        pdf.set_text_color(34, 48, 58)
        pdf.multi_cell(0, 5.5, desc)
        pdf.ln(2)

    # ========== PAGE 13: RUNNING ==========
    pdf.add_page()
    pdf.chapter_title("12. Running the Platform")

    pdf.section_title("12.1 Local Execution (Windows)")
    pdf.body_text(
        "Double-click start-ptransmit.bat in the project root. This launches both the "
        "backend (FastAPI on port 8000) and the frontend (Vite preview on port 4173) "
        "and opens the browser to http://localhost:4173. Keep both server windows open — "
        "close them to stop the platform."
    )

    pdf.section_title("12.2 Single-Process Mode (Backend Serves UI)")
    pdf.body_text(
        "After building the frontend (cd frontend && npm run build), start only the backend: "
        "cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000. "
        "The backend serves both the API and the built React UI from one address: "
        "http://127.0.0.1:8000/. This is the recommended mode for hosting and the mode "
        "currently running."
    )

    pdf.section_title("12.3 Current Access Points")
    pdf.set_font("DejaVu", "B", 10)
    pdf.set_text_color(11, 74, 56)
    pdf.cell(0, 6, "This platform instance is currently running with the following access points:", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)

    access_points = [
        ("Full Platform (Single Link)", "http://127.0.0.1:8000/", "Backend serves both API and built React UI — ONE link opens everything."),
        ("Frontend Only (Dev Preview)", "http://127.0.0.1:4173/", "Vite preview server; proxies API calls to port 8000."),
        ("API Health Check", "http://127.0.0.1:8000/api/health", "Returns status, version, demo mode flag, and disclaimer."),
        ("API Documentation", "http://127.0.0.1:8000/docs", "Interactive Swagger UI for all API endpoints."),
    ]

    for label, url, desc in access_points:
        pdf.set_font("DejaVu", "B", 10)
        pdf.set_text_color(11, 110, 79)
        pdf.cell(0, 6, label, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("DejaVu", "", 10)
        pdf.set_text_color(34, 48, 58)
        pdf.cell(0, 5.5, "  URL: " + url, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("DejaVu", "I", 9.5)
        pdf.set_text_color(80, 80, 80)
        pdf.cell(0, 5.5, "  " + desc, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

    pdf.section_title("12.4 Default Credentials")
    pdf.body_text(
        "Default accounts (change immediately for any real deployment): "
        "Admin: admin / ptransmit-admin | Researcher: demo / demo1234. "
        "In demo mode, you can also click 'Enter live demo' for read-only access without an account."
    )

    # ========== PAGE 14: DATA ==========
    pdf.add_page()
    pdf.chapter_title("13. Data Specifications")

    pdf.section_title("13.1 Input Data Requirements")
    pdf.body_text(
        "Upload a weekly surveillance table (CSV, XLSX, JSON, or TSV) with at minimum: "
        "region (Ghana region, fuzzy-matched to 16 canonical names), week_start_date "
        "(ISO date), and malaria_cases (confirmed case count). Synonyms are auto-detected "
        "for all columns."
    )

    pdf.section_title("13.2 Column Specifications")
    pdf.make_table_header(
        ["Standard Column", "Purpose", "Recognised Synonyms"],
        [45, 55, 90],
    )

    columns = [
        ("region", "Ghana region name", "region_name, admin1, adm1, province"),
        ("week_start_date", "ISO date of epi-week start", "date, week_start, report_date"),
        ("malaria_cases", "Confirmed cases (count)", "mal_cases, cases, confirmed_cases"),
        ("suspected_cases", "Tests conducted / suspected", "tested, suspected"),
        ("test_positivity_rate", "Test positivity percentage", "positivity"),
        ("rainfall_mm", "Rainfall (mm)", "rainfall"),
        ("temperature_mean_c", "Mean temperature (°C)", "temp, temperature"),
        ("humidity_pct", "Relative humidity (%)", "rh, humidity"),
        ("ndvi", "Normalised Difference Vegetation Index", "evi, vegetation_index"),
        ("population_illustrative", "Denominator / population weight", "population, pop"),
    ]

    for row in columns:
        pdf.make_table_row(row, [45, 55, 90])

    # ========== PAGE 15: FINAL ==========
    pdf.add_page()
    pdf.chapter_title("14. Summary")

    pdf.body_text(
        "P-TRANSMIT AI is a thoughtfully engineered decision-support platform that brings "
        "together machine learning, explainable AI, and public-health domain knowledge to "
        "address malaria surveillance in Ghana. Its key strengths are:"
    )

    strengths = [
        "A complete, locally-runnable pipeline from data upload to actionable insights — no cloud dependency required.",
        "Scientific honesty: temporal validation, relative risk categories, clearly stated assumptions, and explicit disclaimers about what predictions are and are not.",
        "Reproducibility: every model training run records its full provenance — data, split, seed, software versions, and timestamp.",
        "Explainability: per-region explanations show what drove each prediction, with the method always disclosed (SHAP when available, perturbation fallback otherwise).",
        "Governance by design: synthetic data is always labelled, no invented thresholds, alerts require human review, and genetic markers are never equated with drug resistance.",
        "Open source (MIT license) with clear data credits (geoBoundaries CC-BY 4.0, OpenStreetMap tiles).",
    ]

    for s in strengths:
        pdf.bullet_point(s)
        pdf.ln(2)

    pdf.ln(3)

    pdf.info_box(
        "BOTTOM LINE",
        "P-TRANSMIT AI supports research and surveillance judgment. Predictions are not "
        "diagnoses and must not independently determine treatment or public-health action. "
        "The platform is a tool for informed decision-making, not an autonomous system. "
        "All outputs require review by qualified public-health researchers and officers.",
        color=(255, 248, 230),
        border_color=(212, 160, 23),
    )

    pdf.ln(5)

    pdf.set_font("DejaVu", "I", 9)
    pdf.set_text_color(128, 128, 128)
    pdf.multi_cell(
        0,
        5,
        "This document was generated from backend/app/ml/transmission.py and "
        "backend/app/services/alerts.py on "
        + datetime.now().strftime("%d %B %Y")
        + ". "
        "Code: MIT (c) 2026 P-TRANSMIT AI contributors. Boundaries: geoBoundaries gbOpen "
        "GHA ADM1, CC-BY 4.0. Research and surveillance decision support — not a diagnostic device.",
    )

    # Save PDF
    output_path = "P-TRANSMIT_AI_Model_Information.pdf"
    pdf.output(output_path)
    print(f"PDF generated: {output_path}")
    return output_path


if __name__ == "__main__":
    import os

    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    create_pdf()
