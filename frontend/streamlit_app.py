from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

import streamlit as st

DEFAULT_API_URL: str = "http://localhost:8000"


def fetch_health(api_url: str) -> dict[str, Any]:
    url: str = f"{api_url.rstrip('/')}/health"
    request: urllib.request.Request = urllib.request.Request(
        url,
        headers={"Accept": "application/json"},
    )

    with urllib.request.urlopen(request, timeout=5) as response:
        body: str = response.read().decode("utf-8")

    payload: Any = json.loads(body)
    if not isinstance(payload, dict):
        raise ValueError("Unexpected health response payload.")

    return payload


def main() -> None:
    st.set_page_config(page_title="JobPilot Agent")
    st.title("JobPilot Agent")

    api_url: str = st.text_input(
        "FastAPI URL",
        value=os.getenv("JOBPILOT_API_URL", DEFAULT_API_URL),
    )

    if st.button("Check backend"):
        try:
            health: dict[str, Any] = fetch_health(api_url)
        except (
            TimeoutError,
            ValueError,
            json.JSONDecodeError,
            urllib.error.URLError,
        ) as exc:
            st.error(f"Backend health check failed: {exc}")
            return

        st.success("Backend is healthy.")
        st.json(health)


if __name__ == "__main__":
    main()
