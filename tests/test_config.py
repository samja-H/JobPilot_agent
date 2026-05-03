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
    assert settings.llm.max_tokens == 1200
    assert settings.matching.skill_weight == 0.4
    assert settings.matching.project_weight == 0.35
    assert settings.matching.keyword_weight == 0.25
    assert settings.database.sqlite_path == "data/jobpilot.db"
    assert settings.embedding.provider == "mock"
    assert settings.embedding.dimension == 384
    assert settings.rag.score_threshold == 0.0
    assert settings.rag.enable_rerank is False
    assert settings.qdrant.timeout == 10.0
    assert settings.agent.max_iterations == 3
    assert settings.agent.enable_tool_calling is True


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
  max_tokens: 900
matching:
  skill_weight: 0.5
  project_weight: 0.3
  keyword_weight: 0.2
rag:
  top_k: 3
  score_threshold: 0.3
  enable_rerank: true
embedding:
  dimension: 16
qdrant:
  timeout: 3.5
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
            "EMBEDDING_DIMENSION": "32",
            "LLM_MAX_TOKENS": "1100",
            "LLM_MODEL": "system-env-model",
            "MATCHING_SKILL_WEIGHT": "0.6",
            "RAG_TOP_K": "7",
            "QDRANT_TIMEOUT": "8.0",
            "AGENT_MAX_ITERATIONS": "5",
            "AGENT_ENABLE_TOOL_CALLING": "false",
        },
    )

    assert settings.app.name == "YAML JobPilot"
    assert settings.app.env == "test"
    assert settings.app.debug is True
    assert settings.server.port == 8200
    assert settings.llm.model == "system-env-model"
    assert settings.llm.max_tokens == 1100
    assert settings.matching.skill_weight == 0.6
    assert settings.matching.project_weight == 0.3
    assert settings.matching.keyword_weight == 0.2
    assert settings.embedding.dimension == 32
    assert settings.rag.top_k == 7
    assert settings.rag.score_threshold == 0.3
    assert settings.rag.enable_rerank is True
    assert settings.qdrant.timeout == 8.0
    assert settings.secrets.secret_key == "env-file-secret"
    assert settings.agent.allowed_tools == ["jd_analyzer", "resume_matcher"]
    assert settings.agent.max_iterations == 5
    assert settings.agent.enable_tool_calling is False


def test_load_settings_reads_rag_qdrant_embedding_options_from_app_yaml() -> None:
    settings = load_settings(
        config_path=Path("config/app.yaml"),
        env_file=Path("missing.env"),
        environ={},
    )

    assert settings.rag.chunk_size == 800
    assert settings.rag.chunk_overlap == 120
    assert settings.rag.top_k == 5
    assert settings.rag.score_threshold == 0.0
    assert settings.rag.enable_rerank is False
    assert settings.qdrant.host == "localhost"
    assert settings.qdrant.port == 6333
    assert settings.qdrant.collection_name == "jobpilot_documents"
    assert settings.qdrant.timeout == 10.0
    assert settings.embedding.provider == "mock"
    assert settings.embedding.model == "mock-embedding"
    assert settings.embedding.dimension == 384
    assert settings.llm.provider == "openai"
    assert settings.llm.model == "gpt-4o-mini"
    assert settings.llm.temperature == 0.2
    assert settings.llm.max_tokens == 1200
    assert settings.matching.skill_weight == 0.4
    assert settings.matching.project_weight == 0.35
    assert settings.matching.keyword_weight == 0.25
    assert settings.agent.max_iterations == 3
    assert settings.agent.enable_tool_calling is True
    assert settings.agent.allowed_tools == [
        "jd_analyzer",
        "resume_matcher",
        "resume_rewriter",
        "interview_question_generator",
        "application_tracker",
        "rag_retriever",
    ]
