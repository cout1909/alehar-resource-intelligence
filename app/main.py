import logging
from contextlib import asynccontextmanager
from threading import Lock

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker

from app.api.review_routes import router as review_router
from app.api.routes import router
from app.core.config import Settings, get_settings
from app.core.logging_config import configure_logging
from app.database.db import make_engine
from app.database.migrations import migrate_phase_two
from app.database.models import Base
from app.database.provenance import migrate_provenance
from app.seed.lenders import seed_lenders
from app.seed.public_snapshot import restore_public_snapshot
from app.services.scheduler import start_scheduler

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()

    @asynccontextmanager
    async def lifespan(application: FastAPI):
        configure_logging(settings.log_level)
        engine = make_engine(settings.database_url)
        application.state.session_factory = sessionmaker(engine, expire_on_commit=False)
        try:
            Base.metadata.create_all(engine)
            migrate_phase_two(engine)
            migrate_provenance(engine)
            with application.state.session_factory() as session:
                if settings.public_demo_snapshot:
                    restore_public_snapshot(session)
                else:
                    seed_lenders(session)
            logger.info("Alehar Resource Intelligence started (%s)", settings.app_env)
            application.state.scheduler = start_scheduler(application)
            yield
        finally:
            if application.state.scheduler is not None:
                application.state.scheduler.shutdown(wait=True)
                application.state.scheduler = None
            engine.dispose()

    application = FastAPI(
        title="Alehar Resource Intelligence API",
        description=(
            "Independent proof of concept. Checks public source identity "
            "using deterministic heuristics and optional Groq analysis. Not commissioned by Alehar. "
            "Results recommend human review; financial facts are not validated."
        ),
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.enable_docs else None,
        redoc_url="/redoc" if settings.enable_docs else None,
        openapi_url="/openapi.json" if settings.enable_docs else None,
    )
    application.state.settings = settings
    application.state.verification_lock = Lock()
    application.state.scheduler = None
    application.include_router(router)
    application.include_router(review_router)

    @application.middleware("http")
    async def public_demo_guard(request: Request, call_next):
        if settings.public_demo_mode and request.method not in {"GET", "HEAD", "OPTIONS"}:
            return JSONResponse(status_code=403, content={
                "detail": "This action is disabled in the public demo."})
        return await call_next(request)

    @application.exception_handler(Exception)
    async def unexpected_error(_request: Request, exc: Exception) -> JSONResponse:
        logger.error("Request failed (%s)", type(exc).__name__)
        return JSONResponse(status_code=500, content={"detail": "The request could not be completed."})

    @application.exception_handler(SQLAlchemyError)
    async def database_error(_request: Request, exc: SQLAlchemyError) -> JSONResponse:
        logger.error("Database operation failed", exc_info=(type(exc), exc, exc.__traceback__))
        return JSONResponse(
            status_code=503,
            content={"detail": "Database operation failed; inspect application logs"},
        )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    return application


app = create_app()
