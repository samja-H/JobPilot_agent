from __future__ import annotations

import logging

from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import Settings, get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging

logger: logging.Logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved_settings: Settings = settings or get_settings()
    configure_logging(resolved_settings)

    app: FastAPI = FastAPI(
        title=resolved_settings.app.name,
        debug=resolved_settings.app.debug,
        version="0.1.0",
    )

    def settings_dependency() -> Settings:
        return resolved_settings

    app.dependency_overrides[get_settings] = settings_dependency
    register_exception_handlers(app)
    app.include_router(api_router)

    logger.info("application_configured")
    return app


app: FastAPI = create_app()
