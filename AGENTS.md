# AGENTS.md

本文件用于约束 Codex 及后续开发者在 `JobPilot-Agent` 仓库中的开发行为。其规则适用于整个仓库，除非子目录中存在更具体的 `AGENTS.md`。

## 项目定位

- 项目名称：`JobPilot-Agent`
- 项目目标：构建一个基于 RAG 与 Tool Calling 的智能求职 Agent。
- 核心能力：
  - 岗位 JD 分析
  - 简历匹配评分
  - 简历优化建议
  - 面试问题生成
  - 投递记录管理

## 技术栈约束

- 后端必须使用 FastAPI。
- 前端 Demo 必须使用 Streamlit。
- Agent 工作流必须使用 LangGraph / LangChain。
- 向量数据库必须使用 Qdrant。
- MVP 数据库必须使用 SQLite。
- 测试必须使用 pytest。
- 部署必须使用 Docker Compose。
- 配置必须采用 `config/app.yaml` + `.env`：
  - `config/app.yaml` 保存非敏感配置，例如端口、模型名称、RAG 参数、Qdrant 地址、SQLite 路径等。
  - `.env` 保存敏感信息，例如 `OPENAI_API_KEY`、`DASHSCOPE_API_KEY`、`DEEPSEEK_API_KEY`、`SECRET_KEY` 等。
  - `.env` 不允许提交到 Git。

## 禁止事项

- 不要实现自动投递功能。
- 不要实现多 Agent 架构。
- 不要引入不必要的新框架。
- 不要把业务逻辑写在 API route 中。
- 不要把 Prompt 散落在多个文件中。
- 不要写大而全的单文件实现。
- 不要提前做复杂抽象或过度设计。
- 不要提交 `.env`、密钥、令牌、真实用户隐私数据或其他敏感信息。

## 开发原则

- 优先实现最小可运行闭环。
- 每个模块职责必须清晰。
- 所有 Python 代码必须有类型注解。
- 业务逻辑应放在 service、tool、repository、agent node 等明确职责层中。
- API route 只负责请求解析、鉴权/校验衔接、调用服务、返回响应。
- Prompt 应集中管理，避免散落在 route、service、tool、test 等多个位置。
- 新增依赖前必须确认现有技术栈无法合理满足需求。
- 保持实现可测试、可替换、可读，避免隐藏副作用。

## 新增功能要求

每个新增功能必须包含以下内容：

- Pydantic schema
- service 或 tool 逻辑
- API route
- pytest 测试

如果功能涉及数据持久化，还必须包含：

- 数据库模型或迁移方式
- repository 层封装
- 对应测试或测试替身

如果功能涉及 RAG，还必须明确：

- 文档解析入口
- 文档切分策略
- Embedding 调用位置
- Qdrant collection / payload 设计
- 检索参数与测试覆盖

如果功能涉及 Agent 工作流，还必须明确：

- LangGraph state
- node 职责
- workflow 边界
- tool 调用输入输出 schema
- 单元测试或集成测试

## 目录约束

- `app/api/`：FastAPI 路由。
- `app/core/`：配置、日志、异常处理。
- `app/schemas/`：Pydantic schema。
- `app/rag/`：文档解析、切分、Embedding、向量库、检索。
- `app/tools/`：JD 分析、简历匹配、简历优化等工具。
- `app/agent/`：LangGraph Agent 状态、节点和工作流。
- `app/db/`：数据库模型和 repository。
- `frontend/`：Streamlit Demo。
- `tests/`：pytest 测试。
- `docs/`：系统设计文档。

## 配置与安全

- 非敏感配置写入 `config/app.yaml`。
- 敏感配置只通过 `.env` 或运行环境变量提供。
- `.env` 必须被 `.gitignore` 忽略。
- 不要在测试、文档、日志或示例代码中写入真实密钥。
- 提供示例配置时，应使用 `.env.example` 或文档中的占位值。

## 测试要求

- 新增功能必须添加或更新 pytest 测试。
- 测试应覆盖 schema 校验、核心 service/tool 行为、API route 行为。
- RAG、LLM、Qdrant、外部模型服务调用应优先使用 mock、fake 或测试替身。
- 测试不应依赖真实 API key。
- 测试不应要求外部网络可用，除非该测试被明确标记为集成测试并默认跳过。

## 代码组织要求

- route、schema、service/tool、repository、agent workflow 应分层清晰。
- 单个文件不应承载多个不相关职责。
- 公共逻辑应抽到清晰命名的模块中，但不要为了抽象而抽象。
- 错误处理应集中、可预期，并优先复用 `app/core/` 中的异常机制。
- 日志应避免输出简历原文、密钥、用户隐私和大段 Prompt。

## Codex 执行要求

- 修改前先阅读相关目录和现有实现风格。
- 只改动完成当前任务所必需的文件。
- 不要顺手重构无关代码。
- 不要覆盖用户已有改动。
- 涉及代码变更时，优先运行相关 pytest。
- 如果无法运行测试，必须在最终回复中说明原因。
