from __future__ import annotations

import importlib

from app.core.config import load_settings


def test_streamlit_app_imports_without_running_ui() -> None:
    module = importlib.import_module("frontend.streamlit_app")

    assert module.NAV_ITEMS[0] == "首页"
    assert module.build_url("http://localhost:8000/", "/health") == "http://localhost:8000/health"
    assert module.split_lines("a\n\n b ") == ["a", "b"]


def test_frontend_config_reads_backend_url_from_app_yaml() -> None:
    settings = load_settings(env_file="missing.env", environ={})

    assert settings.frontend.port == 8501
    assert settings.frontend.backend_url == "http://localhost:8000"
