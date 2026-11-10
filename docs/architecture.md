# OmniSight Architecture

## High-Level System Organs

```
┌─────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   Target App    │     │  React Dashboard │     │     GitHub       │
│ (/mock-app/...) │     │  (Vite + Diff UI)│     │ (Automated PRs)  │
└────────┬────────┘     └────────┬─────────┘     └────────▲─────────┘
         │                       │                         │
         ▼                       ▼                         │
┌────────────────────────────────────────────────────────────────────┐
│                       FastAPI Backend Gateway                      │
│  ┌──────────┐  ┌───────────┐  ┌───────────┐  ┌──────────────────┐  │
│  │ Browser  │→ │ VLM       │→ │ Self-Heal │→ │ GitHub PR        │  │
│  │ Service  │  │ Analyzer  │  │ & AST Gate│  │ Creator          │  │
│  │(Playwrt) │  │ (Gemini)  │  │(tinycss2) │  │ (PyGithub)       │  │
│  └──────────┘  └───────────┘  └───────────┘  └──────────────────┘  │
│                                                                    │
│  ┌───────────────────────────┐  ┌───────────────────────────────┐  │
│  │ AI Design Studio Router   │  │ SQLite Run & Bug History DB   │  │
│  └───────────────────────────┘  └───────────────────────────────┘  │
└────────────────────────────────────────────────────────────────────┘
```

## End-to-End Pipeline Flow

1. **Multi-Viewport Capture** (`automation.py`): Playwright captures Desktop (`1920×1080`), Tablet (`768×1024`), and Mobile (`375×812`) screenshots alongside DOM HTML.
2. **Region Chunking & Vision Audit** (`analyzer.py`): Unified Gemini multimodal pass identifies responsive, contrast, overlap, and accessibility defects with bounding boxes.
3. **Fix Synthesis & AST Sanitization** (`code_fixer.py`): Generates Tailwind class diffs and surgical CSS filtered via `tinycss2` to strip blanket tag rules (`*`, `body`, `html`).
4. **Live DOM Verification** (`orchestrator.py`): Injects synthesized CSS into Playwright's live DOM and re-captures verification screenshots to confirm zero regressions.
5. **Delivery & Design Studio** (`pr_creator.py`, `design_routes.py`): Creates GitHub Pull Requests or exports verified `.txt` / `.zip` patches, and supports natural-language UI restyling.
