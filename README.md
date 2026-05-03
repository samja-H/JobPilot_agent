# JobPilot-Agent

JobPilot-Agent 是一个面向求职场景的智能 Agent 项目，目标是基于 RAG 与 Tool Calling 构建岗位分析、简历匹配、简历优化、面试准备和投递记录管理的一体化求职助手。

当前仓库处于 MVP 演示阶段，已经具备 FastAPI 后端、Streamlit Demo、Qdrant 服务、SQLite 投递记录、统一配置加载、结构化日志、统一异常处理和最小 LangGraph Agent 工作流。

## 核心功能

- 岗位 JD 分析：提取岗位职责、硬性要求、软性要求、关键词和风险提示。
- 简历匹配评分：基于岗位要求和简历内容生成匹配分、证据点和改进建议。
- 简历优化建议：针对 JD 给出简历 bullet 优化方向，突出技能、项目和成果。
- 面试问题生成：根据 JD、简历和匹配结果生成技术面、行为面和项目深挖问题。
- 投递记录管理：记录岗位、公司、状态、时间线和备注，支持后续追踪。
- Agent 对话：根据用户输入显式识别意图，并调用白名单内工具。
- 最小可运行闭环：提供 `/health` 接口、Streamlit Demo、Qdrant Docker Compose、启动脚本和 pytest 测试。

## 技术栈

- 后端：FastAPI
- 前端 Demo：Streamlit
- Agent 工作流：LangGraph / LangChain
- 向量数据库：Qdrant
- MVP 数据库：SQLite
- 配置管理：`config/app.yaml` + `.env` + 系统环境变量
- 测试：pytest
- 部署：Docker Compose

## 系统架构

系统按职责分层，避免把业务逻辑堆在 API route 中：

```text
Streamlit Demo
    |
FastAPI API Layer
    |
Schemas + Services / Tools
    |
RAG / Agent Workflow / DB Repository
    |
Qdrant + SQLite + LLM Provider
```

- `app/api/` 只负责 HTTP 路由、请求响应和服务编排入口。
- `app/schemas/` 统一管理 Pydantic 请求和响应结构。
- `app/tools/` 承载 JD 分析、简历匹配、简历优化等可被 Tool Calling 调用的业务工具。
- `app/rag/` 承载文档解析、切分、Embedding、向量写入和检索逻辑。
- `app/agent/` 承载 LangGraph state、node 和 workflow。
- `app/db/` 承载 SQLite 模型和 repository。
- `app/core/` 承载配置、日志、异常处理等基础设施能力。

## 目录结构

```text
.
├── app/
│   ├── api/              # FastAPI 路由
│   ├── core/             # 配置、日志、异常处理
│   ├── schemas/          # Pydantic schema
│   ├── rag/              # RAG 文档解析、切分、向量库、检索
│   ├── tools/            # JD 分析、简历匹配、简历优化等工具
│   ├── agent/            # LangGraph Agent 状态、节点和工作流
│   ├── db/               # SQLite 模型和 repository
│   └── utils/            # 通用工具函数
├── config/
│   └── app.yaml          # 非敏感配置
├── frontend/
│   └── streamlit_app.py  # Streamlit Demo
├── scripts/
│   ├── run_server.py     # 读取 app.yaml 启动 FastAPI
│   └── run_frontend.py   # 读取 app.yaml 启动 Streamlit
├── tests/                # pytest 测试
├── docs/                 # 系统设计文档
├── docker-compose.yml    # Qdrant 等基础服务
├── .env.example          # 敏感配置字段示例
└── README.md
```

## 配置说明

项目使用 `config/app.yaml`、`.env` 和系统环境变量组合管理配置，优先级为：

```text
默认值 < config/app.yaml < .env < 系统环境变量
```

`config/app.yaml` 保存非敏感配置，包括：

- 端口和前端后端地址：`server.host`、`server.port`、`frontend.port`、`frontend.backend_url`
- 模型名称：`llm.provider`、`llm.model`、`embedding.provider`、`embedding.model`
- RAG 参数：`rag.chunk_size`、`rag.chunk_overlap`、`rag.top_k`
- Qdrant 地址：`qdrant.host`、`qdrant.port`、`qdrant.collection_name`
- SQLite 路径：`database.type`、`database.sqlite_path`
- 日志配置：`logging.level`、`logging.log_file`
- Agent 配置：`agent.allowed_tools`、`agent.max_iterations`、`agent.enable_tool_calling`

`.env` 保存敏感配置，包括：

- `OPENAI_API_KEY`
- `DASHSCOPE_API_KEY`
- `DEEPSEEK_API_KEY`
- `SECRET_KEY`

`.env` 不提交到 Git，必须由本地或部署环境自行提供。`.env.example` 只保留字段名和示例占位符，不包含真实 API Key、真实密钥或用户隐私信息。

## 快速开始

安装依赖：

```bash
python -m pip install -e ".[dev]"
```

准备本地敏感配置：

```bash
cp .env.example .env
```

启动 Qdrant：

```bash
docker compose up -d qdrant
```

启动后端：

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

或使用读取 `config/app.yaml` 的启动脚本：

```bash
python scripts/run_server.py
```

启动前端：

```bash
streamlit run frontend/streamlit_app.py --server.port 8501
```

或使用读取 `config/app.yaml` 的启动脚本：

```bash
python scripts/run_frontend.py
```

运行测试：

```bash
python -m pytest
```

常用本地验证命令：

```bash
python -m compileall app frontend scripts tests
python -m pytest tests/test_config.py tests/test_splitter.py tests/test_embeddings.py
python -m pytest tests/test_jd_analyzer.py tests/test_resume_matcher.py tests/test_agent_workflow.py
```

如果当前 Python 环境尚未安装 FastAPI，API 相关测试会在收集阶段报 `ModuleNotFoundError: No module named 'fastapi'`。先执行 `python -m pip install -e ".[dev]"` 再运行全量测试。

## 工程化说明

- 统一异常处理位于 `app/core/exceptions.py`，FastAPI 创建时自动注册 handler。
- 结构化日志位于 `app/core/logging.py`，输出 JSON 格式日志。
- 日志级别由 `logging.level` 控制。
- 日志文件路径由 `logging.log_file` 控制，默认写入 `logs/jobpilot.log`。
- `.gitignore` 已忽略 `.env`、`logs/`、`data/`、`__pycache__/` 和 `.pytest_cache/`。

## API 说明

当前已实现健康检查接口：

```http
GET /health
```

响应示例：

```json
{
  "status": "ok",
  "app_name": "JobPilot-Agent",
  "environment": "local"
}
```

后续 API 会按功能拆分为 JD 分析、简历匹配、简历优化、面试问题生成和投递记录管理模块。每个新增功能必须包含 schema、service/tool 逻辑、API route 和 pytest 测试。

## 开发路线

- 阶段 1：完成项目骨架、配置系统、日志系统、健康检查和基础文档。
- 阶段 2：实现 JD 分析工具，输出结构化岗位画像。
- 阶段 3：实现简历解析、Embedding、Qdrant 写入和检索。
- 阶段 4：实现简历匹配评分和证据引用。
- 阶段 5：实现简历优化建议和面试问题生成。
- 阶段 6：实现 SQLite 投递记录管理。
- 阶段 7：接入 LangGraph 单 Agent 工作流，统一编排工具调用。
- 阶段 8：完善 Streamlit Demo、测试覆盖和 Docker Compose 本地运行体验。

## 项目亮点

- 面向真实求职流程，而不是通用聊天机器人。
- 采用 RAG 增强简历和岗位上下文，降低模型幻觉。
- 使用 Tool Calling 将 JD 分析、匹配评分、优化建议等能力模块化。
- 使用 LangGraph 描述单 Agent 工作流，便于测试和调试。
- 配置分层清晰，敏感信息与非敏感配置分离。
- 后端、前端、向量库和数据库边界明确，适合作为求职项目展示。

## 后续优化方向

- 增加简历文件解析，支持 PDF、Markdown、DOCX 等格式。
- 增加可解释匹配评分，输出命中证据和缺口证据。
- 增加 Prompt 版本管理和评测样例。
- 增加 Qdrant collection 初始化与迁移脚本。
- 增加 SQLite repository、数据模型和投递状态流转。
- 增加 API 鉴权、限流和更完整的错误处理。
- 增加 CI 测试、代码质量检查和 Docker 化后端服务。
