"""Tweet Brain API — FastAPI entry point."""

import logging
import time
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.api.groups import router as groups_router
from app.api.posts import router as posts_router
from app.api.settings import router as settings_router
from app.api.workflows import router as workflows_router
from app.config import settings
from app.services.credentials import resolve_credentials
from app.services.yaml_store import get_store

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

START_TIME = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s v%s", settings.service_name, settings.service_version)
    settings.database_root.mkdir(parents=True, exist_ok=True)
    settings.posts_dir.mkdir(parents=True, exist_ok=True)
    settings.runs_dir.mkdir(parents=True, exist_ok=True)
    get_store().ensure_default_groups()
    yield
    logger.info("Shutting down")


app = FastAPI(
    title="Tweet Brain API",
    description="Local-first X account tracking and Grok LLM workflows.",
    version=settings.service_version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_origin_regex=settings.cors_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_prefix = settings.api_v1_prefix
app.include_router(groups_router, prefix=api_prefix)
app.include_router(posts_router, prefix=api_prefix)
app.include_router(settings_router, prefix=api_prefix)
app.include_router(workflows_router, prefix=api_prefix)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    if response.status_code >= 400:
        logger.warning(
            "%s %s -> %s (%.0fms)",
            request.method,
            request.url.path,
            response.status_code,
            (time.time() - start) * 1000,
        )
    return response


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok", "service": settings.service_name}


@app.get("/version")
async def version() -> dict[str, Any]:
    creds = resolve_credentials(store=get_store())
    return {
        "service": settings.service_name,
        "version": settings.service_version,
        "environment": settings.environment,
        "uptime_seconds": int(time.time() - START_TIME),
        "x_api_configured": creds.x_configured(),
        "xai_configured": creds.xai_configured(),
    }
