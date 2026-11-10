"""
OmniSight — Tailwind CSS Code Fixer (Autonomous VLM Engineer)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Acts as an autonomous frontend engineer specializing in Tailwind CSS.
Takes detected bugs and generates:
  - Exact Tailwind utility classes (e.g., w-full, max-w-sm, z-50, text-white)
  - JSX/HTML className diff replacements
  - Fallback surgical vanilla CSS when Tailwind classes alone are insufficient

The VLM is prompted to act as a Principal Frontend Engineer who:
  1. Diagnoses root cause from CSS/HTML source
  2. Proposes the minimal Tailwind utility class change
  3. Outputs both the Tailwind className diff AND equivalent raw CSS override
"""

import os
import logging
import asyncio
from backend.core.config import get_settings
from langchain_google_genai import ChatGoogleGenerativeAI

logger = logging.getLogger(__name__)


def validate_and_sanitize_css_ast(raw_css: str) -> str:
    """
    Parses synthesized CSS into an Abstract Syntax Tree (AST) using tinycss2.
    Validates rules, filters out destructive blanket tag selectors (*, body, html, etc.),
    and serializes the validated AST back to clean CSS.
    """
    if not raw_css or not raw_css.strip():
        return ""
    try:
        import tinycss2
        rules = tinycss2.parse_stylesheet(raw_css, skip_whitespace=True, skip_comments=True)
        sanitized_rules = []
        # Prevent global regressions by blocking generic element-level rules
        forbidden_tags = {"*", "body", "html", "p", "span", "div", "a", "button", "input", "select", "h1", "h2", "h3"}

        for rule in rules:
            if isinstance(rule, tinycss2.ast.QualifiedRule):
                selector = tinycss2.serialize(rule.prelude).strip()
                if selector in forbidden_tags:
                    logger.warning(f"AST filter dropped forbidden blanket selector: {selector}")
                    continue
                content = tinycss2.serialize(rule.content).strip()
                if content:
                    sanitized_rules.append(f"{selector} {{\n  {content}\n}}")
            elif isinstance(rule, tinycss2.ast.AtRule):
                prelude = tinycss2.serialize(rule.prelude).strip()
                content = tinycss2.serialize(rule.content).strip() if rule.content else ""
                sanitized_rules.append(f"@{rule.lower_at_keyword} {prelude} {{\n  {content}\n}}")

        if sanitized_rules:
            return "\n\n".join(sanitized_rules)
    except Exception as e:
        logger.warning(f"AST parsing fallback: {e}")

    return raw_css


async def generate_tailwind_fix(source_code: str, bugs: list[dict]) -> dict:
    """
    Takes the original source HTML and the list of detected bugs,
    and asks the VLM to generate BOTH Tailwind utility class fixes
    AND equivalent surgical CSS overrides.

    Returns:
        {
            "tailwind_classname_diffs": [...],
            "css_override": "<style>...</style>",
            "fixed_source": "full HTML with injected style tag",
        }
    """
    settings = get_settings()

    if not bugs:
        return {
            "tailwind_classname_diffs": [],
            "css_override": "",
            "fixed_source": source_code,
        }

    # ── Build bug descriptions for the LLM ────────────────────────────────
    bugs_text = "\n".join([
        f"  {i+1}. Selector: `{b.get('element_selector', 'unknown')}` | "
        f"Issue: {b.get('title', '')} — {b.get('description', '')} | "
        f"Severity: {b.get('severity', 'medium')} | "
        f"Viewport: {b.get('viewport', 'all')}"
        for i, b in enumerate(bugs[:8])
    ])

    # ── Tailwind CSS generation prompt ────────────────────────────────────
    tailwind_prompt = f"""You are a Principal Frontend Engineer specializing in Tailwind CSS and responsive web design.

DETECTED UI BUGS:
{bugs_text}

YOUR TASK: Generate BOTH outputs for each bug:

OUTPUT 1 — TAILWIND UTILITY CLASS DIFFS:
For each bug, specify the exact HTML element selector and the Tailwind classes to add/remove.
Format as a JSON array:
[
  {{
    "selector": ".checkout-button",
    "remove_classes": ["w-[400px]"],
    "add_classes": ["w-full", "max-w-sm", "mx-auto"],
    "explanation": "Fixed checkout button overflow on mobile by replacing fixed width with responsive utilities"
  }}
]

OUTPUT 2 — EQUIVALENT CSS OVERRIDE:
For cases where Tailwind classes cannot be directly applied (e.g., the site doesn't use Tailwind),
generate a surgical CSS override block. Rules:
- Use the MOST SPECIFIC selector possible (e.g., `.hero-banner .hero-text`, NOT `h1`)
- Maximum 2-3 CSS properties per selector
- NEVER use blanket selectors: *, body, html, h1, h2, p, div, button, a, span
- Use modern responsive CSS: clamp(), min(), max(), flex-wrap, z-index
- Preserve existing design intent (dark themes, gradients are intentional)

Output ONLY raw CSS rules (no markdown fences, no HTML tags, no explanation text).

RESPOND WITH THIS EXACT FORMAT:
---TAILWIND---
[...json array...]
---CSS---
...raw css rules...
---END---
"""

    tailwind_diffs = []
    css_override = ""

    # ── Call Gemini for intelligent Tailwind + CSS generation ──────────────
    if settings.gemini_api_key and bugs:
        try:
            llm = ChatGoogleGenerativeAI(
                model=settings.gemini_model or "gemini-3.5-flash",
                google_api_key=settings.gemini_api_key,
                temperature=0.1,
                request_timeout=20.0,
            )

            async with asyncio.timeout(20.0):
                response = await llm.ainvoke(tailwind_prompt)
                ai_response = response.content
                if isinstance(ai_response, list):
                    ai_response = "".join(
                        item if isinstance(item, str) else (item.get("text", "") if isinstance(item, dict) else str(item))
                        for item in ai_response
                    )
                elif not isinstance(ai_response, str):
                    ai_response = str(ai_response or "")

                ai_response = ai_response.strip()

                # Parse the structured response
                import json
                import re

                # Extract Tailwind diffs
                tw_match = re.search(r'---TAILWIND---\s*(.*?)\s*---CSS---', ai_response, re.DOTALL)
                if tw_match:
                    tw_text = tw_match.group(1).strip()
                    if tw_text.startswith("```"):
                        lines = tw_text.splitlines()
                        tw_text = "\n".join(lines[1:-1] if lines[-1].startswith("```") else lines[1:])
                    json_match = re.search(r'\[[\s\S]*\]', tw_text)
                    if json_match:
                        try:
                            tailwind_diffs = json.loads(json_match.group(0))
                        except json.JSONDecodeError:
                            logger.warning("Could not parse Tailwind diffs JSON")

                # Extract CSS override
                css_match = re.search(r'---CSS---\s*(.*?)\s*---END---', ai_response, re.DOTALL)
                if css_match:
                    css_text = css_match.group(1).strip()
                    if css_text.startswith("```"):
                        lines = css_text.splitlines()
                        css_text = "\n".join(lines[1:-1] if lines[-1].startswith("```") else lines[1:])
                    if len(css_text) > 10:
                        css_override = css_text

                # Fallback: try to extract any CSS from the response
                if not css_override:
                    # Look for CSS-like content anywhere in the response
                    css_blocks = re.findall(r'([.\#\[\w][^{]+\{[^}]+\})', ai_response)
                    if css_blocks:
                        css_override = "\n\n".join(css_blocks)

        except Exception as e:
            logger.warning(f"AI Tailwind CSS generation fallback: {e}. Using deterministic patches.")

    # ── Fallback: deterministic CSS patches from bug metadata ─────────────
    if not css_override:
        forbidden_selectors = {"*", "body", "html", "p", "span", "div", "a", "button", "input", "select", "h1", "h2", "h3"}
        css_patches = []
        for b in bugs:
            selector = (b.get("element_selector") or "").strip()
            fix = (b.get("suggested_fix") or "").strip()
            if not selector or selector in forbidden_selectors:
                continue
            if fix:
                css_patches.append(f"/* Bug Fix: {b.get('title', 'UI Fix')} */\n{selector} {{\n  {fix}\n}}")
        if css_patches:
            css_override = "\n\n".join(css_patches)

    # ── AST Validation & Sanitization (Day 6 Milestone) ───────────────────
    if css_override:
        css_override = validate_and_sanitize_css_ast(css_override)

    # ── Inject CSS override into source HTML ──────────────────────────────
    patch_style = f"\n<style id='omnisight-ai-fixes'>\n{css_override}\n</style>\n" if css_override else ""

    if patch_style:
        if "</head>" in source_code:
            fixed_source = source_code.replace("</head>", f"{patch_style}</head>")
        elif "</body>" in source_code:
            fixed_source = source_code.replace("</body>", f"{patch_style}</body>")
        else:
            fixed_source = patch_style + "\n" + source_code
    else:
        fixed_source = source_code

    logger.info(
        "🎨 Generated Tailwind fix: %d class diffs, %d bytes CSS override",
        len(tailwind_diffs), len(css_override)
    )

    return {
        "tailwind_classname_diffs": tailwind_diffs,
        "css_override": css_override,
        "fixed_source": fixed_source,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Legacy compatibility wrapper
# ─────────────────────────────────────────────────────────────────────────────

async def generate_fixed_code(source_code: str, bugs: list[dict]) -> str:
    """
    Legacy wrapper that returns only the fixed HTML source.
    Calls the new Tailwind-aware fixer internally.
    """
    result = await generate_tailwind_fix(source_code, bugs)
    return result["fixed_source"]
