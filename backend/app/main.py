from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from app.config import get_settings
from app.db import init_db
from app.routes.applications import router as applications_router
from app.routes.jobs import router as jobs_router
from app.routes.overview import router as overview_router
from app.routes.preferences import router as preferences_router
from app.routes.recommendations import router as recommendations_router
from app.routes.resumes import router as resumes_router
from app.routes.settings import router as settings_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app):
    init_db()
    yield


app = FastAPI(title="make-jobs-ai backend", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
def dashboard() -> HTMLResponse:
    dashboard_path = Path(__file__).parent / "static" / "dashboard.html"
    if dashboard_path.exists():
        return HTMLResponse(content=dashboard_path.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>Dashboard not found</h1>", status_code=404)


app.include_router(overview_router)
app.include_router(resumes_router)
app.include_router(jobs_router)
app.include_router(applications_router)
app.include_router(recommendations_router)
app.include_router(preferences_router)
app.include_router(settings_router)
