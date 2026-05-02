# app.yaml + .env 配置设计

## 设计目标

配置系统需要同时满足本地开发、测试和部署环境的需求，并明确区分敏感配置与非敏感配置。

配置优先级为：

```text
默认值 < config/app.yaml < .env < 系统环境变量
```

## 非敏感配置

`config/app.yaml` 保存非敏感配置，可提交到 Git，包括：

- 端口：`server.host`、`server.port`、`frontend.port`
- 模型名称：`llm.provider`、`llm.model`、`embedding.provider`、`embedding.model`
- RAG 参数：`rag.chunk_size`、`rag.chunk_overlap`、`rag.top_k`
- Qdrant 地址：`qdrant.host`、`qdrant.port`、`qdrant.collection_name`
- SQLite 路径：`database.type`、`database.sqlite_path`
- 日志配置：`logging.level`、`logging.log_file`
- Agent 工具白名单：`agent.allowed_tools`

## 敏感配置

`.env` 保存敏感配置，不允许提交到 Git，包括：

```dotenv
OPENAI_API_KEY=your-openai-api-key
DASHSCOPE_API_KEY=your-dashscope-api-key
DEEPSEEK_API_KEY=your-deepseek-api-key
SECRET_KEY=your-secret-key
```

`.env.example` 只保留字段名和示例占位符，用于提示开发者需要配置哪些环境变量，不包含真实密钥。

## 环境变量覆盖

系统环境变量优先级最高，适合部署环境覆盖配置。例如：

```bash
SERVER_PORT=9000
LLM_MODEL=gpt-4o-mini
RAG_TOP_K=8
```

配置加载逻辑会把这些值映射到统一的 `settings` 对象中，供 API、日志、前端 Demo 和后续业务模块使用。

## 安全要求

- `.env` 必须被 `.gitignore` 忽略。
- 不在日志中输出 API Key、Secret、简历原文或大段 Prompt。
- 测试不依赖真实 API Key。
- 文档、示例和测试只使用占位符。
