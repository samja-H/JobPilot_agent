from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any, Mapping, MutableMapping

import yaml
from pydantic import BaseModel, Field

BASE_DIR: Path = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH: Path = BASE_DIR / "config" / "app.yaml"
DEFAULT_ENV_FILE: Path = BASE_DIR / ".env"

EnvPath = tuple[str, ...]


class AppConfig(BaseModel):
    name: str = "JobPilot-Agent"
    env: str = "local"
    debug: bool = False


class ServerConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000


class FrontendConfig(BaseModel):
    port: int = 8501


class LLMConfig(BaseModel):
    provider: str = "openai"
    model: str = "gpt-4o-mini"
    temperature: float = 0.2


class EmbeddingConfig(BaseModel):
    provider: str = "openai"
    model: str = "text-embedding-3-small"


class RAGConfig(BaseModel):
    chunk_size: int = 800
    chunk_overlap: int = 120
    top_k: int = 5


class QdrantConfig(BaseModel):
    host: str = "localhost"
    port: int = 6333
    collection_name: str = "jobpilot_documents"


class DatabaseConfig(BaseModel):
    type: str = "sqlite"
    sqlite_path: str = "data/jobpilot.db"


class LoggingConfig(BaseModel):
    level: str = "INFO"
    log_file: str | None = "logs/jobpilot.log"


class AgentConfig(BaseModel):
    allowed_tools: list[str] = Field(default_factory=list)


class SecretConfig(BaseModel):
    openai_api_key: str | None = None
    dashscope_api_key: str | None = None
    deepseek_api_key: str | None = None
    secret_key: str | None = None


class Settings(BaseModel):
    app: AppConfig = Field(default_factory=AppConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)
    frontend: FrontendConfig = Field(default_factory=FrontendConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    rag: RAGConfig = Field(default_factory=RAGConfig)
    qdrant: QdrantConfig = Field(default_factory=QdrantConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    agent: AgentConfig = Field(default_factory=AgentConfig)
    secrets: SecretConfig = Field(default_factory=SecretConfig)

    @property
    def app_name(self) -> str:
        return self.app.name

    @property
    def environment(self) -> str:
        return self.app.env


ENV_KEY_MAP: dict[str, EnvPath] = {
    "APP_NAME": ("app", "name"),
    "APP_ENV": ("app", "env"),
    "APP_DEBUG": ("app", "debug"),
    "SERVER_HOST": ("server", "host"),
    "SERVER_PORT": ("server", "port"),
    "FRONTEND_PORT": ("frontend", "port"),
    "LLM_PROVIDER": ("llm", "provider"),
    "LLM_MODEL": ("llm", "model"),
    "LLM_TEMPERATURE": ("llm", "temperature"),
    "EMBEDDING_PROVIDER": ("embedding", "provider"),
    "EMBEDDING_MODEL": ("embedding", "model"),
    "RAG_CHUNK_SIZE": ("rag", "chunk_size"),
    "RAG_CHUNK_OVERLAP": ("rag", "chunk_overlap"),
    "RAG_TOP_K": ("rag", "top_k"),
    "QDRANT_HOST": ("qdrant", "host"),
    "QDRANT_PORT": ("qdrant", "port"),
    "QDRANT_COLLECTION_NAME": ("qdrant", "collection_name"),
    "DATABASE_TYPE": ("database", "type"),
    "DATABASE_SQLITE_PATH": ("database", "sqlite_path"),
    "LOGGING_LEVEL": ("logging", "level"),
    "LOGGING_LOG_FILE": ("logging", "log_file"),
    "AGENT_ALLOWED_TOOLS": ("agent", "allowed_tools"),
    "OPENAI_API_KEY": ("secrets", "openai_api_key"),
    "DASHSCOPE_API_KEY": ("secrets", "dashscope_api_key"),
    "DEEPSEEK_API_KEY": ("secrets", "deepseek_api_key"),
    "SECRET_KEY": ("secrets", "secret_key"),
}

_settings_fields: Mapping[str, Any] | None = getattr(Settings, "model_fields", None)
if _settings_fields is None:
    _settings_fields = getattr(Settings, "__fields__")
TOP_LEVEL_KEYS: set[str] = set(_settings_fields.keys())


def _model_to_dict(model: BaseModel) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()  # type: ignore[attr-defined]
    return model.dict()


def _validate_settings(data: Mapping[str, Any]) -> Settings:
    if hasattr(Settings, "model_validate"):
        return Settings.model_validate(data)  # type: ignore[attr-defined]
    return Settings.parse_obj(data)


def _read_yaml_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}

    loaded: Any = yaml.safe_load(path.read_text(encoding="utf-8"))
    if loaded is None:
        return {}
    if not isinstance(loaded, dict):
        raise ValueError(f"Config file must contain a mapping: {path}")
    return loaded


def _read_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}

    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line: str = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line.removeprefix("export ").strip()
        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        values[key.strip()] = _strip_env_quotes(value.strip())
    return values


def _strip_env_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value


def _deep_update(target: MutableMapping[str, Any], updates: Mapping[str, Any]) -> None:
    for key, value in updates.items():
        if isinstance(value, Mapping) and isinstance(target.get(key), MutableMapping):
            _deep_update(target[key], value)
            continue
        target[key] = value


def _env_path(key: str) -> EnvPath | None:
    normalized_key: str = key.upper()
    if normalized_key in ENV_KEY_MAP:
        return ENV_KEY_MAP[normalized_key]
    if "__" not in normalized_key:
        return None

    parts: EnvPath = tuple(part.lower() for part in normalized_key.split("__") if part)
    if not parts or parts[0] not in TOP_LEVEL_KEYS:
        return None
    return parts


def _set_nested_value(target: MutableMapping[str, Any], path: EnvPath, value: Any) -> None:
    current: MutableMapping[str, Any] = target
    for part in path[:-1]:
        next_value: Any = current.setdefault(part, {})
        if not isinstance(next_value, MutableMapping):
            next_value = {}
            current[part] = next_value
        current = next_value

    current[path[-1]] = _coerce_env_value(path, value)


def _coerce_env_value(path: EnvPath, value: Any) -> Any:
    if path == ("agent", "allowed_tools") and isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    if path == ("logging", "log_file") and value == "":
        return None
    return value


def _apply_env_values(target: MutableMapping[str, Any], values: Mapping[str, str]) -> None:
    for key, value in values.items():
        path: EnvPath | None = _env_path(key)
        if path is None:
            continue
        _set_nested_value(target, path, value)


def load_settings(
    config_path: str | Path = DEFAULT_CONFIG_PATH,
    env_file: str | Path = DEFAULT_ENV_FILE,
    environ: Mapping[str, str] | None = None,
) -> Settings:
    data: dict[str, Any] = _model_to_dict(Settings())
    _deep_update(data, _read_yaml_file(Path(config_path)))
    _apply_env_values(data, _read_env_file(Path(env_file)))
    _apply_env_values(data, os.environ if environ is None else environ)
    return _validate_settings(data)


@lru_cache
def get_settings() -> Settings:
    return load_settings()


settings: Settings = get_settings()
