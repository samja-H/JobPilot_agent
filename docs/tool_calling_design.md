# Tool Calling 设计

## 目标

Tool Calling 用于把求职场景中的能力拆成可测试、可组合、可被 Agent 调用的工具。每个工具应有清晰输入、输出和边界，避免把复杂逻辑直接写入 Prompt 或 API route。

## 工具规划

MVP 阶段规划以下工具：

- `jd_analyzer`：分析岗位 JD，输出岗位画像。
- `resume_matcher`：对比 JD 与简历，输出匹配分和证据。
- `resume_optimizer`：给出面向岗位的简历优化建议。
- `interview_question_generator`：生成面试问题和追问方向。
- `application_tracker`：管理投递记录和状态。

工具白名单由 `config/app.yaml` 的 `agent.allowed_tools` 管理。

## 设计原则

- 工具输入输出必须有 Pydantic schema。
- 工具逻辑放在 `app/tools/`，不要写在 API route 中。
- 工具可以调用 RAG、LLM 或 repository，但依赖必须显式传入或集中管理。
- 工具返回结构化结果，避免只返回大段自然语言。
- Prompt 集中管理，避免散落在多个业务文件中。
- 每个工具必须有单元测试。

## 调用流程

```text
Agent / Service
 |
选择工具
 |
校验工具输入
 |
执行工具逻辑
 |
返回结构化工具结果
 |
Agent / Service 继续生成最终响应
```

## 单 Agent 约束

项目不实现多 Agent 架构。LangGraph 只用于组织一个 Agent 的状态、节点和工具调用流程，避免过早引入复杂协作模式。

## 示例输出形态

简历匹配工具后续可返回：

```json
{
  "score": 82,
  "matched_requirements": [],
  "missing_requirements": [],
  "evidence": [],
  "suggestions": []
}
```

实际字段以 `app/schemas/` 中定义为准。
