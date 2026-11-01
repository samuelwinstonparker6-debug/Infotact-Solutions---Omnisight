"""
OmniSight — Agent Orchestrator (Full Self-Healing Pipeline)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

LangChain-based orchestrator implementing the complete ReAct
(Reasoning + Acting) self-healing loop:

  1. Capture multi-viewport screenshots via Playwright
  2. Run image chunking to focus on anomalous UI regions
  3. Send chunks + full screenshots to VLM for bug analysis
  4. Generate Tailwind CSS / surgical CSS fixes
  5. Inject CSS in-memory into Playwright's live DOM (no disk writes)
  6. Capture post-fix verification screenshot
  7. Ask VLM to verify: "Is the bug fixed without regressions?"
  8. If YES → persist fix and create GitHub PR
  9. If NO → iterate with revised hypothesis (max 2 retries)
"""

import logging
import os
import subprocess
from pathlib import Path
from typing import Any

from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.prebuilt import create_react_agent

from backend.core.config import get_settings

logger = logging.getLogger(__name__)

# Maximum number of self-healing fix-verify cycles before escalating
MAX_HEAL_RETRIES = 2


# ─────────────────────────────────────────────────────────────────────────────
# LangChain Tools — callable by the ReAct agent
# ─────────────────────────────────────────────────────────────────────────────

@tool
async def capture_ui(url: str) -> dict:
    """Captures screenshots of the given UI URL across different viewports (desktop, tablet, mobile)."""
    from backend.services.browser.automation import capture_screenshots
    return await capture_screenshots(url=url, headless=True)


@tool
async def run_interactive_rpa_flow(url: str) -> dict:
    """Runs a multi-step interactive RPA flow on the target URL.
    Simulates real user actions: Add to Cart, Open Cart, Proceed to Checkout.
    Captures a screenshot at each state transition for VLM analysis."""
    from backend.services.browser.automation import run_interactive_flow
    return await run_interactive_flow(url=url, headless=True)


@tool
async def analyze_ui(image_path: str, url: str, viewport: str) -> dict:
    """Analyzes a UI screenshot for visual bugs using the Gemini VLM."""
    from backend.services.vlm.analyzer import analyze_screenshot
    return await analyze_screenshot(image_path=image_path, page_url=url, viewport=viewport)


@tool
async def chunk_and_analyze(image_path: str, url: str) -> dict:
    """Chunks a full-page screenshot into UI regions (header, content, footer)
    and analyzes each chunk individually for focused bug detection."""
    from backend.services.vlm.analyzer import chunk_screenshot_into_regions, analyze_screenshot
    chunks = chunk_screenshot_into_regions(image_path)
    all_bugs = []
    for chunk in chunks:
        result = await analyze_screenshot(
            image_path=chunk["path"],
            page_url=url,
            viewport=chunk["region"],
        )
        for bug in result.get("bugs", []):
            bug["chunk_region"] = chunk["region"]
            bug["chunk_bbox"] = chunk["bbox"]
            all_bugs.append(bug)
    return {"status": "success", "bugs": all_bugs, "chunks_analyzed": len(chunks)}


@tool
async def inject_css_and_verify(url: str, css_content: str, viewport: str) -> dict:
    """Injects CSS directly into the browser's live DOM (in-memory, no file writes),
    takes a verification screenshot, and returns the path for VLM re-inspection.
    This is the core of the self-healing loop: inject → screenshot → verify."""
    from backend.services.browser.automation import capture_with_injected_css
    output_path = f"./output/screenshots/verification_{viewport}.png"
    result_path = await capture_with_injected_css(
        url=url,
        css_content=css_content,
        viewport_name=viewport,
        output_path=output_path,
        headless=True,
    )
    return {
        "status": "success",
        "verification_screenshot": result_path,
        "css_injected": css_content[:200] + "..." if len(css_content) > 200 else css_content,
        "message": "CSS injected into live DOM. Use analyze_ui on the verification screenshot to check if the bug is fixed."
    }


@tool
async def apply_fix(file_path: str, fix_content: str) -> str:
    """Applies a verified fix to a local file on disk.
    Only call this AFTER the fix has been verified via inject_css_and_verify."""
    full_path = os.path.join(os.getcwd(), file_path)
    try:
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(fix_content)
        return f"Successfully persisted verified fix to {file_path}."
    except Exception as e:
        return f"Error applying fix: {e}"


@tool
async def create_github_pr(file_path: str, bug_description: str, fix_content: str) -> str:
    """Creates a pull request on GitHub for the verified fix.
    Only call AFTER the fix has passed visual verification."""
    from backend.services.github.pr_creator import create_fix_pr
    result = await create_fix_pr(file_path, fix_content, bug_description)
    return str(result)


@tool
async def sync_and_restart(repo_path: str = ".") -> str:
    """Pull latest changes from git and restart backend and frontend servers.
    Returns a summary string of actions performed."""
    try:
        cwd = os.path.abspath(repo_path)
        pull_result = subprocess.run("git pull", cwd=cwd, shell=True, capture_output=True, text=True)
        output = f"Git pull output:\n{pull_result.stdout}\n"
        if os.name == "nt":
            subprocess.run("taskkill /IM python.exe /F", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run("taskkill /IM node.exe /F", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            subprocess.run("pkill -f uvicorn", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.run("pkill -f npm", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        output += "Terminated existing backend/frontend processes.\n"
        subprocess.Popen("python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000", cwd=cwd, shell=True)
        frontend_dir = os.path.join(cwd, "frontend")
        subprocess.Popen("npm run dev", cwd=frontend_dir, shell=True)
        output += "Started new backend and frontend servers."
        return output
    except Exception as e:
        return f"Error during sync and restart: {e}"


# ─────────────────────────────────────────────────────────────────────────────
# Self-Healing Pipeline Orchestrator
# ─────────────────────────────────────────────────────────────────────────────

async def run_pipeline(
    target_url: str,
    auto_fix: bool = False,
    create_pr: bool = False,
) -> dict[str, Any]:
    """
    Execute the full OmniSight self-healing pipeline using a LangChain
    ReAct agent with the complete Plan → Execute → Verify loop.

    The agent autonomously:
    1. Captures multi-viewport screenshots + runs interactive RPA flow
    2. Chunks screenshots into UI regions for focused analysis
    3. Sends chunks to VLM to detect visual bugs
    4. Generates Tailwind CSS / surgical CSS fixes
    5. Injects CSS into live DOM via Playwright (in-memory)
    6. Takes post-fix verification screenshot
    7. Re-runs VLM to verify the fix worked
    8. If fix passes → persists to disk + opens GitHub PR
    9. If fix fails → iterates up to 2 times with a revised approach
    """
    logger.info("🤖 Pipeline execution requested for: %s", target_url)

    settings = get_settings()

    if not settings.gemini_api_key:
        logger.warning("Gemini API key is missing. Attempting to proceed with fallback mock responses.")

    llm = ChatGoogleGenerativeAI(
        model=settings.gemini_model or "gemini-3.5-flash-lite",
        google_api_key=settings.gemini_api_key,
        temperature=0.0,
        max_output_tokens=8192,
    )

    tools = [
        capture_ui,
        run_interactive_rpa_flow,
        analyze_ui,
        chunk_and_analyze,
        inject_css_and_verify,
        apply_fix,
        create_github_pr,
    ]

    agent_executor = create_react_agent(llm, tools)

    command = f"Scan {target_url} for UI bugs using the full self-healing pipeline."
    command += "\n\nFOLLOW THIS EXACT PIPELINE (do NOT skip steps):"
    command += "\n1. CAPTURE: Use capture_ui to take screenshots across desktop, tablet, and mobile viewports."
    command += "\n2. RPA FLOW: Use run_interactive_rpa_flow to simulate user interactions (add to cart, checkout)."
    command += "\n3. CHUNK & ANALYZE: Use chunk_and_analyze on the desktop screenshot to split it into UI regions and detect bugs in each region individually."
    command += "\n4. ANALYZE VIEWPORTS: Use analyze_ui on tablet and mobile screenshots too."

    if auto_fix:
        command += "\n5. FIX: For each detected bug, generate a surgical Tailwind CSS fix (use utility classes like w-full, max-w-sm, z-50, text-white, etc.)."
        command += "\n6. VERIFY IN-MEMORY: Use inject_css_and_verify to inject the CSS into the live DOM without writing files. This takes a verification screenshot."
        command += "\n7. RE-INSPECT: Use analyze_ui on the verification screenshot to confirm the bug is fixed and no new regressions were introduced."
        command += f"\n8. RETRY: If the bug is NOT fixed, revise your CSS approach and repeat steps 6-7 (max {MAX_HEAL_RETRIES} retries). If still failing, skip this bug."
        command += "\n9. PERSIST: Only after visual verification passes, use apply_fix to write the fix to disk."

    if create_pr:
        command += "\n10. PR: After all verified fixes are persisted, use create_github_pr with a summary of all fixes and the combined CSS."

    if not settings.gemini_api_key:
        logger.warning("Mocking agent execution for pipeline — no API key.")
        from backend.services.browser.automation import capture_screenshots
        from backend.services.vlm.analyzer import analyze_screenshot

        res = await capture_screenshots(target_url, headless=True)
        if isinstance(res, tuple):
            screenshots, html = res
        else:
            screenshots = res
        if screenshots:
            image_path = list(screenshots.values())[0]
            await analyze_screenshot(image_path, target_url, "desktop")

        return {
            "status": "completed",
            "target_url": target_url,
            "agent_output": "Mock agent completed (no API key). Captured UI and ran heuristic analysis."
        }

    try:
        system_msg = (
            "You are OmniSight, an autonomous AI UI/UX QA agent powered by Gemini Vision. "
            "Your goal is to audit a live URL for visual regressions and produce surgical, verified CSS fixes.\n\n"

            "SELF-HEALING LOOP (MANDATORY):\n"
            "You MUST follow the Reason → Act → Verify cycle for every fix:\n"
            "  REASON: Analyze the bug from VLM output, understand root cause from CSS/HTML.\n"
            "  ACT: Generate a Tailwind CSS fix (utility classes preferred: w-full, max-w-sm, z-50, text-slate-100, etc.).\n"
            "  VERIFY: Inject CSS into the live DOM using inject_css_and_verify. Take a new screenshot.\n"
            "  CHECK: Re-run analyze_ui on the verification screenshot.\n"
            f"  RETRY: If the bug persists, revise your approach and retry (max {MAX_HEAL_RETRIES} attempts).\n"
            "  PERSIST: Only write to disk (apply_fix) and create PR AFTER visual verification passes.\n\n"

            "TAILWIND CSS GENERATION RULES:\n"
            "- Generate Tailwind CSS utility classes whenever possible (e.g., w-full, max-w-screen-sm, text-white, bg-indigo-600, z-50, flex-wrap).\n"
            "- For complex fixes, output standard CSS but use modern responsive patterns: clamp(), min(), flexbox, grid.\n"
            "- NEVER use blanket selectors (*, body, html, h1, h2, p, div, button, a).\n"
            "- Each fix: max 2-3 CSS properties targeting the most specific selector.\n"
            "- Preserve existing design intent: dark themes, gradients, and intentional styling.\n\n"

            "IMAGE CHUNKING:\n"
            "- Use chunk_and_analyze for the primary (desktop) screenshot to split it into header/content/footer regions.\n"
            "- This gives you higher resolution per-component analysis and better bug localization.\n\n"

            "INTERACTIVE RPA TESTING:\n"
            "- Use run_interactive_rpa_flow to simulate real user journeys through the application.\n"
            "- This tests add-to-cart, cart opening, and checkout flows for state-dependent bugs.\n"
        )

        result = await agent_executor.ainvoke({"messages": [("system", system_msg), ("user", command)]})

        if create_pr:
            sync_msg = await sync_and_restart(repo_path=".")
            logger.info("Sync and restart output: %s", sync_msg)

        return {
            "status": "completed",
            "target_url": target_url,
            "agent_output": result["messages"][-1].content
        }
    except Exception as e:
        logger.error(f"Agent execution failed: {e}")
        return {
            "status": "error",
            "target_url": target_url,
            "message": str(e)
        }
