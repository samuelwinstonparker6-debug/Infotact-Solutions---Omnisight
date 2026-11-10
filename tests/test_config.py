"""
OmniSight — Configuration Unit Tests
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Validates default Settings values and credential configuration flags
without reading or exposing live secrets.
"""

from backend.core.config import Settings


def test_default_settings_without_env_file():
    cfg = Settings(_env_file=None, gemini_api_key="", github_token="")
    assert cfg.app_name == "OmniSight"
    assert cfg.app_port == 8000
    assert cfg.max_fix_retries >= 1
    assert cfg.is_gemini_configured is False
    assert cfg.is_github_configured is False


def test_configured_flags_when_tokens_present():
    cfg = Settings(
        _env_file=None,
        gemini_api_key="test-gemini-key",
        github_token="ghp_test_token_value",
    )
    assert cfg.is_gemini_configured is True
    assert cfg.is_github_configured is True
    placeholder = Settings(_env_file=None, github_token="ghp_your-github-token-here")
    assert placeholder.is_github_configured is False
