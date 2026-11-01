"""
OmniSight — Application Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Centralized configuration management using pydantic-settings.
All environment variables are loaded from .env file and validated
at startup with type checking and sensible defaults.
"""

import os
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict



class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.

    All values can be overridden via a `.env` file in the project root
    or by setting the corresponding environment variable directly.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────
    app_name: str = "OmniSight"
    app_version: str = "0.1.0"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_debug: bool = False

    # ── Logging ──────────────────────────────────────────────
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    # ── Gemini / VLM ────────────────────────────────────────
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.8-flash"

    # ── GitHub ───────────────────────────────────────────────
    github_token: str = ""
    github_repo: str = ""
    github_webhook_secret: str = ""

    # ── Agent ────────────────────────────────────────────────
    max_fix_retries: int = 3

    # ── Target Application ───────────────────────────────────
    staging_url: str = "http://localhost:8000/mock-app/index.html"

    # ── Database ─────────────────────────────────────────────
    database_url: str = "sqlite+aiosqlite:///./omnisight.db"

    # ── Browser / Playwright ─────────────────────────────────
    browser_headless: bool = True
    browser_viewport_width: int = 1280
    browser_viewport_height: int = 720

    @property
    def is_gemini_configured(self) -> bool:
        """Check if Gemini API key is set."""
        return bool(self.gemini_api_key)

    @property
    def is_github_configured(self) -> bool:
        """Check if GitHub token is set."""
        return bool(
            self.github_token
            and self.github_token != "ghp_your-github-token-here"
        )

    def set_github_credentials(self, token: str, repo: str = "") -> None:
        """Update GitHub credentials at runtime and persist to .env."""
        self.github_token = token.strip()
        if repo:
            self.github_repo = repo.strip()
        
        # Persist to .env file
        env_path = os.path.join(os.getcwd(), ".env")
        if os.path.exists(env_path):
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                new_lines = []
                token_written = False
                repo_written = False
                for line in lines:
                    if line.startswith("GITHUB_TOKEN="):
                        new_lines.append(f"GITHUB_TOKEN={self.github_token}\n")
                        token_written = True
                    elif line.startswith("GITHUB_REPO=") and self.github_repo:
                        new_lines.append(f"GITHUB_REPO={self.github_repo}\n")
                        repo_written = True
                    else:
                        new_lines.append(line)
                if not token_written:
                    new_lines.append(f"GITHUB_TOKEN={self.github_token}\n")
                if not repo_written and self.github_repo:
                    new_lines.append(f"GITHUB_REPO={self.github_repo}\n")
                with open(env_path, "w", encoding="utf-8") as f:
                    f.writelines(new_lines)
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"Could not persist to .env: {e}")

    def update_settings(
        self,
        gemini_api_key: Optional[str] = None,
        gemini_model: Optional[str] = None,
        github_token: Optional[str] = None,
        github_repo: Optional[str] = None,
        staging_url: Optional[str] = None,
    ) -> None:
        """Update runtime configuration and persist changes to .env file."""
        if gemini_api_key is not None:
            self.gemini_api_key = gemini_api_key.strip()
        if gemini_model is not None and gemini_model.strip():
            self.gemini_model = gemini_model.strip()
        if github_token is not None:
            self.github_token = github_token.strip()
        if github_repo is not None:
            self.github_repo = github_repo.strip()
        if staging_url is not None and staging_url.strip():
            self.staging_url = staging_url.strip()

        env_path = os.path.join(os.getcwd(), ".env")
        if not os.path.exists(env_path):
            env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")

        try:
            lines = []
            if os.path.exists(env_path):
                with open(env_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()

            keys_to_update = {
                "GEMINI_API_KEY": self.gemini_api_key,
                "GEMINI_MODEL": self.gemini_model,
                "GITHUB_TOKEN": self.github_token,
                "GITHUB_REPO": self.github_repo,
                "STAGING_URL": self.staging_url,
            }
            written_keys = set()
            new_lines = []
            for line in lines:
                matched = False
                for k, v in keys_to_update.items():
                    if line.startswith(f"{k}="):
                        new_lines.append(f"{k}={v}\n")
                        written_keys.add(k)
                        matched = True
                        break
                if not matched:
                    new_lines.append(line)

            for k, v in keys_to_update.items():
                if k not in written_keys and v:
                    new_lines.append(f"{k}={v}\n")

            with open(env_path, "w", encoding="utf-8") as f:
                f.writelines(new_lines)
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Could not persist settings to .env: {e}")

    def clear_github_credentials(self) -> None:
        """Clear GitHub credentials at runtime and persist to .env."""
        self.github_token = ""
        self.github_repo = ""
        
        env_path = os.path.join(os.getcwd(), ".env")
        if os.path.exists(env_path):
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                new_lines = []
                for line in lines:
                    if line.startswith("GITHUB_TOKEN="):
                        new_lines.append("GITHUB_TOKEN=\n")
                    elif line.startswith("GITHUB_REPO="):
                        new_lines.append("GITHUB_REPO=\n")
                    else:
                        new_lines.append(line)
                with open(env_path, "w", encoding="utf-8") as f:
                    f.writelines(new_lines)
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"Could not persist clear to .env: {e}")



@lru_cache
def get_settings() -> Settings:
    """
    Get cached application settings singleton.

    Uses lru_cache to ensure settings are loaded only once
    and reused across the application lifecycle.

    Returns:
        Settings: Validated application settings instance.
    """
    return Settings()

