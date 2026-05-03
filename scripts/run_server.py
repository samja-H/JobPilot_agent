from __future__ import annotations

from app.core.config import get_settings


def main() -> None:
    settings = get_settings()

    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.server.host,
        port=settings.server.port,
        reload=settings.app.env == "local",
    )


if __name__ == "__main__":
    main()
