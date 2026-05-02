# JobPilot-Agent Architecture

This project starts as a minimal FastAPI, Streamlit, Qdrant, and SQLite skeleton.

- FastAPI exposes backend APIs under `app/api/`.
- Streamlit provides the demo UI under `frontend/`.
- Qdrant is provided by Docker Compose for future RAG retrieval.
- SQLite is the MVP persistence target configured through `config/app.yaml`.

RAG, Agent workflows, and job analysis tools are intentionally not implemented in this skeleton.
