"""
OmniSight — Design Studio Intent Classifier Tests
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Validates keyword classification for 'design', 'bugfix', and 'both'
prompt intents in `backend.services.agent.design_interpreter`.
"""

from backend.services.agent.design_interpreter import classify_intent


def test_classify_design_only_prompt():
    assert classify_intent("Make the hero card have a glassmorphism border and gradient") == "design"


def test_classify_bugfix_only_prompt():
    assert classify_intent("Detect bug with overflow and low contrast on the checkout view") == "bugfix"


def test_classify_combined_design_and_bugfix_prompt():
    prompt = "Fix any UI bug causing overlap and also redesign the sidebar with modern spacing"
    assert classify_intent(prompt) == "both"
