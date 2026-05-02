# JobPilot Agent Architecture

JobPilot Agent 目前是最小可运行骨架，只包含 FastAPI 后端、Streamlit Demo、配置加载、结构化日志初始化、Qdrant Docker Compose 和基础测试。

## 模块职责

- `app/api/`: FastAPI 路由层，只负责 HTTP 输入输出。
- `app/schemas/`: Pydantic 请求与响应模型。
- `app/core/`: 配置加载、日志等运行时基础设施。
- `app/rag/`: 后续放置文档切分、向量化、Qdrant 检索逻辑。
- `app/tools/`: 后续放置可被 Agent 调用的求职工具函数。
- `app/agent/`: 后续放置 LangGraph/LangChain Agent 编排与提示词。
- `app/db/`: 后续放置 SQLite 模型、连接和 repository。
- `frontend/`: Streamlit Demo。
- `tests/`: pytest 测试。

