from __future__ import annotations

from fastapi import APIRouter

from app.api.health import router as health_router
from app.api.routes_docs import router as docs_router

api_router: APIRouter = APIRouter()
api_router.include_router(health_router)
api_router.include_router(docs_router)
