from __future__ import annotations

from pathlib import Path

from app.core.config import load_settings


def test_load_settings_uses_default_values_when_files_are_missing(tmp_path: Path) -> None:
    settings = load_settings(
        config_path=tmp_path / "missing.yaml",
        env_file=tmp_path / "missing.env",
        environ={},
    )

    assert settings.app.name == "JobPilot-Agent"
    assert settings.server.port == 8000
    assert settings.database.sqlite_path == "data/jobpilot.db"


def test_load_settings_priority_yaml_env_file_system_env(tmp_path: Path) -> None:
    config_path: Path = tmp_path / "app.yaml"
    env_file: Path = tmp_path / ".env"

    config_path.write_text(
        """
app:
  name: YAML JobPilot
  env: test
server:
  port: 8100
llm:
  model: yaml-model
rag:
  top_k: 3
""".strip(),
        encoding="utf-8",
    )
    env_file.write_text(
        """
SERVER_PORT=8200
LLM_MODEL=env-file-model
SECRET_KEY=env-file-secret
AGENT_ALLOWED_TOOLS=jd_analyzer,resume_matcher
""".strip(),
        encoding="utf-8",
    )

    settings = load_settings(
        config_path=config_path,
        env_file=env_file,
        environ={
            "APP_DEBUG": "true",
            "LLM_MODEL": "system-env-model",
            "RAG_TOP_K": "7",
        },
    )

    assert settings.app.name == "YAML JobPilot"
    assert settings.app.env == "test"
    assert settings.app.debug is True
    assert settings.server.port == 8200
    assert settings.llm.model == "system-env-model"
    assert settings.rag.top_k == 7
    assert settings.secrets.secret_key == "env-file-secret"
    assert settings.agent.allowed_tools == ["jd_analyzer", "resume_matcher"]
