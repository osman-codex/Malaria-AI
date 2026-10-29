# Beamer deck (Overleaf)

## Files
- `main.tex` — the full 15-slide deck (pdfLaTeX)
- Logo images referenced: `kccr_knust.png` and `knust_seal(.jpg/.png)`

## How to use on Overleaf
1. Go to overleaf.com → **New Project** → **Blank Project**, name it e.g. `ptransmit-beamer`.
2. Upload `main.tex` (this folder) — it replaces the auto-generated one.
3. Upload the two logo images from `frontend/presentation/assets/`:
   - `kccr_knust.png` (transparent KCCR + KNUST logo)
   - the KNUST seal; rename it to `knust_seal.jpg` (or `knust_seal.png`) and keep
     the name matching what you upload. The deck checks for `kccr_knust.png`;
     if a logo is missing the build still succeeds and just shows a text brand bar.
4. Menu → Compiler: **pdfLaTeX** (default). TeX Live version: any recent (2022+).
5. Click **Recompile**. Download the PDF.

## Output quality
- `lmodern` + `microtype` give vector fonts that stay sharp at any zoom.
- pgfplots/TikZ figures are drawn as vectors, so they are resolution-independent.
- Logo PNGs are high-resolution; print-quality PDF at 600 dpi+.

## Editing tips
- Presenter name: replace `[Your Name]` on the title slide.
- Colors: the brand palette is defined at the top (`knustred`, `ggreen`, `ggold`, `navy`).
- Demo numbers on slides 10 and 11 reflect the current synthetic dataset
  (MAE 5–9, 9 alerts, upswing regions). Re-run the demo and update if those change.
