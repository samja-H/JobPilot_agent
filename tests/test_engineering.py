from __future__ import annotations

import importlib
import json
import logging
from pathlib import Path

from app.core.config import LoggingConfig, Settings
from app.core.exceptions import AppError, error_payload
from app.core.logging import configure_logging


def test_error_payload_and_app_error_shape() -> None:
    error = AppError(
        message="Invalid request.",
        code="INVALID_REQUEST",
        status_code=400,
        detail={"field": "message"},
    )

    assert error.message == "Invalid request."
    assert error.code == "INVALID_REQUEST"
    assert error.status_code == 400
    assert error.detail == {"field": "message"}
    assert error_payload("INVALID_REQUEST", "Invalid request.", {"field": "message"}) == {
        "code": "INVALID_REQUEST",
        "message": "Invalid request.",
        "detail": {"field": "message"},
    }


def test_structured_logging_writes_json_file(tmp_path: Path) -> None:
    log_file: Path = tmp_path / "jobpilot.log"
    settings = Settings(
        logging=LoggingConfig(
            level="INFO",
            log_file=str(log_file),
        )
    )

    configure_logging(settings)
    logger = logging.getLogger("tests.engineering")
    logger.info("engineering_log_test", extra={"event": "unit_test"})
    for handler in logging.getLogger().handlers:
        handler.flush()

    payload = json.loads(log_file.read_text(encoding="utf-8").splitlines()[-1])
    assert payload["level"] == "INFO"
    assert payload["logger"] == "tests.engineering"
    assert payload["message"] == "engineering_log_test"
    assert payload["extra"]["event"] == "unit_test"


def test_startup_scripts_are_importable_without_running() -> None:
    server_module = importlib.import_module("scripts.run_server")
    frontend_module = importlib.import_module("scripts.run_frontend")

    assert callable(server_module.main)
    assert callable(frontend_module.main)


def test_gitignore_keeps_local_runtime_files_out_of_git() -> None:
    gitignore = Path(".gitignore").read_text(encoding="utf-8").splitlines()

    assert ".env" in gitignore
    assert "logs/" in gitignore
    assert "data/" in gitignore
    assert "__pycache__/" in gitignore
    assert ".pytest_cache/" in gitignore
