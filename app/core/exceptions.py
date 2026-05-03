from __future__ import annotations

import logging
from typing import Any

logger: logging.Logger = logging.getLogger(__name__)


class AppError(Exception):
    def __init__(
        self,
        message: str,
        code: str = "APP_ERROR",
        status_code: int = 400,
        detail: Any | None = None,
    ) -> None:
        super().__init__(message)
        self.message: str = message
        self.code: str = code
        self.status_code: int = status_code
        self.detail: Any | None = detail


def error_payload(
    code: str,
    message: str,
    detail: Any | None = None,
) -> dict[str, Any]:
    return {
        "code": code,
        "message": message,
        "detail": detail if detail is not None else {},
    }


def register_exception_handlers(app: Any) -> None:
    from fastapi import HTTPException, Request
    from fastapi.exceptions import RequestValidationError
    from fastapi.responses import JSONResponse

    @app.exception_handler(AppError)
    async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
        logger.warning(
            "app_error",
            extra={
                "error_code": exc.code,
                "status_code": exc.status_code,
            },
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=error_payload(
                code=exc.code,
                message=exc.message,
                detail=exc.detail,
            ),
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
        logger.warning(
            "http_error",
            extra={
                "status_code": exc.status_code,
            },
        )
        return JSONResponse(
            status_code=exc.status_code,
            content=error_payload(
                code="HTTP_ERROR",
                message="Request failed.",
                detail=exc.detail,
            ),
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        _: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        logger.warning("validation_error")
        return JSONResponse(
            status_code=422,
            content=error_payload(
                code="VALIDATION_ERROR",
                message="Request payload is invalid.",
                detail=exc.errors(),
            ),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled_error", exc_info=exc)
        return JSONResponse(
            status_code=500,
            content=error_payload(
                code="INTERNAL_SERVER_ERROR",
                message="Internal server error.",
            ),
        )
