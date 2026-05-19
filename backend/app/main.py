"""FastAPI application factory."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import Base, engine
from app.core.logging import setup_logging
from app.middleware.error_handler import register_exception_handlers
from app.middleware.logging_middleware import LoggingMiddleware
from app.models import Lead  # noqa: F401 — ensure model is registered
from app.routes import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "AI-powered lead generation and outreach platform. "
            "Discovers local businesses, scores their online presence, "
            "and generates personalized outreach messages."
        ),
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Request logging
    app.add_middleware(LoggingMiddleware)

    # Exception handlers
    register_exception_handlers(app)

    # Routes
    app.include_router(api_router, prefix="/api/v1")

    return app


app = create_app()
