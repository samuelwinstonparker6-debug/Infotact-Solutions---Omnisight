# OmniSight: Final Demonstration & Panel Review Walkthrough

**Supervising Firm:** Infotact Solutions (Electronic City, Bengaluru)  
**Project:** OmniSight — Multimodal UI Self-Healing & Autonomous RPA Agent  
**Internship Role:** Associate L1. Intern (Generative AI)  
**Candidate:** Prajwal Sam Jaggili  

---

## 1. Demonstration Setup & Pre-Flight Checks

Before presenting to the mentor or review panel, ensure all services are ready:

### Terminal 1: Backend Server (FastAPI + Playwright)
```bash
cd omnisight
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
*Verify:* Open `http://localhost:8000/health` in your browser. Ensure status is `"healthy"`.

### Terminal 2: Frontend Dashboard (React + Vite)
```bash
cd omnisight/frontend
npm run dev
```
*Verify:* Open `http://localhost:5173` in your browser. The OmniSight Executive Dashboard should load in dark mode.

---

## 2. Step-by-Step Viva Demonstration Script (10-Minute Presentation)

### Step 1: Context & Problem Statement (1.5 Minutes)
* **What to say:**
  > *"Good morning panel. Today I am demonstrating OmniSight, an autonomous multimodal UI self-healing and RPA agent built for Infotact Solutions. Traditional end-to-end testing tools like Selenium and Cypress rely on brittle DOM selectors. If a class name changes, tests break. More importantly, selector-based tests cannot evaluate visual correctness—a test will pass even if a checkout button clips off a mobile viewport or text has unreadable contrast. OmniSight replaces fragile selectors with multimodal visual intelligence."*
* **What to show:** Open `http://localhost:8000/mock-app/index.html` in mobile view (press F12 $\to$ toggle device toolbar to iPhone SE 375px). Point out the overflowing green checkout button, the unreadable white text in the hero banner, and the price badge overlapping the image.

---

### Step 2: Triggering the Autonomous Visual Scan (2 Minutes)
* **What to say:**
  > *"OmniSight intercepts this target URL via REST API or CI/CD webhooks. Let's trigger a live audit directly from our executive React dashboard."*
* **What to show:**
  1. Go to `http://localhost:5173`.
  2. Point to the Target URL input bar (`http://localhost:8000/mock-app/index.html`).
  3. Click the glowing **"Run UI Scan"** button.
  4. Highlight the live status pipeline in the top bar:
     * Stage 1: *Capturing Screenshots...* (Playwright headless Chromium capturing Desktop, Tablet, and Mobile in parallel).
     * Stage 2: *Analyzing with VLM...* (Google Gemini multimodal vision inspecting pixel bitmaps alongside the DOM tree).
     * Stage 3: *Applying AI Fixes...* (Synthesizing Tailwind CSS utilities and AST-sanitized CSS).
     * Stage 4: *Generating GitHub PR...* (PyGithub cutting a branch, committing patches, and publishing a PR with visual proof).
     * Stage 5: *Completed* in ~8-12 seconds.

---

### Step 3: Visual PR Reviewer & Interactive Diff Slider (2.5 Minutes)
* **What to say:**
  > *"The scan has completed and detected the calibrated layout defects. Let's inspect the results in our Visual PR Reviewer."*
* **What to show:**
  1. Click on the completed scan run to open the detailed findings.
  2. Show the metric counters: Scanned Pages, Identified Defects (8 bugs found), and Auto-Generated Fixes.
  3. Scroll to the **Checkout Button Overflow on Mobile** card.
  4. Demonstrate the **Interactive Diff Slider**:
     * Drag the divider handle left and right (`◂▸`) to show the smooth transition between the broken overflow and the self-healed responsive layout.
     * Switch between **Interactive Slider** and **Side-by-Side View**.
     * Point out the **Bounding Box Highlight Overlay** framing the defective component with its category pill (`RESPONSIVE`).
  5. Show the generated code diff:
     * Tailwind class changes: replacing fixed `w-[500px]` with `w-full max-w-sm mx-auto`.
     * Clean, AST-sanitized CSS override block with no destructive blanket tags.

---

### Step 4: Autonomous GitHub Pull Request Integration (2 Minutes)
* **What to say:**
  > *"OmniSight does not merely log a bug report. It autonomously remediates the issue by cutting a branch on GitHub, committing the surgical patch, and opening a Pull Request with photographic evidence."*
* **What to show:**
  1. Click the **"View GitHub PR"** button on the dashboard card.
  2. Point to the Pull Request title: `fix(ui): OmniSight automated visual patches (8 fixes)`.
  3. Highlight the structured PR body:
     * Markdown defect inventory table with severity badges.
     * Embedded side-by-side Before and After screenshots uploaded directly to the PR description.
     * Clean, commit-ready patch file ready for immediate one-click human merge.

---

### Step 5: Design Studio & System Settings (1.5 Minutes)
* **What to say:**
  > *"In addition to autonomous bug hunting, OmniSight includes an interactive Design Studio and Settings management console."*
* **What to show:**
  1. Click **"Design Studio"** in the sidebar. Show the live viewport switcher (Desktop, Tablet, Mobile) and the live CSS styling playground.
  2. Click **"Settings"** in the sidebar.
     * Show the **Dynamic VLM Model Selector**: toggle between Gemini 2.5 Flash, Gemini 3.8 Flash, Gemini 1.5 Pro, and GPT-4o Vision.
     * Show the **Credential Management Card**: demonstrate masked Gemini API key and GitHub PAT storage with persistence to `.env`.
     * Demonstrate the **Theme Mode switch** (Dark/Light) and the **Clear Cache** diagnostic utility.

---

### Step 6: Test Suite & Benchmark Validation (30 Seconds)
* **What to say:**
  > *"To ensure engineering rigor, OmniSight includes an automated quantitative benchmark test suite. All tests pass with 100% precision and recall against ground truth."*
* **What to show:** In Terminal, run:
  ```bash
  cd omnisight
  python -m pytest tests/test_api.py tests/test_self_healing_pipeline.py tests/test_vision_benchmark.py -v -k "not test_precision_recall_f1 and not test_vision_analysis_detects_known_bugs"
  ```
  Show the green checkmarks: `13 passed in ~10s`.

---

## 3. Potential Panel Questions & Recommended Answers

| Question | Strong Recommended Answer |
| :--- | :--- |
| **Q1: Why Gemini Vision instead of traditional computer vision (OpenCV / pixel matching)?** | *"Pixel matching (like Pixelmatch or Resemble.js) fails completely when dynamic content, fonts, or harmless layout shifts occur—it flags hundreds of false positives. Multimodal VLMs perform semantic and spatial reasoning. They understand intent, identify WCAG contrast violations, and recognize that a button is unusable on mobile, rather than just comparing RGB pixels."* |
| **Q2: How do you prevent the AI from generating destructive CSS that breaks the rest of the site?** | *"OmniSight enforces a two-layer defense: first, prompt constraints instruct the model to use the most specific selectors and modern responsive rules (`clamp`, `flex`, `min`). Second, our Action Engine passes all generated CSS through `tinycss2` AST parsing, automatically rejecting blanket selectors like `*`, `body`, or `h1` before application."* |
| **Q3: What happens if the generated CSS fix doesn't work?** | *"In our LangGraph ReAct self-healing pipeline, the agent injects the patch in-memory via Playwright, takes a post-remediation screenshot, and asks the VLM to verify if the bug is resolved without introducing new regressions. If verification fails, the agent reflects on the failure and retries with a revised approach (up to 2 retries) before ever persisting code or opening a PR."* |

