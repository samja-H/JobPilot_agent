# JobPilot Agent

JobPilot Agent 是一个最小可运行的智能求职 Agent 项目骨架，面向后续扩展 RAG 与 Tool Calling 能力。当前版本只包含工程基础设施：FastAPI 后端、Streamlit 前端 Demo、Qdrant Docker Compose、SQLite 配置、结构化日志、健康检查接口和基础测试。

本仓库暂不实现复杂业务逻辑，不包含自动投递、浏览器自动化或多 Agent 架构。

## 功能范围

- FastAPI 后端应用入口
- `/health` 健康检查接口
- Pydantic 配置加载，默认使用 SQLite MVP 数据库地址
- JSON 结构化日志初始化
- Streamlit Demo，用于检查后端健康状态
- Qdrant 向量数据库 `docker-compose.yml`
- pytest 基础测试

## 快速启动

### 1. 创建虚拟环境并安装依赖

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### 2. 准备环境变量

```bash
cp .env.example .env
```

默认配置：

- FastAPI: `http://localhost:8000`
- Streamlit: `http://localhost:8501`
- Qdrant: `http://localhost:6333`
- SQLite: `sqlite:///./jobpilot.db`

### 3. 启动 Qdrant

```bash
docker compose up -d qdrant
```

### 4. 启动 FastAPI 后端

```bash
uvicorn app.main:app --reload
```

健康检查：

```bash
curl http://localhost:8000/health
```

### 5. 启动 Streamlit Demo

```bash
streamlit run frontend/streamlit_app.py
```

### 6. 运行测试

```bash
pytest
```

## 目录结构

```text
.
├── app/
│   ├── api/          # FastAPI 路由
│   ├── agent/        # 后续放置 Agent 图和 prompts
│   ├── core/         # 配置加载和日志初始化
│   ├── db/           # 后续放置 SQLite 模型与 repository
│   ├── rag/          # 后续放置 RAG 检索逻辑
│   ├── schemas/      # Pydantic schema
│   ├── tools/        # 后续放置 Tool Calling 工具函数
│   └── main.py       # FastAPI 应用工厂
├── docs/             # 项目文档
├── frontend/         # Streamlit Demo
├── tests/            # pytest 测试
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

## 开发约定

- API route 只处理 HTTP 输入输出，业务逻辑放到 service/tool/repository。
- Prompt 放到 `app/agent/prompts.py`，不要写在 route handler 中。
- RAG 相关逻辑放到 `app/rag/`。
- Tool Calling 函数放到 `app/tools/`。
- 数据库模型和 repository 放到 `app/db/`。
- 新增用户可见功能时，同步补充测试和 README。

