"""
OmniSight — CSS AST Sanitizer Unit Tests
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Verifies that `validate_and_sanitize_css_ast` strips forbidden blanket
tag selectors while preserving specific, surgical class/ID rules and
media queries.
"""

from backend.services.vlm.code_fixer import validate_and_sanitize_css_ast


def test_empty_input_returns_empty_string():
    assert validate_and_sanitize_css_ast("") == ""
    assert validate_and_sanitize_css_ast("   \n  ") == ""


def test_strips_forbidden_blanket_selectors():
    raw_css = """
    * { box-sizing: border-box; }
    body { background: white; }
    h1 { font-size: 12px; }
    .checkout-button { width: 100%; max-width: 320px; }
    """
    sanitized = validate_and_sanitize_css_ast(raw_css)
    assert ".checkout-button" in sanitized
    assert "max-width: 320px" in sanitized
    assert "* {" not in sanitized
    assert "body {" not in sanitized
    assert "h1 {" not in sanitized


def test_preserves_media_queries():
    raw_css = "@media (max-width: 600px) { .header-nav { flex-direction: column; } }"
    sanitized = validate_and_sanitize_css_ast(raw_css)
    assert "@media" in sanitized
    assert ".header-nav" in sanitized
