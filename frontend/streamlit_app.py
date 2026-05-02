from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import streamlit as st

ROOT_DIR: Path = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from app.core.config import get_settings  # noqa: E402


def main() -> None:
    settings = get_settings()
    runtime_config: dict[str, Any] = {
        "app": {
            "name": settings.app.name,
            "env": settings.app.env,
            "debug": settings.app.debug,
        },
        "backend": {
            "host": settings.server.host,
            "port": settings.server.port,
        },
        "qdrant": {
            "host": settings.qdrant.host,
            "port": settings.qdrant.port,
            "collection": settings.qdrant.collection_name,
        },
        "database": {
            "type": settings.database.type,
            "sqlite_path": settings.database.sqlite_path,
        },
    }

    st.set_page_config(page_title=settings.app.name, page_icon="JP", layout="wide")
    st.title(settings.app.name)
    st.caption("Minimal Streamlit demo for the JobPilot-Agent backend skeleton.")
    st.json(runtime_config)


if __name__ == "__main__":
    main()
