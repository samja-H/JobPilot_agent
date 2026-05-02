from __future__ import annotations

import logging

from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import Settings, get_settings
from app.core.logging_config import configure_logging

logger: logging.Logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings: Settings = settings or get_settings()
    configure_logging(resolved_settings.log_level)

    app: FastAPI = FastAPI(
        title=resolved_settings.app_name,
        version="0.1.0",
    )

    def settings_dependency() -> Settings:
        return resolved_settings

    app.dependency_overrides[get_settings] = settings_dependency
    app.include_router(api_router)

    logger.info("application_configured")
    return app


app: FastAPI = create_app()

