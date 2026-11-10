# OmniSight

**Multimodal UI Self-Healing & Autonomous RPA Agent**

OmniSight is an intelligent QA & Robotic Process Automation (RPA) agent built during the Infotact Solutions Generative AI internship. It automatically renders live web applications across viewports, detects visual and layout bugs using Vision-Language Models (Google Gemini), generates AST-verified CSS/Tailwind patches, re-verifies fixes in-browser, and submits GitHub Pull Requests with Before/After visual proof.

## Core Modules ("Main Organs")

1. **Headless Navigator (`backend/services/browser/`)**: Uses Python Playwright to visit target URLs and capture screenshots across Desktop (`1920x1080`), Tablet (`768x1024`), and Mobile (`375x812`) viewports.
2. **VLM Analyzer & Code Fixer (`backend/services/vlm/`)**: Performs unified multimodal inspection (screenshots + HTML/CSS) using Google Gemini and generates surgical Tailwind CSS diffs and `tinycss2` AST-sanitized CSS overrides.
3. **Agentic Orchestrator (`backend/services/agent/`)**: Runs the self-healing loop (inject CSS in live DOM -> capture verification screenshot -> confirm resolution) plus the Design Studio prompt interpreter.
4. **CI/CD Gateway & GitHub PR Engine (`backend/api/`, `backend/services/github/`)**: FastAPI server with SQLite run history, CI/CD webhook handlers, and PyGithub automated branching/PR submission.
5. **Executive React Dashboard (`frontend/`)**: Includes Recent Scans, Interactive Before/After Visual Diff Slider, Bounding Box Overlays, AI Design Studio, Live Site Preview, Notepad/ZIP export, and Dynamic VLM Settings.

## Infotact Solutions Week 1–4 Schedule

- **Week 1 (Foundation & Automation)**: Playwright responsive screenshot capture + FastAPI CI/CD webhook scaffolding + SQLite persistence.
- **Week 2 (Multimodal Prompting & Action Engine)**: Gemini Vision prompt engineering + Python fix parser & Mid-Project Vision Audit.
- **Week 3 (Self-Healing Loop & GitHub Integration)**: In-memory live DOM CSS injection + visual re-verification + PyGithub automated PR creation.
- **Week 4 (Optimization & Polish)**: UI Region Image Chunking (`chunk_screenshot_into_regions`), React approval dashboard, AI Design Studio, and vision benchmark evaluation.

## Setup Instructions

1. Ensure **Python 3.10+** and **Node.js 18+** are installed.
2. Install backend dependencies and Playwright Chromium:
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```
3. Copy `.env.example` to `.env` and add `GEMINI_API_KEY` and `GITHUB_TOKEN`.
4. Start the backend server:
   ```bash
   python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
   ```
5. Start the React dashboard (`http://127.0.0.1:5173`):
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
