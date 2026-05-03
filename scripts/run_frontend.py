from __future__ import annotations

import subprocess
import sys

from app.core.config import get_settings


def main() -> None:
    settings = get_settings()
    command: list[str] = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "frontend/streamlit_app.py",
        "--server.port",
        str(settings.frontend.port),
    ]
    subprocess.run(command, check=True)


if __name__ == "__main__":
    main()
