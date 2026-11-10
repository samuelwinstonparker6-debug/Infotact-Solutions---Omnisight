# OmniSight Frontend Dashboard

Executive React + Vite dashboard for **OmniSight — Multimodal UI Self-Healing & RPA Agent**.

## Features

- **Dashboard View**: Trigger multi-viewport UI scans, browse Recent Scans history, and view dynamic AI greetings in the initial panel.
- **Visual PR Reviewer**: Inspect Before/After screenshots with an interactive diff slider, side-by-side mode, and bounding-box overlays.
- **One-Click Delivery**: Push verified patches directly to GitHub Pull Requests, sync merged PRs, or export `.txt` (Notepad) and `.zip` bundles.
- **AI Design Studio**: Submit natural-language UI restyling or combined bug-fix prompts.
- **Settings Console**: Select Gemini / Vision models dynamically, manage API credentials, and toggle Dark/Light themes.

## Development Setup

```bash
npm install
npm run dev
```

The Vite dev server runs at `http://127.0.0.1:5173/` and proxies `/api` requests to the FastAPI backend at `http://127.0.0.1:8000` (configured in `vite.config.js`).

## Scripts

- `npm run dev` — Start Vite dev server with HMR
- `npm run build` — Build production bundle to `dist/`
- `npm run lint` — Run Oxlint static analysis checks
