"""
OmniSight — Browser Automation Module (Full RPA)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Handles Playwright browser lifecycle, multi-step interactive flow
simulation (navigation, add-to-cart, checkout), and screenshot capture
across configurable viewports (desktop, tablet, mobile).

Implements:
  - Static page screenshot capture across viewports
  - Interactive RPA flow: click through a checkout journey and
    capture screenshots at each state transition
  - In-memory CSS injection for self-healing verification loop
"""

import logging
import asyncio
from pathlib import Path
from urllib.parse import urlparse
from typing import Optional, Tuple

from playwright.async_api import async_playwright, Page, BrowserContext

logger = logging.getLogger(__name__)

# Standard viewport configurations for responsive testing
VIEWPORTS = {
    "desktop": {"width": 1920, "height": 1080},
    "tablet":  {"width": 768,  "height": 1024},
    "mobile":  {"width": 375,  "height": 812},
}


def _get_safe_filename(url: str, viewport_name: str, suffix: str = "") -> str:
    """Generate a safe filename from a URL and viewport."""
    parsed = urlparse(url)
    domain = parsed.netloc.replace(":", "_") or "localhost"
    path = parsed.path.strip("/").replace("/", "_") or "index"
    tag = f"_{suffix}" if suffix else ""
    return f"{domain}_{path}_{viewport_name}{tag}.png"


# ─────────────────────────────────────────────────────────────────────────────
# 1. Static multi-viewport screenshot capture
# ─────────────────────────────────────────────────────────────────────────────

async def capture_screenshots(
    url: str,
    output_dir: str = "./output/screenshots",
    viewports: Optional[dict[str, dict[str, int]]] = None,
    headless: bool = True,
) -> Tuple[dict[str, str], str]:
    """
    Capture full-page screenshots at multiple viewport sizes.

    Returns:
        Tuple containing:
        - Dict mapping viewport name to absolute screenshot file path.
        - String containing the scraped HTML content.
    """
    logger.info("📸 Screenshot capture requested for: %s", url)

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    target_viewports = viewports or VIEWPORTS
    results = {}
    html_content = ""

    async def capture_single_viewport(browser, viewport_name, dimensions):
        nonlocal html_content
        logger.info(f"  → Capturing {viewport_name} viewport ({dimensions['width']}×{dimensions['height']})...")
        context = await browser.new_context(
            viewport=dimensions,
            device_scale_factor=1,
        )
        page = await context.new_page()
        try:
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=15000)
                try:
                    await page.wait_for_load_state("load", timeout=4000)
                except Exception:
                    pass
                try:
                    await page.evaluate("() => Promise.race([document.fonts.ready, new Promise(r => setTimeout(r, 1500))])")
                except Exception:
                    pass
            except Exception as nav_err:
                logger.warning(f"Navigation warning for {viewport_name}: {nav_err}")

            await asyncio.sleep(0.5)

            filename = _get_safe_filename(url, viewport_name)
            filepath = out_dir / filename

            try:
                await page.screenshot(
                    path=str(filepath),
                    full_page=False,
                    timeout=12000,
                    type="png",
                    animations="disabled"
                )
            except Exception as ss_err:
                logger.warning(f"Screenshot with disabled animations failed for {viewport_name}: {ss_err}, retrying standard capture")
                try:
                    await page.screenshot(
                        path=str(filepath),
                        full_page=False,
                        timeout=8000,
                        type="png"
                    )
                except Exception as retry_err:
                    logger.error(f"Screenshot completely failed for {viewport_name}: {retry_err}")
                    return None

            if not html_content:
                try:
                    html_content = await page.content()
                except Exception:
                    html_content = ""

            logger.info(f"  ✓ Saved to {filepath}")
            return (viewport_name, str(filepath.absolute()))
        except Exception as e:
            logger.error(f"Failed to capture {viewport_name}: {e}")
            return None
        finally:
            await context.close()

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=headless,
            args=["--disable-gpu", "--disable-dev-shm-usage", "--no-sandbox", "--disable-extensions"]
        )
        try:
            tasks = [
                capture_single_viewport(browser, vp_name, dims)
                for vp_name, dims in target_viewports.items()
            ]
            captured = await asyncio.gather(*tasks)
            for item in captured:
                if item:
                    results[item[0]] = item[1]
        finally:
            await browser.close()

    return results, html_content


# ─────────────────────────────────────────────────────────────────────────────
# 2. Interactive RPA Flow — Multi-step checkout simulation
# ─────────────────────────────────────────────────────────────────────────────

# Common selectors for interactive elements in typical e-commerce apps
INTERACTIVE_SELECTORS = {
    "add_to_cart": [
        "button.add-to-cart",
        "button[data-action='add-to-cart']",
        ".add-to-cart-btn",
        "button:has-text('Add to Cart')",
    ],
    "cart_icon": [
        ".cart-icon",
        "[data-testid='cart']",
        ".shopping-cart",
        "a[href*='cart']",
    ],
    "checkout_button": [
        "button.checkout-button",
        ".checkout-btn",
        "button:has-text('Checkout')",
        "button:has-text('Proceed')",
    ],
}


async def _try_click(page: Page, selectors: list[str], timeout: int = 3000) -> bool:
    """Attempt to click the first visible element matching any of the selectors."""
    for selector in selectors:
        try:
            locator = page.locator(selector).first
            if await locator.is_visible(timeout=timeout):
                await locator.click(timeout=timeout)
                await asyncio.sleep(0.5)  # Wait for UI state transition
                return True
        except Exception:
            continue
    return False


async def run_interactive_flow(
    url: str,
    output_dir: str = "./output/screenshots",
    viewport_name: str = "desktop",
    headless: bool = True,
) -> dict:
    """
    Execute a multi-step interactive RPA flow on the target URL:
      State 1: Initial page load (homepage)
      State 2: Click "Add to Cart" on the first product
      State 3: Open shopping cart drawer / view cart
      State 4: Click "Proceed to Checkout" button

    At each state, a screenshot is captured for VLM analysis.

    Returns:
        {
            "status": "success"|"partial"|"error",
            "states": {
                "state_1_initial": "/path/to/screenshot.png",
                "state_2_add_to_cart": "/path/to/screenshot.png",
                "state_3_cart_view": "/path/to/screenshot.png",
                "state_4_checkout": "/path/to/screenshot.png",
            },
            "html_content": "...",
            "flow_log": ["Step 1: ...", "Step 2: ...", ...]
        }
    """
    logger.info("🤖 Starting interactive RPA flow on: %s (viewport: %s)", url, viewport_name)

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    dimensions = VIEWPORTS.get(viewport_name, VIEWPORTS["desktop"])
    states = {}
    flow_log = []
    html_content = ""

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=headless,
            args=["--disable-gpu", "--disable-dev-shm-usage", "--no-sandbox"]
        )
        try:
            context = await browser.new_context(
                viewport=dimensions,
                device_scale_factor=1,
            )
            page = await context.new_page()

            # ── State 1: Initial page load ────────────────────────────
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=15000)
                try:
                    await page.wait_for_load_state("load", timeout=5000)
                except Exception:
                    pass
            except Exception as e:
                logger.error(f"Failed to navigate to {url}: {e}")
                return {"status": "error", "states": {}, "html_content": "", "flow_log": [f"Navigation failed: {e}"]}

            await asyncio.sleep(0.8)

            # Capture HTML content
            try:
                html_content = await page.content()
            except Exception:
                html_content = ""

            state1_path = out_dir / _get_safe_filename(url, viewport_name, "state1_initial")
            await page.screenshot(path=str(state1_path), full_page=False, type="png")
            states["state_1_initial"] = str(state1_path.absolute())
            flow_log.append("State 1: Captured initial page load screenshot")
            logger.info("  ✓ State 1: Initial page captured")

            # ── State 2: Click "Add to Cart" ──────────────────────────
            clicked_cart = await _try_click(page, INTERACTIVE_SELECTORS["add_to_cart"])
            if clicked_cart:
                await asyncio.sleep(0.6)
                state2_path = out_dir / _get_safe_filename(url, viewport_name, "state2_add_to_cart")
                await page.screenshot(path=str(state2_path), full_page=False, type="png")
                states["state_2_add_to_cart"] = str(state2_path.absolute())
                flow_log.append("State 2: Clicked 'Add to Cart' — captured post-interaction screenshot")
                logger.info("  ✓ State 2: Add to Cart clicked and captured")
            else:
                flow_log.append("State 2: No 'Add to Cart' button found — skipped")
                logger.warning("  ⚠ State 2: Could not find Add to Cart button")

            # ── State 3: Open cart / click cart icon ──────────────────
            clicked_icon = await _try_click(page, INTERACTIVE_SELECTORS["cart_icon"])
            if clicked_icon:
                await asyncio.sleep(0.6)
                state3_path = out_dir / _get_safe_filename(url, viewport_name, "state3_cart_view")
                await page.screenshot(path=str(state3_path), full_page=False, type="png")
                states["state_3_cart_view"] = str(state3_path.absolute())
                flow_log.append("State 3: Opened cart drawer — captured cart view screenshot")
                logger.info("  ✓ State 3: Cart view captured")
            else:
                flow_log.append("State 3: No cart icon found — skipped")
                logger.warning("  ⚠ State 3: Could not find cart icon")

            # ── State 4: Click "Proceed to Checkout" ──────────────────
            clicked_checkout = await _try_click(page, INTERACTIVE_SELECTORS["checkout_button"])
            if clicked_checkout:
                await asyncio.sleep(0.6)
                state4_path = out_dir / _get_safe_filename(url, viewport_name, "state4_checkout")
                await page.screenshot(path=str(state4_path), full_page=False, type="png")
                states["state_4_checkout"] = str(state4_path.absolute())
                flow_log.append("State 4: Clicked 'Proceed to Checkout' — captured checkout screenshot")
                logger.info("  ✓ State 4: Checkout captured")
            else:
                flow_log.append("State 4: No checkout button found — skipped")
                logger.warning("  ⚠ State 4: Could not find checkout button")

            await context.close()

        finally:
            await browser.close()

    status = "success" if len(states) >= 3 else ("partial" if states else "error")
    logger.info("🏁 RPA flow complete — captured %d/%d states (status: %s)", len(states), 4, status)

    return {
        "status": status,
        "states": states,
        "html_content": html_content,
        "flow_log": flow_log,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 3. In-memory CSS injection & verification screenshot
# ─────────────────────────────────────────────────────────────────────────────

async def capture_with_injected_css(
    url: str,
    css_content: str,
    viewport_name: str,
    output_path: str,
    headless: bool = True,
) -> str:
    """
    Launch Playwright at the specified viewport, navigate to url,
    inject the candidate CSS dynamically into the live DOM (in-memory,
    no file writes), wait for layout reflow, and capture the screenshot.

    This is the core of the self-healing verification loop:
    the VLM proposes a CSS fix → we inject it in-memory → screenshot →
    VLM verifies the fix visually → if it passes, we persist to disk/PR.
    """
    logger.info("📸 In-memory DOM injection + verification screenshot for: %s", url)

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        try:
            dimensions = VIEWPORTS.get(viewport_name, VIEWPORTS["desktop"])
            context = await browser.new_context(
                viewport=dimensions,
                device_scale_factor=1,
            )
            page = await context.new_page()

            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=20000)
            except Exception:
                await page.goto(url, wait_until="load", timeout=25000)

            # ── Inject CSS directly into live DOM (in-memory, no disk writes) ──
            await page.add_style_tag(content=css_content)
            logger.info("  → Injected %d bytes of CSS into live DOM", len(css_content))

            # Wait for layout reflow and font rendering
            await asyncio.sleep(0.8)

            # Ensure directory exists
            out_path = Path(output_path)
            out_path.parent.mkdir(parents=True, exist_ok=True)

            # Capture screenshot with fallback
            try:
                await page.screenshot(
                    path=str(out_path.absolute()),
                    full_page=True,
                    timeout=15000,
                    type="png"
                )
            except Exception as ss_err:
                logger.warning(f"Full-page screenshot timed out, capturing viewport: {ss_err}")
                await page.screenshot(
                    path=str(out_path.absolute()),
                    full_page=False,
                    timeout=10000,
                    type="png"
                )
            logger.info(f"  ✓ Saved verification screenshot to {out_path.absolute()}")

        except Exception as e:
            logger.error(f"Failed to capture verification screenshot: {e}")
        finally:
            await browser.close()

    return output_path
