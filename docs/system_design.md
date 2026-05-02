# 系统架构设计

## 设计目标

JobPilot-Agent 的目标是构建一个面向求职流程的智能助手，用 RAG 提供岗位和简历上下文，用 Tool Calling 封装可测试的业务能力，用 LangGraph 编排单 Agent 工作流。

MVP 阶段优先保证最小可运行闭环：FastAPI 后端、Streamlit Demo、统一配置、Qdrant 服务、SQLite 配置和基础测试。

## 架构分层

```text
用户
 |
Streamlit Demo
 |
FastAPI API
 |
Schema / Service / Tool
 |
RAG      Agent Workflow      Repository
 |
Qdrant   LLM Provider        SQLite
```

## 模块职责

- `app/api/`：HTTP API 层，只处理请求、响应和依赖注入，不承载业务逻辑。
- `app/schemas/`：Pydantic schema，定义输入输出结构。
- `app/tools/`：Tool Calling 可调用工具，例如 JD 分析、简历匹配、简历优化。
- `app/rag/`：文档解析、文本切分、Embedding、向量写入、检索。
- `app/agent/`：LangGraph state、node、edge 和 workflow。
- `app/db/`：SQLite 数据模型和 repository。
- `app/core/`：配置加载、日志、异常处理等基础设施。
- `frontend/`：Streamlit Demo，用于展示后端能力。

## 请求流程

1. 用户在 Streamlit 或 API 客户端发起请求。
2. FastAPI route 使用 schema 校验输入。
3. route 调用 service 或 tool，不直接写业务逻辑。
4. service/tool 根据需要调用 RAG、LLM、repository 或 Agent workflow。
5. route 返回结构化响应。

## 数据存储

- Qdrant：保存简历片段、岗位片段、Embedding 向量和检索 payload。
- SQLite：保存投递记录、岗位元信息、简历版本元信息等结构化数据。
- 本地文件：MVP 阶段可用于临时保存上传文件，但不应保存敏感密钥。

## 非目标

- 不实现自动投递。
- 不实现多 Agent 架构。
- 不把 Prompt 分散到 route 或测试中。
- 不把 RAG、工具、数据库和 API 逻辑写进单个大文件。
