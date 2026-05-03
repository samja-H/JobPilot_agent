from __future__ import annotations

from fastapi import APIRouter

from app.api.health import router as health_router
from app.api.routes_applications import router as applications_router
from app.api.routes_docs import router as docs_router
from app.api.routes_interview import router as interview_router
from app.api.routes_jobs import router as jobs_router
from app.api.routes_resume import router as resume_router

api_router: APIRouter = APIRouter()
api_router.include_router(health_router)
api_router.include_router(applications_router)
api_router.include_router(docs_router)
api_router.include_router(jobs_router)
api_router.include_router(resume_router)
api_router.include_router(interview_router)
