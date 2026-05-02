# AGENTS.md

## Project Goal

Build a minimal but production-style job-seeking AI Agent based on RAG and Tool Calling.

The system should help users:
- analyze job descriptions
- match resumes to jobs
- rewrite resume bullets
- generate interview questions
- manage application records

## Hard Constraints

1. Do not implement unrelated features.
2. Do not create duplicate modules.
3. Do not add new frameworks without explicit instruction.
4. Prefer simple, typed, testable Python code.
5. Every module must have a clear responsibility.
6. Do not put business logic inside API routes.
7. Do not put LLM prompts directly inside route handlers.
8. Do not write large monolithic files.
9. Do not add multi-agent architecture in MVP.
10. Do not implement browser automation or auto-apply features.

## Tech Stack

- Backend: FastAPI
- Agent orchestration: LangGraph / LangChain
- Vector database: Qdrant
- Database: SQLite for MVP
- Frontend: Streamlit
- Tests: pytest
- Deployment: Docker Compose

## Directory Rules

- API routes go to `app/api/`
- RAG logic goes to `app/rag/`
- Tool functions go to `app/tools/`
- Agent graph logic goes to `app/agent/`
- Database models and repositories go to `app/db/`
- Pydantic schemas go to `app/schemas/`
- Prompts go to `app/agent/prompts.py`
- Tests go to `tests/`

## Development Rules

For every new feature:
1. Define input and output schema first.
2. Implement business logic as a pure service/tool function.
3. Add API route only after the service works.
4. Add pytest tests.
5. Update README if user-facing behavior changes.

## Code Style

- Use type hints.
- Use Pydantic models for request/response schemas.
- Use dependency injection for services.
- Keep functions under 80 lines when possible.
- Prefer explicit error handling.
- Use structured logging.