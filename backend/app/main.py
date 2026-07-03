from __future__ import annotations

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.documents import router as documents_router
from app.api.ocr import router as ocr_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.database.connection import init_db
from app.exceptions.handlers import register_exception_handlers
from app.middleware.request_id import RequestIdMiddleware

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info(
        "Startup OCR config OCR_ENGINE_URL=%s OCR_API_URL=%s",
        settings.OCR_ENGINE_URL or "<empty>",
        settings.OCR_API_URL or "<empty>",
    )
    app.state.settings = settings
    app.state.mongo_client = await init_db(settings)
    try:
        yield
    finally:
        app.state.mongo_client.close()


def create_app() -> FastAPI:
    settings = get_settings()
    configure_logging(settings.LOG_LEVEL)

    app = FastAPI(
        title=settings.APP_NAME,
        version="1.0.0",
        lifespan=lifespan,
    )
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.CORS_ALLOW_METHODS,
        allow_headers=settings.CORS_ALLOW_HEADERS,
    )
    register_exception_handlers(app)

    app.include_router(documents_router, prefix=settings.API_PREFIX)
    app.include_router(ocr_router)

    @app.get("/health", tags=["Health"])
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
