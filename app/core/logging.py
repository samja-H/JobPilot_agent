from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from app.core.config import BASE_DIR, Settings

STANDARD_LOG_RECORD_KEYS: set[str] = {
    "args",
    "asctime",
    "created",
    "exc_info",
    "exc_text",
    "filename",
    "funcName",
    "levelname",
    "levelno",
    "lineno",
    "module",
    "msecs",
    "message",
    "msg",
    "name",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "stack_info",
    "thread",
    "threadName",
    "taskName",
}


class JsonLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        extras: dict[str, Any] = {
            key: value
            for key, value in record.__dict__.items()
            if key not in STANDARD_LOG_RECORD_KEYS
        }
        if extras:
            payload["extra"] = extras
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=str)


def configure_logging(settings: Settings) -> None:
    level: int = getattr(logging, settings.logging.level.upper(), logging.INFO)
    formatter = JsonLogFormatter()
    handlers: list[logging.Handler] = [logging.StreamHandler()]

    if settings.logging.log_file:
        log_path: Path = Path(settings.logging.log_file)
        if not log_path.is_absolute():
            log_path = BASE_DIR / log_path
        log_path.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(log_path, encoding="utf-8"))

    for handler in handlers:
        handler.setFormatter(formatter)

    logging.basicConfig(
        level=level,
        handlers=handlers,
        force=True,
    )
