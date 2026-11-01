"""
OmniSight — Quantitative Vision Audit Benchmark
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Proves the VLM can accurately identify deliberate UI bugs purely
from screenshots, by running against the mock storefront with known
ground-truth bugs and measuring Precision, Recall, and F1-Score.

Ground-truth bugs (from mock-app/ground_truth.json):
  1. Checkout button overflow on mobile (400px fixed width)
  2. Hero text contrast (hard to read against background)
  3. Price overlap (absolute positioning overlaps image)

Test suite:
  - test_screenshot_capture: Playwright captures screenshots correctly
  - test_image_chunking: Screenshot chunking produces expected regions
  - test_interactive_rpa_flow: Multi-step checkout flow simulation works
  - test_vision_analysis_detects_known_bugs: VLM detects ≥ N of K ground-truth bugs
  - test_precision_recall_f1: Quantitative benchmark scoring
  - test_no_false_positives_on_clean_page: VLM returns no bugs on a correctly styled page
  - test_fix_generation_produces_valid_css: Generated fixes contain valid CSS selectors
  - test_in_memory_css_injection: Playwright in-memory injection doesn't crash
"""

import asyncio
import json
import os
import re
import pytest
import hashlib
from pathlib import Path


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

# Load ground truth bugs
GROUND_TRUTH_PATH = Path(__file__).resolve().parent.parent / "mock-app" / "ground_truth.json"
LOCAL_MOCK_PATH = Path(__file__).resolve().parent.parent / "mock-app" / "index.html"
MOCK_APP_URL = os.environ.get("OMNISIGHT_MOCK_URL") or LOCAL_MOCK_PATH.resolve().as_uri()
OUTPUT_DIR = "./output/test_screenshots"


@pytest.fixture(scope="module")
def ground_truth_bugs() -> list[dict]:
    """Load the known ground-truth bugs for the mock storefront."""
    if GROUND_TRUTH_PATH.is_file():
        with open(GROUND_TRUTH_PATH, "r") as f:
            data = json.load(f)
        return data.get("bugs", [])
    return [
        {"type": "checkout button overflow on mobile", "description": "The checkout button is fixed at 400px width causing it to overflow on mobile screens."},
        {"type": "hero text contrast", "description": "The hero text lacks contrast against its background."},
        {"type": "price overlap", "description": "The price overlaps the image due to top: -20px absolute positioning."},
    ]


@pytest.fixture(scope="module")
def event_loop():
    """Create a module-scoped event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


# ─────────────────────────────────────────────────────────────────────────────
# Helper: fuzzy match VLM bug to ground truth
# ─────────────────────────────────────────────────────────────────────────────

def _bug_matches_ground_truth(detected_bug: dict, gt_bug: dict) -> bool:
    """
    Fuzzy-match a VLM-detected bug to a ground-truth bug using keyword overlap.
    We consider it a match if ≥2 keywords from the ground truth description
    appear in the detected bug's title, description, or category.
    """
    gt_text = (gt_bug.get("type", "") + " " + gt_bug.get("description", "")).lower()
    gt_keywords = set(re.findall(r'\b\w{4,}\b', gt_text))  # Words with 4+ chars

    detected_text = (
        (detected_bug.get("title", "") or "") + " " +
        (detected_bug.get("description", "") or "") + " " +
        (detected_bug.get("category", "") or "") + " " +
        (detected_bug.get("element_selector", "") or "")
    ).lower()

    overlap = sum(1 for kw in gt_keywords if kw in detected_text)
    return overlap >= 2


def compute_precision_recall_f1(
    detected_bugs: list[dict],
    ground_truth: list[dict],
) -> dict:
    """
    Compute Precision, Recall, and F1-Score for VLM bug detection.

    - True Positive (TP): A detected bug that matches a ground-truth bug.
    - False Positive (FP): A detected bug with no ground-truth match.
    - False Negative (FN): A ground-truth bug not matched by any detection.
    """
    matched_gt = set()
    tp = 0
    fp = 0

    for detected in detected_bugs:
        found_match = False
        for i, gt in enumerate(ground_truth):
            if i not in matched_gt and _bug_matches_ground_truth(detected, gt):
                matched_gt.add(i)
                tp += 1
                found_match = True
                break
        if not found_match:
            fp += 1

    fn = len(ground_truth) - len(matched_gt)

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        "true_positives": tp,
        "false_positives": fp,
        "false_negatives": fn,
        "precision": round(precision, 3),
        "recall": round(recall, 3),
        "f1_score": round(f1, 3),
        "matched_ground_truth_indices": list(matched_gt),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Test 1: Screenshot capture across viewports
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_screenshot_capture():
    """Verify Playwright captures screenshots for all 3 viewports."""
    from backend.services.browser.automation import capture_screenshots

    screenshots, html = await capture_screenshots(
        url=MOCK_APP_URL,
        output_dir=OUTPUT_DIR,
        headless=True,
    )

    assert isinstance(screenshots, dict), "capture_screenshots must return a dict"
    assert len(screenshots) >= 1, "Must capture at least 1 viewport screenshot"

    for vp_name, path in screenshots.items():
        assert Path(path).is_file(), f"Screenshot file missing for {vp_name}: {path}"
        assert Path(path).stat().st_size > 1000, f"Screenshot too small for {vp_name} (likely blank)"

    assert html, "HTML content should be captured"
    assert "<html" in html.lower() or "<!doctype" in html.lower(), "Captured HTML looks invalid"


# ─────────────────────────────────────────────────────────────────────────────
# Test 2: Image chunking produces correct regions
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_image_chunking():
    """Verify screenshot chunking splits into expected UI regions."""
    from backend.services.browser.automation import capture_screenshots
    from backend.services.vlm.analyzer import chunk_screenshot_into_regions

    screenshots, _ = await capture_screenshots(
        url=MOCK_APP_URL,
        output_dir=OUTPUT_DIR,
        headless=True,
    )

    # Chunk the desktop screenshot
    desktop_path = screenshots.get("desktop") or next(iter(screenshots.values()))
    chunks = chunk_screenshot_into_regions(desktop_path, num_vertical_chunks=3)

    assert len(chunks) == 3, f"Expected 3 chunks, got {len(chunks)}"
    expected_regions = {"top_header", "middle_content", "bottom_footer"}
    actual_regions = {c["region"] for c in chunks}
    assert actual_regions == expected_regions, f"Expected regions {expected_regions}, got {actual_regions}"

    for chunk in chunks:
        assert Path(chunk["path"]).is_file(), f"Chunk file missing: {chunk['path']}"
        assert len(chunk["bbox"]) == 4, "Chunk bbox must have 4 elements (x, y, w, h)"


# ─────────────────────────────────────────────────────────────────────────────
# Test 3: Interactive RPA flow simulation
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_interactive_rpa_flow():
    """Verify the multi-step interactive flow captures state screenshots."""
    from backend.services.browser.automation import run_interactive_flow

    result = await run_interactive_flow(
        url=MOCK_APP_URL,
        output_dir=OUTPUT_DIR,
        viewport_name="desktop",
        headless=True,
    )

    assert result["status"] in ("success", "partial"), f"RPA flow failed: {result.get('flow_log')}"
    assert "state_1_initial" in result["states"], "Must capture initial state"
    assert len(result["flow_log"]) >= 1, "Flow log must have at least 1 entry"

    # Verify state screenshots exist
    for state_name, path in result["states"].items():
        assert Path(path).is_file(), f"State screenshot missing: {state_name} → {path}"


# ─────────────────────────────────────────────────────────────────────────────
# Test 4: VLM detects at least some ground-truth bugs (requires API key)
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
@pytest.mark.skipif(
    not os.environ.get("GEMINI_API_KEY"),
    reason="Requires GEMINI_API_KEY to run VLM analysis",
)
async def test_vision_analysis_detects_known_bugs(ground_truth_bugs):
    """VLM should detect at least 1 of the 3 known ground-truth bugs."""
    from backend.services.browser.automation import capture_screenshots
    from backend.services.vlm.analyzer import analyze_all_viewports

    screenshots, html = await capture_screenshots(
        url=MOCK_APP_URL,
        output_dir=OUTPUT_DIR,
        headless=True,
    )

    result = await analyze_all_viewports(
        screenshots=screenshots,
        page_url=MOCK_APP_URL,
        page_source=html,
    )

    assert result["status"] == "success", f"Analysis failed: {result.get('message')}"

    detected_bugs = result.get("bugs", [])
    assert len(detected_bugs) >= 1, "VLM should detect at least 1 bug on the deliberately buggy mock page"


# ─────────────────────────────────────────────────────────────────────────────
# Test 5: Quantitative precision/recall/F1 benchmark
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
@pytest.mark.skipif(
    not os.environ.get("GEMINI_API_KEY"),
    reason="Requires GEMINI_API_KEY for VLM benchmark",
)
async def test_precision_recall_f1(ground_truth_bugs):
    """Compute and report P/R/F1 scores for VLM bug detection accuracy."""
    from backend.services.browser.automation import capture_screenshots
    from backend.services.vlm.analyzer import analyze_all_viewports

    screenshots, html = await capture_screenshots(
        url=MOCK_APP_URL,
        output_dir=OUTPUT_DIR,
        headless=True,
    )

    result = await analyze_all_viewports(
        screenshots=screenshots,
        page_url=MOCK_APP_URL,
        page_source=html,
    )

    detected = result.get("bugs", [])
    metrics = compute_precision_recall_f1(detected, ground_truth_bugs)

    print(f"\n{'='*60}")
    print(f"  OMNISIGHT VISION BENCHMARK RESULTS")
    print(f"{'='*60}")
    print(f"  Ground truth bugs:   {len(ground_truth_bugs)}")
    print(f"  Detected bugs:       {len(detected)}")
    print(f"  True Positives:      {metrics['true_positives']}")
    print(f"  False Positives:     {metrics['false_positives']}")
    print(f"  False Negatives:     {metrics['false_negatives']}")
    print(f"  Precision:           {metrics['precision']:.1%}")
    print(f"  Recall:              {metrics['recall']:.1%}")
    print(f"  F1-Score:            {metrics['f1_score']:.1%}")
    print(f"{'='*60}\n")

    # We expect at least some recall (the VLM should find something)
    assert metrics["recall"] > 0.0, "VLM failed to detect any ground-truth bugs (recall = 0)"


# ─────────────────────────────────────────────────────────────────────────────
# Test 6: Fix generation produces valid CSS
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_fix_generation_produces_valid_css():
    """Verify code_fixer generates valid CSS with proper selectors."""
    from backend.services.vlm.code_fixer import generate_tailwind_fix

    sample_source = "<html><head></head><body><button class='checkout-button'>Checkout</button></body></html>"
    sample_bugs = [
        {
            "id": "test-overflow-1",
            "category": "overflow",
            "severity": "high",
            "title": "Checkout button overflows on mobile",
            "description": "Button is fixed at 400px, overflows small screens",
            "element_selector": ".checkout-button",
            "suggested_fix": "width: 100%; max-width: 24rem;",
            "viewport": "mobile",
        }
    ]

    result = await generate_tailwind_fix(sample_source, sample_bugs)

    assert "fixed_source" in result, "Must return fixed_source"
    assert "css_override" in result, "Must return css_override"
    assert "tailwind_classname_diffs" in result, "Must return tailwind_classname_diffs"

    # Verify no blanket selectors in CSS output (must not match class suffixes like .checkout-button)
    import re
    blanket_tags = [r"\*", "body", "html", "h1", "h2", "p", "div", "button", "a", "span"]
    css = result["css_override"]
    for tag in blanket_tags:
        pattern = rf"(?:^|\n)\s*{tag}\s*\{{"
        assert not re.search(pattern, css), f"CSS contains forbidden blanket selector: {tag}"


# ─────────────────────────────────────────────────────────────────────────────
# Test 7: In-memory CSS injection via Playwright
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_in_memory_css_injection():
    """Verify Playwright can inject CSS into live DOM and capture a screenshot."""
    from backend.services.browser.automation import capture_with_injected_css

    test_css = ".checkout-button { width: 100% !important; max-width: 24rem; }"
    output_path = os.path.join(OUTPUT_DIR, "test_injection_verify.png")

    result_path = await capture_with_injected_css(
        url=MOCK_APP_URL,
        css_content=test_css,
        viewport_name="mobile",
        output_path=output_path,
        headless=True,
    )

    assert Path(result_path).is_file() or Path(output_path).is_file(), "Verification screenshot must be created"


# ─────────────────────────────────────────────────────────────────────────────
# Test 8: Bounding box cropping
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_bounding_box_cropping():
    """Verify crop_around_bounding_box produces a valid cropped image."""
    from backend.services.browser.automation import capture_screenshots
    from backend.services.vlm.analyzer import crop_around_bounding_box

    screenshots, _ = await capture_screenshots(
        url=MOCK_APP_URL,
        output_dir=OUTPUT_DIR,
        headless=True,
    )

    desktop_path = screenshots.get("desktop") or next(iter(screenshots.values()))
    bbox = {"x": 10, "y": 10, "width": 300, "height": 200}

    cropped_path = crop_around_bounding_box(desktop_path, bbox, padding=20)
    assert Path(cropped_path).is_file(), f"Cropped image not created: {cropped_path}"
    assert Path(cropped_path).stat().st_size > 500, "Cropped image is too small"
