# P-TRANSMIT AI — Build, Hosting & Presentation Guide

**Ghana Plasmodium Intelligence Platform** · KCCR · KNUST, Kumasi

---

## 1. What was done

| Item | Status |
|---|---|
| Production build (`tsc -b && vite build`) | ✅ Passes — output in `dist/` |
| Local hosting | ✅ Verified on `http://localhost:4173` |
| KCCR + KNUST logos | ✅ Downloaded to `presentation/assets/` |
| 15-slide presentation | ✅ Two formats (HTML deck + PowerPoint) |

---

## 2. Run the app locally on this laptop

The FastAPI backend is already running on **port 8000** (verified).

**Option A — production preview (recommended, uses the built `dist/`):**

```bash
npm run build          # already done
npx vite preview --port 4173          # localhost only
npx vite preview --port 4173 --host   # also reachable from other devices on Wi-Fi
```

Then open **http://localhost:4173** (or `http://10.246.147.117:4173` from your phone/another PC on the same network).

**Option B — dev server (hot reload while editing code):**

```bash
npm run dev            # http://localhost:5173, proxies /api to port 8000
```

**Demo access:** click **“⚡ Enter live demo — no account needed”** on the login screen —
one-click guest access, no credentials required (backend `POST /api/auth/demo`).

Classic logins still work: `demo / demo1234` or `admin / ptransmit-admin`

> The preview server proxies `/api/*` to `http://127.0.0.1:8000`, so the backend
> must be running for data to load. If the backend is started later, just
> refresh the browser.

To stop a preview server: close its terminal, or `npx kill-port 4173 4174`.

---

## 3. Presentation — two formats

### 🖥 HTML deck (interactive, pixel-perfect)
**File:** `presentation/index.html` — double-click to open in Chrome/Edge.

- 15 slides, KCCR + KNUST branding, full-screen title & closing slides
- Navigate: **← / →** arrows, Space, click left/right half of the screen, swipe on touch
- **F** = fullscreen · **Home/End** = first/last · `#7` in the URL jumps to slide 7
- **Export to PDF:** press **Ctrl/Cmd + P** → "Save as PDF" → Landscape → Margins: None → ✅ Background graphics

### 📊 PowerPoint (editable, offline-safe)
**File:** `presentation/P-TRANSMIT_AI_Presentation.pptx` — 15 slides, same content
and branding, fully editable in PowerPoint/Google Slides/LibreOffice.

### Slide list (both formats)
1. Title — AI for Malaria Transmission Intelligence
2. Agenda
3. Malaria in Ghana — the burden
4. Plasmodium — species, biology, genome
5. Transmission dynamics — drivers & lags
6. Why AI, why now
7. Adoption of AI in malaria transmission studies (methods landscape)
8. Data foundations
9. P-TRANSMIT AI — platform overview (10 modules)
10. Transmission forecasting engine — how the AI works
11. Spatial intelligence & early warning
12. Plasmodium genomics & resistance guardrails
13. Responsible AI & governance
14. Roadmap (Phases 1–3)
15. Summary, acknowledgements & close

### Assets
- `presentation/assets/kccr_knust.png` — official KCCR+KNUST logo (transparent, from kccr-ghana.org)
- `presentation/assets/knust_seal.jpg` / `knust_seal_trim.jpg` — KNUST seal (Wikipedia, fair-use)

> Tip: replace `[Your Name]` on slide 1 with the presenter's name in both files.

---

## 4. Notes

- The app shows a demo dataset banner; nothing synthetic is presented as real surveillance data.
- First slide of the HTML deck uses Google Fonts (Fraunces/Inter) — needs internet once; all other content is fully offline.
- The `.pptx` was generated with python-pptx; regenerate/edit freely.
