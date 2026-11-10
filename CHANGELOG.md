# Changelog

All notable engineering milestones and releases for **OmniSight** (Infotact Solutions Internship).

## [v0.1.0] - Week 4: Optimization, Dashboard & Evaluation
- Implemented UI region image chunking (`chunk_screenshot_into_regions`) to cut token overhead and improve defect localization.
- Added unified single-pass multimodal VLM analysis across Desktop (`1920px`), Tablet (`768px`), and Mobile (`375px`) viewports.
- Added **AI Design Studio** (`DesignStudio.jsx`, `design_routes.py`, `design_interpreter.py`) for prompt-driven UI updates and bug fixing.
- Added **Settings Console** (`SettingsView.jsx`) with dynamic VLM model selector and Dark/Light theme switcher.
- Added interactive Before/After visual diff slider, bounding-box overlays, and shuffled AI welcome greetings on the dashboard.
- Completed quantitative vision benchmark (`100%` precision/recall across 8 ground-truth UI defects).

## Week 3: Agentic Self-Healing Loop & GitHub PR Integration
- Implemented LangChain ReAct orchestrator (`orchestrator.py`) for in-memory live DOM CSS injection and post-fix VLM verification.
- Added `tinycss2` AST CSS sanitizer (`validate_and_sanitize_css_ast`) to block destructive blanket tag selectors.
- Integrated PyGithub PR creator (`pr_creator.py`) for automatic branching, commits, and Pull Request opening with visual evidence.

## Week 2: Multimodal VLM Analysis & Code Fixer
- Integrated Google Gemini Vision API (`analyzer.py`) ingesting screenshots paired with DOM HTML/CSS context.
- Built action parser (`code_fixer.py`) extracting Tailwind utility diffs and surgical CSS overrides.

## Week 1: Browser Automation & FastAPI Scaffolding
- Built responsive headless Playwright capture service (`automation.py`).
- Scaffolded FastAPI backend (`main.py`, `webhook.py`), SQLite persistence (`database.py`), and sample `mock-app` storefront.
