from __future__ import annotations

from app.core.config import Settings


def test_settings_defaults() -> None:
    settings: Settings = Settings()

    assert settings.app_name == "JobPilot Agent"
    assert settings.database_url.startswith("sqlite:///")
    assert settings.qdrant_url == "http://localhost:6333"

